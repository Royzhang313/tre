"""AI Builder —— Architect Agent Service + Validator + Lifecycle"""

from datetime import UTC, datetime
from uuid import UUID

from app.ai.lifecycle import SpecLifecycle
from app.ai.models import (
    AIDomainSpec,
    Artifact,
    BuildExecution,
    BuildPlan,
    BuildTask,
    DomainSpecSnapshot,
)
from app.ai.schemas import SpecCreate
from app.ai.validator.capability_rule import CapabilityPermissionRule, CapabilityUniqueRule
from app.ai.validator.entity_rule import EntityFieldTypeRule, EntityFKValidRule, EntityUniqueRule
from app.ai.validator.module_rule import ModuleDependencyRule, ModuleUniqueRule
from app.ai.validator.permission_rule import PermissionFormatRule
from app.ai.validator.workflow_rule import WorkflowStateIntegrityRule, WorkflowTerminalValidRule
from app.core.exceptions import ConflictError, NotFoundError
from app.shared.capability_registry import CapabilityRegistry
from app.shared.module_registry import ModuleRegistry


class SpecRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, spec: AIDomainSpec) -> AIDomainSpec:
        self.session.add(spec)
        await self.session.flush()
        return spec

    async def get_by_id(self, spec_id: UUID) -> AIDomainSpec | None:
        from sqlalchemy import select
        stmt = select(AIDomainSpec).where(AIDomainSpec.id == spec_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_or_raise(self, spec_id: UUID) -> AIDomainSpec:
        spec = await self.get_by_id(spec_id)
        if spec is None:
            raise NotFoundError("Domain Spec 不存在", entity="AIDomainSpec", entity_id=spec_id)
        return spec

    async def update(self, spec: AIDomainSpec) -> AIDomainSpec:
        await self.session.flush()
        return spec

    async def list_all(self, limit: int = 20) -> list[AIDomainSpec]:
        from sqlalchemy import select
        stmt = select(AIDomainSpec).order_by(AIDomainSpec.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_history(self, root_id: UUID) -> list[AIDomainSpec]:
        """获取版本链（parent 回溯）"""
        results = []
        current = await self.get_by_id(root_id)
        while current:
            results.append(current)
            current = await self.get_by_id(current.parent_spec_id) if current.parent_spec_id else None
        return results


class PlanRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, plan: BuildPlan) -> BuildPlan:
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def get_by_id(self, plan_id: UUID) -> BuildPlan | None:
        from sqlalchemy import select
        stmt = select(BuildPlan).where(BuildPlan.id == plan_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, plan: BuildPlan) -> BuildPlan:
        await self.session.flush()
        return plan


class SnapshotRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, snap: DomainSpecSnapshot) -> DomainSpecSnapshot:
        self.session.add(snap)
        await self.session.flush()
        return snap


# ============================================================
# SpecService
# ============================================================


