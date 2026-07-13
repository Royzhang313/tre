"""货运模块 —— FastAPI Router"""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import async_session_factory
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
from app.modules.shipping.service import ShipmentService, ShippingPlanService
from app.shared.base_schema import APIResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/shipping", tags=["货运管理"])


def _shipment_item_dict(si: Any) -> dict:
    """发货明细 → 包含关联计划行的客户/型号/仓库/销售合同"""
    d = _to_dict(si)
    if hasattr(si, "plan_item") and si.plan_item:
        d["model_id"] = str(si.plan_item.model_id)
        d["warehouse_id"] = str(si.plan_item.warehouse_id)
        d["customer_enterprise_id"] = str(si.plan_item.customer_enterprise_id)
        d["sales_contract_id"] = str(si.plan_item.sales_contract_id)
    return d


async def _make_plan_svc() -> AsyncGenerator[ShippingPlanService, None]:
    async with async_session_factory() as session:
        yield ShippingPlanService(
            repo=ShippingPlanRepository(session),
            item_repo=ShippingPlanItemRepository(session),
        )
        await session.commit()


async def _make_ship_svc() -> AsyncGenerator[ShipmentService, None]:
    async with async_session_factory() as session:
        yield ShipmentService(
            repo=ShipmentRepository(session),
            item_repo=ShipmentItemRepository(session),
            plan_repo=ShippingPlanRepository(session),
            plan_item_repo=ShippingPlanItemRepository(session),
        )
        await session.commit()


# ============================================================
# 货运计划
# ============================================================


@router.post("/plans")
async def create_plan(body: ShippingPlanCreate, svc=Depends(_make_plan_svc)):
    """创建货运计划"""
    from uuid import uuid4
    obj = await svc.create(body, user_id=uuid4(), tenant_id=uuid4())
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/contract-usage")
async def contract_usage():
    """查询所有采购合同和销售合同的已计划用量，用于计算可发/可提数量"""
    async with async_session_factory() as session:
        from sqlalchemy import select, func
        from app.modules.shipping.models import ShippingPlan, ShippingPlanItem

        # 采购合同用量：按 purchase_contract_id 聚合 total_planned_quantity
        pc_q = (
            select(ShippingPlan.purchase_contract_id, func.sum(ShippingPlan.total_planned_quantity))
            .where(ShippingPlan.status != "cancelled")
            .group_by(ShippingPlan.purchase_contract_id)
        )
        pc_rows = (await session.execute(pc_q)).all()

        # 销售合同用量：按明细的 sales_contract_id 聚合 planned_quantity
        sc_q = (
            select(ShippingPlanItem.sales_contract_id, func.sum(ShippingPlanItem.planned_quantity))
            .join(ShippingPlan, ShippingPlanItem.plan_id == ShippingPlan.id)
            .where(ShippingPlan.status != "cancelled")
            .group_by(ShippingPlanItem.sales_contract_id)
        )
        sc_rows = (await session.execute(sc_q)).all()

    return APIResponse.ok({
        "purchase_usage": {str(row[0]): float(row[1] or 0) for row in pc_rows},
        "sales_usage": {str(row[0]): float(row[1] or 0) for row in sc_rows},
    })


