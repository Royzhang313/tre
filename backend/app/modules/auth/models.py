"""Auth 模块 —— ORM 数据模型

5 张表:
- User (聚合根)
- Role (聚合根)
- Permission (聚合根)
- UserRole (关联)
- RolePermission (关联)
"""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class UserStatus(enum.StrEnum):
    """用户状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class User(BaseModel):
    """用户（聚合根）"""

    __tablename__ = "auth_users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, comment="手机号，可用于登录")
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=True, default=None)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"),
        nullable=False,
        default=UserStatus.ACTIVE,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    # 关联
    # foreign_keys 必须指定：UserRole 有两个 FK 指向 auth_users（user_id + assigned_by）
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        foreign_keys="UserRole.user_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Role(BaseModel):
    """角色（聚合根）"""

    __tablename__ = "auth_roles"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")

    # 关联
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Role {self.code}>"


class Permission(BaseModel):
    """权限（独立聚合根 —— 不依附于 Role，可单独 CRUD）"""

    __tablename__ = "auth_permissions"

    code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # 关联
    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"


class UserRole(BaseModel):
    """用户-角色关联"""

    __tablename__ = "auth_user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_roles.id", ondelete="CASCADE"), primary_key=True
    )
    assigned_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=lambda: datetime.now(),
        server_default=func.now(),
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles", foreign_keys=[role_id])

    def __repr__(self) -> str:
        return f"<UserRole user={self.user_id} role={self.role_id}>"


class RolePermission(BaseModel):
    """角色-权限关联"""

    __tablename__ = "auth_role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_permissions.id", ondelete="CASCADE"), primary_key=True
    )

    # 关系
    role: Mapped["Role"] = relationship(
        "Role", back_populates="role_permissions", foreign_keys=[role_id]
    )
    permission: Mapped["Permission"] = relationship(
        "Permission", back_populates="role_permissions", foreign_keys=[permission_id]
    )

    def __repr__(self) -> str:
        return f"<RolePermission role={self.role_id} perm={self.permission_id}>"
