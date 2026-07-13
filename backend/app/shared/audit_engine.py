"""Audit Engine —— 操作审计记录

记录用户、动作、对象、before/after 快照。

支持两种模式：
1. 传入 session：复用已有事务，不主动 commit（调用方负责提交）
2. 不传 session：独立开连接 + commit（standalone 场景）
"""

import asyncio
from uuid import UUID

from sqlalchemy import JSON, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import async_session_factory
from app.shared.base_model import BaseModel


class AuditLog(BaseModel):
    """审计日志 —— 只追加不修改"""

    __tablename__ = "shared_audit_logs"

    user_id: Mapped[UUID | None] = mapped_column(nullable=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False, default="系统")
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    before_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    client_type: Mapped[str] = mapped_column(String(20), nullable=False, default="api")
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.entity_type} {self.entity_id}>"


class AuditEngine:
    """审计引擎 —— 记录操作审计

    推荐用法：传入 session 复用已有事务，避免 SQLite 锁竞争。
        await AuditEngine.record(session=self.repo.session, action="create", ...)

    独立用法（无已有 session 时）：
        await AuditEngine.record(action="create", ...)
    """

    @staticmethod
    async def record(
        *,
        session: AsyncSession | None = None,
        action: str,
        entity_type: str,
        entity_id: UUID,
        user_id: UUID | None = None,
        user_name: str = "系统",
        before: dict | None = None,
        after: dict | None = None,
        trace_id: str | None = None,
        ip_address: str | None = None,
        client_type: str = "api",
        remark: str | None = None,
    ) -> AuditLog | None:
        """记录一条审计日志

        Args:
            session: 可选，复用已有 session（推荐，避免 SQLite 锁竞争）
            ...: 审计字段
        """
        log = AuditLog(
            user_id=user_id,
            user_name=user_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_json=before,
            after_json=after,
            trace_id=trace_id,
            ip_address=ip_address,
            client_type=client_type,
            remark=remark,
        )

        if session is not None:
            # 复用已有 session，不 commit（调用方统一提交）
            session.add(log)
            return log

        # 独立模式：自开连接提交，带重试（处理 SQLite 锁竞争）
        for attempt in range(3):
            try:
                async with async_session_factory() as s:
                    s.add(log)
                    await s.commit()
                    return log
            except Exception:
                if attempt < 2:
                    await asyncio.sleep(0.15 * (attempt + 1))
        return None  # 重试耗尽，审计失败不影响主流程
