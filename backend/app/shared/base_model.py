"""ORM 基础模型

提供 Mixin 和组合好的 BaseModel：
- UUIDPrimaryKey: UUID 主键
- TimestampMixin: created_at / updated_at 自动维护
- SoftDeleteMixin: 软删除（deleted_at）
- VersionMixin: 乐观锁（version）
- BaseModel: UUIDPrimaryKey + TimestampMixin

所有业务模块的 ORM 模型继承 BaseModel，按需组合 Mixin。

使用示例::

    class Product(BaseModel, SoftDeleteMixin, VersionMixin):
        __tablename__ = "products"
        name: Mapped[str]
"""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

#: UUID 主键类型注解（带默认 uuid4）
pk_uuid = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]

#: 时间戳类型注解（不带时区，推荐业务层统一使用 UTC）
timestamp_ntz = Annotated[datetime, mapped_column(DateTime(timezone=False))]


class UUIDPrimaryKey:
    """UUID v4 主键 Mixin"""

    id: Mapped[pk_uuid]


class TimestampMixin:
    """自动时间戳 Mixin —— created_at 不可变，updated_at 每次 flush 自动更新"""

    created_at: Mapped[timestamp_ntz] = mapped_column(
        DateTime(timezone=False),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[timestamp_ntz] = mapped_column(
        DateTime(timezone=False),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class SoftDeleteMixin:
    """软删除 Mixin —— 删除时设置 deleted_at 而非物理删除

    模块按需组合，不强制所有实体使用。::

        class Product(BaseModel, SoftDeleteMixin):
            __tablename__ = "products"
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        default=None,
        server_default=None,
        nullable=True,
    )

    @property
    def is_deleted(self) -> bool:
        """是否已被软删除"""
        return self.deleted_at is not None


class VersionMixin:
    """乐观锁 Mixin —— version 字段每次更新自动 +1

    模块按需组合，用于需要并发控制的实体。::

        class Product(BaseModel, VersionMixin):
            __tablename__ = "products"
    """

    version: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )


class BaseModel(Base, UUIDPrimaryKey, TimestampMixin):
    """所有 ORM 模型的抽象基类

    使用示例::

        class Product(BaseModel):
            __tablename__ = "products"
            name: Mapped[str]

    如需软删除和乐观锁::

        class Product(BaseModel, SoftDeleteMixin, VersionMixin):
            __tablename__ = "products"
    """

    __abstract__ = True
