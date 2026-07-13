"""货运模块 —— Repository 层"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.shipping.models import Shipment, ShipmentItem, ShippingPlan, ShippingPlanItem
from app.shared.base_repository import BaseRepository


class ShippingPlanRepository(BaseRepository[ShippingPlan]):
    """货运计划 Repository"""

    def __init__(self, session):
        super().__init__(ShippingPlan, session, entity_name="货运计划")

    async def get_with_items(self, plan_id: UUID) -> ShippingPlan | None:
        """查询计划（含明细和发货记录）"""
        stmt = (
            select(ShippingPlan)
            .where(ShippingPlan.id == plan_id)
            .options(
                selectinload(ShippingPlan.items),
                selectinload(ShippingPlan.shipments).selectinload(Shipment.items),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_date_range(
        self, start_date: str, end_date: str, offset: int = 0, limit: int = 500
    ) -> list[ShippingPlan]:
        """按日期范围查询计划"""
        stmt = (
            select(ShippingPlan)
            .where(
                ShippingPlan.planned_date >= start_date,
                ShippingPlan.planned_date <= end_date,
            )
            .options(selectinload(ShippingPlan.items))
            .order_by(ShippingPlan.planned_date.asc(), ShippingPlan.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_with_items(self, offset: int = 0, limit: int = 500) -> list[ShippingPlan]:
        """查询所有计划（含明细）"""
        stmt = (
            select(ShippingPlan)
            .options(selectinload(ShippingPlan.items))
            .order_by(ShippingPlan.planned_date.desc(), ShippingPlan.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_filtered(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        brand_id: str | None = None,
        supplier_enterprise_id: str | None = None,
        purchase_contract_id: str | None = None,
        customer_enterprise_id: str | None = None,
        sales_contract_id: str | None = None,
        warehouse_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 500,
    ) -> list[ShippingPlan]:
        """多条件筛选计划列表（含明细）"""
        # 字符串 → UUID 转换
        _uid = lambda v: UUID(v) if isinstance(v, str) else v

        # 需要 JOIN ShippingPlanItem 的条件
        needs_join = customer_enterprise_id or sales_contract_id or warehouse_id
        if needs_join:
            from sqlalchemy.orm import contains_eager
            stmt = (
                select(ShippingPlan)
                .join(ShippingPlan.items)
                .options(contains_eager(ShippingPlan.items))
                .distinct()
            )
            if customer_enterprise_id:
                stmt = stmt.where(ShippingPlanItem.customer_enterprise_id == _uid(customer_enterprise_id))
            if sales_contract_id:
                stmt = stmt.where(ShippingPlanItem.sales_contract_id == _uid(sales_contract_id))
            if warehouse_id:
                stmt = stmt.where(ShippingPlanItem.warehouse_id == _uid(warehouse_id))
        else:
            stmt = select(ShippingPlan).options(selectinload(ShippingPlan.items))

        if start_date:
            stmt = stmt.where(ShippingPlan.planned_date >= start_date)
        if end_date:
            stmt = stmt.where(ShippingPlan.planned_date <= end_date)
        if brand_id:
            stmt = stmt.where(ShippingPlan.brand_id == _uid(brand_id))
        if supplier_enterprise_id:
            stmt = stmt.where(ShippingPlan.supplier_enterprise_id == _uid(supplier_enterprise_id))
        if purchase_contract_id:
            stmt = stmt.where(ShippingPlan.purchase_contract_id == _uid(purchase_contract_id))
        if status:
            stmt = stmt.where(ShippingPlan.status == status)

        stmt = stmt.order_by(ShippingPlan.planned_date.asc(), ShippingPlan.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())


class ShippingPlanItemRepository(BaseRepository[ShippingPlanItem]):
    """计划明细 Repository"""

    def __init__(self, session):
        super().__init__(ShippingPlanItem, session, entity_name="计划明细")


class ShipmentRepository(BaseRepository[Shipment]):
    """发货记录 Repository"""

    def __init__(self, session):
        super().__init__(Shipment, session, entity_name="发货记录")

    async def get_by_shipment_no(self, shipment_no: str) -> Shipment | None:
        """按发货编号查询"""
        stmt = select(Shipment).where(Shipment.shipment_no == shipment_no)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_items(self, shipment_id: UUID) -> Shipment | None:
        """查询发货记录（含明细）"""
        stmt = (
            select(Shipment)
            .where(Shipment.id == shipment_id)
            .options(selectinload(Shipment.items))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        plan_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Shipment]:
        """多条件查询发货记录列表（含明细和计划关联）"""
        from sqlalchemy.orm import joinedload
        stmt = (
            select(Shipment)
            .options(
                selectinload(Shipment.items).selectinload(ShipmentItem.plan_item),
                joinedload(Shipment.plan).selectinload(ShippingPlan.items),
            )
        )
        if plan_id:
            stmt = stmt.where(Shipment.plan_id == plan_id)
        if start_date:
            stmt = stmt.where(Shipment.shipped_date >= start_date)
        if end_date:
            stmt = stmt.where(Shipment.shipped_date <= end_date)
        stmt = stmt.order_by(Shipment.shipped_date.desc(), Shipment.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())


class ShipmentItemRepository(BaseRepository[ShipmentItem]):
    """发货明细 Repository"""

    def __init__(self, session):
        super().__init__(ShipmentItem, session, entity_name="发货明细")
