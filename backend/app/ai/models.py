"""AI Builder —— AIDomainSpec + BuildPlan + DomainSpecSnapshot"""

from uuid import UUID

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class AIDomainSpec(BaseModel):
    """Domain Specification —— Architect Agent 业务蓝图"""

    __tablename__ = "ai_domain_specs"

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_spec_id: Mapped[UUID | None] = mapped_column(nullable=True)
    revision_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    business_context: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    spec_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    impact_analysis: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    risks: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(nullable=True)
    reviewed_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class BuildPlan(BaseModel):
    """Builder Agent 执行计划 —— 暂不执行"""

    __tablename__ = "ai_build_plans"

    spec_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    actions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    estimated_changes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    risks: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
    error_log: Mapped[str | None] = mapped_column(String(2000), nullable=True)


class DomainSpecSnapshot(BaseModel):
    """Builder 执行时的冻结快照"""

    __tablename__ = "ai_domain_spec_snapshots"

    spec_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    spec_version: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_id: Mapped[UUID | None] = mapped_column(nullable=True)
    spec_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    module_registry_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    capability_registry_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_context_version: Mapped[str | None] = mapped_column(String(20), nullable=True)


class BuildExecution(BaseModel):
    """Builder Agent 执行记录 —— 一次 BuildPlan 执行"""

    __tablename__ = "ai_build_executions"

    plan_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
    error_log: Mapped[str | None] = mapped_column(String(2000), nullable=True)


class BuildTask(BaseModel):
    """单个生成任务 —— 每个 Action 一个 Task"""

    __tablename__ = "ai_build_tasks"

    execution_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    action_index: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    artifact: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(25), nullable=True)


class Artifact(BaseModel):
    """生成产物 —— 可追溯的代码文件"""

    __tablename__ = "ai_artifacts"

    execution_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    task_id: Mapped[UUID] = mapped_column(nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False, default="")
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending_review")
    source_snapshot_id: Mapped[UUID | None] = mapped_column(nullable=True)
