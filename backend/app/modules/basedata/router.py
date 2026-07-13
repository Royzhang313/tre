"""基础资料 —— Router（SaaS 多租户版）

所有 API 端点通过依赖注入获取 tenant_id，实现租户数据隔离。

注意：
- 当前 MVP 阶段使用默认租户 ID（后续从 JWT token 或 Header 解析）
- 生产环境需通过 TenantMiddleware 或 get_current_tenant 依赖注入
"""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Query

from app.core.database import async_session_factory
from app.modules.basedata.repository import CommissionPlatformRepository, CompanyRepository, EnterpriseRepository, WarehouseRepository
from app.modules.basedata.schemas import CommissionPlatformCreate, CommissionPlatformUpdate, CompanyCreate, CompanyUpdate, EnterpriseCreate, EnterpriseUpdate, WarehouseCreate, WarehouseUpdate
from app.modules.basedata.service import CommissionPlatformService, CompanyService, EnterpriseService, WarehouseService
from app.shared.base_schema import APIResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/basedata", tags=["基础资料"])

# ============================================================
# Tenant ID 获取 —— MVP 阶段从 Header 读取，默认 uuid4
# 生产环境替换为从 JWT 解析或 TenantMiddleware 注入
# ============================================================

# 默认租户（开发阶段，后续从 JWT/Header 获取）
_DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")


async def _get_tenant_id(x_tenant_id: str | None = Header(default=None)) -> UUID:
    """从请求 Header 获取租户 ID

    生产环境：从 JWT token 解析或中间件注入
    MVP 阶段：从 X-Tenant-ID Header 读取，默认使用固定租户 ID
    """
    if x_tenant_id:
        try:
            return UUID(x_tenant_id)
        except ValueError:
            pass
    return _DEFAULT_TENANT_ID


# ============================================================
# Service 工厂依赖
# ============================================================


async def _make_ent_svc() -> AsyncGenerator[EnterpriseService, None]:
    async with async_session_factory() as session:
        yield EnterpriseService(repo=EnterpriseRepository(session))
        await session.commit()


async def _make_comp_svc() -> AsyncGenerator[CompanyService, None]:
    async with async_session_factory() as session:
        yield CompanyService(repo=CompanyRepository(session))
        await session.commit()


async def _make_wh_svc() -> AsyncGenerator[WarehouseService, None]:
    async with async_session_factory() as session:
        yield WarehouseService(repo=WarehouseRepository(session))
        await session.commit()


async def _make_cp_svc() -> AsyncGenerator[CommissionPlatformService, None]:
    async with async_session_factory() as session:
        yield CommissionPlatformService(repo=CommissionPlatformRepository(session))
        await session.commit()


# ============================================================
# Enterprise（企业）
# ============================================================


@router.post("/enterprises")
async def create_enterprise(
    body: EnterpriseCreate,
    tenant_id: UUID = Depends(_get_tenant_id),
    svc=Depends(_make_ent_svc),
):
    obj = await svc.create(body, tenant_id)
    return APIResponse.ok({"id": str(obj.id), "tenant_id": str(obj.tenant_id)})


@router.get("/enterprises")
async def list_enterprises(
    tenant_id: UUID = Depends(_get_tenant_id),
):
    async with async_session_factory() as session:
        repo = EnterpriseRepository(session)
        items = await repo.list_all(tenant_id)
    result = []
    for e in items:
        d = _to_dict(e)
        d["contacts"] = [_to_dict(c) for c in e.contacts]
        result.append(d)
    return APIResponse.ok({"items": result, "total": len(result)})


