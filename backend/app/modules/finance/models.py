"""财务模块 —— ORM 数据模型

AR 收款 / AP 付款 / 分配 / 台账
"""

import enum
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


# ============================================================
# 枚举
# ============================================================


class ReceiptType(enum.StrEnum):
    """收款类型（现金类 + 票据类）"""
    DEPOSIT = "deposit"
    GOODS = "goods"
    BALANCE = "balance"
    PREPAY = "prepay"
    GUARANTEE = "guarantee"
    BANK_ACCEPTANCE = "bank_acceptance"
    COM_ACCEPTANCE = "com_acceptance"


class PaymentType(enum.StrEnum):
    """付款类型（现金类 + 票据类 + 费用类）"""
    DEPOSIT = "deposit"
    GOODS = "goods"
    BALANCE = "balance"
    PREPAY = "prepay"
    GUARANTEE = "guarantee"
    BANK_ACCEPTANCE = "bank_acceptance"
    COM_ACCEPTANCE = "com_acceptance"
    WAREHOUSE_SURCHARGE = "warehouse_surcharge"
    COMMISSION = "commission"
    FREIGHT = "freight"


class ReceiptStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    VOIDED = "voided"


class PaymentStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    VOIDED = "voided"


class PaymentMethod(enum.StrEnum):
    CASH = "cash"
    TRANSFER = "transfer"
    ACCEPTANCE = "acceptance"


# ============================================================
# AR 收款
# ============================================================


class ARReceipt(BaseModel):
    """收款（应收）"""

    __tablename__ = "ar_receipts"

    receipt_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="收款编号 RC-{date}-{seq}")
    company_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("basedata_companies.id", ondelete="RESTRICT"), index=True, nullable=True, comment="主体公司"
    )
    bp_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_enterprises.id", ondelete="RESTRICT"), index=True, nullable=False, comment="付款方（客户）"
    )
    type: Mapped[ReceiptType] = mapped_column(String(30), nullable=False, comment="收款类型")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, comment="收款金额")
    receipt_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="收款日期")
    method: Mapped[PaymentMethod] = mapped_column(String(20), nullable=False, default=PaymentMethod.TRANSFER, comment="收款方式")
    bank_name: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="付款银行")
    bank_account: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="付款账号")
    status: Mapped[ReceiptStatus] = mapped_column(String(20), nullable=False, default=ReceiptStatus.PENDING)
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="OCR 识别摘要")
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="标签列表")
    attachment_path: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="附件列表")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id", ondelete="RESTRICT"), index=True, nullable=False)

    allocations: Mapped[list["ARAllocation"]] = relationship(
        "ARAllocation", back_populates="receipt", cascade="all, delete-orphan", lazy="selectin",
    )


class ARAllocation(BaseModel):
    """收款分配 —— 收款 → 销售合同"""

    __tablename__ = "ar_allocations"

    receipt_id: Mapped[UUID] = mapped_column(ForeignKey("ar_receipts.id", ondelete="CASCADE"), nullable=False)
    sales_contract_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sales_contracts.id", ondelete="RESTRICT"), nullable=True, comment="销售合同（余额分配时为空）"
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, comment="分配金额")
    allocation_type: Mapped[str] = mapped_column(String(20), nullable=False, default="contract", comment="分配类型: contract|balance|fee")

    receipt: Mapped["ARReceipt"] = relationship("ARReceipt", back_populates="allocations")


# ============================================================
# AP 付款
# ============================================================


class APPayment(BaseModel):
    """付款（应付）"""

    __tablename__ = "ap_payments"

    payment_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="付款编号 PM-{date}-{seq}")
    company_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("basedata_companies.id", ondelete="RESTRICT"), index=True, nullable=True, comment="主体公司"
    )
    bp_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_enterprises.id", ondelete="RESTRICT"), index=True, nullable=False, comment="收款方（供方）"
    )
    type: Mapped[PaymentType] = mapped_column(String(30), nullable=False, comment="付款类型")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, comment="付款金额")
    payment_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="付款日期")
    method: Mapped[PaymentMethod] = mapped_column(String(20), nullable=False, default=PaymentMethod.TRANSFER, comment="付款方式")
    bank_name: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="收款银行")
    bank_account: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="收款账号")
    status: Mapped[PaymentStatus] = mapped_column(String(20), nullable=False, default=PaymentStatus.PENDING)
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="OCR 识别摘要")
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="标签列表")
    attachment_path: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="附件列表")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("auth_users.id", ondelete="RESTRICT"), index=True, nullable=False)

    allocations: Mapped[list["APAllocation"]] = relationship(
        "APAllocation", back_populates="payment", cascade="all, delete-orphan", lazy="selectin",
    )


class APAllocation(BaseModel):
    """付款分配 —— 付款 → 采购合同"""

    __tablename__ = "ap_allocations"

    payment_id: Mapped[UUID] = mapped_column(ForeignKey("ap_payments.id", ondelete="CASCADE"), nullable=False)
    purchase_contract_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("purchase_contracts.id", ondelete="RESTRICT"), nullable=True, comment="采购合同（余额分配时为空）"
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, comment="分配金额")
    allocation_type: Mapped[str] = mapped_column(String(20), nullable=False, default="contract", comment="分配类型: contract|balance|fee")

    payment: Mapped["APPayment"] = relationship("APPayment", back_populates="allocations")


# ============================================================
# AR/AP 台账（高性能缓存）
# ============================================================


class ARLedger(BaseModel):
    """AR 台账 —— 按 BP 聚合"""

    __tablename__ = "bp_ar_ledgers"

    bp_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_enterprises.id", ondelete="RESTRICT"), unique=True, nullable=False, comment="客户 BP"
    )
    total_receivable: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0", comment="累计应收")
    total_receipt: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0", comment="累计实收")
    total_allocated: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0", comment="累计已分配")
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0", comment="当前余额 = total_receipt - total_allocated")


class APLedger(BaseModel):
    """AP 台账 —— 按 BP 聚合"""

    __tablename__ = "bp_ap_ledgers"

    bp_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_enterprises.id", ondelete="RESTRICT"), unique=True, nullable=False, comment="供方 BP"
    )
    total_payable: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0", comment="累计应付")
    total_payment: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0", comment="累计实付")
    total_allocated: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0", comment="累计已分配")
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0", comment="当前余额 = total_payment - total_allocated")
