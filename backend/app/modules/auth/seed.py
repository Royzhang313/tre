"""Auth 模块 —— 数据初始化（Seed）

首次启动时自动创建默认角色、权限和管理员账户。
管理员密码通过环境变量 ERP_ADMIN_PASSWORD 设置。
"""

import logging
import os
from datetime import UTC

from app.core.database import async_session_factory
from app.modules.auth.models import Permission, Role, RolePermission, User, UserRole
from app.shared.security import PasswordHasher

logger = logging.getLogger(__name__)

# ============================================================
# 默认数据定义
# ============================================================

DEFAULT_ROLES = [
    {"code": "admin", "name": "系统管理员", "is_system": True},
    {"code": "manager", "name": "经理", "is_system": True},
    {"code": "operator", "name": "操作员", "is_system": True},
]

def _perm(code: str, name: str, module: str, resource: str, action: str) -> dict:
    return {"code": code, "name": name, "module": module, "resource": resource, "action": action}


def _perms(prefix: str, resources: list[str], actions: list[str]) -> list[dict]:
    """批量生成权限: basedata.{resource}.{action}"""
    result = []
    for resource in resources:
        for action in actions:
            code = f"{prefix}.{resource}.{action}"
            name = f"{resource}-{action}"
            result.append(_perm(code, name, prefix, resource, action))
    return result


DEFAULT_PERMISSIONS = [
    # Auth
    _perm("auth.user.create", "创建用户", "auth", "user", "create"),
    _perm("auth.user.read", "查看用户", "auth", "user", "read"),
    _perm("auth.user.update", "更新用户", "auth", "user", "update"),
    _perm("auth.user.delete", "删除用户", "auth", "user", "delete"),
    _perm("auth.role.manage", "管理角色和权限", "auth", "role", "manage"),
    # BaseData（企业/物料/仓库）
    *_perms("basedata", ["enterprise", "product", "warehouse"], ["create", "read", "update", "delete"]),
    # Purchase Contract（采购合同）
    *_perms("purchase-contract", ["contract"], ["create", "read", "update", "delete"]),
]

# admin 角色拥有所有权限
ADMIN_PERMISSION_CODES = [p["code"] for p in DEFAULT_PERMISSIONS]


class SeedManager:
    """数据初始化管理器 —— 幂等（重复执行不报错）"""

    @staticmethod
    async def run() -> None:
        """执行所有 Seed"""
        async with async_session_factory() as session:
            await SeedManager._seed_permissions(session)
            await SeedManager._seed_roles(session)
            await SeedManager._seed_role_permissions(session)
            await SeedManager._seed_admin_user(session)
            await session.commit()

    # ---------- 权限 ----------

    @staticmethod
    async def _seed_permissions(session) -> None:
        from sqlalchemy import select

        for data in DEFAULT_PERMISSIONS:
            stmt = select(Permission).where(Permission.code == data["code"])
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                session.add(Permission(**data))
                logger.info("Seed: 创建权限 %s", data["code"])

    # ---------- 角色 ----------

    @staticmethod
    async def _seed_roles(session) -> None:
        from sqlalchemy import select

        for data in DEFAULT_ROLES:
            stmt = select(Role).where(Role.code == data["code"])
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                session.add(Role(**data))
                logger.info("Seed: 创建角色 %s", data["code"])

    # ---------- 角色-权限关联 ----------

    @staticmethod
    async def _seed_role_permissions(session) -> None:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # 获取 admin 角色（eager load role_permissions）
        stmt = (
            select(Role)
            .where(Role.code == "admin")
            .options(selectinload(Role.role_permissions))
        )
        result = await session.execute(stmt)
        admin_role = result.scalar_one_or_none()
        if admin_role is None:
            return

        # 获取所有权限
        stmt = select(Permission)
        result = await session.execute(stmt)
        all_perms = result.scalars().all()

        # 为 admin 分配所有权限（幂等）
        existing = {
            rp.permission_id
            for rp in admin_role.role_permissions
        }
        for perm in all_perms:
            if perm.id not in existing:
                session.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
                logger.info("Seed: admin 角色获得权限 %s", perm.code)

    # ---------- 管理员账户 ----------

    @staticmethod
    async def _seed_admin_user(session) -> None:
        from sqlalchemy import select

        admin_password = os.getenv("ERP_ADMIN_PASSWORD")
        if not admin_password:
            logger.warning(
                "Seed: ERP_ADMIN_PASSWORD 未设置，跳过管理员创建。"
                "请设置环境变量后重启。"
            )
            return

        admin_username = os.getenv("ERP_ADMIN_USERNAME", "admin")
        admin_email = os.getenv("ERP_ADMIN_EMAIL", "admin@erp.local")

        # 检查是否已存在
        stmt = select(User).where(User.username == admin_username)
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            logger.info("Seed: 管理员 %s 已存在，跳过", admin_username)
            return

        # 创建管理员
        admin = User(
            username=admin_username,
            email=admin_email,
            password_hash=PasswordHasher.hash(admin_password),
            display_name="系统管理员",
        )
        session.add(admin)
        await session.flush()

        # 分配 admin 角色
        role_stmt = select(Role).where(Role.code == "admin")
        role_result = await session.execute(role_stmt)
        admin_role = role_result.scalar_one_or_none()

        if admin_role:
            from datetime import datetime
            session.add(UserRole(
                user_id=admin.id,
                role_id=admin_role.id,
                assigned_at=datetime.now(UTC),
            ))

        logger.info("Seed: 创建管理员 %s", admin_username)
