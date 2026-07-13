"""AI Builder —— Architect + Builder + Sandbox + Promotion API"""
# ruff: noqa: E501,E701,N817

from uuid import UUID

from fastapi import APIRouter, Depends

from app.ai.schemas import SpecApproveRequest, SpecCreate, SpecVersionRequest
from app.ai.service import BuilderExecutionService, PlanRepository, SpecRepository, SpecService
from app.core.database import async_session_factory
from app.modules.auth.context import CurrentUser
from app.modules.auth.dependencies import get_current_user
from app.shared.base_schema import APIResponse
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/ai", tags=["AI Builder"])




# === Spec CRUD + Lifecycle + Version + Plan ===

@router.post("/spec/create")
async def create_spec(body: SpecCreate):
    async with async_session_factory() as session:
        spec = await SpecService(SpecRepository(session)).create(body)
    return APIResponse.ok({"id": str(spec.id), "status": spec.status})

@router.get("/spec")
async def list_specs():
    async with async_session_factory() as session:
        specs = await SpecRepository(session).list_all()
    return APIResponse.ok([_to_dict(s) for s in specs])

@router.get("/spec/{spec_id}")
async def get_spec(spec_id: UUID):
    async with async_session_factory() as session:
        spec = await SpecRepository(session).get_by_id_or_raise(spec_id)
    return APIResponse.ok(_to_dict(spec))

@router.post("/spec/{spec_id}/validate")
async def validate_spec(spec_id: UUID):
    async with async_session_factory() as session:
        result = await SpecService(SpecRepository(session)).validate(spec_id)
    return APIResponse.ok(result)

@router.post("/spec/{spec_id}/approve")
async def approve_spec(spec_id: UUID, body: SpecApproveRequest, current_user: CurrentUser = Depends(get_current_user)):
    async with async_session_factory() as session:
        spec = await SpecService(SpecRepository(session)).approve(spec_id, current_user.id, body.comment)
    return APIResponse.ok({"id": str(spec.id), "status": spec.status})

@router.post("/spec/{spec_id}/reject")
async def reject_spec(spec_id: UUID, body: SpecApproveRequest, current_user: CurrentUser = Depends(get_current_user)):
    async with async_session_factory() as session:
        spec = await SpecService(SpecRepository(session)).reject(spec_id, current_user.id, body.comment)
    return APIResponse.ok({"id": str(spec.id), "status": spec.status})

@router.post("/spec/{spec_id}/version")
async def create_version(spec_id: UUID, body: SpecVersionRequest):
    async with async_session_factory() as session:
        spec = await SpecService(SpecRepository(session)).create_version(spec_id, body.revision_reason)
    return APIResponse.ok({"id": str(spec.id), "version": spec.version})

@router.get("/spec/{spec_id}/history")
async def spec_history(spec_id: UUID):
    async with async_session_factory() as session:
        versions = await SpecRepository(session).get_history(spec_id)
    return APIResponse.ok([{"id": str(v.id), "version": v.version, "status": v.status} for v in versions])

@router.post("/spec/{spec_id}/generate-plan")
async def generate_plan(spec_id: UUID):
    async with async_session_factory() as session:
        plan = await SpecService(SpecRepository(session)).generate_plan(spec_id)
    return APIResponse.ok({"id": str(plan.id), "actions_count": len(plan.actions.get("actions", []))})

@router.get("/plan/{plan_id}")
async def get_plan(plan_id: UUID):
    async with async_session_factory() as session:
        plan = await PlanRepository(session).get_by_id(plan_id)
    if plan is None: return APIResponse.fail(404, "BuildPlan 不存在")
    return APIResponse.ok(_to_dict(plan))

@router.post("/plan/{plan_id}/approve")
async def approve_plan(plan_id: UUID):
    async with async_session_factory() as session:
        repo = PlanRepository(session)
        plan = await repo.get_by_id(plan_id)
        if plan is None: return APIResponse.fail(404, "BuildPlan 不存在")
        plan.status = "approved"
        await repo.update(plan)
    return APIResponse.ok({"id": str(plan.id), "status": "approved"})

# === Builder Execution ===

@router.post("/builder/execute")
async def execute_build(plan_id: UUID):
    return APIResponse.ok(await BuilderExecutionService.execute(plan_id))

# === Sandbox ===

@router.post("/sandbox/create")
async def create_sandbox(execution_id: UUID, module_name: str):
    from app.ai.sandbox.service import SandboxService
    async with async_session_factory() as session:
        inst = await SandboxService.create(session, execution_id, module_name)
    return APIResponse.ok({"id": str(inst.id), "status": inst.status})

@router.post("/sandbox/{instance_id}/install")
async def install_sandbox(instance_id: UUID):
    from app.ai.sandbox.service import SandboxService
    async with async_session_factory() as session:
        inst = await SandboxService.install(session, instance_id)
    return APIResponse.ok({"id": str(inst.id), "status": inst.status})

