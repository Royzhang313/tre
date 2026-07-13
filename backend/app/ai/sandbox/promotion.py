"""PromotionService —— Sandbox → Production 晋升"""

from datetime import UTC, datetime
from uuid import UUID

from app.ai.sandbox.models import PromotionRequest, SandboxInstance
from app.core.exceptions import ConflictError
from app.shared.module_registry import ModuleManifest, ModuleRegistry, UIPageMeta


class PromotionService:
    """晋升服务 —— draft → reviewing → approved → promoting → completed/failed"""

    VALID_TRANSITIONS = {
        "draft": {"reviewing"},
        "reviewing": {"approved", "draft"},
        "approved": {"promoting"},
        "promoting": {"completed", "failed"},
        "completed": set(),
        "failed": {"draft"},
    }

    @staticmethod
    def _repo(session):
        from sqlalchemy import select

        class Repo:
            def __init__(self, s): self.s = s
            async def create(self, obj): self.s.add(obj); await self.s.flush()
            async def get(self, cls, obj_id):
                stmt = select(cls).where(cls.id == obj_id)
                result = await self.s.execute(stmt)
                return result.scalar_one_or_none()
            async def update(self, obj): await self.s.flush()
        return Repo(session)

    @classmethod
    async def create(cls, session, sandbox_id: UUID, module_name: str) -> PromotionRequest:
        """创建 Promotion 请求（draft）"""
        repo = cls._repo(session)
        inst = await repo.get(SandboxInstance, sandbox_id)
        if not inst:
            raise ConflictError("Sandbox 不存在")
        if inst.status != "passed":
            raise ConflictError("只有通过的 Sandbox 可以 Promote")

        pr = PromotionRequest(sandbox_id=sandbox_id, module_name=module_name)
        await repo.create(pr)
        return pr

    @classmethod
    async def approve(cls, session, promo_id: UUID, user_id: UUID) -> PromotionRequest:
        """审批通过 → 自动 Promote"""
        repo = cls._repo(session)
        pr = await repo.get(PromotionRequest, promo_id)
        if not pr:
            raise ConflictError("PromotionRequest 不存在")
        if pr.status not in ("draft", "reviewing"):
            raise ConflictError("当前状态不可审批")

        pr.status = "approved"
        pr.reviewed_by = user_id
        await repo.update(pr)

        # 自动执行 Promote
        return await cls._execute_promotion(session, pr)

    @classmethod
    async def _execute_promotion(cls, session, pr: PromotionRequest) -> PromotionRequest:
        """执行 Promotion —— 注册到 Production ModuleRegistry"""
        repo = cls._repo(session)
        pr.status = "promoting"
        await repo.update(pr)

        try:
            inst = await repo.get(SandboxInstance, pr.sandbox_id)

            # 从 Sandbox 生成 UI Metadata 并注册到 ModuleRegistry
            pages = []
            from app.ai.service import ArtifactRepository
            arts = await ArtifactRepository(session).list_by_execution(inst.execution_id)
            art_types = {a.artifact_type for a in arts}

            if "create_entity" in art_types:
                entity_name = pr.module_name.replace("_", " ").title().replace(" ", "")
                pages.append(UIPageMeta(
                    route=f"/{pr.module_name}/list",
                    title=f"{pr.module_name} 列表",
                    page_type="list", entity=entity_name,
                    columns=["id", "name", "status", "created_at"],
                    actions=["create", "view"],
                ))
                pages.append(UIPageMeta(
                    route=f"/{pr.module_name}/create",
                    title=f"新增 {pr.module_name}",
                    page_type="form", entity=entity_name,
                    columns=["name", "description"],
                ))

            # 记录版本（Evolution Governance）
            from app.ai.evolution.service import EvolutionService
            ui_json = {"pages": [{"route": p.route, "title": p.title, "page_type": p.page_type, "entity": p.entity} for p in pages]}
            await EvolutionService.record_version(session, pr.module_name, pr.id, pr.sandbox_id, ui_json, [])

            # 注册到生产 ModuleRegistry
            ModuleRegistry.register(ModuleManifest(
                name=pr.module_name,
                display_name=pr.module_name,
                version=pr.target_version,
                ui_pages=pages,
                permissions=[f"{pr.module_name}.read", f"{pr.module_name}.create"],
                dependencies=["basedata", "auth"],
            ))

            pr.status = "completed"
            pr.promoted_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

            # 更新 Sandbox 状态
            inst.status = "promoted"
            inst.promoted_to_merge_id = pr.id
            await repo.update(inst)

            await repo.update(pr)
            return pr

        except Exception as e:
            pr.status = "failed"
            pr.review_comment = str(e)[:500]
            await repo.update(pr)
            return pr
