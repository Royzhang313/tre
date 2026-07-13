/** Portal 全局状态 —— 标签页 / 侧边栏 / 菜单组 */

import { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from "react"
import { useLocation, useNavigate } from "react-router-dom"

// ============================================================
// Types
// ============================================================

interface Tab {
  path: string
  title: string
}

interface PortalState {
  /** 已打开的标签页列表 */
  openTabs: Tab[]
  /** 当前活跃标签路径（来自 URL） */
  activeTabPath: string

  openTab: (path: string, title: string) => void
  closeTab: (path: string) => void

  /** 侧边栏折叠的菜单组 */
  collapsedGroups: Set<string>
  toggleGroup: (label: string) => void
  /** 侧边栏是否收起 */
  sidebarCollapsed: boolean
  toggleSidebar: () => void
}

// ============================================================
// Context
// ============================================================

const PortalContext = createContext<PortalState | null>(null)

// ============================================================
// Provider
// ============================================================

export function PortalProvider({ children }: { children: ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()

  const [tabs, setTabs] = useState<Tab[]>(() => [{ path: "/", title: "工作台" }])
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  const activeTabPath = location.pathname

  const openTab = useCallback((path: string, title: string) => {
    setTabs(prev => {
      if (prev.some(t => t.path === path)) return prev
      return [...prev, { path, title }]
    })
    navigate(path)
  }, [navigate])

  const closeTab = useCallback((path: string) => {
    setTabs(prev => {
      const next = prev.filter(t => t.path !== path)
      if (next.length === 0) {
        navigate("/")
        return [{ path: "/", title: "工作台" }]
      }
      if (location.pathname === path) {
        const idx = prev.findIndex(t => t.path === path)
        const target = next[Math.min(idx, next.length - 1)]
        navigate(target.path)
      }
      return next
    })
  }, [navigate, location.pathname])

  const toggleGroup = useCallback((label: string) => {
    setCollapsedGroups(prev => {
      const next = new Set(prev)
      if (next.has(label)) next.delete(label)
      else next.add(label)
      return next
    })
  }, [])

  const toggleSidebar = useCallback(() => setSidebarCollapsed(p => !p), [])

  const value: PortalState = useMemo(() => ({
    openTabs: tabs,
    activeTabPath,
    openTab,
    closeTab,
    collapsedGroups,
    toggleGroup,
    sidebarCollapsed,
    toggleSidebar,
  }), [tabs, activeTabPath, openTab, closeTab, collapsedGroups, toggleGroup, sidebarCollapsed, toggleSidebar])

  return (
    <PortalContext.Provider value={value}>
      {children}
    </PortalContext.Provider>
  )
}

// ============================================================
// Hook
// ============================================================

export function usePortal(): PortalState {
  const ctx = useContext(PortalContext)
  if (!ctx) throw new Error("usePortal() must be used within <PortalProvider>")
  return ctx
}
