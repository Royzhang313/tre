import { useQuery } from "@tanstack/react-query"
import { apiGet } from "../api/client"
import type { RelatedListConfig } from "../api/ui"

interface RelatedListProps {
  config: RelatedListConfig
  parentId: string
}

export function RelatedList({ config, parentId }: RelatedListProps) {
  const apiPath = config.api_path.replace("{id}", parentId)

  const { data, isLoading } = useQuery({
    queryKey: ["related", config.entity, parentId],
    queryFn: () => apiGet<Record<string, unknown>>(apiPath.replace("/api/v1", "")),
    enabled: !!parentId,
  })

  // 数据可能在嵌套结构中
  const items = extractItems(data, config)

  if (isLoading) return <div className="py-4 text-sm text-slate-400">加载中…</div>

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-600 mb-2">{config.title}</h3>
      <div className="overflow-x-auto border border-slate-200 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              {config.columns.map(c => (
                <th key={c.field} className="text-left px-3 py-1.5 font-medium text-slate-500 text-xs">
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={config.columns.length} className="px-3 py-6 text-center text-slate-400 text-xs">
                  暂无数据
                </td>
              </tr>
            ) : items.map((item, i) => (
              <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                {config.columns.map(c => (
                  <td key={c.field} className="px-3 py-1.5 text-xs text-slate-600">
                    {String(item[c.field] ?? "-")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/** 从 API 响应中提取 items 数组 */
function extractItems(data: unknown, config: RelatedListConfig): Record<string, unknown>[] {
  if (!data || typeof data !== "object") return []
  const d = data as Record<string, unknown>

  // 尝试常见嵌套路径
  const candidates = [
    d.items,                           // PageResponse format
    d[config.entity.toLowerCase()],    // e.g. { purchaseLine: [...] }
    d[config.entity.toLowerCase() + "s"], // e.g. { goodsReceipts: [...] }
    d.lines,                           // e.g. { order: {...}, lines: [...] }
    d.receipts,                        // e.g. { order: {...}, receipts: [...] }
    d,                                 // 本身就是数组
  ]

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) return candidate as Record<string, unknown>[]
  }

  return []
}
