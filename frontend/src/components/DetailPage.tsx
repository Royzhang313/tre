import { useParams } from "react-router-dom"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost } from "../api/client"
import type { PageSchema } from "../api/ui"
import { useStateActions } from "../api/ui"
import { WorkflowRenderer } from "./WorkflowRenderer"
import { RelatedList } from "./RelatedList"
import { EventTimeline } from "./EventTimeline"
import { sysToast, sysConfirm } from "./shared/Dialog"

/** 嵌套字段访问 */
function getNested(obj: unknown, path: string): unknown {
  return path.split(".").reduce((acc: unknown, key) => {
    if (acc && typeof acc === "object") return (acc as Record<string, unknown>)[key]
    return undefined
  }, obj)
}

export function DetailPage({ page }: { page: PageSchema }) {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const sections = page.detail_config?.sections ?? []
  const relatedLists = page.detail_config?.related_lists ?? []

  // 从路由推导 module
  const module = page.permission.split(".")[0]
  const entityPath = page.entity?.toLowerCase() + "s"

  // 获取详情数据
  const { data, isLoading } = useQuery({
    queryKey: ["detail", page.entity, id],
    queryFn: () => apiGet<Record<string, unknown>>(`/${module}/${entityPath}/${id}`),
    enabled: !!id && !!page.entity,
  })

  // 状态感知操作
  const entityStatus = data ? String(data.status ?? "") : ""
  const { data: stateActions } = useStateActions(id ? page.entity : null, entityStatus)

  const allActions = [...(page.actions ?? []), ...(stateActions ?? [])]

  if (isLoading) return <div className="p-6 text-slate-500">加载中…</div>
  if (!data) return <div className="p-6 text-red-500">数据加载失败</div>

  // 详情数据可能嵌套
  const detailData = (data.order as Record<string, unknown>) ?? data

  const handleAction = async (action: import("../api/ui").ActionDef) => {
    if (action.confirm_dialog && !window.sysConfirm(action.confirm_dialog)) return
    try {
      const path = (action.http_path ?? "").replace("{id}", id ?? "")
      await apiPost(path)
      queryClient.invalidateQueries({ queryKey: ["detail", page.entity] })
      queryClient.invalidateQueries({ queryKey: ["list"] })
      queryClient.invalidateQueries({ queryKey: ["events"] })
    } catch (err) {
      sysToast(err instanceof Error ? err.message : "操作失败")
    }
  }

  return (
    <div className="max-w-4xl space-y-6">
      {/* 标题 + 操作按钮 */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-800">{page.title}</h2>
        <div className="flex gap-2 flex-wrap">
          {allActions
            .filter(a => a.name !== "view" && a.name !== "create")
            .map((a, i) => (
              <button
                key={i}
                onClick={() => handleAction(a)}
                className="px-3 py-1 text-xs rounded border border-slate-300 text-slate-600 hover:bg-slate-100 hover:border-slate-400 transition-colors"
                title={a.capability}
              >
                {a.label}
              </button>
            ))}
        </div>
      </div>

      {/* 1. 状态流程 */}
      {entityStatus && (
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
          <div className="text-xs text-slate-500 mb-2">状态流程</div>
          <WorkflowRenderer entity={page.entity} currentState={entityStatus} />
        </div>
      )}

      {/* 2. 主信息 */}
      {sections.length > 0 && (
        <div className="border border-slate-200 rounded-lg p-5 bg-white">
          {sections.map((s, i) => (
            <div key={i}>
              {s.title && (
                <div className="text-sm font-semibold text-slate-600 mb-3 border-b border-slate-100 pb-2">
                  {s.title}
                </div>
              )}
              <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3">
                {s.fields.map(f => (
                  <div key={f}>
                    <dt className="text-xs text-slate-400 mb-0.5">{f}</dt>
                    <dd className="text-sm text-slate-700 font-medium">
                      {String(getNested(detailData, f) ?? "-")}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      )}

      {/* 3. 关联列表（子表） */}
      {relatedLists.map((rl, i) => (
        <div key={i} className="border border-slate-200 rounded-lg p-5 bg-white">
          <RelatedList config={rl} parentId={id ?? ""} />
        </div>
      ))}

      {/* 4. 事件历史时间线 */}
      {page.entity && id && (
        <div className="border border-slate-200 rounded-lg p-5 bg-white">
          <EventTimeline entity={page.entity} entityId={id} />
        </div>
      )}
    </div>
  )
}
