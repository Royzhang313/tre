"""内存 Workflow Registry —— 满足 WorkflowRegistry Protocol

各模块在 __init__.py 中注册 WorkflowDefinition，
UISchemaGenerator.generate_state_actions() 查询此注册中心。
"""

from app.shared.workflow.models import WorkflowDefinition


class InMemoryWorkflowRegistry:
    """纯内存 Workflow 注册中心"""

    _definitions: dict[str, WorkflowDefinition] = {}

    @classmethod
    def register(cls, definition: WorkflowDefinition) -> None:
        cls._definitions[definition.name] = definition

    @classmethod
    def get(cls, name: str) -> WorkflowDefinition | None:
        return cls._definitions.get(name)

    @classmethod
    def list_all(cls) -> list[WorkflowDefinition]:
        return list(cls._definitions.values())

    @classmethod
    def get_allowed_transitions(cls, name: str, from_state: str) -> list:
        """获取指定 workflow 从 from_state 出发的可用转换"""
        wf = cls._definitions.get(name)
        if wf is None:
            return []
        return [t for t in wf.transitions if t.from_state == from_state]

    @classmethod
    def clear(cls) -> None:
        cls._definitions.clear()
