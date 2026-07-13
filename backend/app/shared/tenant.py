"""SaaS 多租户 Mixin

提供 TenantMixin —— 所有需要租户隔离的业务模型都应组合此 Mixin。

设计决策：
- tenant_id 使用 UUID 类型（与现有代码一致）
- tenant_id 在创建时由应用层注入，不可为空
- 索引自动创建（用于查询加速）

使用示例::

    from app.shared.tenant import TenantMixin

    class Enterprise(BaseModel, TenantMixin):
        __tablename__ = "basedata_enterprises"
        name: Mapped[str]
"""

from uuid import UUID

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column


class TenantMixin:
    """多租户隔离 Mixin

    所有业务数据表必须包含 tenant_id 字段，实现行级数据隔离。
    查询时强制添加 WHERE tenant_id = ? 条件。

    Note:
        - Auth 模块（User/Role/Permission）属于平台级，不使用此 Mixin
        - 租户间数据完全隔离，不可跨租户访问
    """

    tenant_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
        comment="租户ID（SaaS 多租户隔离字段）",
    )

    # SQLAlchemy 2.0 推荐使用 __table_args__ 来创建命名索引
    # 但 mapped_column(index=True) 会自动创建匿名索引，足够使用
