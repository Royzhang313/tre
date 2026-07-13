/** 合同货权库存看板 */
import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { apiGet } from "../../api/client"

interface ContractStock {
  id: string
  product_id: string
  purchase_contract_id: string
  supplier_id: string
  qty_contracted: number
  qty_in_transit: number
  qty_in_warehouse: number
  qty_allocated: number
  qty_shipped: number
  is_closed: boolean
  // 关联展示
  product_name?: string
  product_code?: string
  contract_no?: string
  supplier_name?: string
}

function statusLabel(cs: ContractStock): { label: string; color: string } {
  if (cs.qty_shipped === cs.qty_contracted && cs.qty_contracted > 0)
    return { label: "完成", color: "bg-slate-100 text-slate-500 border-slate-200" }
  if (cs.qty_shipped > 0)
    return { label: "部分发运", color: "bg-blue-50 text-blue-700 border-blue-200" }
  if (cs.qty_in_warehouse > 0)
    return { label: "在仓", color: "bg-emerald-50 text-emerald-700 border-emerald-200" }
  if (cs.qty_in_transit > 0)
    return { label: "在途", color: "bg-amber-50 text-amber-700 border-amber-200" }
  return { label: "待生效", color: "bg-slate-50 text-slate-400 border-slate-200" }
}

function ProgressBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-10 text-right">{value.toFixed(1)}</span>
    </div>
  )
}

