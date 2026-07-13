import { useEvents, type EventLogEntry } from "../api/ui"

interface EventTimelineProps {
  entity: string
  entityId: string
}

/** 事件类型 → 颜色映射 */
const EVENT_COLORS: Record<string, string> = {
  confirmed: "bg-green-100 text-green-700 border-green-300",
  created:   "bg-blue-100 text-blue-700 border-blue-300",
  cancelled: "bg-red-100 text-red-700 border-red-300",
  reversed:  "bg-orange-100 text-orange-700 border-orange-300",
  closed:    "bg-slate-100 text-slate-600 border-slate-300",
  shipped:   "bg-purple-100 text-purple-700 border-purple-300",
  delivered: "bg-teal-100 text-teal-700 border-teal-300",
}

function eventColor(eventType: string): string {
  for (const [key, color] of Object.entries(EVENT_COLORS)) {
    if (eventType.includes(key)) return color
  }
  return "bg-slate-50 text-slate-500 border-slate-200"
}

function formatTime(dt: string | null): string {
  if (!dt) return ""
  // 截取可读时间部分
  return dt.replace("T", " ").substring(0, 19)
}

export function EventTimeline({ entity, entityId }: EventTimelineProps) {
  const { data: events, isLoading } = useEvents(entity, entityId)

  if (isLoading) return <div className="py-4 text-sm text-slate-400">加载事件历史…</div>
  if (!events || events.length === 0) {
    return <div className="py-4 text-sm text-slate-400 text-center">暂无事件记录</div>
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-600 mb-3">事件历史</h3>
      <div className="relative pl-6 border-l-2 border-slate-200 space-y-3">
        {events.map((e, i) => (
          <div key={e.id} className="relative">
            {/* 时间轴圆点 */}
            <div className={`
              absolute -left-[25px] w-3 h-3 rounded-full border-2 bg-white
              ${e.status === "completed" ? "border-green-400 bg-green-50" :
                e.status === "failed" ? "border-red-400 bg-red-50" :
                "border-blue-400 bg-blue-50"}
            `} />

            {/* 事件内容 */}
            <div className="text-xs">
              <span className={`inline-block px-1.5 py-0.5 rounded border text-xs font-medium ${eventColor(e.event_type)}`}>
                {e.event_type}
              </span>
              <span className="ml-2 text-slate-400">{formatTime(e.created_at)}</span>
              {e.status === "failed" && (
                <span className="ml-1 text-red-500">⚠ 失败</span>
              )}
            </div>
            {/* Payload 摘要 */}
            {e.payload && Object.keys(e.payload).length > 0 && (
              <div className="mt-0.5 text-xs text-slate-500 bg-slate-50 rounded px-2 py-1 font-mono">
                {Object.entries(e.payload).slice(0, 4).map(([k, v]) => (
                  <span key={k} className="mr-3">{k}: {String(v).substring(0, 40)}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
