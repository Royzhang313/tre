"""库存模块 —— FastAPI Router

包含：
- 品牌维度库存统计（聚合视图，过渡方案）
- 合同货权库存 CRUD（ContractStock）
- 库存操作：收货入库、锁货、发运交付
- 批次管理
- 实物库存查询
"""

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query

from app.core.database import async_session_factory
from app.modules.inventory.repository import (
    BatchRepository,
    ContractStockRepository,
    InventoryLedgerRepository,
    WarehouseStockRepository,
)
from app.modules.inventory.schemas import (
    BatchCreate,
    BatchResponse,
    BatchUpdate,
    ContractStockCreate,
    ContractStockListResponse,
    ContractStockResponse,
    ContractStockUpdate,
    InventoryByBrand,
    InventoryByWarehouse,
    InventoryLedgerResponse,
    InventoryStatsResponse,
    InventoryWarehouseStatsResponse,
    StockAllocationRequest,
    StockDeliveryRequest,
    StockReceiptRequest,
    WarehouseStockResponse,
)
from app.modules.inventory.service import BatchService, ContractStockService
from app.shared.base_schema import APIResponse, PageResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/inventory", tags=["库存管理"])


# ============================================================
# 依赖注入
# ============================================================

async def _make_cs_svc() -> AsyncGenerator[ContractStockService, None]:
    async with async_session_factory() as session:
        yield ContractStockService(
            repo=ContractStockRepository(session),
            ledger_repo=InventoryLedgerRepository(session),
            wh_stock_repo=WarehouseStockRepository(session),
            batch_repo=BatchRepository(session),
        )
        await session.commit()


async def _make_batch_svc() -> AsyncGenerator[BatchService, None]:
    async with async_session_factory() as session:
        yield BatchService(repo=BatchRepository(session))
        await session.commit()


# ============================================================
# 品牌维度库存统计（过渡方案 —— 聚合视图）
# ============================================================

