"""Merge Pipeline —— MergeRequest + ConflictLog"""

from uuid import UUID

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class MergeRequest(BaseModel):
    """合并请求 —— 一组 Artifact 的合并操作"""

    __tablename__ = "ai_merge_requests"

    execution_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_review")
    diff_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    conflict_log: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    migration_sql: Mapped[str | None] = mapped_column(nullable=True)
    rollback_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    applied_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
    verified_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(nullable=True)


class ConflictLog(BaseModel):
    """冲突记录"""

    __tablename__ = "ai_conflict_logs"

    merge_request_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    conflict_type: Mapped[str] = mapped_column(String(30), nullable=False)
    existing_content: Mapped[str | None] = mapped_column(nullable=True)
    new_content: Mapped[str | None] = mapped_column(nullable=True)
    resolved: Mapped[bool] = mapped_column(default=False)