export function ContractStockList() {
  const [page, setPage] = useState(1)
  const pageSize = 20

  const { data, isLoading } = useQuery({
    queryKey: ["contract-stocks", page],
    queryFn: () => apiGet<{ items: ContractStock[]; total: number }>(
      `/inventory/contract-stocks?page=${page}&page_size=${pageSize}`
    ),
  })

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / pageSize)

  // Summary cards
  const totalContracted = items.reduce((s, c) => s + (c.qty_contracted ?? 0), 0)
  const totalInTransit = items.reduce((s, c) => s + (c.qty_in_transit ?? 0), 0)
  const totalInWarehouse = items.reduce((s, c) => s + (c.qty_in_warehouse ?? 0), 0)
  const totalAllocated = items.reduce((s, c) => s + (c.qty_allocated ?? 0), 0)
  const totalAvailable = items.reduce((s, c) => s + ((c.qty_in_warehouse ?? 0) - (c.qty_allocated ?? 0)), 0)

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-800">货权库存</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          合同生效即产生货权。双层库存模型：货权层（ContractStock）+ 实物层（WarehouseStock）
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
          <div className="text-xs text-slate-500 mb-1">合同总量</div>
          <div className="text-lg font-bold text-slate-800">{totalContracted.toFixed(2)} <span className="text-xs font-normal text-slate-400">吨</span></div>
        </div>
        <div className="bg-white rounded-xl border border-amber-200 p-4 shadow-sm bg-amber-50/30">
          <div className="text-xs text-amber-600 mb-1">在途</div>
          <div className="text-lg font-bold text-amber-700">{totalInTransit.toFixed(2)} <span className="text-xs font-normal text-amber-400">吨</span></div>
        </div>
        <div className="bg-white rounded-xl border border-emerald-200 p-4 shadow-sm bg-emerald-50/30">
          <div className="text-xs text-emerald-600 mb-1">在仓</div>
          <div className="text-lg font-bold text-emerald-700">{totalInWarehouse.toFixed(2)} <span className="text-xs font-normal text-emerald-400">吨</span></div>
        </div>
        <div className="bg-white rounded-xl border border-indigo-200 p-4 shadow-sm bg-indigo-50/30">
          <div className="text-xs text-indigo-600 mb-1">已分配</div>
          <div className="text-lg font-bold text-indigo-700">{totalAllocated.toFixed(2)} <span className="text-xs font-normal text-indigo-400">吨</span></div>
        </div>
        <div className="bg-white rounded-xl border border-blue-200 p-4 shadow-sm bg-blue-50/30">
          <div className="text-xs text-blue-600 mb-1">可售</div>
          <div className="text-lg font-bold text-blue-700">{totalAvailable.toFixed(2)} <span className="text-xs font-normal text-blue-400">吨</span></div>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <div className="text-4xl mb-3">📊</div>
          <div>暂无货权库存数据</div>
          <p className="text-xs text-slate-300 mt-1">采购合同确认后将自动产生货权记录</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">产品</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">采购合同</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">供应商</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase">合同量</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase">在途</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase">在仓</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase">已分配</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase">可售</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase">状态</th>
              </tr>
            </thead>
            <tbody>
              {items.map(cs => {
                const st = statusLabel(cs)
                const available = (cs.qty_in_warehouse ?? 0) - (cs.qty_allocated ?? 0)
                return (
                  <tr key={cs.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-slate-800">{cs.product_name || cs.product_id?.slice(0, 8)}</div>
                      <div className="text-xs text-slate-400 font-mono">{cs.product_code}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-indigo-600 font-medium">{cs.contract_no || cs.purchase_contract_id?.slice(0, 8)}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{cs.supplier_name || cs.supplier_id?.slice(0, 8)}</td>
                    <td className="px-4 py-3 text-sm text-right text-slate-700 font-medium">{cs.qty_contracted?.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <ProgressBar value={cs.qty_in_transit ?? 0} max={cs.qty_contracted ?? 0} color="bg-amber-500" />
                    </td>
                    <td className="px-4 py-3">
                      <ProgressBar value={cs.qty_in_warehouse ?? 0} max={cs.qty_contracted ?? 0} color="bg-emerald-500" />
                    </td>
                    <td className="px-4 py-3">
                      <ProgressBar value={cs.qty_allocated ?? 0} max={cs.qty_contracted ?? 0} color="bg-indigo-500" />
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      <span className={`font-semibold ${available > 0 ? "text-blue-600" : "text-slate-300"}`}>
                        {available.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium border ${st.color}`}>
                        {st.label}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
              <div className="text-sm text-slate-500">共 {total} 条</div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1 border border-slate-200 rounded text-sm disabled:opacity-40 hover:bg-slate-50"
                >
                  上一页
                </button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  const start = Math.max(1, Math.min(page - 2, totalPages - 4))
                  const pn = start + i
                  if (pn > totalPages) return null
                  return (
                    <button
                      key={pn}
                      onClick={() => setPage(pn)}
                      className={`w-8 h-8 rounded text-sm ${pn === page ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}
                    >
                      {pn}
                    </button>
                  )
                })}
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1 border border-slate-200 rounded text-sm disabled:opacity-40 hover:bg-slate-50"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 图例说明 */}
      <div className="mt-6 p-4 bg-slate-50 rounded-xl border border-slate-100">
        <h3 className="text-sm font-semibold text-slate-700 mb-2">📖 库存模型说明</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-500">
          <div className="flex items-start gap-2">
            <span className="inline-flex px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 font-mono text-[10px] shrink-0 mt-0.5">在途</span>
            <span>采购合同确认后，货权立即产生但货物尚未入库。qty_in_transit = 合同量</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="inline-flex px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 font-mono text-[10px] shrink-0 mt-0.5">在仓</span>
            <span>收货入库后，在途转为在仓。此时货物可用于销售锁货。qty_in_warehouse</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="inline-flex px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 font-mono text-[10px] shrink-0 mt-0.5">已分配</span>
            <span>销售合同确认后，库存被锁定给特定客户。qty_allocated（从可售中扣除）</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="inline-flex px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-mono text-[10px] shrink-0 mt-0.5">可售</span>
            <span>可售 = 在仓 - 已分配。即当前可对外承诺的货权数量</span>
          </div>
        </div>
      </div>
    </div>
  )
}
