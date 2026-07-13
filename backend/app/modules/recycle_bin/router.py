"""回收站 —— FastAPI Router

聚合查询所有已删除（停用/作废）的数据，支持恢复和永久删除。
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.core.database import async_session_factory
from app.shared.base_schema import APIResponse, PageResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/recycle-bin", tags=["回收站"])

# 支持回收的实体类型
ENTITY_TYPES = {
    # 基础资料
    "enterprise": {"table": "basedata_enterprises", "label": "企业", "name_col": "name", "filter": "is_active = 0"},
    "company": {"table": "basedata_companies", "label": "主体公司", "name_col": "name", "filter": "is_active = 0"},
    "warehouse": {"table": "basedata_warehouses", "label": "仓库", "name_col": "name", "filter": "is_active = 0"},
    "commission_platform": {"table": "basedata_commission_platforms", "label": "撮合平台", "name_col": "name", "filter": "is_active = 0"},
    # 品牌
    "brand": {"table": "brands", "label": "品牌", "name_col": "name", "filter": "is_active = 0"},
    "brand_warehouse": {"table": "brand_warehouses", "label": "品牌仓库", "name_col": "name", "filter": "is_active = 0"},
    "brand_model": {"table": "brand_models", "label": "品牌型号", "name_col": "model_name", "filter": "is_active = 0"},
    # 合同
    "purchase_contract": {"table": "purchase_contracts", "label": "采购合同", "name_col": "contract_no", "filter": "status = 'cancelled'"},
    "sales_contract": {"table": "sales_contracts", "label": "销售合同", "name_col": "contract_no", "filter": "status = 'cancelled'"},
    # 货运
    "shipping_plan": {"table": "shipping_plans", "label": "发货计划", "name_col": "id", "filter": "status = 'cancelled'"},
    "shipment": {"table": "shipments", "label": "发货记录", "name_col": "shipment_no", "filter": "status = 'voided'"},
    # 财务
    "ar_receipt": {"table": "ar_receipts", "label": "收款", "name_col": "receipt_no", "filter": "status = 'voided'"},
    "ap_payment": {"table": "ap_payments", "label": "付款", "name_col": "payment_no", "filter": "status = 'voided'"},
}


def _row_to_dict(row: Any) -> dict:
    """将 sqlalchemy Row 转为普通 dict"""
    return dict(row._mapping) if hasattr(row, '_mapping') else dict(row)


async def _fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    from sqlalchemy import text

    async with async_session_factory() as session:
        r = await session.execute(text(sql), params)
        rows = r.fetchall()
        return [_row_to_dict(row) for row in rows]


async def _execute(sql: str, params: dict | None = None) -> None:
    from sqlalchemy import text

    async with async_session_factory() as session:
        await session.execute(text(sql), params or {})
        await session.commit()


@router.get("")
async def list_recycle_bin(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """聚合查询所有已删除数据"""
    all_items: list[dict] = []

    for etype, info in ENTITY_TYPES.items():
        table = info["table"]
        try:
            name_col = info["name_col"]
            sql = f"SELECT id, {name_col} as display_name, updated_at as deleted_at FROM {table} WHERE {info['filter']} ORDER BY updated_at DESC"
            rows = await _fetch_all(sql)
            for row in rows:
                all_items.append({
                    "entity_type": etype,
                    "entity_label": info["label"],
                    "entity_id": str(row["id"]) if isinstance(row["id"], UUID) else row["id"],
                    "display_name": row.get("display_name") or str(row["id"])[:8],
                    "deleted_at": str(row["deleted_at"])[:19] if row.get("deleted_at") else "",
                })
        except Exception:
            pass  # 表可能还不存在

    # 分页
    total = len(all_items)
    start = (page - 1) * page_size
    paged = all_items[start:start + page_size]
    return APIResponse.ok(PageResponse.from_list(paged, total, page, page_size).model_dump())


@router.patch("/{entity_type}/{entity_id}/restore")
async def restore(entity_type: str, entity_id: str):
    """恢复已删除数据"""
    info = ENTITY_TYPES.get(entity_type)
    if not info:
        return JSONResponse(status_code=400, content={"code": 400, "message": f"未知实体类型: {entity_type}"})

    table = info["table"]
    try:
        # 根据 filter 判断恢复方式：is_active → 设 1，status → 设 pending/pending_execution
        filter_col = info["filter"].split()[0]
        if filter_col == "is_active":
            sql = f"UPDATE {table} SET is_active = 1, updated_at = :now WHERE id = :eid"
        else:
            sql = f"UPDATE {table} SET status = 'pending', updated_at = :now WHERE id = :eid"
        await _execute(sql, {"eid": entity_id, "now": datetime.utcnow().isoformat()})
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "message": str(e)})

    return APIResponse.ok(None, message="已恢复")


@router.delete("/{entity_type}/{entity_id}")
async def permanent_delete(entity_type: str, entity_id: str):
    """永久删除"""
    info = ENTITY_TYPES.get(entity_type)
    if not info:
        return JSONResponse(status_code=400, content={"code": 400, "message": f"未知实体类型: {entity_type}"})

    table = info["table"]
    try:
        # 先删子表（如果有）
        if entity_type == "purchase_contract":
            await _execute("DELETE FROM purchase_contract_items WHERE contract_id = :eid", {"eid": entity_id})
        elif entity_type == "sales_contract":
            await _execute("DELETE FROM sales_contract_items WHERE contract_id = :eid", {"eid": entity_id})
        elif entity_type == "enterprise":
            await _execute("DELETE FROM basedata_enterprise_contacts WHERE enterprise_id = :eid", {"eid": entity_id})

        await _execute(f"DELETE FROM {table} WHERE id = :eid", {"eid": entity_id})
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "message": str(e)})

    return APIResponse.ok(None, message="已永久删除")