def _date_bounds() -> dict:
    """返回本月/上月/本季/本年的边界日期"""
    today = datetime.now()
    y = today.year
    m = today.month
    this_m = today.replace(day=1).strftime("%Y-%m-%d")
    if m == 12:
        next_m = today.replace(year=y + 1, month=1, day=1).strftime("%Y-%m-%d")
    else:
        next_m = today.replace(month=m + 1, day=1).strftime("%Y-%m-%d")
    if m == 1:
        last_m = today.replace(year=y - 1, month=12, day=1).strftime("%Y-%m-%d")
    else:
        last_m = today.replace(month=m - 1, day=1).strftime("%Y-%m-%d")
    q_start = ((m - 1) // 3) * 3 + 1
    q_first = today.replace(month=q_start, day=1).strftime("%Y-%m-%d")
    if q_start + 3 > 12:
        q_next = today.replace(year=y + 1, month=1, day=1).strftime("%Y-%m-%d")
    else:
        q_next = today.replace(month=q_start + 3, day=1).strftime("%Y-%m-%d")
    y_first = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    y_next = today.replace(year=y + 1, month=1, day=1).strftime("%Y-%m-%d")
    return {
        "tm": this_m, "nm": next_m, "lm": last_m,
        "qf": q_first, "qn": q_next, "yf": y_first, "yn": y_next,
    }


async def _aggregate() -> list[InventoryByBrand]:
    """按品牌聚合采购/销售/发货数据"""
    from sqlalchemy import text

    bd = _date_bounds()
    async with async_session_factory() as session:
        sql = text(f"""
            SELECT
                b.id          AS brand_id,
                b.name        AS brand_name,
                b.color       AS brand_color,
                COALESCE(pc.qty, 0) AS purchased_qty,
                COALESCE(sc.qty, 0) AS sold_qty,
                COALESCE(sp.qty, 0) AS shipped_qty,
                COALESCE(sm.qty, 0) AS shipped_this_month,
                COALESCE(lm.qty, 0) AS shipped_last_month,
                COALESCE(sq.qty, 0) AS shipped_this_quarter,
                COALESCE(sy.qty, 0) AS shipped_this_year,
                COALESCE(pc.qty, 0) - COALESCE(sc.qty, 0) AS stock_after_sale,
                COALESCE(pc.qty, 0) - COALESCE(sp.qty, 0) AS stock_after_ship
            FROM brands b
            LEFT JOIN (
                SELECT pci.brand_id, ROUND(SUM(pci.quantity), 2) AS qty
                FROM purchase_contract_items pci
                JOIN purchase_contracts pc2 ON pc2.id = pci.contract_id
                WHERE pc2.status != 'cancelled'
                GROUP BY pci.brand_id
            ) pc ON pc.brand_id = b.id
            LEFT JOIN (
                SELECT sci.brand_id, ROUND(SUM(sci.quantity), 2) AS qty
                FROM sales_contract_items sci
                JOIN sales_contracts sc2 ON sc2.id = sci.contract_id
                WHERE sc2.status != 'cancelled'
                GROUP BY sci.brand_id
            ) sc ON sc.brand_id = b.id
            LEFT JOIN (
                SELECT sp2.brand_id, ROUND(SUM(spi.shipped_quantity), 2) AS qty
                FROM shipping_plan_items spi
                JOIN shipping_plans sp2 ON sp2.id = spi.plan_id
                WHERE sp2.status != 'cancelled'
                GROUP BY sp2.brand_id
            ) sp ON sp.brand_id = b.id
            LEFT JOIN (
                SELECT sp2.brand_id, ROUND(SUM(si.shipped_quantity), 2) AS qty
                FROM shipment_items si
                JOIN shipments s ON s.id = si.shipment_id
                JOIN shipping_plan_items spi2 ON spi2.id = si.plan_item_id
                JOIN shipping_plans sp2 ON sp2.id = spi2.plan_id
                WHERE s.shipped_date >= '{bd["tm"]}' AND s.shipped_date < '{bd["nm"]}'
                GROUP BY sp2.brand_id
            ) sm ON sm.brand_id = b.id
            LEFT JOIN (
                SELECT sp2.brand_id, ROUND(SUM(si.shipped_quantity), 2) AS qty
                FROM shipment_items si
                JOIN shipments s ON s.id = si.shipment_id
                JOIN shipping_plan_items spi2 ON spi2.id = si.plan_item_id
                JOIN shipping_plans sp2 ON sp2.id = spi2.plan_id
                WHERE s.shipped_date >= '{bd["lm"]}' AND s.shipped_date < '{bd["tm"]}'
                GROUP BY sp2.brand_id
            ) lm ON lm.brand_id = b.id
            LEFT JOIN (
                SELECT sp2.brand_id, ROUND(SUM(si.shipped_quantity), 2) AS qty
                FROM shipment_items si
                JOIN shipments s ON s.id = si.shipment_id
                JOIN shipping_plan_items spi2 ON spi2.id = si.plan_item_id
                JOIN shipping_plans sp2 ON sp2.id = spi2.plan_id
                WHERE s.shipped_date >= '{bd["qf"]}' AND s.shipped_date < '{bd["qn"]}'
                GROUP BY sp2.brand_id
            ) sq ON sq.brand_id = b.id
            LEFT JOIN (
                SELECT sp2.brand_id, ROUND(SUM(si.shipped_quantity), 2) AS qty
                FROM shipment_items si
                JOIN shipments s ON s.id = si.shipment_id
                JOIN shipping_plan_items spi2 ON spi2.id = si.plan_item_id
                JOIN shipping_plans sp2 ON sp2.id = spi2.plan_id
                WHERE s.shipped_date >= '{bd["yf"]}' AND s.shipped_date < '{bd["yn"]}'
                GROUP BY sp2.brand_id
            ) sy ON sy.brand_id = b.id
            WHERE b.is_active = 1
            ORDER BY b.sort_order ASC, b.name ASC
        """)
        r = await session.execute(sql)
        rows = r.fetchall()

    return [
        InventoryByBrand(
            brand_id=row.brand_id,
            brand_name=row.brand_name,
            brand_color=row.brand_color,
            purchased_qty=float(row.purchased_qty),
            sold_qty=float(row.sold_qty),
            shipped_qty=float(row.shipped_qty),
            shipped_this_month=float(row.shipped_this_month),
            shipped_last_month=float(row.shipped_last_month),
            shipped_this_quarter=float(row.shipped_this_quarter),
            shipped_this_year=float(row.shipped_this_year),
            stock_after_sale=float(row.stock_after_sale),
            stock_after_ship=float(row.stock_after_ship),
        )
        for row in rows
    ]


@router.get("/stats")
async def inventory_stats():
    """品牌维度库存统计"""
    items = await _aggregate()
    return APIResponse.ok(
        InventoryStatsResponse(
            items=items,
            total_purchased=round(sum(i.purchased_qty for i in items), 2),
            total_sold=round(sum(i.sold_qty for i in items), 2),
            total_shipped=round(sum(i.shipped_qty for i in items), 2),
            total_stock_after_sale=round(sum(i.stock_after_sale for i in items), 2),
            total_stock_after_ship=round(sum(i.stock_after_ship for i in items), 2),
        ).model_dump()
    )


# ============================================================
# ContractStock（合同货权库存）CRUD
# ============================================================


@router.post("/contract-stocks")
async def create_contract_stock(body: ContractStockCreate, svc=Depends(_make_cs_svc)):
    """创建合同货权库存记录（通常由合同确认事件自动触发）"""
    stock = await svc.create_from_contract(
        product_id=body.product_id,
        purchase_contract_id=body.purchase_contract_id,
        supplier_id=body.supplier_id,
        tenant_id=uuid4(),
        qty_contracted=body.qty_contracted,
    )
    return APIResponse.ok({"id": str(stock.id)})


@router.get("/contract-stocks")
async def list_contract_stocks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    product_id: UUID | None = Query(default=None, description="按产品筛选"),
    supplier_id: UUID | None = Query(default=None, description="按供应商筛选"),
    is_closed: bool | None = Query(default=None, description="是否已关结"),
):
    """合同货权库存列表"""
    async with async_session_factory() as session:
        repo = ContractStockRepository(session)
        if product_id:
            items = await repo.list_by_product(product_id)
        elif supplier_id:
            items = await repo.list_by_supplier(supplier_id)
        else:
            items = await repo.list_active(
                offset=(page - 1) * page_size,
                limit=page_size,
                is_closed=is_closed,
            )
        total = await repo.count() if not product_id and not supplier_id else len(items)
        # 如果按 product/supplier 筛选，手动分页
        if product_id or supplier_id:
            total = len(items)
            items = items[(page - 1) * page_size : page * page_size]

    result = []
    for cs in items:
        d = _to_dict(cs)
        d["qty_available"] = float(cs.qty_available)
        d["status_label"] = cs.status_label
        result.append(d)
    return APIResponse.ok(
        PageResponse.from_list(result, total, page, page_size).model_dump()
    )


