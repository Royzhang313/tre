"""基础资料 —— Router"""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import async_session_factory
from app.modules.basedata.repository import CommissionPlatformRepository, CompanyRepository, EnterpriseRepository, WarehouseRepository
from app.modules.basedata.schemas import CommissionPlatformCreate, CommissionPlatformUpdate, CompanyCreate, CompanyUpdate, EnterpriseCreate, EnterpriseUpdate, WarehouseCreate, WarehouseUpdate
from app.modules.basedata.service import CommissionPlatformService, CompanyService, EnterpriseService, WarehouseService
from app.shared.base_schema import APIResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/basedata", tags=["基础资料"])


async def _make_ent_svc() -> AsyncGenerator[EnterpriseService, None]:
    async with async_session_factory() as session:
        yield EnterpriseService(repo=EnterpriseRepository(session))
        await session.commit()


async def _make_wh_svc() -> AsyncGenerator[WarehouseService, None]:
    async with async_session_factory() as session:
        yield WarehouseService(repo=WarehouseRepository(session))
        await session.commit()


# ============================================================
# Enterprise
# ============================================================


@router.post("/enterprises")
async def create_enterprise(body: EnterpriseCreate, svc=Depends(_make_ent_svc)):
    obj = await svc.create(body)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/enterprises")
async def list_enterprises():
    async with async_session_factory() as session:
        repo = EnterpriseRepository(session)
        items = await repo.list_all()
    result = []
    for e in items:
        d = _to_dict(e)
        d["contacts"] = [_to_dict(c) for c in e.contacts]
        result.append(d)
    return APIResponse.ok({"items": result, "total": len(result)})


@router.get("/enterprises/{obj_id}")
async def get_enterprise(obj_id: UUID):
    async with async_session_factory() as session:
        repo = EnterpriseRepository(session)
        obj = await repo.get_with_contacts(obj_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("企业不存在", entity="Enterprise", entity_id=obj_id)
        d = _to_dict(obj)
        d["contacts"] = [_to_dict(c) for c in obj.contacts]
    return APIResponse.ok(d)


@router.put("/enterprises/{obj_id}")
async def update_enterprise(obj_id: UUID, body: EnterpriseUpdate, svc=Depends(_make_ent_svc)):
    obj = await svc.update(obj_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/enterprises/{obj_id}")
async def delete_enterprise(obj_id: UUID, svc=Depends(_make_ent_svc)):
    await svc.delete(obj_id)
    return APIResponse.ok(None, message="已停用")


# ============================================================
# Company
# ============================================================


async def _make_comp_svc() -> AsyncGenerator[CompanyService, None]:
    async with async_session_factory() as session:
        yield CompanyService(repo=CompanyRepository(session)); await session.commit()


@router.post("/companies")
async def create_company(body: CompanyCreate, svc=Depends(_make_comp_svc)):
    obj = await svc.create(body); return APIResponse.ok({"id": str(obj.id)})

@router.get("/companies")
async def list_companies():
    async with async_session_factory() as session:
        repo = CompanyRepository(session); items = await repo.list(offset=0, limit=200)
    return APIResponse.ok({"items": [_to_dict(c) for c in items], "total": len(items)})

@router.get("/companies/{obj_id}")
async def get_company(obj_id: UUID):
    async with async_session_factory() as session:
        repo = CompanyRepository(session); obj = await repo.get_by_id_or_raise(obj_id)
    return APIResponse.ok(_to_dict(obj))

@router.put("/companies/{obj_id}")
async def update_company(obj_id: UUID, body: CompanyUpdate, svc=Depends(_make_comp_svc)):
    obj = await svc.update(obj_id, body); return APIResponse.ok({"id": str(obj.id)})

@router.delete("/companies/{obj_id}")
async def delete_company(obj_id: UUID, svc=Depends(_make_comp_svc)):
    await svc.delete(obj_id); return APIResponse.ok(None, message="已停用")


# ============================================================
# Warehouse
# ============================================================


@router.post("/warehouses")
async def create_warehouse(body: WarehouseCreate, svc=Depends(_make_wh_svc)):
    obj = await svc.create(body)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/warehouses")
async def list_warehouses():
    async with async_session_factory() as session:
        repo = WarehouseRepository(session)
        items = await repo.list(offset=0, limit=500)
    return APIResponse.ok({"items": [_to_dict(w) for w in items], "total": len(items)})


@router.get("/warehouses/{obj_id}")
async def get_warehouse(obj_id: UUID):
    async with async_session_factory() as session:
        repo = WarehouseRepository(session)
        obj = await repo.get_by_id_or_raise(obj_id)
    return APIResponse.ok(_to_dict(obj))


@router.put("/warehouses/{obj_id}")
async def update_warehouse(obj_id: UUID, body: WarehouseUpdate, svc=Depends(_make_wh_svc)):
    obj = await svc.update(obj_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/warehouses/{obj_id}")
async def delete_warehouse(obj_id: UUID, svc=Depends(_make_wh_svc)):
    await svc.delete(obj_id)
    return APIResponse.ok(None, message="已停用")


# ============================================================
# CommissionPlatform (撮合平台)
# ============================================================


async def _make_cp_svc() -> AsyncGenerator[CommissionPlatformService, None]:
    async with async_session_factory() as session:
        yield CommissionPlatformService(repo=CommissionPlatformRepository(session))
        await session.commit()


@router.post("/commission-platforms")
async def create_commission_platform(body: CommissionPlatformCreate, svc=Depends(_make_cp_svc)):
    obj = await svc.create(body)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/commission-platforms")
async def list_commission_platforms():
    async with async_session_factory() as session:
        repo = CommissionPlatformRepository(session)
        items = await repo.list(offset=0, limit=500)
    return APIResponse.ok({"items": [_to_dict(w) for w in items], "total": len(items)})


@router.get("/commission-platforms/{obj_id}")
async def get_commission_platform(obj_id: UUID):
    async with async_session_factory() as session:
        repo = CommissionPlatformRepository(session)
        obj = await repo.get_by_id_or_raise(obj_id)
    return APIResponse.ok(_to_dict(obj))


@router.put("/commission-platforms/{obj_id}")
async def update_commission_platform(obj_id: UUID, body: CommissionPlatformUpdate, svc=Depends(_make_cp_svc)):
    obj = await svc.update(obj_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/commission-platforms/{obj_id}")
async def delete_commission_platform(obj_id: UUID, svc=Depends(_make_cp_svc)):
    await svc.delete(obj_id)
    return APIResponse.ok(None, message="已停用")
