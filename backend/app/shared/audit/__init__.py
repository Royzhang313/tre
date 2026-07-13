"""Audit 审计模块 —— M1 仅定义接口

后续 M2 实现具体写入器。
"""

from app.shared.audit.registry import AuditLogWriter, AuditOperator

__all__ = [
    "AuditOperator",
    "AuditLogWriter",
]
