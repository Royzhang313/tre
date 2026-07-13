"""EvolutionService —— 版本管理 + 对比 + 回滚"""
# ruff: noqa: E501,E701,E702

from datetime import UTC, datetime
from uuid import UUID

from app.ai.evolution.models import ArtifactVersion, ModuleVersion, UISnapshot
from app.core.exceptions import ConflictError, NotFoundError
from app.shared.module_registry import ModuleManifest, ModuleRegistry, UIPageMeta


class EvolutionService:
    """版本治理服务"""

    @staticmethod
    def _repo(session):
        from sqlalchemy import select
        class R:
            def __init__(self, s): self.s = s
            async def create(self, obj): self.s.add(obj); await self.s.flush()
            async def get(self, cls, obj_id):
                stmt = select(cls).where(cls.id == obj_id)
                r = await self.s.execute(stmt); return r.scalar_one_or_none()
            async def list_by(self, cls, **filters):
                stmt = select(cls)
                for k, v in filters.items(): stmt = stmt.where(getattr(cls, k) == v)
                stmt = stmt.order_by(cls.created_at.desc())
                r = await self.s.execute(stmt); return list(r.scalars().all())
            async def update(self, obj): await self.s.flush()
        return R(session)

    @classmethod
    async def record_version(cls, session, module_name: str, pr_id: UUID, sandbox_id: UUID, ui_json: dict, artifacts: list) -> ModuleVersion:
        """Promotion 时记录版本快照"""
        repo = cls._repo(session)

        # 确定版本号
        existing = await repo.list_by(ModuleVersion, module_name=module_name)
        version_num = len(existing) + 1

        # 停用旧版本
        for v in existing:
            if v.status == "active":
                v.status = "superseded"
                await repo.update(v)

        mv = ModuleVersion(
            module_name=module_name, version=f"V{version_num}",
            promotion_id=pr_id, sandbox_id=sandbox_id,
            ui_snapshot=ui_json, change_summary=f"Promotion from Sandbox {sandbox_id}",
            deployed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        await repo.create(mv)

        # 保存 Artifact 快照
        for art in artifacts:
            await repo.create(ArtifactVersion(
                module_version_id=mv.id,
                file_path=art.get("file_path", ""),
                content=art.get("content", ""),
                checksum=art.get("checksum"),
                artifact_type=art.get("artifact_type", ""),
            ))

        # 保存 UI 快照
        await repo.create(UISnapshot(
            module_version_id=mv.id, module_name=module_name,
            version=mv.version, pages_json=ui_json,
        ))

        return mv

    @classmethod
    async def list_versions(cls, session, module_name: str) -> list[dict]:
        """列出模块所有版本"""
        repo = cls._repo(session)
        versions = await repo.list_by(ModuleVersion, module_name=module_name)
        return [{"id": str(v.id), "version": v.version, "status": v.status, "deployed_at": v.deployed_at, "change_summary": v.change_summary} for v in versions]

    @classmethod
    async def compare_versions(cls, session, version_id_a: UUID, version_id_b: UUID) -> dict:
        """对比两个版本"""
        repo = cls._repo(session)
        a = await repo.get(ModuleVersion, version_id_a)
        b = await repo.get(ModuleVersion, version_id_b)
        if not a or not b:
            raise NotFoundError("版本不存在")

        a_arts = await repo.list_by(ArtifactVersion, module_version_id=a.id)
        b_arts = await repo.list_by(ArtifactVersion, module_version_id=b.id)

        a_files = {art.file_path: art.content for art in a_arts}
        b_files = {art.file_path: art.content for art in b_arts}

        added = [f for f in b_files if f not in a_files]
        removed = [f for f in a_files if f not in b_files]
        changed = [f for f in b_files if f in a_files and b_files[f] != a_files[f]]

        return {
            "version_a": a.version, "version_b": b.version,
            "added_files": added, "removed_files": removed,
            "changed_files": changed,
            "total_changes": len(added) + len(removed) + len(changed),
        }

    @classmethod
    async def rollback(cls, session, module_name: str, target_version_id: UUID) -> dict:
        """回滚到指定版本"""
        repo = cls._repo(session)
        target = await repo.get(ModuleVersion, target_version_id)
        if not target:
            raise NotFoundError("目标版本不存在")
        if target.module_name != module_name:
            raise ConflictError("版本不属于该模块")

        # 读取目标版本的 UI Snapshot
        snapshots = await repo.list_by(UISnapshot, module_version_id=target.id)
        if not snapshots:
            raise ConflictError("目标版本没有 UI 快照")

        snap = snapshots[0]

        # 注册回到 ModuleRegistry
        pages = []
        for p in snap.pages_json.get("pages", []):
            pages.append(UIPageMeta(
                route=p.get("route", f"/{module_name}"),
                title=p.get("title", module_name),
                page_type=p.get("page_type", "list"),
                entity=p.get("entity", ""),
                columns=p.get("list_config", {}).get("columns", []),
                actions=p.get("actions", []),
            ))

        ModuleRegistry.register(ModuleManifest(
            name=module_name, display_name=module_name,
            version=target.version, ui_pages=pages,
        ))

        # 标记当前 active 版本为 rolled_back
        active_versions = await repo.list_by(ModuleVersion, module_name=module_name, status="active")
        for v in active_versions:
            v.status = "rolled_back"
            v.rolled_back_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            await repo.update(v)

        # 激活目标版本
        target.status = "active"
        await repo.update(target)

        return {"module_name": module_name, "rolled_back_to": target.version, "status": "active"}
