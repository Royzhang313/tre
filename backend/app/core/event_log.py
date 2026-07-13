"""EventLog + DeadLetter —— 事件持久化 + 重试 + 死信"""

from uuid import UUID

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class EventLog(BaseModel):
    """事件日志 —— 只追加。status 管理事件生命周期。"""

    __tablename__ = "core_event_logs"

    event_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    version: Mapped[int] = mapped_column(default=1)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    next_retry_at: Mapped[str | None] = mapped_column(String(25), nullable=True)

    def __repr__(self) -> str:
        return f"<EventLog {self.event_type} [{self.status}]>"


class DeadLetterEvent(BaseModel):
    """死信事件 —— retry_count >= max_retries 后移入此表，待人工处理"""

    __tablename__ = "core_dead_letters"

    event_log_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str] = mapped_column(String(500), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolved: Mapped[bool] = mapped_column(default=False, server_default="false")

