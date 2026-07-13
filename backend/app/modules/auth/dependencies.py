"""Auth 模块 —— FastAPI 依赖注入"""

import os
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import async_session_factory
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.modules.auth.context import CurrentUser
from app.modules.auth.repository import PermissionRepository, RoleRepository, UserRepository
from app.shared.security import JWTTokenManager

_bearer = HTTPBearer(auto_error=False)

# 仅 DEBUG 模式下允许无 Token 访问
_DEBUG = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None:
        if _DEBUG:
            # 开发模式：无 token 时以超级管理员身份运行
            from uuid import uuid4
            from app.modules.auth.models import UserStatus
            return CurrentUser(
                id=uuid4(),
                username="dev_admin",
                email="admin@erp.local",
                display_name="开发管理员",
                status=UserStatus.ACTIVE,
                role_codes=frozenset(["admin"]),
                permission_codes=frozenset(["*"]),
            )
        raise UnauthorizedError("未提供认证令牌")

    payload = JWTTokenManager.verify(credentials.credentials)
    user_id = UUID(payload["sub"])  # JWT sub 是字符串，转 UUID

    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("用户不存在或已删除")

        role_repo = RoleRepository(session)
        perm_repo = PermissionRepository(session)

        try:
            roles = await role_repo.list_by_user_id(user.id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("加载用户角色失败 user_id=%s: %s", user.id, e)
            roles = []

        try:
            permissions = await perm_repo.list_by_user_id(user.id)
            # admin 角色拥有所有权限
            if 'admin' in [r.code for r in roles]:
                permissions = await perm_repo.list(offset=0, limit=500)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("加载用户权限失败 user_id=%s: %s", user.id, e)
            permissions = []

    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        status=user.status,
        role_codes=frozenset(r.code for r in roles),
        permission_codes=frozenset(p.code for p in permissions),
    )


def require_permission(permission_code: str):
    """权限检查依赖工厂 —— 基于 CurrentUser 内存检查，零 DB 查询

    使用示例::

        @router.post("/users")
        async def create_user(
            current_user: CurrentUser = Depends(get_current_user),
            _: None = Depends(require_permission("auth.user.create")),
        ):
            ...
    """

    def checker(current_user: CurrentUser = Depends(get_current_user)) -> None:
        if not current_user.is_active():
            raise ForbiddenError("用户已被停用，无法执行操作")
        # 开发模式通配符 "*" 拥有所有权限
        if "*" in current_user.permission_codes:
            return
        if not current_user.has_permission(permission_code):
            raise ForbiddenError(f"无权限执行此操作: {permission_code}")

    return checker