@router.get("/contract-stocks/{stock_id}")
async def get_contract_stock(stock_id: UUID):
    """合同货权库存详情"""
    async with async_session_factory() as session:
        repo = ContractStockRepository(session)
        cs = await repo.get_by_id_or_raise(stock_id)
    d = _to_dict(cs)
    d["qty_available"] = float(cs.qty_available)
    d["status_label"] = cs.status_label
    return APIResponse.ok(d)


@router.put("/contract-stocks/{stock_id}")
async def update_contract_stock(stock_id: UUID, body: ContractStockUpdate):
    """更新合同货权库存（手动调整）"""
    async with async_session_factory() as session:
        repo = ContractStockRepository(session)
        cs = await repo.get_by_id_or_raise(stock_id)
        update_dict = body.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(cs, k, v)
        await repo.update(cs)
        await session.commit()
    d = _to_dict(cs)
    d["qty_available"] = float(cs.qty_available)
    d["status_label"] = cs.status_label
    return APIResponse.ok(d)


# ============================================================
# 库存操作：收货入库 / 锁货 / 发运交付
# ============================================================


@router.post("/contract-stocks/receipt")
async def receipt_stock(body: StockReceiptRequest, svc=Depends(_make_cs_svc)):
    """收货入库 —— 在途 → 在仓"""
    stock = await svc.receipt(
        contract_stock_id=body.contract_stock_id,
        receipt_qty=body.receipt_qty,
        warehouse_id=body.warehouse_id,
        tenant_id=uuid4(),
    )
    d = _to_dict(stock)
    d["qty_available"] = float(stock.qty_available)
    d["status_label"] = stock.status_label
    return APIResponse.ok(d)


