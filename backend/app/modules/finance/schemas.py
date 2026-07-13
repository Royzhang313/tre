"""财务模块 —— Pydantic Schemas"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.finance.models import (
    PaymentMethod,
    PaymentStatus,
    PaymentType,
    ReceiptStatus,
    ReceiptType,
)


# ============================================================
# AR 收款
# ============================================================


class ARAllocationCreate(BaseModel):
    """收款分配创建"""
    sales_contract_id: UUID | None = Field(default=None, description="销售合同（余额分配时为空）")
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2, description="分配金额")
    allocation_type: str = Field(default="contract", pattern="^(contract|balance|fee)$", description="分配类型")


class ARReceiptCreate(BaseModel):
    """收款创建"""
    company_id: UUID | None = Field(default=None, description="主体公司")
    bp_id: UUID = Field(description="付款方（客户）")
    type: ReceiptType = Field(description="收款类型")
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2, description="收款金额")
    receipt_date: str = Field(min_length=1, max_length=10, description="收款日期")
    method: PaymentMethod = Field(default=PaymentMethod.TRANSFER, description="收款方式")
    bank_name: str | None = Field(default=None, max_length=200, description="付款银行")
    bank_account: str | None = Field(default=None, max_length=50, description="付款账号")
    remark: str | None = Field(default=None, max_length=500, description="备注")
    summary: str | None = Field(default=None, max_length=500, description="OCR 识别的摘要")
    tags: list[str] | None = Field(default=None, description="标签列表")
    attachment_path: list[dict] | None = Field(default=None, description="附件列表")
    allocations: list[ARAllocationCreate] | None = Field(default=None, description="初始分配（可选）")


class ARReceiptUpdate(BaseModel):
    """收款更新"""
    type: ReceiptType | None = Field(default=None, description="收款类型")
    receipt_date: str | None = Field(default=None, description="收款日期")
    method: PaymentMethod | None = Field(default=None, description="收款方式")
    bank_name: str | None = Field(default=None, max_length=200, description="付款银行")
    bank_account: str | None = Field(default=None, max_length=50, description="付款账号")
    remark: str | None = Field(default=None, max_length=500, description="备注")
    tags: list[str] | None = Field(default=None, description="标签列表")
    attachment_path: list[dict] | None = Field(default=None, description="附件列表")


class ARAllocationResponse(BaseModel):
    """收款分配响应"""
    id: UUID
    receipt_id: UUID
    sales_contract_id: UUID | None
    amount: Decimal
    allocation_type: str
    model_config = {"from_attributes": True}


class ARReceiptResponse(BaseModel):
    """收款响应"""
    id: UUID
    receipt_no: str
    company_id: UUID | None
    bp_id: UUID
    type: str
    amount: Decimal
    receipt_date: str
    method: str
    bank_name: str | None
    bank_account: str | None
    status: str
    remark: str | None
    summary: str | None
    tags: list | None
    attachment_path: list | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    allocations: list[ARAllocationResponse] = []
    model_config = {"from_attributes": True}


# ============================================================
# AP 付款
# ============================================================


class APAllocationCreate(BaseModel):
    """付款分配创建"""
    purchase_contract_id: UUID | None = Field(default=None, description="采购合同（余额分配时为空）")
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2, description="分配金额")
    allocation_type: str = Field(default="contract", pattern="^(contract|balance|fee)$", description="分配类型")


class APPaymentCreate(BaseModel):
    """付款创建"""
    company_id: UUID | None = Field(default=None, description="主体公司")
    bp_id: UUID = Field(description="收款方（供方）")
    type: PaymentType = Field(description="付款类型")
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2, description="付款金额")
    payment_date: str = Field(min_length=1, max_length=10, description="付款日期")
    method: PaymentMethod = Field(default=PaymentMethod.TRANSFER, description="付款方式")
    bank_name: str | None = Field(default=None, max_length=200, description="收款银行")
    bank_account: str | None = Field(default=None, max_length=50, description="收款账号")
    remark: str | None = Field(default=None, max_length=500, description="备注")
    summary: str | None = Field(default=None, max_length=500, description="OCR 识别的摘要")
    tags: list[str] | None = Field(default=None, description="标签列表")
    attachment_path: list[dict] | None = Field(default=None, description="附件列表")
    allocations: list[APAllocationCreate] | None = Field(default=None, description="初始分配（可选）")


class APPaymentUpdate(BaseModel):
    """付款更新"""
    type: PaymentType | None = Field(default=None, description="付款类型")
    payment_date: str | None = Field(default=None, description="付款日期")
    method: PaymentMethod | None = Field(default=None, description="付款方式")
    bank_name: str | None = Field(default=None, max_length=200, description="收款银行")
    bank_account: str | None = Field(default=None, max_length=50, description="收款账号")
    remark: str | None = Field(default=None, max_length=500, description="备注")
    tags: list[str] | None = Field(default=None, description="标签列表")
    attachment_path: list[dict] | None = Field(default=None, description="附件列表")


class APAllocationResponse(BaseModel):
    """付款分配响应"""
    id: UUID
    payment_id: UUID
    purchase_contract_id: UUID | None
    amount: Decimal
    allocation_type: str
    model_config = {"from_attributes": True}


class APPaymentResponse(BaseModel):
    """付款响应"""
    id: UUID
    payment_no: str
    company_id: UUID | None
    bp_id: UUID
    type: str
    amount: Decimal
    payment_date: str
    method: str
    bank_name: str | None
    bank_account: str | None
    status: str
    remark: str | None
    summary: str | None
    tags: list | None
    attachment_path: list | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    allocations: list[APAllocationResponse] = []
    model_config = {"from_attributes": True}


# ============================================================
# 台账
# ============================================================


class ARLedgerResponse(BaseModel):
    """AR 台账响应"""
    id: UUID
    bp_id: UUID
    total_receivable: Decimal = Decimal("0")
    total_receipt: Decimal = Decimal("0")
    total_allocated: Decimal = Decimal("0")
    current_balance: Decimal = Decimal("0")
    model_config = {"from_attributes": True}


class APLedgerResponse(BaseModel):
    """AP 台账响应"""
    id: UUID
    bp_id: UUID
    total_payable: Decimal = Decimal("0")
    total_payment: Decimal = Decimal("0")
    total_allocated: Decimal = Decimal("0")
    current_balance: Decimal = Decimal("0")
    model_config = {"from_attributes": True}


# ============================================================
# 分配请求
# ============================================================


class AllocateRequest(BaseModel):
    """批量分配请求 —— AR 和 AP 共用"""
    allocations: list[ARAllocationCreate | APAllocationCreate] = Field(
        min_length=1, max_length=50, description="分配列表"
    )
