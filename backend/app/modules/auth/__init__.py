"""Auth 模块 —— 身份认证和访问控制（RBAC）"""

from app.modules import register
from app.modules.auth.router import router
from app.shared.module_registry import ModuleManifest, ModuleRegistry, UIPageMeta

register("auth", router)

ModuleRegistry.register(ModuleManifest(
    name="auth", display_name="系统管理", version="V1",
    ui_pages=[
        UIPageMeta(route="/auth/users", title="用户管理", page_type="list", entity="User",
                   columns=["username", "email", "display_name", "status", "last_login_at"],
                   filters=["status"], actions=["create", "view", "edit", "delete"]),
        UIPageMeta(route="/auth/roles", title="角色管理", page_type="list", entity="Role",
                   columns=["code", "name", "description", "is_system"],
                   actions=["create", "view", "delete"]),
        UIPageMeta(route="/auth/permissions", title="权限管理", page_type="list", entity="Permission",
                   columns=["code", "name", "module", "resource", "action"],
                   actions=["view"]),
    ],
    permissions=["auth.user.create", "auth.user.read", "auth.user.update", "auth.user.delete", "auth.role.manage"],
    events_published=[],
    events_consumed=[],
    dependencies=[],
))

__all__: list[str] = []
