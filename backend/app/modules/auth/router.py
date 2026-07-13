"""Auth 模块 —— FastAPI Router

Router 只负责 HTTP 层：参数解析 → Service 调用 → 响应包装。
不包含业务逻辑。
"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import async_session_factory
from app.modules.auth.context import CurrentUser
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.repository import PermissionRepository, RoleRepository, UserRepository
from app.modules.auth.schemas import (
    AssignRolesRequest,
    LoginRequest,
    RoleCreate,
    UserCreate,
    UserMeResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.modules.auth.service import AuthService, RoleService, UserService
from app.shared.base_schema import APIResponse, PageResponse

router = APIRouter(prefix="/auth", tags=["认证与授权"])


# ============================================================
# 依赖 —— 获取 Service 实例
# ============================================================


async def _get_auth_service() -> AsyncGenerator[AuthService, None]:
    async with async_session_factory() as session:
        yield AuthService(user_repo=UserRepository(session))


async def _get_user_service() -> AsyncGenerator[UserService, None]:
    async with async_session_factory() as session:
        yield UserService(
            user_repo=UserRepository(session),
            role_repo=RoleRepository(session),
        )
        await session.commit()


async def _get_role_service() -> AsyncGenerator[RoleService, None]:
    async with async_session_factory() as session:
        yield RoleService(
            role_repo=RoleRepository(session),
            perm_repo=PermissionRepository(session),
        )
        await session.commit()


# ============================================================
# 登录限流
# ============================================================

import time
from collections import defaultdict

_login_attempts: dict[str, list[float]] = defaultdict(list)
_LOGIN_MAX_ATTEMPTS = 5       # 每分钟最多尝试次数
_LOGIN_WINDOW_SECONDS = 60    # 限流窗口


def _check_login_rate(identifier: str) -> bool:
    """检查登录频率，超限返回 False"""
    now = time.time()
    window_start = now - _LOGIN_WINDOW_SECONDS
    attempts = [t for t in _login_attempts[identifier] if t > window_start]
    _login_attempts[identifier] = attempts
    if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
        return False
    _login_attempts[identifier].append(now)
    return True


# ============================================================
# 认证
# ============================================================


@router.post("/login", response_model=APIResponse[dict])
async def login(
    body: LoginRequest,
    svc: AuthService = Depends(_get_auth_service),
):
    """登录（限流: 每60秒最多5次）"""
    if not _check_login_rate(body.username):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=429, content={"code": 429, "message": "登录过于频繁，请稍后再试"})
    result = await svc.login(body.username, body.password)
    return APIResponse.ok(result.model_dump())


@router.get("/me", response_model=APIResponse[dict])
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
):
    """当前用户信息 —— 直接从 CurrentUser 获取，零 DB 查询"""
    user_info = UserMeResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name,
        status=current_user.status,
        roles=list(current_user.role_codes),
        permissions=list(current_user.permission_codes),
    )
    return APIResponse.ok(user_info.model_dump())


# ============================================================
# 用户管理
# ============================================================


@router.post("/users", response_model=APIResponse[dict])
async def create_user(
    body: UserCreate,
    svc: UserService = Depends(_get_user_service),
    _: None = Depends(require_permission("auth.user.create")),
):
    """创建用户"""
    user = await svc.create_user(body)
    return APIResponse.ok({
        "id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
    })


@router.get("/users", response_model=APIResponse[dict])
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: str | None = Query(default=None),
    _: None = Depends(require_permission("auth.user.read")),
):
    """用户列表，可按角色筛选"""
    async with async_session_factory() as session:
        repo = UserRepository(session)
        if role:
            users = await repo.list_by_role(role, offset=(page - 1) * page_size, limit=page_size)
            total = await repo.count_by_role(role)
        else:
            users = await repo.list(offset=(page - 1) * page_size, limit=page_size)
            total = await repo.count()

    items = [
        {
            "id": str(u.id),
            "username": u.username,
            "phone": u.phone,
            "email": u.email,
            "display_name": u.display_name,
            "status": str(u.status),
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]
    return APIResponse.ok(PageResponse.from_list(items, total, page, page_size).model_dump())


@router.get("/users/{user_id}", response_model=APIResponse[dict])
async def get_user(
    user_id: UUID,
    _: None = Depends(require_permission("auth.user.read")),
):
    """用户详情"""
    async with async_session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_by_id_or_raise(user_id)
        role_repo = RoleRepository(session)
        roles = await role_repo.list_by_user_id(user.id)

    return APIResponse.ok({
        "id": str(user.id),
        "username": user.username,
        "phone": user.phone,
        "email": user.email,
        "display_name": user.display_name,
        "status": str(user.status),
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "roles": [{"id": str(r.id), "code": r.code, "name": r.name} for r in roles],
    })


@router.patch("/users/{user_id}", response_model=APIResponse[dict])
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    svc: UserService = Depends(_get_user_service),
    _: None = Depends(require_permission("auth.user.update")),
):
    """更新用户资料"""
    user = await svc.update_user(user_id, body)
    return APIResponse.ok({
        "id": str(user.id),
        "phone": user.phone,
        "display_name": user.display_name,
        "email": user.email,
    })


@router.patch("/users/{user_id}/status", response_model=APIResponse[dict])
async def change_user_status(
    user_id: UUID,
    body: UserStatusUpdate,
    svc: UserService = Depends(_get_user_service),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("auth.user.update")),
):
    """变更用户状态（停用/启用）"""
    user = await svc.change_status(user_id, body.status, operator_id=current_user.id)
    return APIResponse.ok({"id": str(user.id), "status": str(user.status)})


@router.patch("/users/{user_id}/roles", response_model=APIResponse[dict])
async def assign_user_roles(
    user_id: UUID,
    body: AssignRolesRequest,
    svc: UserService = Depends(_get_user_service),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_permission("auth.role.manage")),
):
    """分配用户角色"""
    user = await svc.assign_roles(user_id, body, operator_id=current_user.id)
    role_ids = [str(r.role_id) for r in user.user_roles]
    return APIResponse.ok({"id": str(user.id), "role_ids": role_ids})


@router.delete("/users/{user_id}", response_model=APIResponse[dict])
async def delete_user(
    user_id: UUID,
    svc: UserService = Depends(_get_user_service),
    _: None = Depends(require_permission("auth.user.delete")),
):
    """删除用户"""
    await svc.delete_user(user_id)
    return APIResponse.ok(None, message="用户已删除")


# ============================================================
# 角色管理
# ============================================================


@router.post("/roles", response_model=APIResponse[dict])
async def create_role(
    body: RoleCreate,
    svc: RoleService = Depends(_get_role_service),
    _: None = Depends(require_permission("auth.role.manage")),
):
    """创建角色"""
    role = await svc.create_role(body)
    return APIResponse.ok({"id": str(role.id), "code": role.code, "name": role.name})


@router.get("/roles", response_model=APIResponse[dict])
async def list_roles(
    _: None = Depends(require_permission("auth.role.manage")),
):
    """角色列表"""
    async with async_session_factory() as session:
        repo = RoleRepository(session)
        roles = await repo.list(offset=0, limit=100)

    return APIResponse.ok({
        "items": [
            {"id": str(r.id), "code": r.code, "name": r.name, "description": r.description, "is_system": r.is_system}
            for r in roles
        ]
    })


@router.get("/roles/{role_id}", response_model=APIResponse[dict])
async def get_role(
    role_id: UUID,
    _: None = Depends(require_permission("auth.role.manage")),
):
    """角色详情（含权限）"""
    async with async_session_factory() as session:
        repo = RoleRepository(session)
        role = await repo.get_by_id_or_raise(role_id)
        perm_repo = PermissionRepository(session)
        perms = await perm_repo.list_by_role_id(role_id)

    return APIResponse.ok({
        "id": str(role.id), "code": role.code, "name": role.name,
        "description": role.description, "is_system": role.is_system,
        "permissions": [{"id": str(p.id), "code": p.code, "name": p.name} for p in perms],
    })


@router.patch("/roles/{role_id}", response_model=APIResponse[dict])
async def update_role(
    role_id: UUID,
    body: dict,
    svc: RoleService = Depends(_get_role_service),
    _: None = Depends(require_permission("auth.role.manage")),
):
    """更新角色名称和描述"""
    async with async_session_factory() as session:
        repo = RoleRepository(session)
        role = await repo.get_by_id_or_raise(role_id)
        if "name" in body:
            role.name = body["name"]
        if "description" in body:
            role.description = body["description"]
        await repo.update(role)
        await session.commit()
    return APIResponse.ok({"id": str(role.id), "name": role.name, "description": role.description})


@router.patch("/roles/{role_id}/permissions", response_model=APIResponse[dict])
async def assign_role_permissions(
    role_id: UUID,
    body: dict,
    svc: RoleService = Depends(_get_role_service),
    _: None = Depends(require_permission("auth.role.manage")),
):
    """分配角色权限 —— body: {permission_ids: [...]}"""
    perm_ids = [UUID(pid) for pid in body.get("permission_ids", [])]
    await svc.assign_permissions(role_id, perm_ids)
    return APIResponse.ok(None, message="权限已更新")


@router.delete("/roles/{role_id}", response_model=APIResponse[dict])
async def delete_role(
    role_id: UUID,
    svc: RoleService = Depends(_get_role_service),
    _: None = Depends(require_permission("auth.role.manage")),
):
    """删除角色"""
    await svc.delete_role(role_id)
    return APIResponse.ok(None, message="角色已删除")


# ============================================================
# 权限管理
# ============================================================


@router.get("/permissions", response_model=APIResponse[dict])
async def list_permissions(
    _: None = Depends(require_permission("auth.role.manage")),
):
    """权限列表"""
    async with async_session_factory() as session:
        repo = PermissionRepository(session)
        perms = await repo.list(offset=0, limit=200)

    return APIResponse.ok({
        "items": [
            {
                "id": str(p.id), "code": p.code, "name": p.name,
                "module": p.module, "resource": p.resource, "action": p.action,
            }
            for p in perms
        ]
    })
