import { useQuery } from "@tanstack/react-query"
import { apiGet } from "./client"

// ============================================================
// 菜单
// ============================================================

export interface MenuItem {
  label: string; icon: string; route?: string; permission?: string
  children?: MenuItem[]
}

// ============================================================
// Dashboard 配置
// ============================================================

export interface KPICard {
  label: string; field: string; icon: string
  color: string; source: string; format: string
}

export interface QuickAction {
  label: string; route: string; icon: string; permission: string
}

export interface RecentTask {
  label: string; field: string; source: string
}

export interface DashboardConfig {
  kpi_cards: KPICard[]
  quick_actions: QuickAction[]
  recent_tasks: RecentTask[]
}

// ============================================================
// 过滤 / 排序
// ============================================================

export interface FilterDef {
  field: string
  label: string
  filter_type?: string   // "text" | "select" | "date_range"
  options?: { label: string; value: string }[]
}

// ============================================================
// 关联列表 / 详情扩展
// ============================================================

export interface RelatedListConfig {
  title: string
  entity: string
  api_path: string         // {id} 替换为父实体 ID
  columns: ColumnDef[]
  foreign_key: string
}

export interface EventLogEntry {
  id: string
  event_id: string
  event_type: string
  aggregate_type: string
  aggregate_id: string
  status: string
  payload: Record<string, unknown> | null
  created_at: string | null
}

// ============================================================
// 页面 Schema
// ============================================================

export interface ColumnDef { field: string; header: string }

export interface ActionDef {
  name: string
  label: string
  capability: string
  http_method?: string
  http_path?: string
  action_type?: string        // "api_call" | "state_transition" | "navigate"
  confirm_dialog?: string
  pre_state?: string
  post_state?: string
}

export interface PageSchema {
  route: string; title: string; page_type: "list" | "form" | "detail" | "dashboard"
  entity: string; permission: string
  list_config?: { columns: ColumnDef[]; filters: FilterDef[] }
  form_config?: { fields: { field: string; label: string; field_type: string }[] }
  detail_config?: {
    sections: { title: string; fields: string[] }[]
    related_lists?: RelatedListConfig[]
  }
  dashboard_config?: DashboardConfig
  actions: ActionDef[]
  events_api?: string
}

export interface UISchema {
  module_name: string; module_display: string; version: string
  pages: PageSchema[]
}

// ============================================================
// Workflow
// ============================================================

export interface WorkflowStateDef {
  code: string
  name: string
  terminal?: boolean
}

// ============================================================
// 分页
// ============================================================

export interface PageResponse<T = Record<string, unknown>> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// ============================================================
// Hooks
// ============================================================

export function useMenu() {
  return useQuery({ queryKey: ["menu"], queryFn: () => apiGet<MenuItem[]>("/ui/menu") })
}

export function useModuleSchema(module: string | null) {
  return useQuery({
    queryKey: ["ui-schema", module],
    queryFn: () => apiGet<UISchema>(`/ui/${module}/schema`),
    enabled: !!module,
  })
}

/** 获取工作台 Dashboard Schema（portal 模块） */
export function useDashboard() {
  return useQuery({
    queryKey: ["ui-schema", "portal"],
    queryFn: () => apiGet<UISchema>("/ui/portal/schema"),
  })
}

/** 获取实体在当前状态下的可用操作 */
export function useStateActions(entity: string | null, state: string | null) {
  return useQuery({
    queryKey: ["state-actions", entity, state],
    queryFn: () => apiGet<ActionDef[]>(`/ui/state-actions/${entity}/${state}`),
    enabled: !!entity && !!state,
    staleTime: 30000,
  })
}

/** 获取实体事件历史时间线 */
export function useEvents(entity: string | null, entityId: string | null) {
  return useQuery({
    queryKey: ["events", entity, entityId],
    queryFn: () => apiGet<EventLogEntry[]>(`/events/${entity}/${entityId}`),
    enabled: !!entity && !!entityId,
    staleTime: 30000,
  })
}
