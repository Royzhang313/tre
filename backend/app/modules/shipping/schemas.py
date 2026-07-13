"""货运模块 —— Pydantic Schemas V2"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# 计划明细
# ============================================================


class PlanItemCreate(BaseModel):
    """计划明细创建 —— 客户→销售合同→型号/仓库/吨数"""
    customer_enterprise_id: UUID = Field(description="客户企业")
    sales_contract_id: UUID = Field(description="客户销售合同")
    model_id: UUID = Field(description="发货型号（按计划品牌筛选）")
    warehouse_id: UUID = Field(description="发货仓库（按计划品牌筛选）")
    planned_quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    unit: str = Field(default="吨", max_length=10)
    purchase_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    sale_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    surcharge_type: str | None = Field(default=None, max_length=20)
    surcharge_amount: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)


class PlanItemResponse(BaseModel):
    """计划明细响应"""
    id: UUID
    line_no: int
    customer_enterprise_id: UUID
    sales_contract_id: UUID
    model_id: UUID
    warehouse_id: UUID
    planned_quantity: Decimal
    unit: str
    purchase_price: Decimal
    sale_price: Decimal
    surcharge_type: str | None = None
    surcharge_amount: Decimal
    shipped_quantity: Decimal
    model_config = {"from_attributes": True}


# ============================================================
# 计划主表
# ============================================================


class ShippingPlanCreate(BaseModel):
    """创建货运计划 —— 品牌→采购合同→日期→配送方式→明细列表"""
    company_id: UUID = Field(description="执行主体公司")
    brand_id: UUID = Field(description="发货品牌（主筛选维度）")
    supplier_enterprise_id: UUID = Field(description="供方企业")
    purchase_contract_id: UUID = Field(description="货源采购合同（按品牌+供方筛选）")
    planned_date: str = Field(min_length=1, max_length=10, description="计划发货日期")
    delivery_method: str = Field(default="SH", max_length=2, description="配送方式: ZT=自提 SH=送货")
    remark: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None)
    items: list[PlanItemCreate] = Field(min_length=1, max_length=100)


class PlanItemUpdate(BaseModel):
    """计划明细更新 —— id 定位，其余字段按需覆盖"""
    id: UUID = Field(description="计划明细ID")
    planned_quantity: Decimal | None = Field(default=None, gt=0, max_digits=18, decimal_places=4)
    surcharge_type: str | None = Field(default=None, max_length=20)
    surcharge_amount: Decimal | None = Field(default=None, max_digits=18, decimal_places=4)


class ShippingPlanUpdate(BaseModel):
    """更新货运计划"""
    planned_date: str | None = Field(default=None, min_length=1, max_length=10)
    delivery_method: str | None = Field(default=None, max_length=2)
    remark: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    items: list[PlanItemUpdate] | None = Field(default=None, description="计划明细更新（可选）")


class ShippingPlanDateUpdate(BaseModel):
    """拖拽修改日期"""
    planned_date: str = Field(min_length=1, max_length=10)


class ShippingPlanResponse(BaseModel):
    """货运计划响应"""
    id: UUID
    company_id: UUID
    brand_id: UUID
    supplier_enterprise_id: UUID
    purchase_contract_id: UUID
    planned_date: str
    delivery_method: str
    status: str
    total_planned_quantity: Decimal
    remark: str | None = None
    tags: list | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    items: list[PlanItemResponse] = []
    model_config = {"from_attributes": True}


# ============================================================
# 发货明细
# ============================================================


class ShipmentItemCreate(BaseModel):
    """发货明细创建"""
    plan_item_id: UUID
    shipped_quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    unit: str = Field(default="吨", max_length=10)


class ShipmentItemResponse(BaseModel):
    """发货明细响应"""
    id: UUID
    plan_item_id: UUID
    shipped_quantity: Decimal
    unit: str
    model_config = {"from_attributes": True}


# ============================================================
# 发货主表
# ============================================================


class ShipmentCreate(BaseModel):
    """创建发货记录"""
    shipped_date: str = Field(min_length=1, max_length=10, description="实际发货日期")
    driver_name: str | None = Field(default=None, max_length=50)
    driver_phone: str | None = Field(default=None, max_length=20)
    driver_license_plate: str | None = Field(default=None, max_length=20)
    driver_id_card: str | None = Field(default=None, max_length=30)
    freight_total: Decimal | None = Field(default=None, max_digits=18, decimal_places=2)
    freight_tax_rate: Decimal | None = Field(default=None, max_digits=5, decimal_places=2)
    remark: str | None = Field(default=None, max_length=500)
    items: list[ShipmentItemCreate] = Field(min_length=1, max_length=100)


class ShipmentUpdate(BaseModel):
    """更新发货记录"""
    shipped_date: str | None = None
    driver_name: str | None = None
    driver_phone: str | None = None
    driver_license_plate: str | None = None
    driver_id_card: str | None = None
    freight_total: Decimal | None = None
    status: str | None = None
    remark: str | None = None


class ShipmentResponse(BaseModel):
    """发货记录响应"""
    id: UUID
    plan_id: UUID
    shipment_no: str
    shipped_date: str
    driver_name: str | None = None
    driver_phone: str | None = None
    driver_license_plate: str | None = None
    driver_id_card: str | None = None
    freight_total: Decimal | None = None
    freight_unit_price: Decimal | None = None
    status: str
    remark: str | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    items: list[ShipmentItemResponse] = []
    model_config = {"from_attributes": True}
