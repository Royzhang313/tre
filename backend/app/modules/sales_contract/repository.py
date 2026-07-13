"""销售合同模块 —— Repository 层"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.sales_contract.models import SalesContract, SalesContractItem
from app.shared.base_repository import BaseRepository


class SalesContractRepository(BaseRepository[SalesContract]):
    def __init__(self, session: AsyncSession):
        super().__init__(SalesContract, session, entity_name="销售合同")

    async def get_with_items(self, contract_id: UUID) -> SalesContract | None:
        """查询合同及其明细"""
        stmt = (
            select(SalesContract)
            .where(SalesContract.id == contract_id)
            .options(selectinload(SalesContract.items))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_contract_no(self, contract_no: str) -> SalesContract | None:
        stmt = select(SalesContract).where(SalesContract.contract_no == contract_no)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_with_items(
        self, offset: int = 0, limit: int = 20
    ) -> list[SalesContract]:
        """分页查询合同列表（含明细）"""
        stmt = (
            select(SalesContract)
            .options(selectinload(SalesContract.items))
            .order_by(SalesContract.created_at.desc())
            .offset(offset).limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def list_with_supplier(
        self, offset: int = 0, limit: int = 20
    ) -> list[SalesContract]:
        """分页查询合同列表"""
        stmt = (
            select(SalesContract)
            .order_by(SalesContract.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class SalesContractItemRepository(BaseRepository[SalesContractItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(SalesContractItem, session, entity_name="销售合同明细")
