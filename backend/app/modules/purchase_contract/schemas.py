"""采购合同模块 —— Pydantic Schemas V2"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# 合同明细
# ============================================================


class ContractItemCreate(BaseModel):
    brand_id: UUID
    model_id: UUID
    shipping_warehouse_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    unit: str = Field(default="吨", max_length=10)
    purchase_price: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    tax_rate: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=2)
    storage_fee_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    commission_fee_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    commission_fee: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=2)


class ContractItemResponse(BaseModel):
    id: UUID; line_no: int
    brand_id: UUID; model_id: UUID; shipping_warehouse_id: UUID
    quantity: Decimal; unit: str; purchase_price: Decimal; amount: Decimal
    tax_rate: Decimal; storage_fee_price: Decimal; commission_fee_price: Decimal; commission_fee: Decimal
    model_config = {"from_attributes": True}


# ============================================================
# 合同主表
# ============================================================


class PurchaseContractCreate(BaseModel):
    company_id: UUID = Field(description="执行主体公司")
    contract_no: str = Field(min_length=1, max_length=30, description="合同编号（手动输入）")
    supplier_enterprise_id: UUID
    contract_date: str = Field(min_length=1, max_length=10)
    contract_start_date: str = Field(min_length=1, max_length=10, description="合同开始日期")
    contract_end_date: str = Field(min_length=1, max_length=10, description="合同结束日期")
    commission_platform_id: UUID | None = Field(default=None, description="撮合平台")
    attachment_path: list[dict] | None = Field(default=None, description="附件列表 [{path, filename}]")
    remark: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None, description="标签列表")
    items: list[ContractItemCreate] = Field(min_length=1, max_length=100)


class ContractItemUpdate(BaseModel):
    """采购合同明细更新 —— 先删后建，id 字段保留兼容"""
    id: UUID | None = None
    brand_id: UUID
    model_id: UUID
    shipping_warehouse_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    unit: str = Field(default="吨", max_length=10)
    purchase_price: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    tax_rate: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=2)
    storage_fee_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    commission_fee_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    commission_fee: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=2)


class PurchaseContractUpdate(BaseModel):
    company_id: UUID | None = None
    supplier_enterprise_id: UUID | None = None
    commission_platform_id: UUID | None = None
    contract_date: str | None = None
    contract_start_date: str | None = None
    contract_end_date: str | None = None
    attachment_path: list[dict] | None = None
    remark: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    items: list[ContractItemUpdate] | None = None


class PurchaseContractResponse(BaseModel):
    id: UUID; company_id: UUID; contract_no: str; supplier_enterprise_id: UUID
    commission_platform_id: UUID | None = None
    contract_date: str; contract_start_date: str; contract_end_date: str
    attachment_path: list | None
    status: str; total_quantity: Decimal; total_amount: Decimal
    delivery_progress: Decimal; payment_progress: Decimal
    remark: str | None; tags: list | None; created_by: UUID
    created_at: datetime; updated_at: datetime
    items: list[ContractItemResponse] = []
    model_config = {"from_attributes": True}
