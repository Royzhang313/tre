"""Auth 模块 —— Repository 层

继承 BaseRepository，仅增加领域特有查询方法。
不重复 CRUD（由 BaseRepository 提供）。
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Permission, Role, RolePermission, User, UserRole
from app.shared.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户仓储"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session, entity_name="用户")

    async def get_by_username(self, username: str) -> User | None:
        """按用户名查询"""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """按邮箱查询"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        """按手机号查询"""
        stmt = select(User).where(User.phone == phone)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_role(self, role_code: str, offset: int = 0, limit: int = 100) -> list[User]:
        """按角色编码筛选用户"""
        from app.modules.auth.models import Role
        stmt = (
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.code == role_code)
            .order_by(User.created_at.desc())
            .offset(offset).limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_role(self, role_code: str) -> int:
        """按角色统计用户数"""
        from sqlalchemy import func
        from app.modules.auth.models import Role
        stmt = (
            select(func.count())
            .select_from(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.code == role_code)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class RoleRepository(BaseRepository[Role]):
    """角色仓储"""

    def __init__(self, session: AsyncSession):
        super().__init__(Role, session, entity_name="角色")

    async def get_by_code(self, code: str) -> Role | None:
        """按编码查询"""
        stmt = select(Role).where(Role.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user_id(self, user_id: UUID) -> list[Role]:
        """查询用户的所有角色 —— JOIN 方式，避免 ORM relationship lazy load"""
        stmt = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PermissionRepository(BaseRepository[Permission]):
    """权限仓储"""

    def __init__(self, session: AsyncSession):
        super().__init__(Permission, session, entity_name="权限")

    async def get_by_code(self, code: str) -> Permission | None:
        """按编码查询"""
        stmt = select(Permission).where(Permission.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_module(self, module: str) -> list[Permission]:
        """按模块列出权限"""
        return await self.list(filters=(Permission.module == module,))

    async def list_by_user_id(self, user_id: UUID) -> list[Permission]:
        """查询用户的所有权限 —— JOIN 方式，避免 ORM relationship lazy load"""
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_role_id(self, role_id: UUID) -> list[Permission]:
        """查询角色的所有权限"""
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
