"""财务模块 —— Service 层

AR 收款 / AP 付款 / 分配引擎 / 台账同步
"""

from decimal import Decimal
from uuid import UUID

from app.core.exceptions import ConflictError, ValidationError
from app.modules.finance.models import (
    ARAllocation,
    ARLedger,
    ARReceipt,
    APAllocation,
    APLedger,
    APPayment,
    PaymentStatus,
    ReceiptStatus,
)
from app.modules.finance.repository import (
    ARLedgerRepository,
    ARReceiptRepository,
    APLedgerRepository,
    APPaymentRepository,
)
from app.modules.finance.schemas import (
    ARAllocationCreate,
    APAllocationCreate,
    APPaymentCreate,
    APPaymentUpdate,
    ARReceiptCreate,
    ARReceiptUpdate,
)
from app.shared.audit_helper import audit_record, orm_to_dict
from app.shared.number_engine import NumberEngine

# 确保 FK 引用表已注册
import app.modules.auth.models  # noqa: F401
import app.modules.basedata.models  # noqa: F401


# ============================================================
# AR 收款 Service
# ============================================================


class ARReceiptService:
    """AR 收款服务 —— 创建、确认、作废、更新、分配、台账同步"""

    def __init__(self, repo: ARReceiptRepository, ledger_repo: ARLedgerRepository):
        self.repo = repo
        self.ledger_repo = ledger_repo

    async def create(self, data: ARReceiptCreate, user_id: UUID) -> ARReceipt:
        """创建收款，自动生成编号 RC-{date}-{seq}"""
        receipt_no = await NumberEngine.generate("RC")

        receipt = ARReceipt(
            receipt_no=receipt_no,
            company_id=data.company_id,
            bp_id=data.bp_id,
            type=data.type,
            amount=data.amount,
            receipt_date=data.receipt_date,
            method=data.method,
            bank_name=data.bank_name,
            bank_account=data.bank_account,
            remark=data.remark,
            summary=data.summary,
            tags=data.tags,
            attachment_path=data.attachment_path,
            created_by=user_id,
        )
        await self.repo.create(receipt)

        # 处理初始分配
        if data.allocations:
            for alloc in data.allocations:
                allocation = ARAllocation(
                    receipt_id=receipt.id,
                    sales_contract_id=alloc.sales_contract_id,
                    amount=alloc.amount,
                    allocation_type=alloc.allocation_type,
                )
                self.repo.session.add(allocation)
            await self.repo.session.flush()

        # 更新台账
        await self._sync_ledger(data.bp_id)

        receipt = await self.repo.get_with_allocations(receipt.id) or receipt
        await audit_record(
            session=self.repo.session,
            action="create",
            entity_type="ar_receipt",
            entity_id=receipt.id,
            after=orm_to_dict(receipt),
        )
        return receipt

    async def confirm(self, receipt_id: UUID) -> ARReceipt:
        """确认收款 —— 状态从 pending → confirmed，同步台账，发布事件"""
        obj = await self.repo.get_by_id_or_raise(receipt_id)
        if obj.status != ReceiptStatus.PENDING:
            raise ConflictError("只能确认待处理状态的收款", entity="ARReceipt")
        before = orm_to_dict(obj)
        obj.status = ReceiptStatus.CONFIRMED
        await self.repo.update(obj)
        await self._sync_ledger(obj.bp_id)
        await audit_record(
            session=self.repo.session,
            action="confirm",
            entity_type="ar_receipt",
            entity_id=obj.id,
            before=before,
            after=orm_to_dict(obj),
        )
        # 发布领域事件
        from app.modules.finance.events import ARReceiptConfirmed
        from app.core.events import event_bus
        await event_bus.publish(ARReceiptConfirmed(
            aggregate_id=obj.id,
            receipt_no=obj.receipt_no,
            bp_id=obj.bp_id,
            amount=obj.amount,
        ))
        return obj

    async def void(self, receipt_id: UUID) -> ARReceipt:
        """作废收款 —— 状态 → voided，同步台账，发布事件"""
        obj = await self.repo.get_by_id_or_raise(receipt_id)
        if obj.status == ReceiptStatus.VOIDED:
            raise ConflictError("收款已作废", entity="ARReceipt")
        before = orm_to_dict(obj)
        obj.status = ReceiptStatus.VOIDED
        await self.repo.update(obj)
        await self._sync_ledger(obj.bp_id)
        await audit_record(
            session=self.repo.session,
            action="void",
            entity_type="ar_receipt",
            entity_id=obj.id,
            before=before,
            after=orm_to_dict(obj),
        )
        # 发布领域事件
        from app.modules.finance.events import ARReceiptVoided
        from app.core.events import event_bus
        await event_bus.publish(ARReceiptVoided(
            aggregate_id=obj.id,
            receipt_no=obj.receipt_no,
            bp_id=obj.bp_id,
            amount=obj.amount,
        ))
        return obj

    async def update(self, receipt_id: UUID, data: ARReceiptUpdate) -> ARReceipt:
        """更新收款基本信息"""
        obj = await self.repo.get_by_id_or_raise(receipt_id)
        before = orm_to_dict(obj)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(
            session=self.repo.session,
            action="update",
            entity_type="ar_receipt",
            entity_id=obj.id,
            before=before,
            after=orm_to_dict(obj),
        )
        return obj

    async def allocate(self, receipt_id: UUID, data: list[ARAllocationCreate]) -> ARReceipt:
        """为收款分配合同 —— 分配总额不得超过收款金额"""
        obj = await self.repo.get_with_allocations(receipt_id)
        if not obj:
            raise ValidationError("收款不存在")
        total_alloc = sum(a.amount for a in obj.allocations) + sum(a.amount for a in data)
        if total_alloc > obj.amount:
            raise ValidationError(f"分配总额 {total_alloc} 超过收款金额 {obj.amount}")
        for alloc in data:
            allocation = ARAllocation(
                receipt_id=receipt_id,
                sales_contract_id=alloc.sales_contract_id,
                amount=alloc.amount,
                allocation_type=alloc.allocation_type,
            )
            self.repo.session.add(allocation)
        await self.repo.session.flush()
        await self._sync_ledger(obj.bp_id)
        obj = await self.repo.get_with_allocations(receipt_id) or obj
        await audit_record(
            session=self.repo.session,
            action="allocate",
            entity_type="ar_receipt",
            entity_id=obj.id,
            remark=f"分配 {total_alloc}",
        )
        return obj

    async def _sync_ledger(self, bp_id: UUID) -> None:
        """同步 AR 台账 —— 从收款流水和合同汇总重新计算"""
        from sqlalchemy import func, select

        # 汇总已确认收款
        receipt_total = await self.repo.session.execute(
            select(func.coalesce(func.sum(ARReceipt.amount), 0)).where(
                ARReceipt.bp_id == bp_id,
                ARReceipt.status == ReceiptStatus.CONFIRMED,
            )
        )
        total_receipt = receipt_total.scalar_one()

        # 汇总已分配
        alloc_total = await self.repo.session.execute(
            select(func.coalesce(func.sum(ARAllocation.amount), 0))
            .join(ARReceipt, ARAllocation.receipt_id == ARReceipt.id)
            .where(ARReceipt.bp_id == bp_id, ARReceipt.status == ReceiptStatus.CONFIRMED)
        )
        total_allocated = alloc_total.scalar_one()

        # 从销售合同汇总应收金额
        from app.modules.sales_contract.models import SalesContract
        receivable_total = await self.repo.session.execute(
            select(func.coalesce(func.sum(SalesContract.total_amount), 0)).where(
                SalesContract.customer_enterprise_id == bp_id,
            )
        )
        total_receivable = receivable_total.scalar_one()

        # 创建或更新台账
        ledger = await self.ledger_repo.get_by_bp(bp_id)
        if not ledger:
            ledger = ARLedger(bp_id=bp_id)
            self.repo.session.add(ledger)
        ledger.total_receivable = total_receivable
        ledger.total_receipt = total_receipt
        ledger.total_allocated = total_allocated
        ledger.current_balance = total_receipt - total_allocated
        await self.repo.session.flush()


