"""领域异常体系

所有业务异常继承自 DomainError，FastAPI 异常处理器统一捕获并转换为 API 响应。

使用示例:
    if not product:
        raise NotFoundError("产品不存在", entity="Product", entity_id=product_id)
"""

from uuid import UUID


class DomainError(Exception):
    """领域异常基类 —— 所有业务异常继承此类"""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "DOMAIN_ERROR",
        details: dict | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(DomainError):
    """实体未找到"""

    def __init__(
        self,
        message: str = "资源不存在",
        *,
        entity: str | None = None,
        entity_id: UUID | str | None = None,
    ):
        details = {}
        if entity:
            details["entity"] = entity
        if entity_id:
            details["entity_id"] = str(entity_id)
        super().__init__(message, error_code="NOT_FOUND", details=details)


class ValidationError(DomainError):
    """数据校验失败"""

    def __init__(self, message: str, *, field_name: str | None = None):
        details = {}
        if field_name:
            details["field"] = field_name
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)


class ConflictError(DomainError):
    """数据冲突（唯一约束、状态冲突等）"""

    def __init__(self, message: str, *, entity: str | None = None):
        details = {}
        if entity:
            details["entity"] = entity
        super().__init__(message, error_code="CONFLICT", details=details)


class UnauthorizedError(DomainError):
    """未认证 —— 用户未登录或 Token 无效 (HTTP 401)"""

    def __init__(self, message: str = "未登录或令牌无效"):
        super().__init__(message, error_code="UNAUTHORIZED")


class ForbiddenError(DomainError):
    """无权限 —— 用户已登录但无操作权限 (HTTP 403)"""

    def __init__(self, message: str = "无权限执行此操作"):
        super().__init__(message, error_code="FORBIDDEN")


class BusinessRuleViolationError(DomainError):
    """业务规则违反"""

    def __init__(self, message: str, *, rule: str | None = None):
        details = {}
        if rule:
            details["rule"] = rule
        super().__init__(message, error_code="BUSINESS_RULE_VIOLATION", details=details)
