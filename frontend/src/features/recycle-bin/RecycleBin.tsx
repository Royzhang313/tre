/** 回收站 —— 聚合显示所有已删除数据 */
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPatch, apiDelete } from "../../api/client"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

interface BinItem {
  entity_type: string
  entity_label: string
  entity_id: string
  display_name: string
  deleted_at: string
}

const TYPE_COLORS: Record<string, string> = {
  enterprise: "bg-indigo-50 text-indigo-700 border-indigo-200",
  company: "bg-blue-50 text-blue-700 border-blue-200",
  purchase_contract: "bg-amber-50 text-amber-700 border-amber-200",
  sales_contract: "bg-emerald-50 text-emerald-700 border-emerald-200",
}

export function RecycleBin() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ["recycle-bin", page],
    queryFn: () => apiGet<{ items: BinItem[]; total: number; pages: number }>(`/recycle-bin?page=${page}&page_size=50`),
  })

  const restoreMut = useMutation({
    mutationFn: ({ entity_type, entity_id }: { entity_type: string; entity_id: string }) =>
      apiPatch(`/recycle-bin/${entity_type}/${entity_id}/restore`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recycle-bin"] }),
  })

  const permDeleteMut = useMutation({
    mutationFn: ({ entity_type, entity_id }: { entity_type: string; entity_id: string }) =>
      apiDelete(`/recycle-bin/${entity_type}/${entity_id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recycle-bin"] }),
  })

  const items = data?.items ?? []

  return (
    <div className="page-enter p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">回收站</h1>
          <p className="text-sm text-slate-500 mt-1">已删除的数据汇总</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="py-20 text-center text-slate-300">加载中...</div>
        ) : items.length === 0 ? (
          <div className="py-20 text-center text-slate-300">回收站为空</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                {["数据类型", "名称/编号", "删除时间", "操作"].map(h => (
                  <th key={h} className="px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={`${item.entity_type}-${item.entity_id}`} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                  <td className="px-5 py-3.5">
                    <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium border ${TYPE_COLORS[item.entity_type] ?? "bg-slate-50 text-slate-600 border-slate-200"}`}>
                      {item.entity_label}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 font-medium text-slate-800">{item.display_name}</td>
                  <td className="px-5 py-3.5 text-slate-500 text-xs">{item.deleted_at?.slice(0, 10)}</td>
                  <td className="px-5 py-3.5">
                    <div className="flex gap-2">
                      <button
                        onClick={() => restoreMut.mutate({ entity_type: item.entity_type, entity_id: item.entity_id })}
                        className="px-3 py-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-colors"
                      >
                        恢复
                      </button>
                      <button
                        onClick={async () => { if (sysConfirm("确定永久删除？此操作不可撤销。")) permDeleteMut.mutate({ entity_type: item.entity_type, entity_id: item.entity_id }) }}
                        className="px-3 py-1.5 text-xs font-medium text-rose-500 bg-rose-50 hover:bg-rose-100 rounded-lg transition-colors"
                      >
                        永久删除
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50/50">
            <span className="text-xs text-slate-500">共 {data.total} 条</span>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="px-2.5 py-1.5 text-xs text-slate-600 hover:bg-white rounded disabled:opacity-30">←</button>
              {Array.from({ length: Math.min(data.pages, 5) }, (_, i) => i + 1).map(p => (
                <button key={p} onClick={() => setPage(p)} className={`w-7 h-7 rounded text-xs font-medium ${p === page ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-white"}`}>{p}</button>
              ))}
              <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={page >= data.pages} className="px-2.5 py-1.5 text-xs text-slate-600 hover:bg-white rounded disabled:opacity-30">→</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
