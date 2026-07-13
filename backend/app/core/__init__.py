"""核心基础设施模块 —— 配置、数据库、EventBus、DI、异常"""

from app.core.config import settings
from app.core.database import Base, async_session_factory, engine, get_db
from app.core.di import DIContainer, di
from app.core.events import DomainEvent, EventBus, event_bus, event_handler
from app.core.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

__all__ = [
    # 配置
    "settings",
    # 数据库
    "Base",
    "engine",
    "async_session_factory",
    "get_db",
    # DI
    "DIContainer",
    "di",
    # EventBus
    "DomainEvent",
    "EventBus",
    "event_bus",
    "event_handler",
    # 异常
    "DomainError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    "BusinessRuleViolationError",
]
