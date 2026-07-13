"""产品模块 —— FastAPI Router（MVP）"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import async_session_factory
from app.modules.product.repository import ProductRepository
from app.modules.product.schemas import ProductCreate, ProductUpdate
from app.modules.product.service import ProductService
from app.shared.base_schema import APIResponse, PageResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/products", tags=["产品管理"])


async def _make_svc() -> AsyncGenerator[ProductService, None]:
    async with async_session_factory() as session:
        yield ProductService(repo=ProductRepository(session))
        await session.commit()


# ============================================================
# CRUD
# ============================================================


@router.post("")
async def create_product(body: ProductCreate, svc=Depends(_make_svc)):
    """创建产品"""
    obj = await svc.create(body)
    return APIResponse.ok({"id": str(obj.id), "product_code": obj.product_code})


@router.get("")
async def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    search: str | None = Query(default=None, description="搜索关键词（名称/编码/品牌）"),
    model_type: str | None = Query(default=None, description="型号类型筛选"),
    is_active: bool | None = Query(default=None, description="启用状态筛选"),
):
    """产品列表（支持分页和筛选）"""
    async with async_session_factory() as session:
        repo = ProductRepository(session)
        items = await repo.list_all_with_filters(
            offset=(page - 1) * page_size,
            limit=page_size,
            search=search,
            model_type=model_type,
            is_active=is_active,
        )
        total = await repo.count_with_filters(
            search=search,
            model_type=model_type,
            is_active=is_active,
        )
    result = [_to_dict(p) for p in items]
    return APIResponse.ok(
        PageResponse.from_list(result, total, page, page_size).model_dump()
    )


@router.get("/{product_id}")
async def get_product(product_id: UUID):
    """产品详情"""
    async with async_session_factory() as session:
        repo = ProductRepository(session)
        obj = await repo.get_by_id_or_raise(product_id)
    return APIResponse.ok(_to_dict(obj))


@router.put("/{product_id}")
async def update_product(product_id: UUID, body: ProductUpdate, svc=Depends(_make_svc)):
    """更新产品"""
    obj = await svc.update(product_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/{product_id}")
async def delete_product(product_id: UUID, svc=Depends(_make_svc)):
    """停用产品"""
    await svc.delete(product_id)
    return APIResponse.ok(None, message="产品已停用")


# ============================================================
# 快捷查询
# ============================================================


@router.get("/check-code/{code}")
async def check_product_code(code: str):
    """校验产品编码是否已存在"""
    async with async_session_factory() as session:
        repo = ProductRepository(session)
        existing = await repo.get_by_product_code(code)
    return APIResponse.ok({"exists": existing is not None})
