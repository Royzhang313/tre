import { useQuery } from "@tanstack/react-query"
import { apiGet } from "../api/client"
import type { WorkflowStateDef, ActionDef } from "../api/ui"

// ============================================================
// Props
// ============================================================

interface WorkflowRendererProps {
  /** 实体名，如 "PurchaseOrder" */
  entity: string
  /** 当前状态 code，如 "draft" */
  currentState: string
  /** 紧凑模式（用于列表列内联） */
  compact?: boolean
  /** 自定义状态列表（metadata driven），不传则用内置 fallback */
  states?: WorkflowStateDef[]
}

// ============================================================
// 内置状态 fallback（按 entity 名称分发）
// ============================================================

const FALLBACK_STATES: Record<string, WorkflowStateDef[]> = {
  PurchaseOrder: [
    { code: "draft", name: "草稿" },
    { code: "effective", name: "已生效" },
    { code: "closed", name: "已关闭", terminal: true },
  ],
  default: [
    { code: "draft", name: "草稿" },
    { code: "confirmed", name: "已确认" },
    { code: "completed", name: "已完成", terminal: true },
  ],
}

// ============================================================
// 组件
// ============================================================

export function WorkflowRenderer({ entity, currentState, compact = false, states }: WorkflowRendererProps) {
  const { data: actions } = useQuery({
    queryKey: ["state-actions", entity, currentState],
    queryFn: () => apiGet<ActionDef[]>(`/ui/state-actions/${entity}/${currentState}`),
    enabled: !!entity && !!currentState,
    staleTime: 30000,
  })

  const resolved = states ?? FALLBACK_STATES[entity] ?? FALLBACK_STATES.default
  const currentIdx = resolved.findIndex(s => s.code === currentState)

  return (
    <div className="flex items-center gap-1 flex-wrap">
      {resolved.map((state, idx) => {
        const isCompleted = currentIdx >= 0 && idx < currentIdx
        const isCurrent = idx === currentIdx
        const isFuture = currentIdx >= 0 && idx > currentIdx
        const isUnknown = currentIdx < 0

        return (
          <div key={state.code} className="flex items-center">
            {/* 步骤圆 */}
            <div className={`
              w-5 h-5 rounded-full flex items-center justify-center text-xs font-medium
              transition-colors
              ${isCompleted ? "bg-green-500 text-white" : ""}
              ${isCurrent ? "bg-blue-600 text-white ring-2 ring-blue-300" : ""}
              ${isFuture ? "bg-slate-200 text-slate-400" : ""}
              ${isUnknown ? "bg-slate-100 text-slate-400" : ""}
            `}>
              {isCompleted ? "✓" : idx + 1}
            </div>

            {/* 标签 */}
            {!compact && (
              <span className={`
                ml-1 text-xs
                ${isCurrent ? "text-blue-700 font-medium" : "text-slate-500"}
                ${isFuture ? "text-slate-300" : ""}
              `}>
                {state.name}
              </span>
            )}

            {/* 连接线 */}
            {idx < resolved.length - 1 && (
              <div className={`
                w-4 h-0.5 mx-1
                ${isCompleted || (currentIdx >= 0 && idx < currentIdx && idx + 1 <= currentIdx)
                  ? "bg-green-400"
                  : "bg-slate-200"
                }
              `} />
            )}
          </div>
        )
      })}

      {/* 可用操作提示 */}
      {actions && actions.length > 0 && !compact && (
        <div className="w-full mt-2 flex gap-1 flex-wrap">
          <span className="text-xs text-slate-400">可用操作：</span>
          {actions.map((a, i) => (
            <span key={i} className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded">
              {a.label}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
