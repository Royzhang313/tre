"""品牌模块 —— Repository"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.brand.models import Brand, BrandModel, BrandWarehouse
from app.shared.base_repository import BaseRepository


class BrandRepository(BaseRepository[Brand]):
    def __init__(self, session: AsyncSession):
        super().__init__(Brand, session, entity_name="品牌")

    async def get_by_name(self, name: str) -> Brand | None:
        """查重：仅查活跃数据，已删除的不计"""
        r = await self.session.execute(
            select(Brand).where(Brand.name == name, Brand.is_active == True)
        )
        return r.scalar_one_or_none()

    async def get_full(self, brand_id: UUID) -> Brand | None:
        return await self._get_with_relations(brand_id, active_only=True)

    async def get_with_relations(self, brand_id: UUID) -> Brand | None:
        """带关系的完整加载（用于删除等写操作）"""
        return await self._get_with_relations(brand_id, active_only=False)

    async def _get_with_relations(self, brand_id: UUID, active_only: bool) -> Brand | None:
        filters = [Brand.id == brand_id]
        if active_only:
            filters.append(Brand.is_active == True)
        r = await self.session.execute(
            select(Brand).where(*filters)
            .options(selectinload(Brand.warehouses), selectinload(Brand.models))
        )
        return r.scalar_one_or_none()

    async def list_active(self) -> list[Brand]:
        r = await self.session.execute(
            select(Brand).where(Brand.is_active == True).order_by(Brand.sort_order.asc())
        )
        return list(r.scalars().all())

    async def get_max_sort_order(self) -> int:
        r = await self.session.execute(
            select(Brand.sort_order).where(Brand.is_active == True).order_by(Brand.sort_order.desc()).limit(1)
        )
        val = r.scalar()
        return val if val is not None else 0

    async def check_brand_referenced(self, brand_id: UUID) -> str | None:
        """检查品牌是否被业务单据引用。返回首个引用表名，无引用返回 None。"""
        from app.modules.purchase_contract.models import PurchaseContractItem
        from app.modules.sales_contract.models import SalesContractItem
        from app.modules.shipping.models import ShippingPlan

        checks: list[tuple[type, str]] = [
            (PurchaseContractItem, "采购合同明细"),
            (SalesContractItem, "销售合同明细"),
            (ShippingPlan, "发货计划"),
        ]
        for model_cls, label in checks:
            r: Any = await self.session.execute(
                select(model_cls).where(getattr(model_cls, "brand_id") == brand_id).limit(1)
            )
            if r.scalar_one_or_none():
                return label
        return None


class BrandWarehouseRepository(BaseRepository[BrandWarehouse]):
    def __init__(self, session: AsyncSession):
        super().__init__(BrandWarehouse, session, entity_name="品牌仓库")

    async def list_active_by_brand(self, brand_id: UUID) -> list[BrandWarehouse]:
        r = await self.session.execute(
            select(BrandWarehouse)
            .where(BrandWarehouse.brand_id == brand_id, BrandWarehouse.is_active == True)
            .order_by(BrandWarehouse.sort_order.asc())
        )
        return list(r.scalars().all())

    async def get_max_sort_order(self, brand_id: UUID) -> int:
        r = await self.session.execute(
            select(BrandWarehouse.sort_order)
            .where(BrandWarehouse.brand_id == brand_id, BrandWarehouse.is_active == True)
            .order_by(BrandWarehouse.sort_order.desc()).limit(1)
        )
        val = r.scalar()
        return val if val is not None else 0

    async def check_warehouse_referenced(self, warehouse_id: UUID) -> str | None:
        """检查仓库是否被业务单据引用。返回首个引用表名，无引用返回 None。"""
        from app.modules.purchase_contract.models import PurchaseContractItem
        from app.modules.sales_contract.models import SalesContractItem
        from app.modules.shipping.models import ShippingPlanItem

        checks: list[tuple[type, str, str]] = [
            (PurchaseContractItem, "shipping_warehouse_id", "采购合同明细"),
            (SalesContractItem, "shipping_warehouse_id", "销售合同明细"),
            (ShippingPlanItem, "warehouse_id", "发货计划明细"),
        ]
        for model_cls, col, label in checks:
            r: Any = await self.session.execute(
                select(model_cls).where(getattr(model_cls, col) == warehouse_id).limit(1)
            )
            if r.scalar_one_or_none():
                return label
        return None


class BrandModelRepository(BaseRepository[BrandModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(BrandModel, session, entity_name="品牌型号")

    async def list_active_by_brand(self, brand_id: UUID) -> list[BrandModel]:
        r = await self.session.execute(
            select(BrandModel)
            .where(BrandModel.brand_id == brand_id, BrandModel.is_active == True)
            .order_by(BrandModel.sort_order.asc())
        )
        return list(r.scalars().all())

    async def get_max_sort_order(self, brand_id: UUID) -> int:
        r = await self.session.execute(
            select(BrandModel.sort_order)
            .where(BrandModel.brand_id == brand_id, BrandModel.is_active == True)
            .order_by(BrandModel.sort_order.desc()).limit(1)
        )
        val = r.scalar()
        return val if val is not None else 0

    async def check_model_referenced(self, model_id: UUID) -> str | None:
        """检查型号是否被业务单据引用。返回首个引用表名，无引用返回 None。"""
        from app.modules.purchase_contract.models import PurchaseContractItem
        from app.modules.sales_contract.models import SalesContractItem
        from app.modules.shipping.models import ShippingPlanItem

        checks: list[tuple[type, str]] = [
            (PurchaseContractItem, "采购合同明细"),
            (SalesContractItem, "销售合同明细"),
            (ShippingPlanItem, "发货计划明细"),
        ]
        for model_cls, label in checks:
            r: Any = await self.session.execute(
                select(model_cls).where(getattr(model_cls, "model_id") == model_id).limit(1)
            )
            if r.scalar_one_or_none():
                return label
        return None
