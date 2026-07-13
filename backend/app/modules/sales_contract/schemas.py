"""销售合同模块 —— Pydantic Schemas"""

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
    sale_price: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    tax_rate: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=2)
    storage_fee_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    commission_fee_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    commission_fee: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=2)


class ContractItemResponse(BaseModel):
    id: UUID; line_no: int
    brand_id: UUID; model_id: UUID; shipping_warehouse_id: UUID
    quantity: Decimal; unit: str; sale_price: Decimal; amount: Decimal
    tax_rate: Decimal; storage_fee_price: Decimal; commission_fee_price: Decimal; commission_fee: Decimal
    model_config = {"from_attributes": True}


# ============================================================
# 合同主表
# ============================================================


class SalesContractCreate(BaseModel):
    company_id: UUID = Field(description="执行主体公司")
    contract_type: str = Field(default="SH", description="合同类型: SH=送货 ZT=自提 HH=还货")
    sales_person_id: UUID | None = Field(default=None, description="销售人员")
    customer_enterprise_id: UUID
    commission_platform_id: UUID | None = Field(default=None, description="撮合")
    contract_date: str = Field(min_length=1, max_length=10)
    contract_start_date: str = Field(min_length=1, max_length=10, description="合同开始日期")
    contract_end_date: str = Field(min_length=1, max_length=10, description="合同结束日期")
    attachment_path: list[dict] | None = Field(default=None, description="附件列表 [{path, filename}]")
    remark: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = Field(default=None, description="标签列表")
    items: list[ContractItemCreate] = Field(min_length=1, max_length=100)


class ContractItemUpdate(BaseModel):
    """合同明细更新 —— 有 id 则更新，无 id 则新建"""
    id: UUID | None = None
    brand_id: UUID
    model_id: UUID
    shipping_warehouse_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    unit: str = Field(default="吨", max_length=10)
    sale_price: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    tax_rate: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=2)
    storage_fee_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    commission_fee_price: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4)
    commission_fee: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=2)


class SalesContractUpdate(BaseModel):
    company_id: UUID | None = None
    customer_enterprise_id: UUID | None = None
    commission_platform_id: UUID | None = None
    contract_date: str | None = None
    contract_start_date: str | None = None
    contract_end_date: str | None = None
    attachment_path: list[dict] | None = None
    remark: str | None = None
    tags: list[str] | None = None
    status: str | None = None
    items: list[ContractItemUpdate] | None = None


class SalesContractResponse(BaseModel):
    id: UUID; company_id: UUID; contract_no: str; contract_type: str | None = None
    sales_person_id: UUID | None = None
    customer_enterprise_id: UUID
    commission_platform_id: UUID | None = None
    contract_date: str; contract_start_date: str; contract_end_date: str
    attachment_path: list | None
    status: str; total_quantity: Decimal; total_amount: Decimal
    pickup_progress: Decimal; collection_progress: Decimal
    remark: str | None; tags: list | None; created_by: UUID
    created_at: datetime; updated_at: datetime
    items: list[ContractItemResponse] = []
    model_config = {"from_attributes": True}
