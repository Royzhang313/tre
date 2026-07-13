"""Audit Log —— 审计日志接口（Protocol）

M1 仅定义接口，具体实现（数据库写入、Elasticsearch 等）在业务模块中注入。

所有跨模块通信通过 EventBus 触发审计事件，不直接调用 AuditLogWriter。
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuditOperator:
    """操作人信息

    Attributes:
        user_id: 操作人 ID（未登录为 None）
        user_name: 操作人姓名
        ip_address: 客户端 IP
        client_type: 客户端类型（web / api / system）
        trace_id: 链路追踪 ID，与 EventBus / Workflow / API 共享，方便排查
    """

    user_id: UUID | None = None
    user_name: str = "系统"
    ip_address: str | None = None
    client_type: str = "system"
    trace_id: str | None = None


class AuditLogWriter(Protocol):
    """审计日志写入接口 —— 所有模块通过此接口记录操作

    M2 Auth 模块会提供首个具体实现（数据库写入）。
    后续可扩展 Elasticsearch、文件等实现。
    """

    async def record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: UUID,
        changes: dict[str, tuple] | None = None,
        operator: AuditOperator,
    ) -> None:
        """记录一条审计日志

        Args:
            action: 操作类型，建议 "CREATE" / "UPDATE" / "DELETE"
            entity_type: 实体类型，例如 "PurchaseOrder"
            entity_id: 实体 ID
            changes: 变更详情，{"status": ("draft", "submitted")}
            operator: 操作人信息
        """
        ...
