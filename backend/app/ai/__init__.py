"""AI Builder —— Architect Agent (M7)"""

from app.shared.module_registry import ModuleManifest, ModuleRegistry, UIPageMeta

ModuleRegistry.register(ModuleManifest(
    name="ai", display_name="AI Builder", version="M7",
    ui_pages=[
        UIPageMeta(route="/ai/spec", title="Domain Spec", page_type="list", entity="AIDomainSpec",
                   columns=["title", "version", "status", "business_context", "created_at"],
                   filters=["status"], actions=["create", "view", "validate", "approve", "reject"]),
        UIPageMeta(route="/ai/spec/create", title="新建 Domain Spec", page_type="form", entity="AIDomainSpec",
                   columns=["title", "business_context"]),
        UIPageMeta(route="/ai/sandbox", title="Sandbox 管理", page_type="list", entity="SandboxInstance",
                   columns=["module_name", "status", "sandbox_path", "test_summary"],
                   filters=["status"], actions=["create", "install", "test", "promote", "destroy"]),
    ],
    permissions=[],
    events_published=[],
    events_consumed=[],
    dependencies=[],
))

__all__: list[str] = []
