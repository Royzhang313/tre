"""首页仪表盘 —— 汇总统计"""
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.shared.base_schema import APIResponse

router = APIRouter(tags=["仪表盘"])


@router.get("/dashboard/stats")
async def dashboard_stats():
    """首页汇总统计"""
    async with async_session_factory() as session:
        # 采购合同
        from app.modules.purchase_contract.models import PurchaseContract, PurchaseContractItem
        pc_total_r = await session.execute(
            select(func.count(PurchaseContract.id)).where(PurchaseContract.status != "cancelled")
        )
        pc_count = pc_total_r.scalar() or 0
        pc_amt_r = await session.execute(
            select(func.coalesce(func.sum(PurchaseContract.total_amount), 0))
            .where(PurchaseContract.status != "cancelled")
        )
        pc_amount = float(pc_amt_r.scalar() or 0)
        pc_qty_r = await session.execute(
            select(func.coalesce(func.sum(PurchaseContract.total_quantity), 0))
            .where(PurchaseContract.status != "cancelled")
        )
        pc_quantity = float(pc_qty_r.scalar() or 0)

        # 销售合同
        from app.modules.sales_contract.models import SalesContract
        sc_total_r = await session.execute(
            select(func.count(SalesContract.id)).where(SalesContract.status != "cancelled")
        )
        sc_count = sc_total_r.scalar() or 0
        sc_amt_r = await session.execute(
            select(func.coalesce(func.sum(SalesContract.total_amount), 0))
            .where(SalesContract.status != "cancelled")
        )
        sc_amount = float(sc_amt_r.scalar() or 0)
        sc_qty_r = await session.execute(
            select(func.coalesce(func.sum(SalesContract.total_quantity), 0))
            .where(SalesContract.status != "cancelled")
        )
        sc_quantity = float(sc_qty_r.scalar() or 0)

        # 发货计划
        from app.modules.shipping.models import ShippingPlan
        sp_total_r = await session.execute(
            select(func.count(ShippingPlan.id)).where(ShippingPlan.status != "cancelled")
        )
        sp_count = sp_total_r.scalar() or 0
        sp_active_r = await session.execute(
            select(func.count(ShippingPlan.id)).where(
                ShippingPlan.status.in_(["pending", "in_progress", "partially_shipped"])
            )
        )
        sp_active = sp_active_r.scalar() or 0
        sp_qty_r = await session.execute(
            select(func.coalesce(func.sum(ShippingPlan.total_planned_quantity), 0))
        )
        sp_quantity = float(sp_qty_r.scalar() or 0)

        # 发货记录
        from app.modules.shipping.models import Shipment
        sh_total_r = await session.execute(select(func.count(Shipment.id)))
        sh_count = sh_total_r.scalar() or 0

        # 企业数
        from app.modules.basedata.models import Enterprise
        ent_r = await session.execute(
            select(func.count(Enterprise.id)).where(Enterprise.is_active == True)
        )
        ent_count = ent_r.scalar() or 0

        # 品牌数
        from app.modules.brand.models import Brand
        brand_r = await session.execute(
            select(func.count(Brand.id)).where(Brand.is_active == True)
        )
        brand_count = brand_r.scalar() or 0

        # 主体公司数
        from app.modules.basedata.models import Company
        comp_r = await session.execute(
            select(func.count(Company.id)).where(Company.is_active == True)
        )
        comp_count = comp_r.scalar() or 0

        # AR 应收 / AP 应付
        from app.modules.finance.models import ARReceipt, APPayment
        ar_r = await session.execute(
            select(func.coalesce(func.sum(ARReceipt.amount), 0))
        )
        ar_amount = float(ar_r.scalar() or 0)
        ap_r = await session.execute(
            select(func.coalesce(func.sum(APPayment.amount), 0))
        )
        ap_amount = float(ap_r.scalar() or 0)

    return APIResponse.ok({
        "purchase": {"count": pc_count, "amount": pc_amount, "quantity": pc_quantity},
        "sales": {"count": sc_count, "amount": sc_amount, "quantity": sc_quantity},
        "shipping_plan": {"count": sp_count, "active": sp_active, "quantity": sp_quantity},
        "shipment": {"count": sh_count},
        "enterprise_count": ent_count,
        "brand_count": brand_count,
        "company_count": comp_count,
        "ar_amount": ar_amount,
        "ap_amount": ap_amount,
    })
