"""EventConsumerLog —— 消费者处理记录

追踪每个消费者是否已处理某个事件，支持幂等和重试。
"""

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class EventConsumerLog(BaseModel):
    """事件消费者日志 —— 每个 (event_id, consumer) 一条记录"""

    __tablename__ = "core_event_consumer_logs"

    event_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    consumer: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processed")
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
