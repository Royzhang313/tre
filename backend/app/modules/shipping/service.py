"""货运模块 —— Service 层 V2"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.shipping.models import (
    DeliveryMethod,
    PlanStatus,
    Shipment,
    ShipmentItem,
    ShipmentStatus,
    ShippingPlan,
    ShippingPlanItem,
)
from app.modules.shipping.repository import (
    ShipmentItemRepository,
    ShipmentRepository,
    ShippingPlanItemRepository,
    ShippingPlanRepository,
)
from app.modules.shipping.schemas import (
    ShipmentCreate,
    ShipmentUpdate,
    ShippingPlanCreate,
    ShippingPlanDateUpdate,
    ShippingPlanUpdate,
)
from app.shared.audit_helper import audit_record, orm_to_dict


class ShippingPlanService:
    """货运计划 Service —— 品牌→采购合同为主维度"""

    def __init__(self, repo: ShippingPlanRepository, item_repo: ShippingPlanItemRepository):
        self.repo = repo
        self.item_repo = item_repo

    async def create(self, data: ShippingPlanCreate, user_id: UUID, tenant_id: UUID) -> ShippingPlan:
        """创建货运计划"""
        total_qty = Decimal("0")

        plan = ShippingPlan(
            tenant_id=tenant_id,
            company_id=data.company_id,
            brand_id=data.brand_id,
            supplier_enterprise_id=data.supplier_enterprise_id,
            purchase_contract_id=data.purchase_contract_id,
            planned_date=data.planned_date,
            delivery_method=DeliveryMethod(data.delivery_method or "SH"),
            status=PlanStatus.PENDING,
            remark=data.remark,
            tags=data.tags,
            created_by=user_id,
        )
        await self.repo.create(plan)

        for i, it in enumerate(data.items, 1):
            total_qty += it.planned_quantity
            item = ShippingPlanItem(
                plan_id=plan.id,
                line_no=i,
                customer_enterprise_id=it.customer_enterprise_id,
                sales_contract_id=it.sales_contract_id,
                model_id=it.model_id,
                warehouse_id=it.warehouse_id,
                planned_quantity=it.planned_quantity,
                unit=it.unit,
                purchase_price=it.purchase_price,
                sale_price=it.sale_price,
                surcharge_type=it.surcharge_type,
                surcharge_amount=it.surcharge_amount,
            )
            await self.item_repo.create(item)

        plan.total_planned_quantity = total_qty
        await self.repo.update(plan)

        plan = await self.repo.get_with_items(plan.id) or plan
        await audit_record(session=self.repo.session, action="create", entity_type="shipping_plan", entity_id=plan.id, after=orm_to_dict(plan))
        return plan

    async def update(self, plan_id: UUID, data: ShippingPlanUpdate) -> ShippingPlan:
        obj = await self.repo.get_with_items(plan_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("计划不存在", entity="ShippingPlan", entity_id=plan_id)
        # 记录修改前的完整数据（含明细）
        before_dict = orm_to_dict(obj)
        before_dict["items"] = [{k: v for k, v in orm_to_dict(it).items()} for it in obj.items]

        update_dict = data.model_dump(exclude_unset=True)
        items_data = update_dict.pop("items", None)

        # 更新 header 字段
        for k, v in update_dict.items():
            setattr(obj, k, v)

        # 更新明细行
        if items_data is not None:
            item_map = {it.id: it for it in obj.items}
            for it_data in items_data:
                item = item_map.get(it_data["id"])
                if item is None:
                    continue
                for k, v in it_data.items():
                    if k != "id" and v is not None:
                        setattr(item, k, v)
            await self._recalc_totals(plan_id)

        await self.repo.update(obj)
        # 记录修改后完整数据（含明细）
        after_dict = orm_to_dict(obj)
        after_dict["items"] = [{k: v for k, v in orm_to_dict(it).items()} for it in obj.items]
        await audit_record(session=self.repo.session, action="update", entity_type="shipping_plan", entity_id=obj.id, before=before_dict, after=after_dict)
        return obj

    async def change_date(self, plan_id: UUID, data: ShippingPlanDateUpdate) -> ShippingPlan:
        obj = await self.repo.get_by_id_or_raise(plan_id)
        old_date = obj.planned_date
        obj.planned_date = data.planned_date
        await self.repo.update(obj)
        before_dict = {"planned_date": old_date}
        after_dict = {"planned_date": data.planned_date}
        await audit_record(
            session=self.repo.session, action="update", entity_type="shipping_plan",
            entity_id=obj.id,
            before=before_dict, after=after_dict,
            remark=f"日期 {old_date} → {data.planned_date}",
        )
        return obj

    async def cancel(self, plan_id: UUID) -> None:
        obj = await self.repo.get_by_id_or_raise(plan_id)
        if obj.status == PlanStatus.CANCELLED:
            raise ConflictError("计划已取消", entity="ShippingPlan")
        before = orm_to_dict(obj)
        obj.status = PlanStatus.CANCELLED
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="cancel", entity_type="shipping_plan", entity_id=obj.id, before=before, after=orm_to_dict(obj))

    async def _recalc_totals(self, plan_id: UUID) -> None:
        plan = await self.repo.get_with_items(plan_id)
        if plan:
            plan.total_planned_quantity = sum((it.planned_quantity for it in plan.items), Decimal("0"))
            await self.repo.update(plan)


class ShipmentService:
    """发货 Service"""

    def __init__(
        self,
        repo: ShipmentRepository,
        item_repo: ShipmentItemRepository,
        plan_repo: ShippingPlanRepository,
        plan_item_repo: ShippingPlanItemRepository,
    ):
        self.repo = repo
        self.item_repo = item_repo
        self.plan_repo = plan_repo
        self.plan_item_repo = plan_item_repo

    async def create(self, plan_id: UUID, data: ShipmentCreate, user_id: UUID) -> Shipment:
        plan = await self.plan_repo.get_with_items(plan_id)
        if plan is None:
            raise NotFoundError("计划不存在", entity="ShippingPlan", entity_id=plan_id)
        if plan.status == PlanStatus.CANCELLED:
            raise ConflictError("已取消的计划不能发货", entity="ShippingPlan")

        shipment_no = f"FH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        while await self.repo.get_by_shipment_no(shipment_no):
            shipment_no = f"FH-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        total_qty = Decimal("0")
        plan_item_map: dict[UUID, ShippingPlanItem] = {it.id: it for it in plan.items}

        for it in data.items:
            plan_item = plan_item_map.get(it.plan_item_id)
            if plan_item is None:
                raise NotFoundError("计划明细不存在", entity="ShippingPlanItem", entity_id=it.plan_item_id)
            available = plan_item.planned_quantity - plan_item.shipped_quantity
            if it.shipped_quantity > available:
                raise ConflictError(
                    f"发货数量({it.shipped_quantity}吨)超过可发数量({available}吨)",
                    entity="ShippingPlanItem",
                )
            total_qty += it.shipped_quantity

        freight_unit_price = None
        if data.freight_total and total_qty > 0:
            base_price = data.freight_total / total_qty
            if data.freight_tax_rate:
                freight_unit_price = (base_price * data.freight_tax_rate).quantize(Decimal("0.0001"))
            else:
                freight_unit_price = base_price.quantize(Decimal("0.0001"))

        shipment = Shipment(
            plan_id=plan_id,
            shipment_no=shipment_no,
            shipped_date=data.shipped_date,
            driver_name=data.driver_name,
            driver_phone=data.driver_phone,
            driver_license_plate=data.driver_license_plate,
            driver_id_card=data.driver_id_card,
            freight_total=data.freight_total,
            freight_unit_price=freight_unit_price,
            freight_tax_rate=data.freight_tax_rate,
            status=ShipmentStatus.SHIPPED,
            remark=data.remark,
            created_by=user_id,
        )
        await self.repo.create(shipment)

        for it in data.items:
            shipment_item = ShipmentItem(
                shipment_id=shipment.id,
                plan_item_id=it.plan_item_id,
                shipped_quantity=it.shipped_quantity,
                unit=it.unit,
            )
            await self.item_repo.create(shipment_item)

            plan_item = plan_item_map[it.plan_item_id]
            plan_item.shipped_quantity += it.shipped_quantity
            await self.plan_item_repo.update(plan_item)

        all_shipped = all(it.shipped_quantity >= it.planned_quantity for it in plan_item_map.values())
        if all_shipped:
            plan.status = PlanStatus.COMPLETED
        elif any(it.shipped_quantity > 0 for it in plan_item_map.values()):
            plan.status = PlanStatus.PARTIALLY_SHIPPED
        await self.plan_repo.update(plan)

        shipment = await self.repo.get_with_items(shipment.id) or shipment
        await audit_record(session=self.repo.session, action="create", entity_type="shipment", entity_id=shipment.id, after=orm_to_dict(shipment))
        return shipment

    async def update(self, shipment_id: UUID, data: ShipmentUpdate) -> Shipment:
        obj = await self.repo.get_by_id_or_raise(shipment_id)
        before = orm_to_dict(obj)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="update", entity_type="shipment", entity_id=obj.id, before=before, after=orm_to_dict(obj))
        return obj
