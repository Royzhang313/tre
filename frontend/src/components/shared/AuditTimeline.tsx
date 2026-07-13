/** 操作记录时间线 —— 可嵌入任意详情页 */
import { useQuery } from "@tanstack/react-query"
import { apiGet } from "../../api/client"

interface AuditEntry {
  id: string
  action: string
  entity_type: string
  entity_id: string
  user_name: string
  before_json: any
  after_json: any
  remark: string | null
  created_at: string
}

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  create: { label: "创建", color: "bg-emerald-100 text-emerald-700" },
  update: { label: "编辑", color: "bg-blue-100 text-blue-700" },
  delete: { label: "删除", color: "bg-rose-100 text-rose-700" },
  cancel: { label: "作废", color: "bg-rose-100 text-rose-700" },
  confirm: { label: "确认", color: "bg-indigo-100 text-indigo-700" },
  void: { label: "作废", color: "bg-rose-100 text-rose-700" },
  allocate: { label: "分配", color: "bg-amber-100 text-amber-700" },
  ship: { label: "发货", color: "bg-sky-100 text-sky-700" },
}

function fieldDiff(before: any, after: any): string[] {
  if (!before || !after) return []
  const changes: string[] = []
  for (const key of Object.keys(after)) {
    const bv = before[key]
    const av = after[key]
    if (JSON.stringify(bv) !== JSON.stringify(av)) {
      changes.push(`${key}`)
    }
  }
  return changes.slice(0, 5) // 最多展示5个变更字段
}

export function AuditTimeline({ entityType, entityId }: { entityType: string; entityId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["audit", entityType, entityId],
    queryFn: () => apiGet<{ items: AuditEntry[] }>(`/audit-logs?entity_type=${entityType}&entity_id=${entityId}&page_size=30`),
    enabled: !!entityId,
  })

  const logs = data?.items ?? []

  return (
    <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-5 mt-6">
      <h3 className="text-sm font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">
        操作记录 <span className="text-xs text-slate-400 font-normal">{logs.length} 条</span>
      </h3>
      {isLoading ? (
        <p className="text-sm text-slate-300 py-4">加载中...</p>
      ) : logs.length === 0 ? (
        <p className="text-sm text-slate-300 py-4">暂无操作记录</p>
      ) : (
        <div className="space-y-3">
          {logs.map(log => {
            const act = ACTION_LABELS[log.action] ?? { label: log.action, color: "bg-slate-100 text-slate-600" }
            const changes = log.action === "update" ? fieldDiff(log.before_json, log.after_json) : []
            return (
              <div key={log.id} className="flex items-start gap-3 text-sm">
                <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${act.color}`}>{act.label}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 text-xs">{log.user_name}</span>
                    <span className="text-slate-300 text-xs">·</span>
                    <span className="text-slate-400 text-xs">{log.created_at?.slice(0, 19).replace("T", " ")}</span>
                  </div>
                  {changes.length > 0 && (
                    <p className="text-xs text-slate-400 mt-0.5">变更字段：{changes.join("、")}</p>
                  )}
                  {log.remark && <p className="text-xs text-slate-400 mt-0.5">{log.remark}</p>}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
