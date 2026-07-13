"""财务模块 —— Router"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.database import async_session_factory
from app.modules.finance.repository import (
    ARLedgerRepository, ARReceiptRepository,
    APLedgerRepository, APPaymentRepository,
)
from app.modules.finance.schemas import (
    ARAllocationCreate, ARReceiptCreate, ARReceiptUpdate,
    APAllocationCreate, APPaymentCreate, APPaymentUpdate,
)
from app.modules.auth.context import CurrentUser
from app.modules.auth.dependencies import get_current_user
from app.modules.finance.service import ARReceiptService, APPaymentService
from app.shared.base_schema import APIResponse, PageResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/finance", tags=["财务"])


# ============================================================
# AR 收款
# ============================================================


async def _make_ar_svc() -> AsyncGenerator[ARReceiptService, None]:
    async with async_session_factory() as session:
        yield ARReceiptService(
            repo=ARReceiptRepository(session),
            ledger_repo=ARLedgerRepository(session),
        )
        await session.commit()


@router.post("/ar/receipts")
async def create_ar_receipt(
    body: ARReceiptCreate,
    svc=Depends(_make_ar_svc),
    current_user: CurrentUser = Depends(get_current_user),
):
    obj = await svc.create(body, user_id=current_user.id)
    return APIResponse.ok({"id": str(obj.id), "receipt_no": obj.receipt_no})


@router.get("/ar/receipts")
async def list_ar_receipts(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    async with async_session_factory() as session:
        repo = ARReceiptRepository(session)
        offset = (page - 1) * page_size
        items = await repo.list(offset=offset, limit=page_size)
        total = await repo.count()
    result = [_to_dict(r) for r in items]
    return APIResponse.ok(PageResponse.from_list(result, total, page, page_size).model_dump())


@router.get("/ar/receipts/{receipt_id}")
async def get_ar_receipt(receipt_id: UUID):
    async with async_session_factory() as session:
        repo = ARReceiptRepository(session)
        obj = await repo.get_with_allocations(receipt_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("收款不存在", entity="ARReceipt", entity_id=receipt_id)
        d = _to_dict(obj)
        d["allocations"] = [_to_dict(a) for a in obj.allocations]
    return APIResponse.ok(d)


@router.put("/ar/receipts/{receipt_id}")
async def update_ar_receipt(receipt_id: UUID, body: ARReceiptUpdate, svc=Depends(_make_ar_svc)):
    obj = await svc.update(receipt_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/ar/receipts/{receipt_id}")
async def void_ar_receipt(receipt_id: UUID, svc=Depends(_make_ar_svc)):
    await svc.void(receipt_id)
    return APIResponse.ok(None, message="已作废")


@router.post("/ar/receipts/{receipt_id}/allocate")
async def allocate_ar_receipt(receipt_id: UUID, body: list[ARAllocationCreate], svc=Depends(_make_ar_svc)):
    obj = await svc.allocate(receipt_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.post("/ar/receipts/{receipt_id}/confirm")
async def confirm_ar_receipt(receipt_id: UUID, svc=Depends(_make_ar_svc)):
    obj = await svc.confirm(receipt_id)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/ar/ledger")
async def get_ar_ledger(bp_id: UUID = Query(), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    async with async_session_factory() as session:
        repo = ARLedgerRepository(session)
        offset = (page - 1) * page_size
        items = await repo.list(offset=offset, limit=page_size)
        filtered = [r for r in items if str(r.bp_id) == str(bp_id)] if bp_id else items
        total = await repo.count() if not bp_id else len(filtered)
    return APIResponse.ok(PageResponse.from_list(
        [_to_dict(r) for r in filtered], total, page, page_size
    ).model_dump())


# ============================================================
# AP 付款
# ============================================================


async def _make_ap_svc() -> AsyncGenerator[APPaymentService, None]:
    async with async_session_factory() as session:
        yield APPaymentService(
            repo=APPaymentRepository(session),
            ledger_repo=APLedgerRepository(session),
        )
        await session.commit()


@router.post("/ap/payments")
async def create_ap_payment(
    body: APPaymentCreate,
    svc=Depends(_make_ap_svc),
    current_user: CurrentUser = Depends(get_current_user),
):
    obj = await svc.create(body, user_id=current_user.id)
    return APIResponse.ok({"id": str(obj.id), "payment_no": obj.payment_no})


@router.get("/ap/payments")
async def list_ap_payments(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    async with async_session_factory() as session:
        repo = APPaymentRepository(session)
        offset = (page - 1) * page_size
        items = await repo.list(offset=offset, limit=page_size)
        total = await repo.count()
    result = [_to_dict(r) for r in items]
    return APIResponse.ok(PageResponse.from_list(result, total, page, page_size).model_dump())


@router.get("/ap/payments/{payment_id}")
async def get_ap_payment(payment_id: UUID):
    async with async_session_factory() as session:
        repo = APPaymentRepository(session)
        obj = await repo.get_with_allocations(payment_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("付款不存在", entity="APPayment", entity_id=payment_id)
        d = _to_dict(obj)
        d["allocations"] = [_to_dict(a) for a in obj.allocations]
    return APIResponse.ok(d)


@router.put("/ap/payments/{payment_id}")
async def update_ap_payment(payment_id: UUID, body: APPaymentUpdate, svc=Depends(_make_ap_svc)):
    obj = await svc.update(payment_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.delete("/ap/payments/{payment_id}")
async def void_ap_payment(payment_id: UUID, svc=Depends(_make_ap_svc)):
    await svc.void(payment_id)
    return APIResponse.ok(None, message="已作废")


@router.post("/ap/payments/{payment_id}/allocate")
async def allocate_ap_payment(payment_id: UUID, body: list[APAllocationCreate], svc=Depends(_make_ap_svc)):
    obj = await svc.allocate(payment_id, body)
    return APIResponse.ok({"id": str(obj.id)})


@router.post("/ap/payments/{payment_id}/confirm")
async def confirm_ap_payment(payment_id: UUID, svc=Depends(_make_ap_svc)):
    obj = await svc.confirm(payment_id)
    return APIResponse.ok({"id": str(obj.id)})


@router.get("/ap/ledger")
async def get_ap_ledger(bp_id: UUID = Query(), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    async with async_session_factory() as session:
        repo = APLedgerRepository(session)
        offset = (page - 1) * page_size
        items = await repo.list(offset=offset, limit=page_size)
        filtered = [r for r in items if str(r.bp_id) == str(bp_id)] if bp_id else items
        total = await repo.count() if not bp_id else len(filtered)
    return APIResponse.ok(PageResponse.from_list(
        [_to_dict(r) for r in filtered], total, page, page_size
    ).model_dump())


# ============================================================
# 统一资金台账 —— AR 收款 + AP 付款 合并列表
# ============================================================


@router.get("/ledger")
async def get_unified_ledger(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    direction: str | None = Query(default=None, pattern="^(ar|ap)$"),
    bp_id: str | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(pending|confirmed|voided)$"),
):
    """统一资金台账：AR 收款 + AP 付款 合并，按日期倒序"""
    async with async_session_factory() as session:
        ar_repo = ARReceiptRepository(session)
        ap_repo = APPaymentRepository(session)

        rows: list[dict] = []

        if not direction or direction == "ar":
            ar_items = await ar_repo.list(offset=0, limit=5000)
            for r in ar_items:
                d = _to_dict(r)
                d["_direction"] = "ar"
                d["_label"] = "收款"
                d["_date"] = d.get("receipt_date", "")
                d["_no"] = d.get("receipt_no", "")
                d["_counterparty_id"] = d.get("bp_id", "")
                rows.append(d)

        if not direction or direction == "ap":
            ap_items = await ap_repo.list(offset=0, limit=5000)
            for p in ap_items:
                d = _to_dict(p)
                d["_direction"] = "ap"
                d["_label"] = "付款"
                d["_date"] = d.get("payment_date", "")
                d["_no"] = d.get("payment_no", "")
                d["_counterparty_id"] = d.get("bp_id", "")
                rows.append(d)

    # 筛选
    if bp_id:
        rows = [r for r in rows if r["_counterparty_id"] == bp_id]
    if status:
        rows = [r for r in rows if r.get("status") == status]

    # 按日期倒序
    rows.sort(key=lambda r: r["_date"], reverse=True)

    total = len(rows)
    # 分页
    start = (page - 1) * page_size
    page_items = rows[start:start + page_size]

    # 汇总
    ar_total = sum(r.get("amount", 0) for r in rows if r["_direction"] == "ar")
    ap_total = sum(r.get("amount", 0) for r in rows if r["_direction"] == "ap")

    return APIResponse.ok({
        "items": page_items,
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size if total else 0,
        "ar_total": ar_total,
        "ap_total": ap_total,
    })
