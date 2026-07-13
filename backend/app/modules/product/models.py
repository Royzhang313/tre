"""产品模块 —— ORM 模型（MVP 简化版）

产品 = 品牌 + 型号 的合并实体，用于快速验证业务流程。
后续可演进为 Brand + BrandModel + BrandWarehouse 体系。
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class Product(BaseModel):
    """产品（PET 瓶片贸易商品）

    将 Brand + BrandModel 合并为单一实体，简化 MVP 数据模型。
    合同明细中可引用此产品，替代同时引用 brand_id + model_id。
    """

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_code", name="uq_product_code"),
    )

    tenant_id: Mapped[UUID] = mapped_column(nullable=False, default=None)
    product_code: Mapped[str] = mapped_column(String(30), nullable=False, comment="产品编码（自动生成: PRD-{seq}）")
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="产品名称")
    brand_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="品牌名称")
    model_type: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="型号类型: 热料/冷料/蓝白片等")
    warehouse_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="默认发货仓库")
    unit: Mapped[str] = mapped_column(String(10), default="吨", server_default="吨", comment="计量单位")
    default_purchase_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0", comment="默认采购单价")
    default_sale_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0", comment="默认销售单价")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="产品描述")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true", comment="是否启用")

    def __repr__(self) -> str:
        return f"<Product {self.product_code} {self.name}>"
