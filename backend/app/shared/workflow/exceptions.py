"""Workflow 领域异常 —— M1 仅定义，M5 实现引擎时使用"""

from app.core.exceptions import DomainError


class WorkflowError(DomainError):
    """工作流异常基类"""

    def __init__(self, message: str, *, workflow: str | None = None):
        details = {}
        if workflow:
            details["workflow"] = workflow
        super().__init__(message, error_code="WORKFLOW_ERROR", details=details)


class InvalidTransitionError(WorkflowError):
    """非法的状态转换"""

    def __init__(
        self,
        message: str = "非法的状态转换",
        *,
        workflow: str | None = None,
        from_state: str | None = None,
        to_state: str | None = None,
    ):
        details: dict = {}
        if workflow:
            details["workflow"] = workflow
        if from_state:
            details["from_state"] = from_state
        if to_state:
            details["to_state"] = to_state
        super().__init__(message, workflow=workflow)
        self.error_code = "INVALID_TRANSITION"


class WorkflowStateNotFoundError(WorkflowError):
    """状态未找到"""

    def __init__(
        self,
        message: str = "工作流状态不存在",
        *,
        workflow: str | None = None,
        state: str | None = None,
    ):
        details: dict = {}
        if workflow:
            details["workflow"] = workflow
        if state:
            details["state"] = state
        super().__init__(message, workflow=workflow)
        self.error_code = "WORKFLOW_STATE_NOT_FOUND"
