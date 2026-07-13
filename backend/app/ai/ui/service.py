"""UISchemaGenerator —— 从 ModuleManifest + Capability 生成 UI Schema"""

from app.ai.ui.models import (
    ActionSchema,
    ColumnDef,
    DashboardConfig,
    DetailConfig,
    DetailSection,
    FilterDef,
    FormConfig,
    FormField,
    KPICard,
    ListConfig,
    MenuNode,
    PageSchema,
    QuickAction,
    RecentTask,
    RelatedListConfig,
    UISchema,
)
from app.shared.capability_registry import CapabilityRegistry
from app.shared.module_registry import ModuleRegistry

# 模块 → 图标名映射（前端 Icon 组件按名渲染 SVG）
MODULE_ICONS: dict[str, str] = {
    "auth": "Users",
    "basedata": "Database",
    "inventory": "Package",
    "purchase": "ShoppingCart",
    "sales": "Receipt",
    "shipment": "Truck",
    "ai": "Bot",
    "portal": "LayoutDashboard",
}


class UISchemaGenerator:
    """从 Registry 元数据生成 UI Schema"""

    @staticmethod
    def generate_menu() -> list[MenuNode]:
        """生成全系统菜单树（跳过纯 dashboard 模块）"""
        menu = []
        for manifest in ModuleRegistry.list_all():
            if not manifest.ui_pages:
                continue
            # 跳过纯 dashboard 模块（如 portal），不显示在侧边栏
            if all(p.page_type == "dashboard" for p in manifest.ui_pages):
                continue
            children = []
            for page in manifest.ui_pages:
                children.append(MenuNode(
                    label=page.title,
                    route=page.route,
                    icon="FileText",
                    permission=f"{manifest.name}.{page.entity}.read" if page.entity else None,
                ))
            menu.append(MenuNode(
                label=manifest.display_name,
                icon=MODULE_ICONS.get(manifest.name, "Folder"),
                children=children,
            ))
        return menu

    @staticmethod
    def generate_module_schema(module_name: str) -> UISchema | None:
        """生成单个模块的完整 UI Schema"""
        manifest = ModuleRegistry.get(module_name)
        if not manifest:
            return None

        pages = []
        for page_meta in manifest.ui_pages:
            page = PageSchema(
                route=page_meta.route,
                title=page_meta.title,
                page_type=page_meta.page_type,
                entity=page_meta.entity,
                permission=f"{module_name}.{page_meta.entity}.read" if page_meta.entity else "",
            )

            # List page
            if page_meta.page_type == "list":
                page.list_config = ListConfig(
                    columns=[ColumnDef(field=c, header=c) for c in page_meta.columns],
                    filters=[FilterDef(field=f, label=f) for f in page_meta.filters],
                    row_actions=[
                        ActionSchema(name=a, label=a, capability=f"{module_name}.{page_meta.entity}.{a}")
                        for a in page_meta.actions
                    ],
                )

            # Form page
            if page_meta.page_type == "form":
                page.form_config = FormConfig(
                    fields=[FormField(field=f, label=f) for f in page_meta.columns],
                    submit_action=f"{module_name}.{page_meta.entity}.create",
                )

            # Detail page
            if page_meta.page_type == "detail":
                rl_configs: list = []
                if page_meta.related_lists:
                    for rl in page_meta.related_lists:
                        rl_configs.append(RelatedListConfig(
                            title=rl["title"],
                            entity=rl["entity"],
                            api_path=rl["api_path"],
                            columns=[ColumnDef(field=c, header=c) for c in rl.get("columns", [])],
                            foreign_key=rl.get("foreign_key", ""),
                        ))
                page.detail_config = DetailConfig(
                    sections=[DetailSection(title="基本信息", fields=page_meta.columns)],
                    related_lists=rl_configs,
                )
                page.events_api = f"/api/v1/events/{page_meta.entity}/{{id}}"

            # Dashboard page
            if page_meta.page_type == "dashboard":
                dc = page_meta.dashboard_config or {}
                page.dashboard_config = DashboardConfig(
                    kpi_cards=[KPICard(**k) for k in dc.get("kpi_cards", [])],
                    quick_actions=[QuickAction(**q) for q in dc.get("quick_actions", [])],
                    recent_tasks=[RecentTask(**t) for t in dc.get("recent_tasks", [])],
                )

            # Actions (state-driven)
            page.actions = [
                ActionSchema(
                    name=a, label=a,
                    action_type="api_call",
                    http_method="POST",
                    http_path=f"/api/v1/{module_name}/{page_meta.entity}/{{id}}/{a}",
                    capability=f"{module_name}.{page_meta.entity}.{a}",
                )
                for a in page_meta.actions
            ]

            pages.append(page)

        return UISchema(
            module_name=module_name,
            module_display=manifest.display_name,
            version=manifest.version,
            pages=pages,
        )

    @staticmethod
    def generate_state_actions(entity: str, state: str) -> list[ActionSchema]:
        """根据实体+当前状态生成可执行的操作

        优先从 InMemoryWorkflowRegistry 查找状态转换，
        Fallback 从 CapabilityRegistry 查找匹配的能力。
        """
        from app.shared.workflow.in_memory_registry import InMemoryWorkflowRegistry

        actions: list[ActionSchema] = []

        # 1. 从 WorkflowDefinition 查找状态转换
        for wf_def in InMemoryWorkflowRegistry.list_all():
            allowed = InMemoryWorkflowRegistry.get_allowed_transitions(wf_def.name, state)
            if not allowed:
                continue

            # 找到对应的模块名
            module_name = ""
            for manifest in ModuleRegistry.list_all():
                for page_meta in manifest.ui_pages:
                    if page_meta.entity == entity:
                        module_name = manifest.name
                        break
                if module_name:
                    break

            for t in allowed:
                is_dangerous = t.name in ("取消", "关闭", "冲销", "删除")
                # 从 module 的 ui_pages 获取实际路由前缀
                route_prefix = ""
                for page_meta in manifest.ui_pages:
                    if page_meta.entity == entity and page_meta.route:
                        route_prefix = page_meta.route
                        break
                action_name = t.api_action or t.to_state
                actions.append(ActionSchema(
                    name=action_name,
                    label=t.name,
                    action_type="state_transition",
                    http_method="POST",
                    http_path=f"/api/v1{route_prefix}/{{id}}/{action_name}" if route_prefix else "",
                    capability=f"{module_name}.{entity}.{action_name}" if module_name else "",
                    pre_state=t.from_state,
                    post_state=t.to_state,
                    confirm_dialog=f"确认执行「{t.name}」操作？" if is_dangerous else None,
                ))
            # 找到了 workflow 就不再 fallback
            if actions:
                return actions

        # 2. Fallback: 从 CapabilityRegistry 推断
        for cap in CapabilityRegistry.list_all():
            if entity.lower() in cap.name and cap.http_path:
                actions.append(ActionSchema(
                    name=cap.name.split(".")[-1],
                    label=cap.display_name,
                    action_type="api_call",
                    http_method=cap.http_method,
                    http_path=cap.http_path,
                    capability=cap.name,
                ))

        return actions