@router.post("/contract-stocks/allocate")
async def allocate_stock(body: StockAllocationRequest, svc=Depends(_make_cs_svc)):
    """锁货 —— 为销售合同分配库存"""
    stock = await svc.allocate(
        contract_stock_id=body.contract_stock_id,
        allocate_qty=body.allocate_qty,
        tenant_id=uuid4(),
        sales_contract_id=body.sales_contract_id,
    )
    d = _to_dict(stock)
    d["qty_available"] = float(stock.qty_available)
    d["status_label"] = stock.status_label
    return APIResponse.ok(d)


@router.post("/contract-stocks/deliver")
async def deliver_stock(body: StockDeliveryRequest, svc=Depends(_make_cs_svc)):
    """发运交付 —— 已分配 → 已发运"""
    stock = await svc.deliver(
        contract_stock_id=body.contract_stock_id,
        deliver_qty=body.deliver_qty,
        tenant_id=uuid4(),
    )
    d = _to_dict(stock)
    d["qty_available"] = float(stock.qty_available)
    d["status_label"] = stock.status_label
    return APIResponse.ok(d)


# ============================================================
# 库存分类账
# ============================================================


@router.get("/contract-stocks/{stock_id}/ledger")
async def get_stock_ledger(
    stock_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    """查询某个货权库存的分类账"""
    async with async_session_factory() as session:
        repo = InventoryLedgerRepository(session)
        items = await repo.list_by_stock(stock_id, offset=(page - 1) * page_size, limit=page_size)
        from sqlalchemy import func, select
        from app.modules.inventory.models import InventoryLedger

        count_stmt = select(func.count()).select_from(InventoryLedger).where(
            InventoryLedger.contract_stock_id == stock_id
        )
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()
    result = [_to_dict(it) for it in items]
    return APIResponse.ok(PageResponse.from_list(result, total, page, page_size).model_dump())


# ============================================================
# 批次管理
# ============================================================


@router.post("/batches")
async def create_batch(body: BatchCreate, svc=Depends(_make_batch_svc)):
    """创建批次"""
    batch = await svc.create_batch(
        product_id=body.product_id,
        batch_number=body.batch_number,
        quantity=body.quantity,
        cost_price=body.cost_price,
        purchase_contract_id=body.purchase_contract_id,
        warehouse_id=body.warehouse_id,
        receipt_date=body.receipt_date,
        tenant_id=uuid4(),
    )
    return APIResponse.ok({"id": str(batch.id)})


@router.get("/batches")
async def list_batches(
    product_id: UUID | None = Query(default=None, description="按产品筛选"),
    contract_id: UUID | None = Query(default=None, description="按采购合同筛选"),
):
    """批次列表"""
    async with async_session_factory() as session:
        repo = BatchRepository(session)
        if product_id:
            items = await repo.list_by_product(product_id)
        elif contract_id:
            items = await repo.list_by_contract(contract_id)
        else:
            items = await repo.list(offset=0, limit=200)
    result = [_to_dict(b) for b in items]
    return APIResponse.ok({"items": result, "total": len(result)})


@router.get("/batches/{batch_id}")
async def get_batch(batch_id: UUID):
    """批次详情"""
    async with async_session_factory() as session:
        repo = BatchRepository(session)
        batch = await repo.get_by_id_or_raise(batch_id)
    return APIResponse.ok(_to_dict(batch))


@router.put("/batches/{batch_id}")
async def update_batch(batch_id: UUID, body: BatchUpdate):
    """更新批次"""
    async with async_session_factory() as session:
        repo = BatchRepository(session)
        batch = await repo.get_by_id_or_raise(batch_id)
        update_dict = body.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            setattr(batch, k, v)
        await repo.update(batch)
        await session.commit()
    return APIResponse.ok(_to_dict(batch))


# ============================================================
# 实物库存查询
# ============================================================


@router.get("/warehouse-stocks")
async def list_warehouse_stocks(
    warehouse_id: UUID | None = Query(default=None, description="按仓库筛选"),
):
    """实物库存列表"""
    async with async_session_factory() as session:
        repo = WarehouseStockRepository(session)
        if warehouse_id:
            items = await repo.list_by_warehouse(warehouse_id)
        else:
            items = await repo.list(offset=0, limit=500)
    result = [_to_dict(ws) for ws in items]
    return APIResponse.ok({"items": result, "total": len(result)})
