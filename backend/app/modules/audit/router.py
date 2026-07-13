"""操作审计 —— FastAPI Router"""

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select, func

from app.core.database import async_session_factory
from app.shared.audit_engine import AuditLog
from app.shared.orm_utils import orm_to_dict as _to_dict
from app.shared.base_schema import APIResponse, PageResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/audit-logs", tags=["操作审计"])


@router.get("")
async def list_audit_logs(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """查询操作审计日志"""
    async with async_session_factory() as session:
        q = select(AuditLog).order_by(AuditLog.created_at.desc())

        if entity_type:
            q = q.where(AuditLog.entity_type == entity_type)
        if entity_id:
            q = q.where(AuditLog.entity_id == UUID(entity_id))

        # count
        count_q = select(func.count()).select_from(AuditLog)
        if entity_type:
            count_q = count_q.where(AuditLog.entity_type == entity_type)
        if entity_id:
            count_q = count_q.where(AuditLog.entity_id == UUID(entity_id))

        total = (await session.execute(count_q)).scalar() or 0

        offset = (page - 1) * page_size
        q = q.offset(offset).limit(page_size)
        result = await session.execute(q)
        items = [_to_dict(row) for row in result.scalars().all()]

    return APIResponse.ok(PageResponse.from_list(items, total, page, page_size).model_dump())
