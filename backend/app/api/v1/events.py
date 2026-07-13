"""Event API —— 按实体查询事件历史"""

from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.event_log import EventLog
from app.shared.base_schema import APIResponse

router = APIRouter(prefix="/events", tags=["事件历史"])


@router.get("/{entity_type}/{entity_id}")
async def list_events(entity_type: str, entity_id: UUID):
    """获取实体的完整事件历史时间线"""
    async with async_session_factory() as session:
        stmt = (
            select(EventLog)
            .where(
                EventLog.aggregate_type == entity_type,
                EventLog.aggregate_id == entity_id,
            )
            .order_by(EventLog.created_at.desc())
            .limit(50)
        )
        result = await session.execute(stmt)
        events = list(result.scalars().all())

    return APIResponse.ok([
        {
            "id": str(e.id),
            "event_id": str(e.event_id),
            "event_type": e.event_type,
            "aggregate_type": e.aggregate_type,
            "aggregate_id": str(e.aggregate_id),
            "status": e.status,
            "payload": e.payload,
            "created_at": str(e.created_at) if e.created_at else None,
        }
        for e in events
    ])
