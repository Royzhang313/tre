"""品牌模块 —— Router"""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import async_session_factory
from app.modules.brand.repository import BrandModelRepository, BrandRepository, BrandWarehouseRepository
from app.modules.brand.schemas import BrandCreate, BrandModelCreate, BrandModelReorderRequest, BrandReorderRequest, BrandUpdate, BrandWarehouseCreate, BrandWarehouseReorderRequest
from app.modules.brand.service import BrandModelService, BrandService, BrandWarehouseService
from app.shared.base_schema import APIResponse, PageResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/brand", tags=["品牌管理"])


async def _make_brand_svc() -> AsyncGenerator[BrandService, None]:
    async with async_session_factory() as session:
        yield BrandService(repo=BrandRepository(session)); await session.commit()


async def _make_bw_svc() -> AsyncGenerator[BrandWarehouseService, None]:
    async with async_session_factory() as session:
        yield BrandWarehouseService(repo=BrandWarehouseRepository(session)); await session.commit()


async def _make_bm_svc() -> AsyncGenerator[BrandModelService, None]:
    async with async_session_factory() as session:
        yield BrandModelService(repo=BrandModelRepository(session)); await session.commit()


# ============================================================
# Brand
# ============================================================


@router.post("/brands")
async def create_brand(body: BrandCreate, svc=Depends(_make_brand_svc)):
    obj = await svc.create(body)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/brands")
async def list_brands():
    async with async_session_factory() as session:
        repo = BrandRepository(session)
        items = await repo.list_active()
    return APIResponse.ok({"items": [{**_to_dict(i), "color": i.color} for i in items], "total": len(items)})


