"""Evolution —— ModuleVersion + ArtifactVersion + UISnapshot"""

from uuid import UUID

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class ModuleVersion(BaseModel):
    """模块版本 —— 每次 Promotion 产生一条记录"""

    __tablename__ = "ai_module_versions"

    module_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(10), nullable=False)
    promotion_id: Mapped[UUID] = mapped_column(nullable=False)
    sandbox_id: Mapped[UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    ui_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    change_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    deployed_at: Mapped[str | None] = mapped_column(String(25), nullable=True)
    rolled_back_at: Mapped[str | None] = mapped_column(String(25), nullable=True)


class ArtifactVersion(BaseModel):
    """Artifact 版本快照"""

    __tablename__ = "ai_artifact_versions"

    module_version_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_type: Mapped[str] = mapped_column(String(30), nullable=False)


class UISnapshot(BaseModel):
    """UI 快照 —— 每次 Promotion 冻结当时的 UI Metadata"""

    __tablename__ = "ai_ui_snapshots"

    module_version_id: Mapped[UUID] = mapped_column(nullable=False, unique=True)
    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    version: Mapped[str] = mapped_column(String(10), nullable=False)
    pages_json: Mapped[dict] = mapped_column(JSON, nullable=False)