@router.get("/enterprises/{obj_id}")
async def get_enterprise(
    obj_id: UUID,
    tenant_id: UUID = Depends(_get_tenant_id),
):
    async with async_session_factory() as session:
        repo = EnterpriseRepository(session)
        obj = await repo.get_with_contacts(obj_id, tenant_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("企业不存在", entity="Enterprise", entity_id=obj_id)
        d = _to_dict(obj)
        d["contacts"] = [_to_dict(c) for c in obj.contacts]
    return APIResponse.ok(d)


@router.put("/enterprises/{obj_id}")
async def update_enterprise(
    obj_id: UUID,
    body: EnterpriseUpdate,
    tenant_id: UUID = Depends(_get_tenant_id),
    svc=Depends(_make_ent_svc),
):
    obj = await svc.update(obj_id, body, tenant_id)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/enterprises/{obj_id}")
async def delete_enterprise(
    obj_id: UUID,
    svc=Depends(_make_ent_svc),
):
    await svc.delete(obj_id)
    return APIResponse.ok(None, message="已停用")


# ============================================================
# Company（执行主体公司）
# ============================================================


@router.post("/companies")
async def create_company(
    body: CompanyCreate,
    tenant_id: UUID = Depends(_get_tenant_id),
    svc=Depends(_make_comp_svc),
):
    obj = await svc.create(body, tenant_id)
    return APIResponse.ok({"id": str(obj.id), "tenant_id": str(obj.tenant_id)})


@router.get("/companies")
async def list_companies(
    tenant_id: UUID = Depends(_get_tenant_id),
):
    async with async_session_factory() as session:
        repo = CompanyRepository(session)
        items = await repo.list_active(tenant_id)
    return APIResponse.ok({"items": [_to_dict(c) for c in items], "total": len(items)})


@router.get("/companies/{obj_id}")
async def get_company(
    obj_id: UUID,
):
    async with async_session_factory() as session:
        repo = CompanyRepository(session)
        obj = await repo.get_by_id_or_raise(obj_id)
    return APIResponse.ok(_to_dict(obj))


@router.put("/companies/{obj_id}")
async def update_company(
    obj_id: UUID,
    body: CompanyUpdate,
    tenant_id: UUID = Depends(_get_tenant_id),
    svc=Depends(_make_comp_svc),
):
    obj = await svc.update(obj_id, body, tenant_id)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/companies/{obj_id}")
async def delete_company(
    obj_id: UUID,
    svc=Depends(_make_comp_svc),
):
    await svc.delete(obj_id)
    return APIResponse.ok(None, message="已停用")


# ============================================================
# Warehouse（仓库）
# ============================================================


@router.post("/warehouses")
async def create_warehouse(
    body: WarehouseCreate,
    tenant_id: UUID = Depends(_get_tenant_id),
    svc=Depends(_make_wh_svc),
):
    obj = await svc.create(body, tenant_id)
    return APIResponse.ok({"id": str(obj.id), "tenant_id": str(obj.tenant_id)})


@router.get("/warehouses")
async def list_warehouses(
    tenant_id: UUID = Depends(_get_tenant_id),
):
    async with async_session_factory() as session:
        repo = WarehouseRepository(session)
        items = await repo.list(
            offset=0,
            limit=500,
            filters=(Warehouse.tenant_id == tenant_id,) if tenant_id else None,
        )
    return APIResponse.ok({"items": [_to_dict(w) for w in items], "total": len(items)})


@router.get("/warehouses/{obj_id}")
async def get_warehouse(
    obj_id: UUID,
):
    async with async_session_factory() as session:
        repo = WarehouseRepository(session)
        obj = await repo.get_by_id_or_raise(obj_id)
    return APIResponse.ok(_to_dict(obj))


@router.put("/warehouses/{obj_id}")
async def update_warehouse(
    obj_id: UUID,
    body: WarehouseUpdate,
    svc=Depends(_make_wh_svc),
):
    obj = await svc.update(obj_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/warehouses/{obj_id}")
async def delete_warehouse(
    obj_id: UUID,
    svc=Depends(_make_wh_svc),
):
    await svc.delete(obj_id)
    return APIResponse.ok(None, message="已停用")


# ============================================================
# CommissionPlatform（撮合平台）
# ============================================================


@router.post("/commission-platforms")
async def create_commission_platform(
    body: CommissionPlatformCreate,
    tenant_id: UUID = Depends(_get_tenant_id),
    svc=Depends(_make_cp_svc),
):
    obj = await svc.create(body, tenant_id)
    return APIResponse.ok({"id": str(obj.id), "tenant_id": str(obj.tenant_id)})


@router.get("/commission-platforms")
async def list_commission_platforms(
    tenant_id: UUID = Depends(_get_tenant_id),
):
    async with async_session_factory() as session:
        repo = CommissionPlatformRepository(session)
        items = await repo.list(
            offset=0,
            limit=500,
            filters=(CommissionPlatform.tenant_id == tenant_id,) if tenant_id else None,
        )
    return APIResponse.ok({"items": [_to_dict(w) for w in items], "total": len(items)})


@router.get("/commission-platforms/{obj_id}")
async def get_commission_platform(
    obj_id: UUID,
):
    async with async_session_factory() as session:
        repo = CommissionPlatformRepository(session)
        obj = await repo.get_by_id_or_raise(obj_id)
    return APIResponse.ok(_to_dict(obj))


@router.put("/commission-platforms/{obj_id}")
async def update_commission_platform(
    obj_id: UUID,
    body: CommissionPlatformUpdate,
    tenant_id: UUID = Depends(_get_tenant_id),
    svc=Depends(_make_cp_svc),
):
    obj = await svc.update(obj_id, body, tenant_id)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/commission-platforms/{obj_id}")
async def delete_commission_platform(
    obj_id: UUID,
    svc=Depends(_make_cp_svc),
):
    await svc.delete(obj_id)
    return APIResponse.ok(None, message="已停用")
