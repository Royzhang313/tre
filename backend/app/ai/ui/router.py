"""UI Metadata API"""

from fastapi import APIRouter

from app.ai.ui.service import UISchemaGenerator
from app.shared.base_schema import APIResponse

router = APIRouter(prefix="/ui", tags=["Dynamic UI"])


@router.get("/menu")
async def get_menu():
    """全系统菜单树"""
    menu = UISchemaGenerator.generate_menu()
    return APIResponse.ok([{
        "label": m.label, "icon": m.icon, "route": m.route,
        "permission": m.permission,
        "children": [{"label": c.label, "route": c.route, "icon": c.icon, "permission": c.permission} for c in m.children],
    } for m in menu])


@router.get("/{module}/schema")
async def get_module_schema(module: str):
    """模块 UI Schema"""
    schema = UISchemaGenerator.generate_module_schema(module)
    if schema is None:
        return APIResponse.fail(404, f"模块 {module} 不存在")
    return APIResponse.ok({
        "module_name": schema.module_name,
        "module_display": schema.module_display,
        "version": schema.version,
        "pages": [
            {
                "route": p.route, "title": p.title, "page_type": p.page_type,
                "entity": p.entity, "permission": p.permission,
                "list_config": {
                    "columns": [{"field": c.field, "header": c.header} for c in p.list_config.columns],
                    "filters": [{"field": f.field, "label": f.label} for f in p.list_config.filters],
                } if p.list_config else None,
                "form_config": {
                    "fields": [{"field": f.field, "label": f.label, "field_type": f.field_type} for f in p.form_config.fields],
                } if p.form_config else None,
                "actions": [
                    {"name": a.name, "label": a.label, "capability": a.capability,
                     "http_method": a.http_method, "http_path": a.http_path}
                    for a in p.actions
                ],
                "dashboard_config": {
                    "kpi_cards": [
                        {"label": k.label, "field": k.field, "icon": k.icon,
                         "color": k.color, "source": k.source, "format": k.format}
                        for k in p.dashboard_config.kpi_cards
                    ],
                    "quick_actions": [
                        {"label": q.label, "route": q.route, "icon": q.icon,
                         "permission": q.permission}
                        for q in p.dashboard_config.quick_actions
                    ],
                    "recent_tasks": [
                        {"label": t.label, "field": t.field, "source": t.source}
                        for t in p.dashboard_config.recent_tasks
                    ],
                } if p.dashboard_config else None,
                "detail_config": {
                    "sections": [
                        {"title": s.title, "fields": s.fields}
                        for s in p.detail_config.sections
                    ],
                    "related_lists": [
                        {
                            "title": rl.title, "entity": rl.entity,
                            "api_path": rl.api_path, "foreign_key": rl.foreign_key,
                            "columns": [{"field": c.field, "header": c.header} for c in rl.columns],
                        }
                        for rl in p.detail_config.related_lists
                    ],
                } if p.detail_config else None,
                "events_api": p.events_api or None,
            }
            for p in schema.pages
        ],
    })


@router.get("/state-actions/{entity}/{state}")
async def get_state_actions(entity: str, state: str):
    """状态驱动操作"""
    actions = UISchemaGenerator.generate_state_actions(entity, state)
    return APIResponse.ok([
        {"name": a.name, "label": a.label, "capability": a.capability,
         "http_method": a.http_method, "http_path": a.http_path}
        for a in actions
    ])


# ============================================================
# Sandbox Preview
# ============================================================


@router.get("/preview/menu")
async def get_preview_menu():
    """Sandbox 预览菜单"""
    from app.ai.ui.preview import SandboxPreviewService
    result = await SandboxPreviewService.generate_preview_menu()
    return APIResponse.ok(result)


@router.get("/preview/{sandbox_id}/:module/schema")
async def get_preview_schema(sandbox_id: str):
    """Sandbox 预览 UI Schema"""
    from app.ai.ui.preview import SandboxPreviewService
    schema = await SandboxPreviewService.generate_preview_schema(sandbox_id)
    if schema is None:
        return APIResponse.fail(404, "Sandbox 不存在或未就绪")
    return APIResponse.ok(schema)
