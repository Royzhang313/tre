"""销售合同模块 —— FastAPI Router"""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.core.database import async_session_factory
from app.core.exceptions import ConflictError
from app.modules.sales_contract.repository import SalesContractItemRepository, SalesContractRepository
from app.modules.sales_contract.schemas import SalesContractCreate, SalesContractUpdate
from app.modules.sales_contract.service import SalesContractService
from app.shared.base_schema import APIResponse, PageResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/sales-contracts", tags=["销售合同"])




async def _make_svc() -> AsyncGenerator[SalesContractService, None]:
    async with async_session_factory() as session:
        yield SalesContractService(repo=SalesContractRepository(session), item_repo=SalesContractItemRepository(session))
        await session.commit()


# ============================================================
# CRUD
# ============================================================


@router.post("")
async def create(body: SalesContractCreate, svc=Depends(_make_svc)):
    try:
        contract = await svc.create(body, user_id=uuid4(), tenant_id=uuid4())
    except ConflictError as e:
        return JSONResponse(status_code=409, content={"code": 409, "message": e.message})
    return APIResponse.ok({"id": str(contract.id), "contract_no": contract.contract_no})


@router.get("")
async def list_contracts(page: int = Query(default=1, ge=1), page_size: int = Query(default=20, ge=1, le=100)):
    async with async_session_factory() as session:
        repo = SalesContractRepository(session)
        items = await repo.list_with_items(offset=(page - 1) * page_size, limit=page_size)
        total = await repo.count()
    result = []
    for c in items:
        d = _to_dict(c)
        d["items"] = [_to_dict(it) for it in c.items]
        result.append(d)
    return APIResponse.ok(PageResponse.from_list(result, total, page, page_size).model_dump())


# 校验合同编号唯一（必须在 /{contract_id} 之前注册）
@router.get("/check-contract-no")
async def check_contract_no(contract_no: str = Query()):
    async with async_session_factory() as session:
        repo = SalesContractRepository(session)
        existing = await repo.get_by_contract_no(contract_no)
    return APIResponse.ok({"exists": existing is not None})


@router.get("/{contract_id}")
async def get(contract_id: UUID):
    async with async_session_factory() as session:
        repo = SalesContractRepository(session)
        c = await repo.get_with_items(contract_id)
        if not c:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("销售合同不存在", entity="SalesContract", entity_id=contract_id)
        d = _to_dict(c)
        d["items"] = [_to_dict(it) for it in c.items]
    return APIResponse.ok(d)


@router.put("/{contract_id}")
async def update(contract_id: UUID, body: SalesContractUpdate, svc=Depends(_make_svc)):
    c = await svc.update(contract_id, body)
    return APIResponse.ok({"id": str(c.id)})


@router.delete("/{contract_id}")
async def cancel(contract_id: UUID, svc=Depends(_make_svc)):
    await svc.cancel(contract_id)
    return APIResponse.ok(None, message="合同已作废")


@router.patch("/{contract_id}/tags")
async def update_tags(contract_id: UUID, body: dict):
    """快速编辑标签 —— 接受 {"tags": ["标签1","标签2"]}"""
    async with async_session_factory() as session:
        repo = SalesContractRepository(session)
        c = await repo.get_by_id_or_raise(contract_id)
        c.tags = body.get("tags", [])
        await repo.update(c)
        await session.commit()
    return APIResponse.ok({"tags": c.tags})


@router.delete("/{contract_id}/items/{item_id}")
async def delete_item(contract_id: UUID, item_id: UUID, svc=Depends(_make_svc)):
    await svc.delete_item(item_id)
    return APIResponse.ok(None, message="明细已删除")