# ============================================================
# AP 付款 Service
# ============================================================


class APPaymentService:
    """AP 付款服务 —— 创建、确认、作废、更新、分配、台账同步"""

    def __init__(self, repo: APPaymentRepository, ledger_repo: APLedgerRepository):
        self.repo = repo
        self.ledger_repo = ledger_repo

    async def create(self, data: APPaymentCreate, user_id: UUID) -> APPayment:
        """创建付款，自动生成编号 PM-{date}-{seq}"""
        payment_no = await NumberEngine.generate("PM")

        payment = APPayment(
            payment_no=payment_no,
            company_id=data.company_id,
            bp_id=data.bp_id,
            type=data.type,
            amount=data.amount,
            payment_date=data.payment_date,
            method=data.method,
            bank_name=data.bank_name,
            bank_account=data.bank_account,
            remark=data.remark,
            summary=data.summary,
            tags=data.tags,
            attachment_path=data.attachment_path,
            created_by=user_id,
        )
        await self.repo.create(payment)

        # 处理初始分配
        if data.allocations:
            for alloc in data.allocations:
                allocation = APAllocation(
                    payment_id=payment.id,
                    purchase_contract_id=alloc.purchase_contract_id,
                    amount=alloc.amount,
                    allocation_type=alloc.allocation_type,
                )
                self.repo.session.add(allocation)
            await self.repo.session.flush()

        # 更新台账
        await self._sync_ledger(data.bp_id)

        payment = await self.repo.get_with_allocations(payment.id) or payment
        await audit_record(
            session=self.repo.session,
            action="create",
            entity_type="ap_payment",
            entity_id=payment.id,
            after=orm_to_dict(payment),
        )
        return payment

    async def confirm(self, payment_id: UUID) -> APPayment:
        """确认付款 —— 状态从 pending → confirmed，同步台账，发布事件"""
        obj = await self.repo.get_by_id_or_raise(payment_id)
        if obj.status != PaymentStatus.PENDING:
            raise ConflictError("只能确认待处理状态的付款", entity="APPayment")
        before = orm_to_dict(obj)
        obj.status = PaymentStatus.CONFIRMED
        await self.repo.update(obj)
        await self._sync_ledger(obj.bp_id)
        await audit_record(
            session=self.repo.session,
            action="confirm",
            entity_type="ap_payment",
            entity_id=obj.id,
            before=before,
            after=orm_to_dict(obj),
        )
        # 发布领域事件
        from app.modules.finance.events import APPaymentConfirmed
        from app.core.events import event_bus
        await event_bus.publish(APPaymentConfirmed(
            aggregate_id=obj.id,
            payment_no=obj.payment_no,
            bp_id=obj.bp_id,
            amount=obj.amount,
        ))
        return obj

    async def void(self, payment_id: UUID) -> APPayment:
        """作废付款 —— 状态 → voided，同步台账，发布事件"""
        obj = await self.repo.get_by_id_or_raise(payment_id)
        if obj.status == PaymentStatus.VOIDED:
            raise ConflictError("付款已作废", entity="APPayment")
        before = orm_to_dict(obj)
        obj.status = PaymentStatus.VOIDED
        await self.repo.update(obj)
        await self._sync_ledger(obj.bp_id)
        await audit_record(
            session=self.repo.session,
            action="void",
            entity_type="ap_payment",
            entity_id=obj.id,
            before=before,
            after=orm_to_dict(obj),
        )
        # 发布领域事件
        from app.modules.finance.events import APPaymentVoided
        from app.core.events import event_bus
        await event_bus.publish(APPaymentVoided(
            aggregate_id=obj.id,
            payment_no=obj.payment_no,
            bp_id=obj.bp_id,
            amount=obj.amount,
        ))
        return obj

    async def update(self, payment_id: UUID, data: APPaymentUpdate) -> APPayment:
        """更新付款基本信息"""
        obj = await self.repo.get_by_id_or_raise(payment_id)
        before = orm_to_dict(obj)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(
            session=self.repo.session,
            action="update",
            entity_type="ap_payment",
            entity_id=obj.id,
            before=before,
            after=orm_to_dict(obj),
        )
        return obj

    async def allocate(self, payment_id: UUID, data: list[APAllocationCreate]) -> APPayment:
        """为付款分配合同 —— 分配总额不得超过付款金额"""
        obj = await self.repo.get_with_allocations(payment_id)
        if not obj:
            raise ValidationError("付款不存在")
        total_alloc = sum(a.amount for a in obj.allocations) + sum(a.amount for a in data)
        if total_alloc > obj.amount:
            raise ValidationError(f"分配总额 {total_alloc} 超过付款金额 {obj.amount}")
        for alloc in data:
            allocation = APAllocation(
                payment_id=payment_id,
                purchase_contract_id=alloc.purchase_contract_id,
                amount=alloc.amount,
                allocation_type=alloc.allocation_type,
            )
            self.repo.session.add(allocation)
        await self.repo.session.flush()
        await self._sync_ledger(obj.bp_id)
        obj = await self.repo.get_with_allocations(payment_id) or obj
        await audit_record(
            session=self.repo.session,
            action="allocate",
            entity_type="ap_payment",
            entity_id=obj.id,
            remark=f"分配 {total_alloc}",
        )
        return obj

    async def _sync_ledger(self, bp_id: UUID) -> None:
        """同步 AP 台账 —— 从付款流水和合同汇总重新计算"""
        from sqlalchemy import func, select

        # 汇总已确认付款
        payment_total = await self.repo.session.execute(
            select(func.coalesce(func.sum(APPayment.amount), 0)).where(
                APPayment.bp_id == bp_id,
                APPayment.status == PaymentStatus.CONFIRMED,
            )
        )
        total_payment = payment_total.scalar_one()

        # 汇总已分配
        alloc_total = await self.repo.session.execute(
            select(func.coalesce(func.sum(APAllocation.amount), 0))
            .join(APPayment, APAllocation.payment_id == APPayment.id)
            .where(APPayment.bp_id == bp_id, APPayment.status == PaymentStatus.CONFIRMED)
        )
        total_allocated = alloc_total.scalar_one()

        # 从采购合同汇总应付金额
        from app.modules.purchase_contract.models import PurchaseContract
        payable_total = await self.repo.session.execute(
            select(func.coalesce(func.sum(PurchaseContract.total_amount), 0)).where(
                PurchaseContract.supplier_enterprise_id == bp_id,
            )
        )
        total_payable = payable_total.scalar_one()

        # 创建或更新台账
        ledger = await self.ledger_repo.get_by_bp(bp_id)
        if not ledger:
            ledger = APLedger(bp_id=bp_id)
            self.repo.session.add(ledger)
        ledger.total_payable = total_payable
        ledger.total_payment = total_payment
        ledger.total_allocated = total_allocated
        ledger.current_balance = total_payment - total_allocated
        await self.repo.session.flush()
