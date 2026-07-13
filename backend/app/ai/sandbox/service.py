"""SandboxService —— 生命周期管理"""

import os
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.ai.sandbox.models import PromotionRequest, SandboxInstance
from app.core.exceptions import ConflictError


class SandboxService:
    SANDBOX_ROOT = tempfile.gettempdir() + "/erp_builder_sandboxes"
    EXPIRE_HOURS = 24

    @staticmethod
    def _repo(session):
        """内联 Repository"""
        from sqlalchemy import select

        class Repo:
            def __init__(self, s):
                self.s = s

            async def create(self, obj) -> None:
                self.s.add(obj)
                await self.s.flush()

            async def get(self, cls, obj_id: UUID):
                stmt = select(cls).where(cls.id == obj_id)
                result = await self.s.execute(stmt)
                return result.scalar_one_or_none()

            async def update(self, obj) -> None:
                await self.s.flush()

        return Repo(session)

    # ============================================================
    # Lifecycle
    # ============================================================

    @classmethod
    async def create(cls, session, execution_id: UUID, module_name: str) -> SandboxInstance:
        inst = SandboxInstance(execution_id=execution_id, module_name=module_name)
        await cls._repo(session).create(inst)
        return inst

    @classmethod
    async def install(cls, session, instance_id: UUID) -> SandboxInstance:
        repo = cls._repo(session)
        inst = await repo.get(SandboxInstance, instance_id)
        if inst is None:
            raise ConflictError("Sandbox 不存在")

        inst.status = "building"
        await repo.update(inst)

        sandbox_dir = os.path.join(cls.SANDBOX_ROOT, f"{inst.module_name}_{inst.id}")
        os.makedirs(sandbox_dir, exist_ok=True)
        inst.sandbox_path = sandbox_dir

        # 从 Artifacts 安装文件
        from app.ai.service import ArtifactRepository
        arts = await ArtifactRepository(session).list_by_execution(inst.execution_id)
        for art in arts:
            file_name = os.path.basename(art.file_path)
            target = os.path.join(sandbox_dir, file_name)
            with open(target, "w") as f:
                f.write(art.content)

        inst.status = "installed"
        inst.expired_at = (datetime.now(UTC) + timedelta(hours=cls.EXPIRE_HOURS)).isoformat()
        await repo.update(inst)
        return inst

    @classmethod
    async def test(cls, session, instance_id: UUID) -> SandboxInstance:
        repo = cls._repo(session)
        inst = await repo.get(SandboxInstance, instance_id)
        if inst is None or inst.sandbox_path is None:
            raise ConflictError("Sandbox 未就绪")

        inst.status = "testing"
        await repo.update(inst)

        # 运行 pytest（隔离进程，10秒超时）
        results = {"total": 0, "passed": 0, "failed": 0}
        try:
            proc = subprocess.run(
                ["python3", "-m", "pytest", inst.sandbox_path, "-q", "--tb=short"],
                capture_output=True, text=True, timeout=30, cwd=inst.sandbox_path,
            )
            # 解析结果
            output = proc.stdout + proc.stderr
            for line in output.split("\n"):
                if "passed" in line and "failed" in line:
                    # parse "10 passed, 2 failed"
                    parts = line.strip().split(",")
                    for p in parts:
                        p = p.strip()
                        if "passed" in p:
                            results["passed"] = int(p.split()[0])
                        elif "failed" in p:
                            results["failed"] = int(p.split()[0])
            results["total"] = results["passed"] + results["failed"]
            inst.status = "passed" if results["failed"] == 0 and results["total"] > 0 else "failed"
        except subprocess.TimeoutExpired:
            inst.status = "failed"
            inst.error_log = "pytest 执行超时 (30s)"
        except Exception as e:
            inst.status = "failed"
            inst.error_log = str(e)[:2000]

        inst.test_summary = results
        await repo.update(inst)
        return inst

    @classmethod
    async def promote(cls, session, instance_id: UUID) -> PromotionRequest:
        repo = cls._repo(session)
        inst = await repo.get(SandboxInstance, instance_id)
        if inst is None:
            raise ConflictError("Sandbox 不存在")
        if inst.status != "passed":
            raise ConflictError("只有通过的 Sandbox 可以 Promote")

        pr = PromotionRequest(sandbox_id=inst.id)
        await repo.create(pr)
        return pr

    @classmethod
    async def approve_promotion(cls, session, promo_id: UUID, user_id: UUID) -> PromotionRequest:
        repo = cls._repo(session)
        pr = await repo.get(PromotionRequest, promo_id)
        if pr is None:
            raise ConflictError("PromotionRequest 不存在")

        # 创建 MergeRequest
        inst = await repo.get(SandboxInstance, pr.sandbox_id)
        from app.ai.service import MergeService
        merge_result = await MergeService.create_request(inst.execution_id, inst.module_name)
        from uuid import UUID as _UUID
        pr.merge_request_id = _UUID(merge_result["merge_request_id"])
        pr.status = "approved"
        pr.reviewed_by = user_id
        await repo.update(pr)

        inst.status = "promoted"
        inst.promoted_to_merge_id = pr.merge_request_id
        await repo.update(inst)
        return pr

    @classmethod
    async def destroy(cls, session, instance_id: UUID) -> SandboxInstance:
        repo = cls._repo(session)
        inst = await repo.get(SandboxInstance, instance_id)
        if inst is None:
            raise ConflictError("Sandbox 不存在")
        if inst.sandbox_path and os.path.exists(inst.sandbox_path):
            shutil.rmtree(inst.sandbox_path, ignore_errors=True)
        inst.status = "destroyed"
        await repo.update(inst)
        return inst