class SpecService:
    def __init__(self, repo: SpecRepository):
        self.repo = repo

    async def create(self, data: SpecCreate) -> AIDomainSpec:
        spec = AIDomainSpec(title=data.title, business_context=data.business_context, spec_json=data.spec_json)
        await self.repo.create(spec)
        return spec

    async def validate(self, spec_id: UUID) -> dict:
        spec = await self.repo.get_by_id_or_raise(spec_id)
        SpecLifecycle.transition(spec, "validating")
        await self.repo.update(spec)
        return SpecValidator.validate(spec.spec_json)

    async def approve(self, spec_id: UUID, user_id: UUID, comment: str | None) -> AIDomainSpec:
        spec = await self.repo.get_by_id_or_raise(spec_id)
        SpecLifecycle.transition(spec, "approved")
        spec.reviewed_by = user_id
        spec.reviewed_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        spec.review_comment = comment
        await self.repo.update(spec)
        return spec

    async def reject(self, spec_id: UUID, user_id: UUID, comment: str | None) -> AIDomainSpec:
        spec = await self.repo.get_by_id_or_raise(spec_id)
        SpecLifecycle.transition(spec, "draft")
        spec.reviewed_by = user_id
        spec.reviewed_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        spec.review_comment = comment
        await self.repo.update(spec)
        return spec

    async def create_version(self, spec_id: UUID, reason: str) -> AIDomainSpec:
        """从已部署的 Spec 创建新版本"""
        parent = await self.repo.get_by_id_or_raise(spec_id)
        if parent.status != "deployed":
            raise ConflictError("只有已部署的 Spec 可以创建新版本")
        new_spec = AIDomainSpec(
            version=parent.version + 1, parent_spec_id=parent.id,
            revision_reason=reason, title=parent.title,
            business_context=parent.business_context, spec_json=parent.spec_json,
        )
        await self.repo.create(new_spec)
        return new_spec

    async def generate_plan(self, spec_id: UUID) -> BuildPlan:
        spec = await self.repo.get_by_id_or_raise(spec_id)
        if spec.status != "approved":
            raise ConflictError("只有已审批的 Spec 可以生成 BuildPlan")

        actions = []
        spec_json = spec.spec_json
        for mod in spec_json.get("new_modules", []):
            actions.append({"action_type": "create_module", "payload": mod, "status": "pending"})
        for entity in spec_json.get("new_entities", []):
            actions.append({"action_type": "create_entity", "payload": entity, "status": "pending"})
        for cap in spec_json.get("new_capabilities", []):
            actions.append({"action_type": "create_capability", "payload": cap, "status": "pending"})
        for wf in spec_json.get("new_workflows", []):
            actions.append({"action_type": "create_workflow", "payload": wf, "status": "pending"})
        for perm in spec_json.get("new_permissions", []):
            actions.append({"action_type": "create_permission", "payload": perm, "status": "pending"})
        for entity in spec_json.get("extended_entities", []):
            actions.append({"action_type": "extend_entity", "payload": entity, "status": "pending"})
        for page in spec_json.get("ui_pages", []):
            actions.append({"action_type": "create_ui_page", "payload": page, "status": "pending"})

        plan = BuildPlan(spec_id=spec.id, actions={"actions": actions}, estimated_changes=f"{len(actions)} 个操作")
        plan_repo = PlanRepository(self.repo.session)
        return await plan_repo.create(plan)

    async def create_snapshot(self, spec_id: UUID) -> DomainSpecSnapshot:
        spec = await self.repo.get_by_id_or_raise(spec_id)
        snap = DomainSpecSnapshot(
            spec_id=spec.id, spec_version=spec.version,
            spec_json=spec.spec_json,
        )
        async with self.repo.session as session:
            return await SnapshotRepository(session).create(snap)


# ============================================================
# SpecValidator (规则框架)
# ============================================================


class SpecValidator:
    _rules = [
        ModuleUniqueRule(), ModuleDependencyRule(),
        EntityUniqueRule(), EntityFKValidRule(), EntityFieldTypeRule(),
        CapabilityUniqueRule(), CapabilityPermissionRule(),
        WorkflowStateIntegrityRule(), WorkflowTerminalValidRule(),
        PermissionFormatRule(),
    ]

    @classmethod
    def validate(cls, spec_json: dict) -> dict:
        context = {
            "existing_modules": {m.name for m in ModuleRegistry.list_all()},
            "existing_capabilities": {c.name for c in CapabilityRegistry.list_all()},
        }
        results = []
        for rule in cls._rules:
            results.extend(rule.validate(spec_json, context))

        errors = [{"rule": r.rule_name, "message": r.message, "path": r.path} for r in results if r.level == "error"]
        warnings = [{"rule": r.rule_name, "message": r.message, "path": r.path} for r in results if r.level == "warning"]
        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings, "rules_executed": len(cls._rules)}


# ============================================================
# Builder Execution
# ============================================================


class ExecutionRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, exe: "BuildExecution") -> "BuildExecution":
        self.session.add(exe)
        await self.session.flush()
        return exe

    async def get_by_id(self, exe_id: UUID) -> "BuildExecution | None":
        from sqlalchemy import select
        stmt = select(BuildExecution).where(BuildExecution.id == exe_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, exe: "BuildExecution") -> "BuildExecution":
        await self.session.flush()
        return exe


class TaskRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, task: "BuildTask") -> "BuildTask":
        self.session.add(task)
        await self.session.flush()
        return task

    async def list_by_execution(self, exe_id: UUID) -> list["BuildTask"]:
        from sqlalchemy import select
        stmt = select(BuildTask).where(BuildTask.execution_id == exe_id).order_by(BuildTask.action_index)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, task: "BuildTask") -> "BuildTask":
        await self.session.flush()
        return task


class GeneratorRegistry:
    """生成器注册表 —— 按 action_type 注册"""

    _generators: dict[str, type] = {}

    @classmethod
    def register(cls, action_type: str, gen_class: type) -> None:
        cls._generators[action_type] = gen_class

    @classmethod
    def get(cls, action_type: str) -> type | None:
        return cls._generators.get(action_type)

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._generators.keys())


class ArtifactRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, art: "Artifact") -> "Artifact":
        self.session.add(art)
        await self.session.flush()
        return art

    async def list_by_execution(self, exe_id: UUID) -> list["Artifact"]:
        from sqlalchemy import select

        from app.ai.models import Artifact
        stmt = select(Artifact).where(Artifact.execution_id == exe_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, art_id: UUID) -> "Artifact | None":
        from sqlalchemy import select

        from app.ai.models import Artifact
        stmt = select(Artifact).where(Artifact.id == art_id)
        result = await self.session.execute(stmt)
        return result.scalars().one_or_none()


class BuilderExecutionService:
    """Builder Agent 执行服务"""

    @classmethod
    async def execute(cls, plan_id: UUID) -> dict:
        """执行 BuildPlan → 创建 BuildExecution + BuildTasks + 生成 Artifacts"""
        from app.ai.models import Artifact
        from app.core.database import async_session_factory

        async with async_session_factory() as session:
            plan_repo = PlanRepository(session)
            plan = await plan_repo.get_by_id(plan_id)
            if plan is None:
                raise NotFoundError("BuildPlan 不存在")

            if plan.status != "approved":
                raise ConflictError("只有已审批的 BuildPlan 可以执行")

            exe = BuildExecution(plan_id=plan_id, status="running")
            await ExecutionRepository(session).create(exe)

            actions = plan.actions.get("actions", [])
            artifacts = []
            for i, action in enumerate(actions):
                action_type = action.get("action_type", "")
                gen_cls = GeneratorRegistry.get(action_type)
                task = BuildTask(execution_id=exe.id, action_type=action_type, action_index=i, status="running")
                await TaskRepository(session).create(task)

                if gen_cls:
                    try:
                        generator = gen_cls()
                        result = generator.generate(action.get("payload", {}), {"module_name": action.get("payload", {}).get("name", "")})
                        art = Artifact(
                            execution_id=exe.id, task_id=task.id,
                            artifact_type=result.artifact_type, file_path=result.path,
                            content=result.content, checksum=result.checksum,
                        )
                        await ArtifactRepository(session).create(art)
                        task.artifact = {"path": result.path, "type": result.artifact_type, "artifact_id": str(art.id)}
                        task.status = "completed"
                        artifacts.append({"id": str(art.id), "path": result.path, "type": result.artifact_type})
                    except Exception as e:
                        task.status = "failed"
                        task.error_message = str(e)[:1000]
                else:
                    task.status = "skipped"

                await TaskRepository(session).update(task)

            exe.status = "generated"
            await ExecutionRepository(session).update(exe)

            return {"execution_id": str(exe.id), "status": exe.status, "tasks": len(actions), "artifacts": len(artifacts), "files": artifacts}



