"""产品模块 —— Pydantic 请求/响应 Schema"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.base_schema import FilterSchema, PageRequest


# ---- 请求 Schema ----

class ProductCreate(BaseModel):
    """创建产品请求"""
    product_code: str = Field(..., max_length=30, description="产品编码")
    name: str = Field(..., max_length=200, description="产品名称")
    brand_name: str | None = Field(None, max_length=100, description="品牌名称")
    model_type: str | None = Field(None, max_length=30, description="型号类型: 热料/冷料/蓝白片等")
    warehouse_name: str | None = Field(None, max_length=100, description="默认发货仓库")
    unit: str = Field(default="吨", max_length=10, description="计量单位")
    default_purchase_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4, description="默认采购单价")
    default_sale_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4, description="默认销售单价")
    description: str | None = Field(None, max_length=500, description="产品描述")
    is_active: bool = Field(default=True, description="是否启用")


class ProductUpdate(BaseModel):
    """更新产品请求（所有字段可选）"""
    product_code: str | None = Field(None, max_length=30, description="产品编码")
    name: str | None = Field(None, max_length=200, description="产品名称")
    brand_name: str | None = Field(None, max_length=100, description="品牌名称")
    model_type: str | None = Field(None, max_length=30, description="型号类型")
    warehouse_name: str | None = Field(None, max_length=100, description="默认发货仓库")
    unit: str | None = Field(None, max_length=10, description="计量单位")
    default_purchase_price: Decimal | None = Field(None, max_digits=18, decimal_places=4, description="默认采购单价")
    default_sale_price: Decimal | None = Field(None, max_digits=18, decimal_places=4, description="默认销售单价")
    description: str | None = Field(None, max_length=500, description="产品描述")
    is_active: bool | None = Field(None, description="是否启用")


class ProductFilter(FilterSchema):
    """产品过滤条件"""
    is_active: bool | None = Field(None, description="是否启用")
    model_type: str | None = Field(None, description="型号类型")


# ---- 响应 Schema ----

class ProductResponse(BaseModel):
    """产品响应"""
    id: UUID
    product_code: str
    name: str
    brand_name: str | None
    model_type: str | None
    warehouse_name: str | None
    unit: str
    default_purchase_price: Decimal
    default_sale_price: Decimal
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
