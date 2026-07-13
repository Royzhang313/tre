"""Auth 模块 —— Service 层（业务逻辑）

3 个 Service:
- AuthService: 登录、JWT、密码验证
- UserService: 用户 CRUD、状态变更、角色分配
- RoleService: 角色 CRUD、权限分配
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.core.events import DomainEvent, event_bus
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.modules.auth.models import Role, RolePermission, User, UserRole, UserStatus
from app.modules.auth.repository import PermissionRepository, RoleRepository, UserRepository
from app.modules.auth.schemas import (
    AssignRolesRequest,
    LoginResponse,
    RoleCreate,
    UserCreate,
    UserMeResponse,
    UserUpdate,
)
from app.shared.security import JWTTokenManager, PasswordHasher


@dataclass(frozen=True, slots=True, kw_only=True)
class UserCreated(DomainEvent):
    """用户创建事件"""
    user_id: UUID
    username: str


@dataclass(frozen=True, slots=True, kw_only=True)
class UserLoggedIn(DomainEvent):
    """用户登录事件"""
    user_id: UUID
    username: str


@dataclass(frozen=True, slots=True, kw_only=True)
class UserStatusChanged(DomainEvent):
    """用户状态变更事件"""
    user_id: UUID
    old_status: str
    new_status: str


@dataclass(frozen=True, slots=True, kw_only=True)
class RoleAssigned(DomainEvent):
    """角色分配给用户事件"""
    user_id: UUID
    role_ids: list[UUID]


@dataclass(frozen=True, slots=True, kw_only=True)
class RoleRevoked(DomainEvent):
    """角色从用户移除事件"""
    user_id: UUID
    role_id: UUID


# ============================================================
# AuthService
# ============================================================


class AuthService:
    """认证服务 —— 登录"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    # ---------- 登录 ----------

    async def login(self, username: str, password: str) -> LoginResponse:
        """登录 —— 支持用户名或手机号

        Raises:
            UnauthorizedError: 用户名或密码错误 / 用户已停用
        """
        user = await self.user_repo.get_by_username(username)
        # 也尝试手机号登录
        if user is None:
            user = await self.user_repo.get_by_phone(username)

        if user is None:
            raise UnauthorizedError("用户名或密码错误")

        if not PasswordHasher.verify(password, user.password_hash):
            raise UnauthorizedError("用户名或密码错误")

        # 状态检查
        if user.status == UserStatus.INACTIVE:
            raise UnauthorizedError("用户已停用，请联系管理员")
        if user.status == UserStatus.LOCKED:
            raise UnauthorizedError("用户已锁定，请联系管理员")

        # 更新最后登录时间
        user.last_login_at = datetime.now(UTC)
        await self.user_repo.update(user)

        # 生成 token
        access_token = JWTTokenManager.create_token(user.id, user.username)

        # 发布事件
        await event_bus.publish(UserLoggedIn(user_id=user.id, username=user.username))

        # 加载角色和权限（复用当前 session）
        from app.modules.auth.repository import RoleRepository, PermissionRepository
        role_repo = RoleRepository(self.user_repo.session)
        perm_repo = PermissionRepository(self.user_repo.session)
        try:
            roles = await role_repo.list_by_user_id(user.id)
        except Exception:
            roles = []
        try:
            permissions = await perm_repo.list_by_user_id(user.id)
            if 'admin' in [r.code for r in roles]:
                all_perms = await perm_repo.list(offset=0, limit=500)
                permissions = all_perms
        except Exception:
            permissions = []

        # 构建响应
        user_info = UserMeResponse(
            id=user.id,
            username=user.username,
            phone=user.phone,
            email=user.email,
            display_name=user.display_name,
            status=user.status,
            roles=[r.code for r in roles],
            permissions=[p.code for p in permissions],
        )
        return LoginResponse(access_token=access_token, user=user_info)


# ============================================================
# UserService
# ============================================================


