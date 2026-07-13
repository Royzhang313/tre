"""通用工具模块 —— Result 类型、共享类型定义"""

from app.common.result import Failure, Result, Success
from app.common.types import EntityId, Money, Timestamp

__all__ = [
    "Result",
    "Success",
    "Failure",
    "EntityId",
    "Money",
    "Timestamp",
]