@router.get("/plans")
async def list_plans(
    start_date: str | None = Query(default=None, description="开始日期 YYYY-MM-DD"),
    end_date: str | None = Query(default=None, description="结束日期 YYYY-MM-DD"),
    brand_id: str | None = Query(default=None),
    warehouse_id: str | None = Query(default=None, description="按计划明细仓库筛选"),
    supplier_enterprise_id: str | None = Query(default=None),
    customer_enterprise_id: str | None = Query(default=None, description="按计划明细客户筛选"),
    purchase_contract_id: str | None = Query(default=None),
    sales_contract_id: str | None = Query(default=None, description="按计划明细销售合同筛选"),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=500, ge=1, le=500),
):
    """查询计划列表（支持多维筛选）"""
    async with async_session_factory() as session:
        repo = ShippingPlanRepository(session)
        has_filters = any([
            brand_id, warehouse_id, supplier_enterprise_id,
            customer_enterprise_id, purchase_contract_id, sales_contract_id, status,
        ])
        if start_date and end_date and not has_filters:
            # 仅日期范围筛选（保留旧路径兼容）
            items = await repo.list_by_date_range(start_date, end_date, offset=0, limit=page_size)
        elif has_filters or (start_date and end_date):
            items = await repo.list_filtered(
                start_date=start_date, end_date=end_date,
                brand_id=brand_id, supplier_enterprise_id=supplier_enterprise_id,
                purchase_contract_id=purchase_contract_id, customer_enterprise_id=customer_enterprise_id,
                sales_contract_id=sales_contract_id, warehouse_id=warehouse_id,
                status=status, offset=0, limit=page_size,
            )
        else:
            items = await repo.list_all_with_items(offset=(page - 1) * page_size, limit=page_size)
    result = []
    for p in items:
        d = _to_dict(p)
        d["items"] = [_to_dict(it) for it in p.items]
        result.append(d)
    return APIResponse.ok({"items": result, "total": len(result)})


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: UUID):
    """获取计划详情"""
    async with async_session_factory() as session:
        repo = ShippingPlanRepository(session)
        obj = await repo.get_with_items(plan_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("计划不存在", entity="ShippingPlan", entity_id=plan_id)
        d = _to_dict(obj)
        d["items"] = [_to_dict(it) for it in obj.items]
        d["shipments"] = []
        for s in obj.shipments:
            sd = _to_dict(s)
            sd["items"] = [_to_dict(si) for si in s.items]
            d["shipments"].append(sd)
    return APIResponse.ok(d)


@router.put("/plans/{plan_id}")
async def update_plan(plan_id: UUID, body: ShippingPlanUpdate, svc=Depends(_make_plan_svc)):
    """更新计划"""
    obj = await svc.update(plan_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.patch("/plans/{plan_id}/date")
async def change_plan_date(plan_id: UUID, body: ShippingPlanDateUpdate, svc=Depends(_make_plan_svc)):
    """拖拽修改计划日期"""
    obj = await svc.change_date(plan_id, body)
    return APIResponse.ok({"id": str(obj.id), "planned_date": obj.planned_date})


@router.delete("/plans/{plan_id}")
async def cancel_plan(plan_id: UUID, svc=Depends(_make_plan_svc)):
    """取消计划"""
    await svc.cancel(plan_id)
    return APIResponse.ok(None, message="已取消")


# ============================================================
# 发货
# ============================================================


@router.post("/plans/{plan_id}/shipments")
async def create_shipment(plan_id: UUID, body: ShipmentCreate, svc=Depends(_make_ship_svc)):
    """创建发货记录"""
    from uuid import uuid4
    obj = await svc.create(plan_id, body, user_id=uuid4())
    return APIResponse.ok({"id": str(obj.id), "shipment_no": obj.shipment_no})


@router.get("/shipments")
async def list_shipments(
    plan_id: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
):
    """查询发货台账列表（含计划摘要和明细）"""
    async with async_session_factory() as session:
        repo = ShipmentRepository(session)
        items = await repo.list_filtered(
            plan_id=plan_id, start_date=start_date, end_date=end_date,
            offset=(page - 1) * page_size, limit=page_size,
        )
    result = []
    for s in items:
        d = _to_dict(s)
        # 计划摘要
        if s.plan:
            d["plan"] = {
                "id": str(s.plan.id),
                "brand_id": str(s.plan.brand_id),
                "planned_date": s.plan.planned_date,
                "delivery_method": s.plan.delivery_method,
                "total_planned_quantity": float(s.plan.total_planned_quantity) if s.plan.total_planned_quantity else 0,
                "supplier_enterprise_id": str(s.plan.supplier_enterprise_id),
                "purchase_contract_id": str(s.plan.purchase_contract_id),
            }
        d["items"] = [_shipment_item_dict(si) for si in s.items]
        result.append(d)
    return APIResponse.ok({"items": result, "total": len(result)})


@router.get("/shipments/{shipment_id}")
async def get_shipment(shipment_id: UUID):
    """获取发货详情"""
    async with async_session_factory() as session:
        repo = ShipmentRepository(session)
        obj = await repo.get_with_items(shipment_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("发货记录不存在", entity="Shipment", entity_id=shipment_id)
        d = _to_dict(obj)
        d["items"] = [_shipment_item_dict(si) for si in obj.items]
    return APIResponse.ok(d)


@router.put("/shipments/{shipment_id}")
async def update_shipment(shipment_id: UUID, body: ShipmentUpdate, svc=Depends(_make_ship_svc)):
    """更新发货记录"""
    obj = await svc.update(shipment_id, body)
    return APIResponse.ok({"id": str(obj.id)})