class UserService:
    """用户服务 —— CRUD、状态变更、角色分配"""

    def __init__(self, user_repo: UserRepository, role_repo: RoleRepository):
        self.user_repo = user_repo
        self.role_repo = role_repo

    # ---------- 创建 ----------

    async def create_user(self, data: UserCreate) -> User:
        """创建用户 —— 校验唯一性、哈希密码、可选初始角色"""
        if await self.user_repo.get_by_username(data.username):
            raise ConflictError("用户名已存在", entity="User")
        if data.phone and await self.user_repo.get_by_phone(data.phone):
            raise ConflictError("手机号已存在", entity="User")
        if data.email and await self.user_repo.get_by_email(data.email):
            raise ConflictError("邮箱已存在", entity="User")

        user = User(
            username=data.username,
            phone=data.phone or None,
            email=data.email or f"{data.username}@local",
            password_hash=PasswordHasher.hash(data.password),
            display_name=data.display_name or data.username,
        )
        await self.user_repo.create(user)

        # 创建时分配角色
        if data.role_ids:
            for rid in data.role_ids:
                if await self.role_repo.exists(rid):
                    user.user_roles.append(UserRole(user_id=user.id, role_id=rid))
            await self.user_repo.update(user)

        await event_bus.publish(UserCreated(user_id=user.id, username=user.username))
        return user

    # ---------- 更新 ----------

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        """更新用户资料"""
        user = await self.user_repo.get_by_id_or_raise(user_id)

        if data.email is not None and data.email != user.email:
            if await self.user_repo.get_by_email(data.email):
                raise ConflictError("邮箱已存在", entity="User")
            user.email = data.email

        if data.display_name is not None:
            user.display_name = data.display_name

        await self.user_repo.update(user)
        return user

    # ---------- 状态变更 ----------

    async def change_status(
        self, user_id: UUID, new_status: UserStatus, *, operator_id: UUID
    ) -> User:
        """变更用户状态 —— 禁止操作自己"""
        if user_id == operator_id:
            raise ConflictError("不能修改自己的状态")

        user = await self.user_repo.get_by_id_or_raise(user_id)
        old_status = user.status

        if old_status == new_status:
            return user

        user.status = new_status
        await self.user_repo.update(user)

        await event_bus.publish(UserStatusChanged(
            user_id=user.id,
            old_status=str(old_status),
            new_status=str(new_status),
        ))
        return user

    # ---------- 角色分配 ----------

    async def assign_roles(
        self, user_id: UUID, data: AssignRolesRequest, *, operator_id: UUID
    ) -> User:
        """为用户分配角色 —— 替换式（先清空再设置）"""
        user = await self.user_repo.get_by_id_or_raise(user_id)

        # 验证所有角色存在
        for role_id in data.role_ids:
            if not await self.role_repo.exists(role_id):
                raise NotFoundError("角色不存在", entity="Role", entity_id=role_id)

        # 清空现有角色
        user.user_roles.clear()

        # 设置新角色
        for role_id in data.role_ids:
            user.user_roles.append(UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=operator_id,
                assigned_at=datetime.now(UTC),
            ))

        await self.user_repo.update(user)

        await event_bus.publish(RoleAssigned(user_id=user.id, role_ids=data.role_ids))
        return user

    async def delete_user(self, user_id: UUID) -> None:
        """停用用户（软删除）"""
        user = await self.user_repo.get_by_id_or_raise(user_id)
        user.status = UserStatus.INACTIVE
        await self.user_repo.update(user)


# ============================================================
# RoleService
# ============================================================


class RoleService:
    """角色服务 —— CRUD、权限分配"""

    def __init__(self, role_repo: RoleRepository, perm_repo: PermissionRepository):
        self.role_repo = role_repo
        self.perm_repo = perm_repo

    # ---------- 创建 ----------

    async def create_role(self, data: RoleCreate):
        """创建角色"""
        if await self.role_repo.get_by_code(data.code):
            raise ConflictError("角色编码已存在", entity="Role")

        role = Role(code=data.code, name=data.name, description=data.description)
        await self.role_repo.create(role)
        return role

    # ---------- 删除 ----------

    async def delete_role(self, role_id: UUID) -> None:
        """删除角色 —— 禁止删除系统角色"""
        role = await self.role_repo.get_by_id_or_raise(role_id)

        if role.is_system:
            raise ConflictError(f"系统内置角色 '{role.code}' 不可删除", entity="Role")

        await self.role_repo.delete(role)

    # ---------- 权限分配 ----------

    async def assign_permissions(self, role_id: UUID, permission_ids: list[UUID]):
        """为角色分配权限 —— 替换式"""
        role = await self.role_repo.get_by_id_or_raise(role_id)

        for perm_id in permission_ids:
            if not await self.perm_repo.exists(perm_id):
                raise NotFoundError("权限不存在", entity="Permission", entity_id=perm_id)

        role.role_permissions.clear()

        for perm_id in permission_ids:
            role.role_permissions.append(RolePermission(
                role_id=role_id,
                permission_id=perm_id,
            ))

        await self.role_repo.update(role)
        return role

    async def revoke_permission(self, role_id: UUID, permission_id: UUID) -> None:
        """移除角色的单个权限"""
        role = await self.role_repo.get_by_id_or_raise(role_id)
        role.role_permissions = [
            rp for rp in role.role_permissions
            if rp.permission_id != permission_id
        ]
        await self.role_repo.update(role)
