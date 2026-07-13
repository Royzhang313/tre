"""SandboxPreviewService —— 完全异常隔离，不影响主 ERP UI"""

from app.ai.sandbox.models import SandboxInstance
from app.ai.ui.models import ActionSchema, ColumnDef, ListConfig, PageSchema


class SandboxPreviewService:

    @staticmethod
    async def generate_preview_menu() -> dict:
        """返回 {items: []} 格式，任何异常返回空列表"""
        try:
            from sqlalchemy import select, text

            from app.core.database import async_session_factory
            async with async_session_factory() as session:
                # 先测试 DB 连通性
                await session.execute(text("SELECT 1"))
                stmt = select(SandboxInstance).where(
                    SandboxInstance.status.in_(["installed", "testing", "passed"])
                ).order_by(SandboxInstance.created_at.desc())
                result = await session.execute(stmt)
                instances = result.scalars().all()
            return {"items": [
                {"label": f"Sandbox: {inst.module_name}", "route": f"/preview/{inst.id}",
                 "status": inst.status}
                for inst in instances
            ]}
        except Exception:
            return {"items": []}

    @staticmethod
    async def generate_preview_schema(sandbox_id: str) -> dict | None:
        """为 Sandbox 生成预览 UISchema，异常返回 None"""
        try:
            from sqlalchemy import select, text

            from app.ai.service import ArtifactRepository
            from app.core.database import async_session_factory
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
                stmt = select(SandboxInstance).where(SandboxInstance.id == sandbox_id)
                result = await session.execute(stmt)
                inst = result.scalar_one_or_none()
                if inst is None:
                    return None
                arts = await ArtifactRepository(session).list_by_execution(inst.execution_id)
            pages = [PageSchema(
                route=f"/preview/{sandbox_id}", title=f"{inst.module_name} 列表",
                page_type="list", entity=inst.module_name,
                list_config=ListConfig(columns=[
                    ColumnDef(field="id", header="ID"),
                    ColumnDef(field="name", header="名称"),
                ]),
                actions=[ActionSchema(name="create", label="新增", capability="preview.create")],
                permission="preview.read",
            )]
            return {
                "module_name": f"preview_{inst.module_name}",
                "module_display": f"预览: {inst.module_name}",
                "version": "sandbox",
                "pages": [
                    {"route": p.route, "title": p.title, "page_type": p.page_type,
                     "entity": p.entity, "permission": p.permission,
                     "list_config": {"columns": [{"field": c.field, "header": c.header} for c in (p.list_config.columns if p.list_config else [])]},
                     "actions": [{"name": a.name, "label": a.label, "capability": a.capability} for a in p.actions]}
                    for p in pages
                ],
            }
        except Exception:
            return None
