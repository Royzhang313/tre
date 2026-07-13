"""财务模块 —— 领域事件

供其他模块通过 EventBus 订阅，实现跨模块联动。
例如：发货模块可订阅 ARReceiptConfirmed 更新回款进度。
"""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from app.core.events import DomainEvent


# ============================================================
# AR 收款事件
# ============================================================


@dataclass(frozen=True, slots=True, kw_only=True)
class ARReceiptConfirmed(DomainEvent):
    """收款已确认 —— 通知发货/销售模块更新回款进度"""
    aggregate_id: UUID
    receipt_no: str = ""
    bp_id: UUID = field(default_factory=lambda: UUID("00000000-0000-0000-0000-000000000000"))
    amount: Decimal = Decimal("0")

    def __post_init__(self):
        object.__setattr__(self, "event_type", "finance.ar_receipt.confirmed")
        object.__setattr__(self, "aggregate_type", "ARReceipt")


@dataclass(frozen=True, slots=True, kw_only=True)
class ARReceiptVoided(DomainEvent):
    """收款已作废 —— 通知相关模块回滚回款进度"""
    aggregate_id: UUID
    receipt_no: str = ""
    bp_id: UUID = field(default_factory=lambda: UUID("00000000-0000-0000-0000-000000000000"))
    amount: Decimal = Decimal("0")

    def __post_init__(self):
        object.__setattr__(self, "event_type", "finance.ar_receipt.voided")
        object.__setattr__(self, "aggregate_type", "ARReceipt")


# ============================================================
# AP 付款事件
# ============================================================


@dataclass(frozen=True, slots=True, kw_only=True)
class APPaymentConfirmed(DomainEvent):
    """付款已确认 —— 通知采购模块更新付款进度"""
    aggregate_id: UUID
    payment_no: str = ""
    bp_id: UUID = field(default_factory=lambda: UUID("00000000-0000-0000-0000-000000000000"))
    amount: Decimal = Decimal("0")

    def __post_init__(self):
        object.__setattr__(self, "event_type", "finance.ap_payment.confirmed")
        object.__setattr__(self, "aggregate_type", "APPayment")


@dataclass(frozen=True, slots=True, kw_only=True)
class APPaymentVoided(DomainEvent):
    """付款已作废 —— 通知相关模块回滚付款进度"""
    aggregate_id: UUID
    payment_no: str = ""
    bp_id: UUID = field(default_factory=lambda: UUID("00000000-0000-0000-0000-000000000000"))
    amount: Decimal = Decimal("0")

    def __post_init__(self):
        object.__setattr__(self, "event_type", "finance.ap_payment.voided")
        object.__setattr__(self, "aggregate_type", "APPayment")