@router.post("/sandbox/{instance_id}/test")
async def test_sandbox(instance_id: UUID):
    from app.ai.sandbox.service import SandboxService
    async with async_session_factory() as session:
        inst = await SandboxService.test(session, instance_id)
    return APIResponse.ok({"id": str(inst.id), "status": inst.status, "test_summary": inst.test_summary})

@router.post("/sandbox/{instance_id}/destroy")
async def destroy_sandbox(instance_id: UUID):
    from app.ai.sandbox.service import SandboxService
    async with async_session_factory() as session:
        inst = await SandboxService.destroy(session, instance_id)
    return APIResponse.ok({"id": str(inst.id), "status": inst.status})

@router.get("/sandbox/{instance_id}")
async def get_sandbox(instance_id: UUID):
    from sqlalchemy import select

    from app.ai.sandbox.models import SandboxInstance as SI
    async with async_session_factory() as session:
        stmt = select(SI).where(SI.id == instance_id)
        inst = (await session.execute(stmt)).scalar_one_or_none()
    if inst is None: return APIResponse.fail(404, "Sandbox 不存在")
    return APIResponse.ok({"id": str(inst.id), "module_name": inst.module_name, "status": inst.status})

# === Promotion (M9) ===

@router.post("/promotion/create")
async def create_promotion(sandbox_id: UUID, module_name: str):
    from app.ai.sandbox.promotion import PromotionService
    async with async_session_factory() as session:
        pr = await PromotionService.create(session, sandbox_id, module_name)
    return APIResponse.ok({"id": str(pr.id), "module_name": pr.module_name, "status": pr.status})

@router.post("/promotion/{promo_id}/approve")
async def approve_promotion_m9(promo_id: UUID, current_user: CurrentUser = Depends(get_current_user)):
    from app.ai.sandbox.promotion import PromotionService
    async with async_session_factory() as session:
        pr = await PromotionService.approve(session, promo_id, current_user.id)
    return APIResponse.ok({"id": str(pr.id), "module_name": pr.module_name, "status": pr.status})

@router.get("/promotion/{promo_id}")
async def get_promotion(promo_id: UUID):
    from sqlalchemy import select

    from app.ai.sandbox.models import PromotionRequest as PR
    async with async_session_factory() as session:
        stmt = select(PR).where(PR.id == promo_id)
        pr = (await session.execute(stmt)).scalar_one_or_none()
    if pr is None: return APIResponse.fail(404, "Promotion 不存在")
    return APIResponse.ok({"id": str(pr.id), "module_name": pr.module_name, "status": pr.status})

# === Merge ===

@router.post("/merge/request")
async def create_merge_request(execution_id: UUID, module_name: str):
    from app.ai.service import MergeService
    return APIResponse.ok(await MergeService.create_request(execution_id, module_name))

# === Artifact ===

@router.get("/artifacts/{execution_id}")
async def list_artifacts(execution_id: UUID):
    from app.ai.service import ArtifactRepository
    async with async_session_factory() as session:
        arts = await ArtifactRepository(session).list_by_execution(execution_id)
    return APIResponse.ok([{"id": str(a.id), "artifact_type": a.artifact_type, "file_path": a.file_path} for a in arts])

@router.post("/artifact/{artifact_id}/approve")
async def approve_artifact(artifact_id: UUID):
    from app.ai.service import ArtifactRepository
    async with async_session_factory() as session:
        repo = ArtifactRepository(session)
        art = await repo.get_by_id(artifact_id)
        if art is None: return APIResponse.fail(404, "Artifact 不存在")
        art.status = "approved"
        await session.flush()
    return APIResponse.ok({"id": str(art.id), "status": "approved"})


# ============================================================
# Evolution (M10)
# ============================================================


@router.get("/evolution/{module_name}/versions")
async def list_versions(module_name: str):
    """模块版本列表"""
    from app.ai.evolution.service import EvolutionService
    async with async_session_factory() as session:
        versions = await EvolutionService.list_versions(session, module_name)
    return APIResponse.ok(versions)


@router.get("/evolution/compare")
async def compare_versions(version_a: UUID, version_b: UUID):
    """对比两个版本"""
    from app.ai.evolution.service import EvolutionService
    async with async_session_factory() as session:
        diff = await EvolutionService.compare_versions(session, version_a, version_b)
    return APIResponse.ok(diff)


@router.post("/evolution/{module_name}/rollback")
async def rollback_version(module_name: str, target_version_id: UUID):
    """回滚到指定版本"""
    from app.ai.evolution.service import EvolutionService
    async with async_session_factory() as session:
        result = await EvolutionService.rollback(session, module_name, target_version_id)
    return APIResponse.ok(result)
