import { Link, useLocation } from "react-router-dom"
import { useMenu, type MenuItem } from "../api/ui"
import { useQuery } from "@tanstack/react-query"
import { apiGet } from "../api/client"
import { usePortal } from "../contexts/PortalContext"
import { Icon } from "./ui/Icon"

// ============================================================
// 单个菜单节点
// ============================================================

function MenuNode({ item, collapsed }: { item: MenuItem; collapsed: boolean }) {
  const loc = useLocation()
  const { collapsedGroups, toggleGroup, openTab } = usePortal()
  const hasChildren = item.children && item.children.length > 0

  if (hasChildren) {
    const isExpanded = !collapsedGroups.has(item.label)

    return (
      <div className="mb-1">
        <button
          onClick={() => toggleGroup(item.label)}
          className={`
            w-full flex items-center gap-2 px-3 py-1.5 text-xs font-semibold
            text-slate-500 uppercase tracking-wider hover:bg-slate-100 rounded-md transition-colors
            ${collapsed ? "justify-center px-2" : ""}
          `}
          title={collapsed ? item.label : undefined}
        >
          <Icon name={item.icon} size={14} className="shrink-0" />
          {!collapsed && (
            <>
              <span className="flex-1 text-left truncate">{item.label}</span>
              <Icon
                name={isExpanded ? "ChevronDown" : "ChevronRight"}
                size={12}
                className="shrink-0"
              />
            </>
          )}
        </button>

        {isExpanded && (
          <div className={collapsed ? "mt-1 space-y-0.5" : "mt-1 ml-1 space-y-0.5"}>
            {item.children!.map((child, i) => (
              <Link
                key={i}
                to={child.route ?? "#"}
                onClick={() => child.route && openTab(child.route, child.label)}
                className={`
                  flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors
                  ${loc.pathname === child.route
                    ? "bg-blue-100 text-blue-700 font-medium"
                    : "text-slate-700 hover:bg-slate-100"
                  }
                  ${collapsed ? "justify-center px-2" : ""}
                `}
                title={collapsed ? child.label : undefined}
              >
                <Icon name={child.icon} size={14} className="shrink-0" />
                {!collapsed && <span className="truncate">{child.label}</span>}
              </Link>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <Link
      to={item.route ?? "#"}
      className={`
        flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors
        ${loc.pathname === item.route
          ? "bg-blue-100 text-blue-700 font-medium"
          : "text-slate-700 hover:bg-slate-100"
        }
        ${collapsed ? "justify-center px-2" : ""}
      `}
      title={collapsed ? item.label : undefined}
    >
      <Icon name={item.icon} size={14} className="shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
    </Link>
  )
}

// ============================================================
// 侧边栏
// ============================================================

interface PreviewMenuItem {
  label: string
  route: string
  status: string
}

export function Sidebar() {
  const { data: menu } = useMenu()
  const { sidebarCollapsed } = usePortal()

  const { data: previewMenu } = useQuery({
    queryKey: ["preview-menu"],
    queryFn: () => apiGet<PreviewMenuItem[]>("/ui/preview/menu"),
    refetchInterval: 10000,
  })

  return (
    <aside
      className={`
        border-r border-slate-200 bg-slate-50 h-screen overflow-y-auto shrink-0
        transition-all duration-200 ease-in-out
        ${sidebarCollapsed ? "w-16 px-1.5" : "w-56 px-3"}
      `}
    >
      {/* Logo / 标题 */}
      <div className={`
        flex items-center gap-2 py-4 mb-2
        ${sidebarCollapsed ? "justify-center" : "px-1"}
      `}>
        <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0">
          <Icon name="LayoutDashboard" size={15} />
        </div>
        {!sidebarCollapsed && (
          <span className="text-base font-bold text-slate-800 tracking-tight">ERP Builder</span>
        )}
      </div>

      {/* 主菜单 */}
      <nav className="space-y-0.5">
        {/* 首页快捷入口 */}
        <Link
          to="/"
          className={`
            flex items-center gap-2 px-3 py-1.5 rounded-md text-sm text-slate-700 hover:bg-slate-100 transition-colors
            ${sidebarCollapsed ? "justify-center px-2" : ""}
          `}
          title="工作台"
        >
          <Icon name="Home" size={16} />
          {!sidebarCollapsed && <span className="truncate">工作台</span>}
        </Link>

        {/* 采购 */}
        <Link
          to="/purchase-contracts"
          className={`
            flex items-center gap-2 px-3 py-1.5 rounded-md text-sm text-slate-700 hover:bg-slate-100 transition-colors
            ${sidebarCollapsed ? "justify-center px-2" : ""}
          `}
          title="采购"
        >
          <Icon name="FileText" size={16} />
          {!sidebarCollapsed && <span className="truncate">采购</span>}
        </Link>

        {/* 销售 */}
        <Link
          to="/sales-contracts"
          className={`
            flex items-center gap-2 px-3 py-1.5 rounded-md text-sm text-slate-700 hover:bg-slate-100 transition-colors
            ${sidebarCollapsed ? "justify-center px-2" : ""}
          `}
          title="销售"
        >
          <Icon name="ShoppingCart" size={16} />
          {!sidebarCollapsed && <span className="truncate">销售</span>}
        </Link>

        {/* 产品 */}
        <Link
          to="/products"
          className={`
            flex items-center gap-2 px-3 py-1.5 rounded-md text-sm text-slate-700 hover:bg-slate-100 transition-colors
            ${sidebarCollapsed ? "justify-center px-2" : ""}
          `}
          title="产品"
        >
          <Icon name="Package" size={16} />
          {!sidebarCollapsed && <span className="truncate">产品</span>}
        </Link>

        {/* 货权库存 */}
        <Link
          to="/inventory"
          className={`
            flex items-center gap-2 px-3 py-1.5 rounded-md text-sm text-slate-700 hover:bg-slate-100 transition-colors
            ${sidebarCollapsed ? "justify-center px-2" : ""}
          `}
          title="库存"
        >
          <Icon name="BarChart3" size={16} />
          {!sidebarCollapsed && <span className="truncate">库存</span>}
        </Link>

        {/* 回收站 */}
        <Link
          to="/recycle-bin"
          className={`
            flex items-center gap-2 px-3 py-1.5 rounded-md text-sm text-slate-700 hover:bg-slate-100 transition-colors
            ${sidebarCollapsed ? "justify-center px-2" : ""}
          `}
          title="回收站"
        >
          <Icon name="Trash2" size={16} />
          {!sidebarCollapsed && <span className="truncate">回收站</span>}
        </Link>

        {menu?.map((item, i) => (
          <MenuNode key={i} item={item} collapsed={sidebarCollapsed} />
        ))}
      </nav>

      {/* Sandbox 预览 */}
      {previewMenu && previewMenu.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-200">
          <div className={`
            flex items-center gap-2 px-3 py-1 text-xs font-semibold text-amber-600 uppercase tracking-wider
            ${sidebarCollapsed ? "justify-center" : ""}
          `}>
            <Icon name="Bot" size={12} />
            {!sidebarCollapsed && "Sandbox"}
          </div>
          <div className="mt-1 space-y-0.5">
            {previewMenu.map((p, i) => (
              <Link
                key={i}
                to={p.route}
                className={`
                  flex items-center gap-2 px-3 py-1.5 rounded-md text-sm text-amber-700 hover:bg-amber-50 transition-colors
                  ${sidebarCollapsed ? "justify-center px-2" : ""}
                `}
                title={sidebarCollapsed ? p.label : undefined}
              >
                <Icon name="FileText" size={14} className="shrink-0" />
                {!sidebarCollapsed && (
                  <>
                    <span className="flex-1 truncate">{p.label}</span>
                    <span className={`text-xs px-1.5 rounded-full shrink-0 ${p.status === "passed" ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                      {p.status}
                    </span>
                  </>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}
    </aside>
  )
}
