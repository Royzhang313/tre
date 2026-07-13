"""品牌模块 —— ORM 模型（应用层查重，排除软删除数据）"""

from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class Brand(BaseModel):
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


class BrandWarehouse(BaseModel):
    """品牌发货仓库"""

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


class BrandModel(BaseModel):
    """品牌型号"""

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