@router.get("/brands/{brand_id}")
async def get_brand(brand_id: UUID):
    async with async_session_factory() as session:
        repo = BrandRepository(session)
        obj = await repo.get_full(brand_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("品牌不存在", entity="Brand", entity_id=brand_id)
        d = _to_dict(obj)
        d["color"] = obj.color
        d["warehouses"] = [_to_dict(bw) for bw in obj.warehouses if bw.is_active]
        d["models"] = [_to_dict(bm) for bm in obj.models if bm.is_active]
    return APIResponse.ok(d)


@router.put("/brands/{brand_id}")
async def update_brand(brand_id: UUID, body: BrandUpdate, svc=Depends(_make_brand_svc)):
    obj = await svc.update(brand_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.patch("/brands/reorder")
async def reorder_brands(body: BrandReorderRequest):
    """拖拽排序 —— 批量更新 sort_order"""
    async with async_session_factory() as session:
        repo = BrandRepository(session)
        for item in body.items:
            obj = await repo.get_by_id_or_raise(item.id)
            obj.sort_order = item.sort_order
            await repo.update(obj)
        await session.commit()
    return APIResponse.ok(None, message="排序已更新")


@router.get("/brands/{brand_id}/check-references")
async def check_brand_references(brand_id: UUID):
    """检查品牌是否被采购合同/销售合同/发货计划引用"""
    async with async_session_factory() as session:
        repo = BrandRepository(session)
        ref = await repo.check_brand_referenced(brand_id)
    return APIResponse.ok({"referenced": ref is not None, "ref_table": ref})


@router.delete("/brands/{brand_id}")
async def delete_brand(brand_id: UUID, svc=Depends(_make_brand_svc)):
    await svc.soft_delete(brand_id)
    return APIResponse.ok(None, message="已停用")


# ============================================================
# Brand Warehouse
# ============================================================


@router.post("/warehouses")
async def add_warehouse(body: BrandWarehouseCreate, svc=Depends(_make_bw_svc)):
    obj = await svc.create(body)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/brands/{brand_id}/warehouses")
async def list_warehouses(brand_id: UUID, page: int = Query(default=1, ge=1), page_size: int = Query(default=5, ge=1, le=100)):
    async with async_session_factory() as session:
        repo = BrandWarehouseRepository(session)
        all_items = await repo.list_active_by_brand(brand_id)
        total = len(all_items)
        start = (page - 1) * page_size
        items = all_items[start:start + page_size]
    return APIResponse.ok(PageResponse.from_list([_to_dict(i) for i in items], total, page, page_size).model_dump())


@router.patch("/warehouses/reorder")
async def reorder_warehouses(body: BrandWarehouseReorderRequest):
    """拖拽排序 —— 批量更新仓库 sort_order"""
    async with async_session_factory() as session:
        repo = BrandWarehouseRepository(session)
        for item in body.items:
            obj = await repo.get_by_id_or_raise(item.id)
            obj.sort_order = item.sort_order
            await repo.update(obj)
        await session.commit()
    return APIResponse.ok(None, message="排序已更新")


@router.put("/warehouses/{obj_id}")
async def update_warehouse(obj_id: UUID, body: dict, svc=Depends(_make_bw_svc)):
    obj = await svc.update(obj_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/brands/{brand_id}/shipping-warehouses")
async def list_shipping_warehouses(brand_id: UUID):
    """返回品牌关联的物理仓库列表（按名称匹配 brand_warehouses.name）"""
    async with async_session_factory() as session:
        from app.modules.brand.repository import BrandWarehouseRepository
        from app.modules.basedata.repository import WarehouseRepository
        bw_repo = BrandWarehouseRepository(session)
        wh_repo = WarehouseRepository(session)
        brand_whs = await bw_repo.list_active_by_brand(brand_id)
        brand_wh_names = [bw.name for bw in brand_whs]
        all_whs = await wh_repo.list(offset=0, limit=500)
        # 按名称模糊匹配（品牌仓库名称 vs 物理仓库名称）
        matched = []
        for wh in all_whs:
            for bn in brand_wh_names:
                if bn in wh.name or wh.name in bn:
                    matched.append(_to_dict(wh))
                    break
    return APIResponse.ok({"items": matched, "total": len(matched)})


@router.get("/warehouses/{obj_id}/check-references")
async def check_warehouse_references(obj_id: UUID):
    """检查发货仓库是否被采购合同/销售合同/发货计划引用"""
    async with async_session_factory() as session:
        repo = BrandWarehouseRepository(session)
        ref = await repo.check_warehouse_referenced(obj_id)
    return APIResponse.ok({"referenced": ref is not None, "ref_table": ref})


@router.delete("/warehouses/{obj_id}")
async def delete_warehouse(obj_id: UUID, svc=Depends(_make_bw_svc)):
    await svc.soft_delete(obj_id)
    return APIResponse.ok(None, message="已停用")


# ============================================================
# Brand Model
# ============================================================


@router.post("/models")
async def add_model(body: BrandModelCreate, svc=Depends(_make_bm_svc)):
    obj = await svc.create(body)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/brands/{brand_id}/models")
async def list_models(brand_id: UUID, page: int = Query(default=1, ge=1), page_size: int = Query(default=5, ge=1, le=100)):
    async with async_session_factory() as session:
        repo = BrandModelRepository(session)
        all_items = await repo.list_active_by_brand(brand_id)
        total = len(all_items)
        start = (page - 1) * page_size
        items = all_items[start:start + page_size]
    return APIResponse.ok(PageResponse.from_list([_to_dict(i) for i in items], total, page, page_size).model_dump())


@router.patch("/models/reorder")
async def reorder_models(body: BrandModelReorderRequest):
    """拖拽排序 —— 批量更新型号 sort_order"""
    async with async_session_factory() as session:
        repo = BrandModelRepository(session)
        for item in body.items:
            obj = await repo.get_by_id_or_raise(item.id)
            obj.sort_order = item.sort_order
            await repo.update(obj)
        await session.commit()
    return APIResponse.ok(None, message="排序已更新")


@router.put("/models/{obj_id}")
async def update_model(obj_id: UUID, body: dict, svc=Depends(_make_bm_svc)):
    obj = await svc.update(obj_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/models/{obj_id}/check-references")
async def check_model_references(obj_id: UUID):
    """检查品牌型号是否被采购合同/销售合同/发货计划引用"""
    async with async_session_factory() as session:
        repo = BrandModelRepository(session)
        ref = await repo.check_model_referenced(obj_id)
    return APIResponse.ok({"referenced": ref is not None, "ref_table": ref})


@router.delete("/models/{obj_id}")
async def delete_model(obj_id: UUID, svc=Depends(_make_bm_svc)):
    await svc.soft_delete(obj_id)
    return APIResponse.ok(None, message="已停用")
