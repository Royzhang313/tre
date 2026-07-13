"""Workflow 数据模型和接口单元测试"""

from app.shared.workflow.models import WorkflowDefinition, WorkflowState, WorkflowTransition


class TestWorkflowState:
    """WorkflowState 测试"""

    def test_create_state(self):
        """创建状态"""
        state = WorkflowState("draft", "草稿")
        assert state.code == "draft"
        assert state.name == "草稿"
        assert state.terminal is False

    def test_terminal_state(self):
        """终态"""
        state = WorkflowState("approved", "已通过", terminal=True)
        assert state.terminal is True

    def test_immutable(self):
        """不可变"""
        state = WorkflowState("draft", "草稿")
        try:
            state.code = "new"  # type: ignore
        except Exception:
            pass  # frozen dataclass 应该抛异常
        assert state.code == "draft"


class TestWorkflowTransition:
    """WorkflowTransition 测试"""

    def test_create_transition(self):
        """创建状态转换"""
        t = WorkflowTransition("提交审批", "draft", "pending")
        assert t.name == "提交审批"
        assert t.from_state == "draft"
        assert t.to_state == "pending"

    def test_immutable(self):
        """不可变"""
        t = WorkflowTransition("approve", "pending", "approved")
        try:
            t.to_state = "rejected"  # type: ignore
        except Exception:
            pass
        assert t.to_state == "approved"


class TestWorkflowDefinition:
    """WorkflowDefinition 测试"""

    def test_create_definition(self):
        """创建工作流定义"""
        states = [
            WorkflowState("draft", "草稿"),
            WorkflowState("pending", "待审批"),
            WorkflowState("approved", "已通过", terminal=True),
            WorkflowState("rejected", "已驳回", terminal=True),
        ]
        transitions = [
            WorkflowTransition("提交", "draft", "pending"),
            WorkflowTransition("通过", "pending", "approved"),
            WorkflowTransition("驳回", "pending", "rejected"),
        ]
        wf = WorkflowDefinition(
            name="purchase_approval",
            states=states,
            transitions=transitions,
            initial_state="draft",
        )
        assert wf.name == "purchase_approval"
        assert len(wf.states) == 4
        assert len(wf.transitions) == 3
        assert wf.initial_state == "draft"
        # 有两个终态
        terminal_states = [s for s in wf.states if s.terminal]
        assert len(terminal_states) == 2

    def test_immutable(self):
        """不可变"""
        wf = WorkflowDefinition(
            name="test",
            states=[WorkflowState("s1", "状态1")],
            transitions=[],
            initial_state="s1",
        )
        try:
            wf.name = "changed"  # type: ignore
        except Exception:
            pass
        assert wf.name == "test"


class TestWorkflowRegistryProtocol:
    """WorkflowRegistry Protocol 测试"""

    def test_concrete_implementation(self):
        """具体实现满足 Protocol 接口"""

        class InMemoryWorkflowRegistry:
            def __init__(self):
                self._defs: dict[str, WorkflowDefinition] = {}

            def register(self, definition: WorkflowDefinition) -> None:
                if definition.name in self._defs:
                    raise ValueError(f"工作流 '{definition.name}' 已存在")
                self._defs[definition.name] = definition

            def get(self, name: str) -> WorkflowDefinition | None:
                return self._defs.get(name)

            def list_all(self) -> list[str]:
                return list(self._defs.keys())

        registry = InMemoryWorkflowRegistry()

        wf = WorkflowDefinition(
            name="purchase_approval",
            states=[
                WorkflowState("draft", "草稿"),
                WorkflowState("approved", "已通过", terminal=True),
            ],
            transitions=[WorkflowTransition("通过", "draft", "approved")],
            initial_state="draft",
        )

        # 注册
        registry.register(wf)
        assert registry.list_all() == ["purchase_approval"]

        # 获取
        retrieved = registry.get("purchase_approval")
        assert retrieved is not None
        assert retrieved.name == "purchase_approval"

        # 重复注册应抛异常
        try:
            registry.register(wf)
            assert False, "应该抛出异常"
        except ValueError:
            pass

        # 不存在的返回 None
        assert registry.get("not_exist") is None
