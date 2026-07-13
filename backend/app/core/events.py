"""内存异步 EventBus —— 跨模块通信基础设施

所有跨模块联动必须通过事件驱动，不允许模块之间直接调用业务 Service。

使用示例:
    # 定义事件
    @dataclass
    class PurchaseOrderCreated(DomainEvent):
        order_id: UUID
        supplier_id: UUID

    # 注册处理器
    @event_handler(PurchaseOrderCreated)
    async def on_order_created(event: PurchaseOrderCreated):
        await inventory_service.reserve(event.order_id)

    # 发布事件
    await event_bus.publish(PurchaseOrderCreated(order_id=..., supplier_id=...))
"""

from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """领域事件基类 —— 所有事件继承此类

    event_type: 事件类型（如 purchase.order.confirmed）
    aggregate_type: 聚合类型（如 PurchaseOrder）
    aggregate_id: 聚合 ID
    trace_id: 链路追踪 ID（跨模块共享，方便排查）
    """

    event_id: UUID = field(default_factory=uuid4)
    event_type: str = ""
    aggregate_type: str = ""
    aggregate_id: UUID = field(default_factory=uuid4)
    version: int = 1
    trace_id: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# 事件处理器类型: async callable 接收一个 DomainEvent
EventHandler = Callable[[DomainEvent], Any]

# 全局处理器注册表: {事件类名: [handler1, handler2, ...]}
_handlers: dict[str, list[EventHandler]] = defaultdict(list)


def event_handler(event_class: type[DomainEvent] | str):
    """装饰器 —— 注册事件处理器

    支持类名或字符串注册:
        @event_handler(PurchaseOrderConfirmed)
        @event_handler("PurchaseOrderConfirmed")

    Args:
        event_class: 事件类 或 事件类名字符串
    """

    def decorator(func: EventHandler) -> EventHandler:
        event_name = event_class if isinstance(event_class, str) else event_class.__name__
        _handlers[event_name].append(func)
        return func

    return decorator


def register_handler(event_name: str, handler: EventHandler) -> None:
    """显式注册事件处理器（字符串方式，避免循环 import）"""
    _handlers[event_name].append(handler)


class EventBus:
    """内存异步事件总线 —— 支持幂等和事件持久化"""

    _processed: set[UUID] = set()  # 已处理事件 ID（幂等）

    @staticmethod
    async def publish(event: DomainEvent) -> list[Any]:
        """发布事件到所有注册的处理器

        幂等: 同一 event_id 不会重复处理。
        """
        # 幂等检查
        if event.event_id in EventBus._processed:
            return []

        event_name = type(event).__name__
        handlers = _handlers.get(event_name, [])
        results: list[Any] = []
        for handler in handlers:
            result = handler(event)
            if inspect.isawaitable(result):
                result = await result
            results.append(result)

        EventBus._processed.add(event.event_id)
        return results

    @staticmethod
    def is_processed(event_id: UUID) -> bool:
        """检查事件是否已处理（消费者幂等）"""
        return event_id in EventBus._processed

    @staticmethod
    def subscribe(event_class: type[DomainEvent], handler: EventHandler) -> None:
        """显式订阅（替代装饰器，方便动态注册）"""
        event_name = event_class.__name__
        _handlers[event_name].append(handler)

    @staticmethod
    def is_consumer_processed(event_id: UUID, consumer: str) -> bool:
        """检查特定消费者是否已处理该事件"""
        # 内存级消费者追踪（生产环境用 EventConsumerLog 表）
        key = f"{consumer}:{event_id}"
        return key in EventBus._processed_str_keys

    @staticmethod
    def mark_consumer_processed(event_id: UUID, consumer: str) -> None:
        key = f"{consumer}:{event_id}"
        EventBus._processed_str_keys.add(key)

    _processed_str_keys: set[str] = set()

    @staticmethod
    def clear() -> None:
        """清空所有注册和幂等记录（仅在测试中使用）"""
        _handlers.clear()
        EventBus._processed.clear()

    @staticmethod
    def registered_handlers() -> dict[str, int]:
        """返回已注册的处理器统计（方便调试）"""
        return {name: len(handlers) for name, handlers in _handlers.items()}


# 全局单例
event_bus = EventBus()
