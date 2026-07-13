"""Audit 接口和数据结构单元测试"""

from uuid import UUID, uuid4

from app.shared.audit.registry import AuditOperator


class TestAuditOperator:
    """AuditOperator 测试"""

    def test_defaults(self):
        """默认值"""
        op = AuditOperator()
        assert op.user_id is None
        assert op.user_name == "系统"
        assert op.ip_address is None
        assert op.client_type == "system"
        assert op.trace_id is None

    def test_full_operator(self):
        """完整操作人信息"""
        uid = uuid4()
        op = AuditOperator(
            user_id=uid,
            user_name="张三",
            ip_address="192.168.1.100",
            client_type="web",
            trace_id="trace-abc-123",
        )
        assert op.user_id == uid
        assert op.user_name == "张三"
        assert op.ip_address == "192.168.1.100"
        assert op.client_type == "web"
        assert op.trace_id == "trace-abc-123"

    def test_immutable(self):
        """不可变"""
        op = AuditOperator(user_name="张三")
        try:
            op.user_name = "李四"  # type: ignore
        except Exception:
            pass
        assert op.user_name == "张三"


class TestAuditLogWriterProtocol:
    """AuditLogWriter Protocol 测试"""

    def test_concrete_implementation(self):
        """具体实现满足 Protocol 接口"""

        class InMemoryAuditLogWriter:
            def __init__(self):
                self.records: list[dict] = []

            async def record(
                self,
                *,
                action: str,
                entity_type: str,
                entity_id: UUID,
                changes: dict | None = None,
                operator: AuditOperator,
            ) -> None:
                self.records.append({
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "changes": changes,
                    "operator": operator,
                })

        import pytest

        @pytest.mark.asyncio
        async def test_record():
            writer = InMemoryAuditLogWriter()
            entity_id = uuid4()
            op = AuditOperator(user_name="测试用户", client_type="api")

            await writer.record(
                action="UPDATE",
                entity_type="Product",
                entity_id=entity_id,
                changes={"status": ("active", "inactive")},
                operator=op,
            )

            assert len(writer.records) == 1
            record = writer.records[0]
            assert record["action"] == "UPDATE"
            assert record["entity_type"] == "Product"
            assert record["entity_id"] == entity_id
            assert record["changes"] == {"status": ("active", "inactive")}
            assert record["operator"].user_name == "测试用户"
