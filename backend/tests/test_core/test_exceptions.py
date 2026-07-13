"""领域异常单元测试"""


from app.core.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestDomainExceptions:
    """领域异常体系测试"""

    def test_base_domain_error(self):
        """基础 DomainError 正确设置属性"""
        err = DomainError("测试错误", error_code="TEST", details={"key": "value"})
        assert err.message == "测试错误"
        assert err.error_code == "TEST"
        assert err.details == {"key": "value"}
        assert isinstance(err, Exception)

    def test_not_found_error_default(self):
        """NotFoundError 默认消息"""
        err = NotFoundError()
        assert err.error_code == "NOT_FOUND"
        assert "不存在" in err.message

    def test_not_found_error_with_entity(self):
        """NotFoundError 带实体信息"""
        err = NotFoundError(entity="Product", entity_id="abc-123")
        assert err.details["entity"] == "Product"
        assert err.details["entity_id"] == "abc-123"

    def test_validation_error(self):
        """ValidationError 带字段信息"""
        err = ValidationError("名称不能为空", field_name="name")
        assert err.error_code == "VALIDATION_ERROR"
        assert err.details["field"] == "name"

    def test_conflict_error(self):
        """ConflictError 带实体信息"""
        err = ConflictError("SKU 已存在", entity="Product")
        assert err.error_code == "CONFLICT"
        assert err.details["entity"] == "Product"

    def test_unauthorized_error(self):
        """UnauthorizedError"""
        err = UnauthorizedError()
        assert err.error_code == "UNAUTHORIZED"

    def test_business_rule_violation(self):
        """BusinessRuleViolation 带规则信息"""
        err = BusinessRuleViolationError("入库数量不能超过采购数量", rule="INBOUND_QTY_EXCEED")
        assert err.error_code == "BUSINESS_RULE_VIOLATION"
        assert err.details["rule"] == "INBOUND_QTY_EXCEED"
