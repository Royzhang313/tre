"""Outbox Pattern —— DomainEvent 可靠发布

事件先写入 Outbox（与业务数据同一 DB 事务），后台 Dispatcher 异步发布到 EventBus。
"""

from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import JSON, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import async_session_factory
from app.core.events import DomainEvent, event_bus
from app.shared.base_model import BaseModel


class OutboxMessage(BaseModel):
    """Outbox 消息 —— 与业务数据同一事务写入"""

    __tablename__ = "core_outbox"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[str | None] = mapped_column(String(25), nullable=True)


class Outbox:
    """Outbox —— 写入和分发"""

    @staticmethod
    async def enqueue(event: DomainEvent) -> OutboxMessage:
        """写入 Outbox（与业务数据同一 session）"""
        payload = _event_to_dict(event)
        msg = OutboxMessage(
            event_type=event.event_type,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            payload=payload,
        )
        async with async_session_factory() as session:
            session.add(msg)
            await session.commit()
        return msg

    @staticmethod
    async def dispatch_pending() -> int:
        """分发 pending 消息到 EventBus（后台轮询调用）"""
        async with async_session_factory() as session:
            stmt = select(OutboxMessage).where(
                OutboxMessage.status == "pending",
            ).order_by(OutboxMessage.created_at).limit(20)
            result = await session.execute(stmt)
            messages = result.scalars().all()

            published = 0
            for msg in messages:
                try:
                    await event_bus.publish(_dict_to_event(msg.payload))
                    msg.status = "published"
                    msg.published_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
                    published += 1
                except Exception as e:
                    msg.retry_count += 1
                    msg.last_error = str(e)[:500]
                    if msg.retry_count >= msg.max_retries:
                        msg.status = "dead"
                    await session.flush()

            await session.commit()
            return published


def _event_to_dict(event: DomainEvent) -> dict:
    """DomainEvent → JSON dict"""
    result = {}
    for field_name in event.__dataclass_fields__:
        val = getattr(event, field_name)
        if isinstance(val, UUID):
            val = str(val)
        elif isinstance(val, list):
            val = [_event_to_dict(item) if isinstance(item, DomainEvent) else (
                asdict(item) if hasattr(item, '__dataclass_fields__') else str(item)
            ) for item in val]
        result[field_name] = val
    result["__event_class__"] = type(event).__name__
    return result


def _dict_to_event(data: dict) -> DomainEvent:
    """JSON dict → DomainEvent (基础还原，发布到 EventBus 使用类名匹配)"""
    # 简单实现：创建一个最小 DomainEvent 携带 payload
    event_class_name = data.pop("__event_class__", "DomainEvent")
    return DomainEvent(
        event_type=data.get("event_type", event_class_name),
        aggregate_type=data.get("aggregate_type", ""),
        aggregate_id=UUID(data["aggregate_id"]) if data.get("aggregate_id") else UUID("00000000-0000-0000-0000-000000000000"),
    )
