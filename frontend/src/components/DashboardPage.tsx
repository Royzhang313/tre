/** 首页 —— 库存统计概览 */
import { useQuery } from "@tanstack/react-query"
import { apiGet } from "../api/client"
import { fmtQty } from "../lib/utils"

interface InventoryItem {
  brand_id: string
  brand_name: string
  brand_color: string
  purchased_qty: number
  sold_qty: number
  shipped_qty: number
  stock_after_sale: number
  stock_after_ship: number
}

interface InventoryStats {
  items: InventoryItem[]
  total_purchased: number
  total_sold: number
  total_shipped: number
  total_stock_after_sale: number
  total_stock_after_ship: number
}

export function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["inventory-stats"],
    queryFn: async () => {
      const r = await apiGet<InventoryStats>("/inventory/stats")
      return r
    },
    staleTime: 30000,
  })

  if (isLoading) return <div className="p-8 text-slate-400 text-sm">加载中...</div>

  const stats = data
  if (!stats || stats.items.length === 0) return <div className="p-8 text-slate-400 text-sm">暂无库存数据</div>

  return (
    <div className="p-4 sm:p-6 max-w-5xl mx-auto">
      {/* 总计卡片 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <StatCard label="采购总量" value={fmtQty(stats.total_purchased)} unit="吨" />
        <StatCard label="销售合同" value={fmtQty(stats.total_sold)} unit="吨" />
        <StatCard label="已发货" value={fmtQty(stats.total_shipped)} unit="吨" />
        <StatCard label="当前库存" value={fmtQty(stats.total_stock_after_ship)} unit="吨"
          highlight={stats.total_stock_after_ship > 0} />
      </div>

      {/* 品牌明细 */}
      <div className="text-xs text-slate-400 mb-2 ml-1">
        销售后库存 = 采购量 − 销售合同量 &nbsp;|&nbsp; 发货后库存 = 采购量 − 已发货量
      </div>
      <div className="bg-white rounded-xl border border-slate-200/60 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              <th className="text-left px-4 py-2.5 text-xs font-semibold text-slate-400 w-6"></th>
              <th className="text-left px-2 py-2.5 text-xs font-semibold text-slate-400">品牌</th>
              <th className="text-right px-2 py-2.5 text-xs font-semibold text-slate-400">采购量</th>
              <th className="text-right px-2 py-2.5 text-xs font-semibold text-slate-400">销售后库存</th>
              <th className="text-right px-2 py-2.5 text-xs font-semibold text-slate-400">发货后库存</th>
            </tr>
          </thead>
          <tbody>
            {stats.items.map((item, idx) => (
              <tr key={item.brand_id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                <td className="px-4 py-2.5">
                  <span className="inline-block w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: item.brand_color || "#94a3b8" }} />
                </td>
                <td className="px-2 py-2.5 font-medium text-slate-700">{item.brand_name}</td>
                <td className="px-2 py-2.5 text-right tabular-nums text-slate-600">{fmtQty(item.purchased_qty)}</td>
                <td className={`px-2 py-2.5 text-right tabular-nums font-medium ${item.stock_after_sale > 0 ? "text-slate-800" : "text-slate-400"}`}>{fmtQty(item.stock_after_sale)}</td>
                <td className={`px-2 py-2.5 text-right tabular-nums font-semibold ${item.stock_after_ship > 0 ? "text-indigo-700" : "text-slate-400"}`}>{fmtQty(item.stock_after_ship)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StatCard({ label, value, unit, highlight }: { label: string; value: string; unit: string; highlight?: boolean }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg px-4 py-3">
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`text-xl font-bold tabular-nums ${highlight ? "text-indigo-600" : "text-slate-800"}`}>
        {value}
        <span className="text-sm font-normal text-slate-400 ml-1">{unit}</span>
      </div>
    </div>
  )
}
