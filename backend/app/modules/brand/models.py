"""品牌模块 —— ORM 模型（SaaS 多租户版）

品牌/型号/品牌仓库均按租户隔离。
应用层查重时排除软删除数据。

独立模块设计：
- Brand 不并入 BaseData，保持独立 CRUD
- 采购/销售/产品均可引用 Brand
"""

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel
from app.shared.tenant import TenantMixin


class Brand(BaseModel, TenantMixin):
    """PET 品牌"""

    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="indigo", server_default="indigo", comment="品牌颜色")
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0", comment="排序序号")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    warehouses: Mapped[list["BrandWarehouse"]] = relationship(
        "BrandWarehouse", back_populates="brand", cascade="all, delete-orphan"
    )
    models: Mapped[list["BrandModel"]] = relationship(
        "BrandModel", back_populates="brand", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Brand {self.name}>"


class BrandWarehouse(BaseModel, TenantMixin):
    """品牌发货仓库（品牌维度下的发货/提货仓库）"""

    __tablename__ = "brand_warehouses"

    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0", comment="排序序号")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    brand: Mapped["Brand"] = relationship("Brand", back_populates="warehouses")

    def __repr__(self) -> str:
        return f"<BrandWarehouse {self.name}>"


class BrandModel(BaseModel, TenantMixin):
    """品牌型号（规格）"""

    __tablename__ = "brand_models"

    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(30), nullable=False, default="热料", server_default="热料")
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0", comment="排序序号")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    brand: Mapped["Brand"] = relationship("Brand", back_populates="models")

    def __repr__(self) -> str:
        return f"<BrandModel {self.model_name}>"