# ============================================================
# Merge Service
# ============================================================


class MergeService:
    """合并服务 —— Conflict Check → Diff → Apply → Verify"""

    @staticmethod
    async def create_request(execution_id: UUID, module_name: str) -> dict:
        """创建 MergeRequest + Conflict Check + Diff"""
        from app.ai.merge.conflict import ConflictChecker
        from app.ai.merge.diff_gen import DiffGenerator
        from app.ai.merge.models import MergeRequest as MR
        from app.core.database import async_session_factory

        async with async_session_factory() as session:
            # 获取 artifacts
            arts = await ArtifactRepository(session).list_by_execution(execution_id)
            art_dicts = [{"file_path": a.file_path, "artifact_type": a.artifact_type, "content": a.content, "payload": {}} for a in arts]

            conflict_result = ConflictChecker.check(art_dicts, module_name)
            diff = DiffGenerator.generate(art_dicts, module_name)

            mr = MR(execution_id=execution_id, module_name=module_name, diff_summary=diff, conflict_log=conflict_result)
            session.add(mr)
            await session.flush()

            return {"merge_request_id": str(mr.id), "status": mr.status, "diff": diff, "conflicts": conflict_result}

    @staticmethod
    async def approve(merge_id: UUID, user_id: UUID) -> dict:
        from app.ai.merge.models import MergeRequest as MR
        from app.core.database import async_session_factory
        async with async_session_factory() as session:
            from sqlalchemy import select
            stmt = select(MR).where(MR.id == merge_id)
            result = await session.execute(stmt)
            mr = result.scalar_one_or_none()
            if mr is None:
                return {"error": "MergeRequest 不存在"}
            mr.status = "approved"
            mr.reviewed_by = user_id
            await session.flush()
            return {"id": str(mr.id), "status": "approved"}

    @staticmethod
    async def apply(merge_id: UUID) -> dict:
        from app.ai.merge.applier import MergeApplier
        from app.ai.merge.models import MergeRequest as MR
        from app.ai.merge.verifier import MergeVerifier
        from app.core.database import async_session_factory

        async with async_session_factory() as session:
            from sqlalchemy import select
            stmt = select(MR).where(MR.id == merge_id)
            result = await session.execute(stmt)
            mr = result.scalar_one_or_none()
            if mr is None:
                return {"error": "MergeRequest 不存在"}
            if mr.status != "approved":
                return {"error": "MergeRequest 未审批"}

            mr.status = "applying"
            await session.flush()

            # Apply
            arts = await ArtifactRepository(session).list_by_execution(mr.execution_id)
            art_dicts = [{"file_path": a.file_path, "content": a.content} for a in arts]
            apply_result = MergeApplier.apply(art_dicts, mr.module_name)

            # Verify
            verify_result = MergeVerifier.verify()

            mr.status = "completed" if verify_result["all_pass"] else "failed"
            mr.applied_at = str(__import__("datetime").datetime.now())
            mr.verified_at = str(__import__("datetime").datetime.now())
            await session.flush()

            return {"id": str(mr.id), "status": mr.status, "apply": apply_result, "verify": verify_result}

    @staticmethod
    async def rollback(merge_id: UUID) -> dict:
        from app.ai.merge.applier import MergeApplier
        from app.ai.merge.models import MergeRequest as MR
        from app.core.database import async_session_factory

        async with async_session_factory() as session:
            from sqlalchemy import select
            stmt = select(MR).where(MR.id == merge_id)
            result = await session.execute(stmt)
            mr = result.scalar_one_or_none()
            if mr is None:
                return {"error": "MergeRequest 不存在"}

            rollback_result = MergeApplier.rollback(mr.module_name)
            mr.status = "rolled_back"
            await session.flush()
            return {"id": str(mr.id), "status": "rolled_back", "rollback": rollback_result}
