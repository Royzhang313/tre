"""Workflow Registry —— M1 仅定义注册接口（Protocol），不实现引擎

后续 M5 将在此目录扩展具体的 Registry 实现。

使用示例::

    class InMemoryWorkflowRegistry:
        def register(self, definition: WorkflowDefinition) -> None: ...
        def get(self, name: str) -> WorkflowDefinition | None: ...
"""

from typing import Protocol

from app.shared.workflow.models import WorkflowDefinition


class WorkflowRegistry(Protocol):
    """工作流注册中心接口 —— 只注册，不执行

    后续具体实现（M5）：
    - 内存注册（InMemoryWorkflowRegistry）
    - 验证状态图合法性
    - 注册去重检查
    """

    def register(self, definition: WorkflowDefinition) -> None:
        """注册工作流定义

        Args:
            definition: 工作流定义

        Raises:
            WorkflowError: 工作流名称已存在或状态图非法
        """
        ...

    def get(self, name: str) -> WorkflowDefinition | None:
        """按名称获取工作流定义"""
        ...

    def list_all(self) -> list[str]:
        """列出所有已注册的工作流名称"""
        ...
