"""EventBus 单元测试"""

from dataclasses import dataclass

import pytest

from app.core.events import DomainEvent, EventBus, event_bus, event_handler


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderCreated(DomainEvent):
    order_id: str
    amount: float


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderCancelled(DomainEvent):
    order_id: str
    reason: str


class TestEventBus:
    """EventBus 核心功能测试"""

    def setup_method(self):
        """每个测试前清空处理器"""
        EventBus.clear()

    def teardown_method(self):
        """每个测试后清空"""
        EventBus.clear()

    @pytest.mark.asyncio
    async def test_publish_without_handlers(self):
        """无处理器时 publish 不报错"""
        event = OrderCreated(order_id="1", amount=100.0)
        results = await event_bus.publish(event)
        assert results == []

    @pytest.mark.asyncio
    async def test_single_handler(self):
        """单个处理器正确接收事件"""
        received = []

        @event_handler(OrderCreated)
        async def handle(event: OrderCreated):
            received.append(event)

        event = OrderCreated(order_id="1", amount=100.0)
        await event_bus.publish(event)

        assert len(received) == 1
        assert received[0].order_id == "1"
        assert received[0].amount == 100.0

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self):
        """同一事件多个处理器"""
        results = []

        @event_handler(OrderCreated)
        async def handler_a(event: OrderCreated):
            results.append("a")

        @event_handler(OrderCreated)
        async def handler_b(event: OrderCreated):
            results.append("b")

        event = OrderCreated(order_id="1", amount=100.0)
        await event_bus.publish(event)

        assert results == ["a", "b"]

    @pytest.mark.asyncio
    async def test_different_events(self):
        """不同事件类型只触发对应处理器"""
        created = []
        cancelled = []

        @event_handler(OrderCreated)
        async def handle_created(event: OrderCreated):
            created.append(event)

        @event_handler(OrderCancelled)
        async def handle_cancelled(event: OrderCancelled):
            cancelled.append(event)

        await event_bus.publish(OrderCreated(order_id="1", amount=100.0))

        assert len(created) == 1
        assert len(cancelled) == 0

    @pytest.mark.asyncio
    async def test_handler_returns_value(self):
        """处理器返回值被收集"""

        @event_handler(OrderCreated)
        async def handle(event: OrderCreated) -> str:
            return "ok"

        results = await event_bus.publish(OrderCreated(order_id="1", amount=100.0))
        assert results == ["ok"]

    def test_registered_handlers_info(self):
        """registered_handlers 返回注册信息"""

        @event_handler(OrderCreated)
        async def handle(event: OrderCreated):
            pass

        info = EventBus.registered_handlers()
        assert "OrderCreated" in info
        assert info["OrderCreated"] == 1

    def test_clear(self):
        """clear 清空所有处理器"""

        @event_handler(OrderCreated)
        async def handle(event: OrderCreated):
            pass

        assert EventBus.registered_handlers() != {}
        EventBus.clear()
        assert EventBus.registered_handlers() == {}
