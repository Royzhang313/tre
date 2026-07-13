"""Workflow 数据模型 —— M1 仅定义数据结构，不实现引擎

Workflow Engine 后续将在此目录扩展（Definition、History、Events 等）。

所有状态转换通过代码注册，数据库仅保存：
- Workflow 状态历史
- 少量元数据
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkflowState:
    """工作流状态

    Attributes:
        code: 状态编码，例如 "draft"、"submitted"、"approved"、"rejected"
        name: 状态中文名，例如 "草稿"、"已提交"、"已审批"、"已驳回"
        terminal: 是否为终态（终态不可再流转）
    """

    code: str
    name: str
    terminal: bool = False


@dataclass(frozen=True, slots=True)
class WorkflowTransition:
    """工作流状态转换

    Attributes:
        name: 转换名称，例如 "提交审批"、"审批通过"、"驳回"
        from_state: 源状态 code
        to_state: 目标状态 code
    """

    name: str
    from_state: str
    to_state: str
    api_action: str = ""  # 对应 API 端点动作名，如 "confirm"/"cancel"；空则用 to_state


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """工作流定义 —— 通过代码注册，不存数据库

    Attributes:
        name: 工作流名称，例如 "purchase_order_approval"
        states: 所有状态列表
        transitions: 所有允许的状态转换
        initial_state: 初始状态 code

    使用示例::

        purchase_approval = WorkflowDefinition(
            name="purchase_order_approval",
            states=[
                WorkflowState("draft", "草稿"),
                WorkflowState("pending_approval", "待审批"),
                WorkflowState("approved", "已通过", terminal=True),
                WorkflowState("rejected", "已驳回", terminal=True),
            ],
            transitions=[
                WorkflowTransition("提交审批", "draft", "pending_approval"),
                WorkflowTransition("审批通过", "pending_approval", "approved"),
                WorkflowTransition("驳回", "pending_approval", "rejected"),
            ],
            initial_state="draft",
        )
    """

    name: str
    states: list[WorkflowState]
    transitions: list[WorkflowTransition]
    initial_state: str

    @classmethod
    def from_json(cls, data: dict) -> "WorkflowDefinition":
        """从 JSON dict 创建工作流定义

        示例:
            {
                "name": "sales_contract",
                "initial_state": "draft",
                "states": [
                    {"code": "draft", "name": "草稿"},
                    {"code": "confirmed", "name": "已确认"},
                    {"code": "delivered", "name": "已交付", "terminal": true}
                ],
                "transitions": [
                    {"name": "确认", "from_state": "draft", "to_state": "confirmed"},
                    {"name": "交付", "from_state": "confirmed", "to_state": "delivered"}
                ]
            }
        """
        states = [WorkflowState(s["code"], s.get("name", s["code"]), s.get("terminal", False)) for s in data["states"]]
        transitions = [WorkflowTransition(t["name"], t["from_state"], t["to_state"]) for t in data["transitions"]]
        return cls(name=data["name"], states=states, transitions=transitions, initial_state=data["initial_state"])
