"""Sandbox —— SandboxInstance + PromotionRequest"""

from uuid import UUID

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class SandboxInstance(BaseModel):
    __tablename__ = "ai_sandbox_instances"
    execution_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    sandbox_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    migration_applied: Mapped[bool] = mapped_column(default=False)
    test_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_log: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    promoted_to_merge_id: Mapped[UUID | None] = mapped_column(nullable=True)
    expired_at: Mapped[str | None] = mapped_column(String(25), nullable=True)


class SandboxTestResult(BaseModel):
    __tablename__ = "ai_sandbox_test_results"
    instance_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    test_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    duration: Mapped[float | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class PromotionRequest(BaseModel):
    """Promotion 请求 —— Sandbox → Production"""

    __tablename__ = "ai_promotion_requests"

    sandbox_id: Mapped[UUID] = mapped_column(nullable=False)
    artifact_id: Mapped[UUID | None] = mapped_column(nullable=True)
    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    source_version: Mapped[str] = mapped_column(String(10), nullable=False, default="sandbox")
    target_version: Mapped[str] = mapped_column(String(10), nullable=False, default="V1")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    ui_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(nullable=True)
    review_comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    promoted_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
