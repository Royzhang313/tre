"""库存模块 —— Repository 层"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.inventory.models import (
    Batch,
    ContractStock,
    InventoryLedger,
    WarehouseStock,
)
from app.shared.base_repository import BaseRepository


class ContractStockRepository(BaseRepository[ContractStock]):
    def __init__(self, session: AsyncSession):
        super().__init__(ContractStock, session, entity_name="合同货权库存")

    async def get_by_product_and_po(
        self, product_id: UUID, purchase_contract_id: UUID
    ) -> ContractStock | None:
        """按产品+采购合同查找唯一的货权记录"""
        stmt = select(ContractStock).where(
            ContractStock.product_id == product_id,
            ContractStock.purchase_contract_id == purchase_contract_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_product(self, product_id: UUID) -> list[ContractStock]:
        """按产品查询所有货权记录"""
        stmt = (
            select(ContractStock)
            .where(ContractStock.product_id == product_id)
            .order_by(ContractStock.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_supplier(self, supplier_id: UUID) -> list[ContractStock]:
        """按供应商查询所有货权记录"""
        stmt = (
            select(ContractStock)
            .where(ContractStock.supplier_id == supplier_id)
            .order_by(ContractStock.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_active(
        self,
        offset: int = 0,
        limit: int = 50,
        is_closed: bool | None = None,
    ) -> list[ContractStock]:
        """分页查询货权库存列表"""
        stmt = select(ContractStock)
        if is_closed is not None:
            stmt = stmt.where(ContractStock.is_closed == is_closed)
        stmt = stmt.order_by(ContractStock.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class WarehouseStockRepository(BaseRepository[WarehouseStock]):
    def __init__(self, session: AsyncSession):
        super().__init__(WarehouseStock, session, entity_name="实物库存")

    async def get_by_warehouse_and_product(
        self, warehouse_id: UUID, product_id: UUID
    ) -> WarehouseStock | None:
        """按仓库+产品查找实物库存"""
        stmt = select(WarehouseStock).where(
            WarehouseStock.warehouse_id == warehouse_id,
            WarehouseStock.product_id == product_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_warehouse(self, warehouse_id: UUID) -> list[WarehouseStock]:
        """按仓库查询所有实物库存"""
        stmt = (
            select(WarehouseStock)
            .where(WarehouseStock.warehouse_id == warehouse_id)
            .order_by(WarehouseStock.product_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class BatchRepository(BaseRepository[Batch]):
    def __init__(self, session: AsyncSession):
        super().__init__(Batch, session, entity_name="批次")

    async def list_by_product(self, product_id: UUID) -> list[Batch]:
        """按产品查询批次列表"""
        stmt = (
            select(Batch)
            .where(Batch.product_id == product_id, Batch.is_active == True)
            .order_by(Batch.receipt_date.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_contract(self, contract_id: UUID) -> list[Batch]:
        """按采购合同查询批次列表"""
        stmt = (
            select(Batch)
            .where(Batch.purchase_contract_id == contract_id)
            .order_by(Batch.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class InventoryLedgerRepository(BaseRepository[InventoryLedger]):
    def __init__(self, session: AsyncSession):
        super().__init__(InventoryLedger, session, entity_name="库存分类账")

    async def list_by_stock(
        self, contract_stock_id: UUID, offset: int = 0, limit: int = 100
    ) -> list[InventoryLedger]:
        """按货权库存查询分类账"""
        stmt = (
            select(InventoryLedger)
            .where(InventoryLedger.contract_stock_id == contract_stock_id)
            .order_by(InventoryLedger.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
