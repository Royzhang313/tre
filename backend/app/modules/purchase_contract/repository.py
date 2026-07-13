"""采购合同模块 —— Repository 层"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.purchase_contract.models import PurchaseContract, PurchaseContractItem
from app.shared.base_repository import BaseRepository


class PurchaseContractRepository(BaseRepository[PurchaseContract]):
    def __init__(self, session: AsyncSession):
        super().__init__(PurchaseContract, session, entity_name="采购合同")

    async def get_with_items(self, contract_id: UUID) -> PurchaseContract | None:
        """查询合同及其明细"""
        stmt = (
            select(PurchaseContract)
            .where(PurchaseContract.id == contract_id)
            .options(selectinload(PurchaseContract.items))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_contract_no(self, contract_no: str) -> PurchaseContract | None:
        stmt = select(PurchaseContract).where(PurchaseContract.contract_no == contract_no)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_items(
        self, offset: int = 0, limit: int = 20
    ) -> list[PurchaseContract]:
        """分页查询合同列表（含明细）"""
        stmt = (
            select(PurchaseContract)
            .options(selectinload(PurchaseContract.items))
            .order_by(PurchaseContract.created_at.desc())
            .offset(offset).limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_with_supplier(
        self, offset: int = 0, limit: int = 20
    ) -> list[PurchaseContract]:
        """分页查询合同列表"""
        stmt = (
            select(PurchaseContract)
            .order_by(PurchaseContract.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PurchaseContractItemRepository(BaseRepository[PurchaseContractItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(PurchaseContractItem, session, entity_name="合同明细")
