"""财务模块 —— Repository"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.finance.models import (
    ARAllocation, ARLedger, ARReceipt,
    APAllocation, APLedger, APPayment,
)
from app.shared.base_repository import BaseRepository


class ARReceiptRepository(BaseRepository[ARReceipt]):
    def __init__(self, session: AsyncSession):
        super().__init__(ARReceipt, session, entity_name="收款")

    async def get_with_allocations(self, receipt_id: UUID) -> ARReceipt | None:
        r = await self.session.execute(
            select(ARReceipt).options(selectinload(ARReceipt.allocations)).where(ARReceipt.id == receipt_id)
        )
        return r.scalar_one_or_none()

    async def get_by_receipt_no(self, no: str) -> ARReceipt | None:
        r = await self.session.execute(select(ARReceipt).where(ARReceipt.receipt_no == no))
        return r.scalar_one_or_none()


class APPaymentRepository(BaseRepository[APPayment]):
    def __init__(self, session: AsyncSession):
        super().__init__(APPayment, session, entity_name="付款")

    async def get_with_allocations(self, payment_id: UUID) -> APPayment | None:
        r = await self.session.execute(
            select(APPayment).options(selectinload(APPayment.allocations)).where(APPayment.id == payment_id)
        )
        return r.scalar_one_or_none()

    async def get_by_payment_no(self, no: str) -> APPayment | None:
        r = await self.session.execute(select(APPayment).where(APPayment.payment_no == no))
        return r.scalar_one_or_none()


class ARLedgerRepository(BaseRepository[ARLedger]):
    def __init__(self, session: AsyncSession):
        super().__init__(ARLedger, session, entity_name="AR台账")

    async def get_by_bp(self, bp_id: UUID) -> ARLedger | None:
        r = await self.session.execute(select(ARLedger).where(ARLedger.bp_id == bp_id))
        return r.scalar_one_or_none()


class APLedgerRepository(BaseRepository[APLedger]):
    def __init__(self, session: AsyncSession):
        super().__init__(APLedger, session, entity_name="AP台账")

    async def get_by_bp(self, bp_id: UUID) -> APLedger | None:
        r = await self.session.execute(select(APLedger).where(APLedger.bp_id == bp_id))
        return r.scalar_one_or_none()
