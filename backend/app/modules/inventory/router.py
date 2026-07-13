"""库存统计 —— 聚合视图（SQL GROUP BY 优化）"""
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select, text

from app.core.database import async_session_factory
from app.modules.inventory.schemas import (
    InventoryByBrand,
    InventoryByWarehouse,
    InventoryStatsResponse,
    InventoryWarehouseStatsResponse,
)
from app.shared.base_schema import APIResponse

router = APIRouter(prefix="/inventory", tags=["库存统计"])


def _date_bounds() -> dict:
    """返回本月/上月/本季/本年的边界日期"""
    today = datetime.now()
    y = today.year; m = today.month
    # 月
    this_m = today.replace(day=1).strftime("%Y-%m-%d")
    if m == 12: next_m = today.replace(year=y+1, month=1, day=1).strftime("%Y-%m-%d")
    else: next_m = today.replace(month=m+1, day=1).strftime("%Y-%m-%d")
    if m == 1: last_m = today.replace(year=y-1, month=12, day=1).strftime("%Y-%m-%d")
    else: last_m = today.replace(month=m-1, day=1).strftime("%Y-%m-%d")
    # 季
    q_start = ((m - 1) // 3) * 3 + 1
    q_first = today.replace(month=q_start, day=1).strftime("%Y-%m-%d")
    if q_start + 3 > 12: q_next = today.replace(year=y+1, month=1, day=1).strftime("%Y-%m-%d")
    else: q_next = today.replace(month=q_start+3, day=1).strftime("%Y-%m-%d")
    # 年
    y_first = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    y_next = today.replace(year=y+1, month=1, day=1).strftime("%Y-%m-%d")
    return {"tm": this_m, "nm": next_m, "lm": last_m, "qf": q_first, "qn": q_next, "yf": y_first, "yn": y_next}


async def _aggregate() -> list[InventoryByBrand]:
    """按品牌聚合采购/销售/发货数据 —— 全在数据库完成，无需 Python 遍历"""
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
    return APIResponse.ok(InventoryStatsResponse(
        items=items,
        total_purchased=round(sum(i.purchased_qty for i in items), 2),
        total_sold=round(sum(i.sold_qty for i in items), 2),
        total_shipped=round(sum(i.shipped_qty for i in items), 2),
        total_stock_after_sale=round(sum(i.stock_after_sale for i in items), 2),
        total_stock_after_ship=round(sum(i.stock_after_ship for i in items), 2),
    ).model_dump())


async def _aggregate_warehouse() -> list[InventoryByWarehouse]:
    """按品牌+仓库聚合采购/销售/发货数据"""
    bd = _date_bounds()
    async with async_session_factory() as session:
        sql = text(f"""
            SELECT
                b.id          AS brand_id,
                b.name        AS brand_name,
                b.color       AS brand_color,
                bw.id         AS warehouse_id,
                bw.name       AS warehouse_name,
                COALESCE(pc.qty, 0) AS purchased_qty,
                COALESCE(sc.qty, 0) AS sold_qty,
                COALESCE(sp.qty, 0) AS shipped_qty,
                COALESCE(sm.qty, 0) AS shipped_this_month,
                COALESCE(lm.qty, 0) AS shipped_last_month,
                COALESCE(sq.qty, 0) AS shipped_this_quarter,
                COALESCE(sy.qty, 0) AS shipped_this_year,
                COALESCE(pc.qty, 0) - COALESCE(sc.qty, 0) AS stock_after_sale,
                COALESCE(pc.qty, 0) - COALESCE(sp.qty, 0) AS stock_after_ship
            FROM brand_warehouses bw
            JOIN brands b ON b.id = bw.brand_id AND b.is_active = 1
            LEFT JOIN (
                SELECT pci.shipping_warehouse_id AS wh_id,
                       pci.brand_id,
                       ROUND(SUM(pci.quantity), 2) AS qty
                FROM purchase_contract_items pci
                JOIN purchase_contracts pc2 ON pc2.id = pci.contract_id
                WHERE pc2.status != 'cancelled'
                GROUP BY pci.shipping_warehouse_id, pci.brand_id
            ) pc ON pc.wh_id = bw.id AND pc.brand_id = b.id
            LEFT JOIN (
                SELECT sci.shipping_warehouse_id AS wh_id,
                       sci.brand_id,
                       ROUND(SUM(sci.quantity), 2) AS qty
                FROM sales_contract_items sci
                JOIN sales_contracts sc2 ON sc2.id = sci.contract_id
                WHERE sc2.status != 'cancelled'
                GROUP BY sci.shipping_warehouse_id, sci.brand_id
            ) sc ON sc.wh_id = bw.id AND sc.brand_id = b.id
            LEFT JOIN (
                SELECT spi.warehouse_id AS wh_id,
                       sp2.brand_id,
                       ROUND(SUM(spi.shipped_quantity), 2) AS qty
                FROM shipping_plan_items spi
                JOIN shipping_plans sp2 ON sp2.id = spi.plan_id
                WHERE sp2.status != 'cancelled'
                GROUP BY spi.warehouse_id, sp2.brand_id
            ) sp ON sp.wh_id = bw.id AND sp.brand_id = b.id
            LEFT JOIN (
                SELECT spi2.warehouse_id AS wh_id,
                       sp2.brand_id,
                       ROUND(SUM(si.shipped_quantity), 2) AS qty
                FROM shipment_items si
                JOIN shipments s ON s.id = si.shipment_id
                JOIN shipping_plan_items spi2 ON spi2.id = si.plan_item_id
                JOIN shipping_plans sp2 ON sp2.id = spi2.plan_id
                WHERE s.shipped_date >= '{bd["tm"]}' AND s.shipped_date < '{bd["nm"]}'
                GROUP BY spi2.warehouse_id, sp2.brand_id
            ) sm ON sm.wh_id = bw.id AND sm.brand_id = b.id
            LEFT JOIN (
                SELECT spi2.warehouse_id AS wh_id,
                       sp2.brand_id,
                       ROUND(SUM(si.shipped_quantity), 2) AS qty
                FROM shipment_items si
                JOIN shipments s ON s.id = si.shipment_id
                JOIN shipping_plan_items spi2 ON spi2.id = si.plan_item_id
                JOIN shipping_plans sp2 ON sp2.id = spi2.plan_id
                WHERE s.shipped_date >= '{bd["lm"]}' AND s.shipped_date < '{bd["tm"]}'
                GROUP BY spi2.warehouse_id, sp2.brand_id
            ) lm ON lm.wh_id = bw.id AND lm.brand_id = b.id
            LEFT JOIN (
                SELECT spi2.warehouse_id AS wh_id,
                       sp2.brand_id,
                       ROUND(SUM(si.shipped_quantity), 2) AS qty
                FROM shipment_items si
                JOIN shipments s ON s.id = si.shipment_id
                JOIN shipping_plan_items spi2 ON spi2.id = si.plan_item_id
                JOIN shipping_plans sp2 ON sp2.id = spi2.plan_id
                WHERE s.shipped_date >= '{bd["qf"]}' AND s.shipped_date < '{bd["qn"]}'
                GROUP BY spi2.warehouse_id, sp2.brand_id
            ) sq ON sq.wh_id = bw.id AND sq.brand_id = b.id
            LEFT JOIN (
                SELECT spi2.warehouse_id AS wh_id,
                       sp2.brand_id,
                       ROUND(SUM(si.shipped_quantity), 2) AS qty
                FROM shipment_items si
                JOIN shipments s ON s.id = si.shipment_id
                JOIN shipping_plan_items spi2 ON spi2.id = si.plan_item_id
                JOIN shipping_plans sp2 ON sp2.id = spi2.plan_id
                WHERE s.shipped_date >= '{bd["yf"]}' AND s.shipped_date < '{bd["yn"]}'
                GROUP BY spi2.warehouse_id, sp2.brand_id
            ) sy ON sy.wh_id = bw.id AND sy.brand_id = b.id
            WHERE bw.is_active = 1
            ORDER BY b.sort_order ASC, b.name ASC, bw.sort_order ASC, bw.name ASC
        """)
        r = await session.execute(sql)
        rows = r.fetchall()

    return [
        InventoryByWarehouse(
            brand_id=row.brand_id,
            brand_name=row.brand_name,
            brand_color=row.brand_color,
            warehouse_id=row.warehouse_id,
            warehouse_name=row.warehouse_name,
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


@router.get("/warehouse-stats")
async def warehouse_stats():
    """品牌+仓库维度库存统计"""
    items = await _aggregate_warehouse()
    return APIResponse.ok(InventoryWarehouseStatsResponse(
        items=items,
        total_purchased=round(sum(i.purchased_qty for i in items), 2),
        total_sold=round(sum(i.sold_qty for i in items), 2),
        total_shipped=round(sum(i.shipped_qty for i in items), 2),
        total_stock_after_sale=round(sum(i.stock_after_sale for i in items), 2),
        total_stock_after_ship=round(sum(i.stock_after_ship for i in items), 2),
    ).model_dump())
