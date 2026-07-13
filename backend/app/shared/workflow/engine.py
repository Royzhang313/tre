"""Workflow Engine —— 轻量状态机（不做 BPMN）

基于 WorkflowDefinition 运行时执行状态转换和校验。
"""

from uuid import UUID

from sqlalchemy import ForeignKey, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import async_session_factory
from app.shared.base_model import BaseModel
from app.shared.workflow.exceptions import InvalidTransitionError
from app.shared.workflow.models import WorkflowDefinition, WorkflowTransition

# ============================================================
# WorkflowInstance —— 运行时实例
# ============================================================


class WorkflowInstance(BaseModel):
    """工作流实例 —— 记录某个实体的当前状态"""

    __tablename__ = "shared_workflow_instances"

    workflow_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    current_state: Mapped[str] = mapped_column(String(50), nullable=False)
    operator_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<WorkflowInstance {self.workflow_name} {self.entity_id} [{self.current_state}]>"


# ============================================================
# WorkflowHistory —— 状态变更历史
# ============================================================


class WorkflowHistory(BaseModel):
    """工作流历史 —— 只追加，记录每次状态转换"""

    __tablename__ = "shared_workflow_history"

    instance_id: Mapped[UUID] = mapped_column(
        ForeignKey("shared_workflow_instances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_state: Mapped[str] = mapped_column(String(50), nullable=False)
    to_state: Mapped[str] = mapped_column(String(50), nullable=False)
    transition_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operator_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True
    )
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<WorkflowHistory {self.transition_name}: {self.from_state} → {self.to_state}>"


# ============================================================
# WorkflowEngine
# ============================================================


class WorkflowEngine:
    """轻量状态机引擎 —— 基于代码注册的 WorkflowDefinition"""

    def __init__(self, definition: WorkflowDefinition):
        self.definition = definition

    def can_transition(self, from_state: str, to_state: str) -> bool:
        """检查是否允许状态转换"""
        for t in self.definition.transitions:
            if t.from_state == from_state and t.to_state == to_state:
                return True
        return False

    def get_allowed_transitions(self, from_state: str) -> list[WorkflowTransition]:
        """获取当前状态允许的所有转换"""
        return [t for t in self.definition.transitions if t.from_state == from_state]

    async def get_or_create_instance(
        self, entity_type: str, entity_id: UUID, operator_id: UUID | None = None,
    ) -> WorkflowInstance:
        """获取或创建工作流实例"""
        async with async_session_factory() as session:
            stmt = select(WorkflowInstance).where(
                WorkflowInstance.workflow_name == self.definition.name,
                WorkflowInstance.entity_type == entity_type,
                WorkflowInstance.entity_id == entity_id,
            )
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if instance is None:
                instance = WorkflowInstance(
                    workflow_name=self.definition.name,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    current_state=self.definition.initial_state,
                    operator_id=operator_id,
                )
                session.add(instance)
                await session.flush()

                # 记录初始状态历史
                session.add(WorkflowHistory(
                    instance_id=instance.id,
                    from_state="__start__",
                    to_state=self.definition.initial_state,
                    transition_name="初始化",
                    operator_id=operator_id,
                ))
                await session.commit()
            return instance

    async def transition(
        self,
        entity_type: str,
        entity_id: UUID,
        to_state: str,
        *,
        operator_id: UUID | None = None,
        transition_name: str = "",
        remark: str | None = None,
    ) -> WorkflowInstance:
        """执行状态转换

        Raises:
            InvalidTransitionError: 非法转换
        """
        instance = await self.get_or_create_instance(entity_type, entity_id, operator_id)

        if not self.can_transition(instance.current_state, to_state):
            raise InvalidTransitionError(
                f"非法转换: {instance.current_state} → {to_state}",
                workflow=self.definition.name,
                from_state=instance.current_state,
                to_state=to_state,
            )

        from_state = instance.current_state
        instance.current_state = to_state
        instance.operator_id = operator_id

        async with async_session_factory() as session:
            merged = await session.merge(instance)
            await session.flush()

            history = WorkflowHistory(
                instance_id=merged.id,
                from_state=from_state,
                to_state=to_state,
                transition_name=transition_name or f"{from_state}→{to_state}",
                operator_id=operator_id,
                remark=remark,
            )
            session.add(history)
            await session.commit()
            return merged
