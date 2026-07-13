/** 首页 —— 库存看板：可发货库存 + 可销售库存 */
import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { apiGet } from "../../api/client"
import { fmtQty, fmtMoney } from "../../lib/utils"

/** Tailwind 颜色名 → HEX 映射，用于 inline style */
const COLOR_MAP: Record<string, string> = {
  amber: "#f59e0b", sky: "#0ea5e9", blue: "#3b82f6", indigo: "#6366f1",
  violet: "#8b5cf6", orange: "#f97316", emerald: "#10b981", rose: "#f43f5e",
  red: "#ef4444", green: "#22c55e", yellow: "#eab308", purple: "#a855f7",
  pink: "#ec4899", teal: "#14b8a6", cyan: "#06b6d4", lime: "#84cc16",
  slate: "#64748b", gray: "#6b7280", zinc: "#71717a", neutral: "#737373",
  stone: "#78716c",
}
const toColor = (c: string | undefined | null, fallback: string): string =>
  c ? (COLOR_MAP[c] || c) : fallback

interface Stats { purchase: { count: number; amount: number; quantity: number }; sales: { count: number; amount: number; quantity: number }; shipping_plan: { count: number; active: number; quantity: number }; shipment: { count: number }; enterprise_count: number; brand_count: number; company_count: number; ar_amount: number; ap_amount: number }

interface InventoryItem {
  brand_id: string; brand_name: string; brand_color: string
  purchased_qty: number; sold_qty: number; shipped_qty: number
  shipped_this_month: number; shipped_last_month: number
  shipped_this_quarter: number; shipped_this_year: number
  stock_after_sale: number; stock_after_ship: number
}
interface InventoryStats { items: InventoryItem[]; total_purchased: number; total_sold: number; total_shipped: number; total_stock_after_sale: number; total_stock_after_ship: number }
interface WarehouseItem {
  brand_id: string; brand_name: string; brand_color: string
  warehouse_id: string; warehouse_name: string
  purchased_qty: number; sold_qty: number; shipped_qty: number
  shipped_this_month: number; shipped_last_month: number
  shipped_this_quarter: number; shipped_this_year: number
  stock_after_sale: number; stock_after_ship: number
}
interface WarehouseStats { items: WarehouseItem[] }

/** 颜色条 —— 总长 100%，已用/剩余分段 */
function ProgressBar({ used, total, usedColor, remainColor }: { used: number; total: number; usedColor: string; remainColor: string }) {
  const pct = total > 0 ? Math.min(100, Math.max(0, (used / total) * 100)) : 0
  return (
    <div className="w-4/5 mx-auto h-2 bg-slate-100 rounded-full overflow-hidden flex">
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: usedColor }} />
      <div className="h-full flex-1 transition-all duration-500" style={{ backgroundColor: remainColor, opacity: pct < 100 ? 0.2 : 0 }} />
    </div>
  )
}

export function Dashboard() {
  const { data: stats, isLoading: sLoading } = useQuery({
    queryKey: ["dashboard-stats"], queryFn: () => apiGet<Stats>("/dashboard/stats"),
  })
  const { data: inv, isLoading: iLoading } = useQuery({
    queryKey: ["inventory-stats"], queryFn: () => apiGet<InventoryStats>("/inventory/stats"), staleTime: 30000,
  })
  const { data: whStats } = useQuery({
    queryKey: ["warehouse-stats"], queryFn: () => apiGet<WarehouseStats>("/inventory/warehouse-stats"), staleTime: 30000,
  })

  /** 品牌排序由后端按 sort_order 返回，前端直接使用 */
  const sortedItems = inv?.items ?? []

  /** 仓库数据按品牌分组 */
  const whGrouped = useMemo(() => {
    if (!whStats?.items) return {}
    const g: Record<string, WarehouseItem[]> = {}
    for (const it of whStats.items) {
      if (!g[it.brand_id]) g[it.brand_id] = []
      g[it.brand_id].push(it)
    }
    return g
  }, [whStats])

  const saleableTotal = inv?.total_stock_after_sale ?? 0
  const shippableTotal = inv?.total_stock_after_ship ?? 0
  const purchasedTotal = inv?.total_purchased ?? 0

  if (sLoading && iLoading) return <div className="p-8 text-slate-400 text-sm">加载中...</div>
  const s = stats!

  return (
    <div className="page-enter p-4 sm:p-6 max-w-7xl mx-auto">
      {/* 标题行 */}
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-bold text-slate-900">PET 瓶片贸易</h1>
        <span className="text-xs text-slate-400">{s.brand_count} 品牌 · {s.enterprise_count} 企业</span>
      </div>

      {/* ============================================================ */}
      {/* 核心 KPI：两大库存指标突出展示 */}
      {/* ============================================================ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        {/* 可销售库存 */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-emerald-500 rounded-l-2xl" />
          <div className="text-xs text-slate-400 mb-1.5 tracking-wide uppercase">可销售库存</div>
          <div className="flex items-baseline gap-2 mb-1">
            <span className={`text-3xl font-bold tabular-nums ${saleableTotal > 0 ? "text-emerald-700" : "text-slate-400"}`}>{fmtQty(saleableTotal)}</span>
            <span className="text-sm text-slate-400">吨</span>
          </div>
          <div className="text-xs text-slate-400">
            采购 {fmtQty(purchasedTotal)} 吨 − 已售 {fmtQty(inv?.total_sold ?? 0)} 吨
          </div>
          <ProgressBar used={inv?.total_sold ?? 0} total={purchasedTotal} usedColor="#10b981" remainColor="#10b981" />
        </div>

        {/* 可发货库存 */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1.5 h-full bg-indigo-500 rounded-l-2xl" />
          <div className="text-xs text-slate-400 mb-1.5 tracking-wide uppercase">可发货库存</div>
          <div className="flex items-baseline gap-2 mb-1">
            <span className={`text-3xl font-bold tabular-nums ${shippableTotal > 0 ? "text-indigo-700" : "text-slate-400"}`}>{fmtQty(shippableTotal)}</span>
            <span className="text-sm text-slate-400">吨</span>
          </div>
          <div className="text-xs text-slate-400">
            采购 {fmtQty(purchasedTotal)} 吨 − 已发 {fmtQty(inv?.total_shipped ?? 0)} 吨
          </div>
          <ProgressBar used={inv?.total_shipped ?? 0} total={purchasedTotal} usedColor="#6366f1" remainColor="#6366f1" />
        </div>
      </div>

      {/* ============================================================ */}
      {/* 品牌库存明细 —— 可展开仓库子表，关联画线 */}
      {/* ============================================================ */}
      {inv && inv.items.length > 0 && (
        <BrandWarehouseTable
          brands={sortedItems}
          whGrouped={whGrouped}
        />
      )}

      {/* ============================================================ */}
      {/* 业务概览卡片 */}
      {/* ============================================================ */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
        <MiniCard label="采购合同" value={`${s.purchase.count}个`} sub={`${fmtQty(s.purchase.quantity)}吨`} color="blue" />
        <MiniCard label="销售合同" value={`${s.sales.count}个`} sub={`${fmtQty(s.sales.quantity)}吨`} color="emerald" />
        <MiniCard label="发货计划" value={`${s.shipping_plan.active}个`} sub="进行中" color="indigo" />
        <MiniCard label="应收" value={`¥${fmtMoney(s.ar_amount)}`} sub="" color="emerald" />
        <MiniCard label="应付" value={`¥${fmtMoney(s.ap_amount)}`} sub="" color="rose" />
      </div>

      {/* 快捷入口 */}
      <div className="flex flex-wrap gap-3">
        <Link to="/purchase-contracts/create" className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 hover:border-blue-300 hover:text-blue-700 transition-colors">📄 采购合同</Link>
        <Link to="/sales-contracts/create" className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 hover:border-emerald-300 hover:text-emerald-700 transition-colors">📋 销售合同</Link>
        <Link to="/shipping/plans/create" className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 hover:border-indigo-300 hover:text-indigo-700 transition-colors">🚚 发货计划</Link>
        <Link to="/finance" className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 hover:border-amber-300 hover:text-amber-700 transition-colors">💰 财务</Link>
        <Link to="/brand" className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 hover:border-orange-300 hover:text-orange-700 transition-colors">🏷️ 品牌管理</Link>
      </div>
    </div>
  )
}

/** 品牌+仓库关联表 —— 品牌行可展开显示仓库子行，带关联画线 */
function BrandWarehouseTable({ brands, whGrouped }: { brands: InventoryItem[]; whGrouped: Record<string, WarehouseItem[]> }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  const toggle = (brandId: string) => setExpanded(p => ({ ...p, [brandId]: !p[brandId] }))

  return (
    <div className="mb-6">
      <h2 className="text-sm font-semibold text-slate-700 mb-3 ml-1">📦 品牌库存明细</h2>
      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-hidden">
        {/* 表头 */}
        <div className="hidden sm:grid grid-cols-12 gap-1 px-4 py-2.5 bg-slate-50/50 border-b border-slate-100 text-xs font-semibold text-slate-400">
          <div className="col-span-2">品牌 / 仓库</div>
          <div className="col-span-1 text-center">采购量</div>
          <div className="col-span-2 text-center">可销售库存</div>
          <div className="col-span-2 text-center">可发货库存</div>
          <div className="col-span-1 text-center">本月</div>
          <div className="col-span-1 text-center">上月</div>
          <div className="col-span-1 text-center">季度</div>
          <div className="col-span-1 text-center">年度</div>
          <div className="col-span-1 text-center">累计</div>
        </div>

        {brands.map(item => {
          const salePct = item.purchased_qty > 0 ? (item.stock_after_sale / item.purchased_qty) * 100 : 0
          const shipPct = item.purchased_qty > 0 ? (item.stock_after_ship / item.purchased_qty) * 100 : 0
          const isOpen = expanded[item.brand_id] || false
          const whs = whGrouped[item.brand_id] || []

          return (
            <div key={item.brand_id}>
              {/* ====== 品牌主行 ====== */}
              <div
                onClick={() => whs.length > 0 && toggle(item.brand_id)}
                className={`px-4 py-3 border-b border-slate-50 transition-colors ${whs.length > 0 ? "cursor-pointer hover:bg-slate-50/50" : ""}`}
              >
                {/* 移动端 */}
                <div className="sm:hidden space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {whs.length > 0 && (
                        <svg className={`w-3 h-3 text-slate-400 transition-transform ${isOpen ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                      )}
                      <span className="inline-block w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: toColor(item.brand_color, "#94a3b8") }} />
                      <span className="text-sm font-semibold text-slate-800">{item.brand_name}</span>
                    </div>
                    <span className="text-xs text-slate-400">采购 {fmtQty(item.purchased_qty)}吨</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-emerald-50 rounded-lg px-2.5 py-1.5">
                      <div className="text-[10px] text-emerald-500">可销售</div>
                      <div className="text-sm font-bold" style={{ color: toColor(item.brand_color, "#10b981") }}>{fmtQty(item.stock_after_sale)}吨</div>
                    </div>
                    <div className="bg-indigo-50 rounded-lg px-2.5 py-1.5">
                      <div className="text-[10px] text-indigo-400">可发货</div>
                      <div className="text-sm font-bold" style={{ color: toColor(item.brand_color, "#6366f1") }}>{fmtQty(item.stock_after_ship)}吨</div>
                    </div>
                  </div>
                </div>

                {/* 桌面端 */}
                <div className="hidden sm:grid grid-cols-12 gap-1 items-center">
                  <div className="col-span-2 flex items-center gap-2">
                    {whs.length > 0 ? (
                      <svg className={`w-3.5 h-3.5 text-slate-400 transition-transform shrink-0 ${isOpen ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                    ) : (
                      <span className="w-3.5 shrink-0" />
                    )}
                    <span className="inline-block w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: toColor(item.brand_color, "#94a3b8") }} />
                    <span className="text-sm font-semibold text-slate-800">{item.brand_name}</span>
                  </div>
                  <div className="col-span-1 text-center text-sm tabular-nums text-slate-600">{fmtQty(item.purchased_qty)}{item.purchased_qty > 0 && <span className="text-xs text-slate-400 ml-0.5">吨</span>}</div>
                  <div className="col-span-2 flex items-center justify-center">
                    <span className="text-sm font-semibold tabular-nums" style={{ color: item.stock_after_sale > 0 ? (toColor(item.brand_color, "#10b981")) : "#94a3b8" }}>{fmtQty(item.stock_after_sale)}{item.stock_after_sale > 0 && <span className="text-xs font-normal ml-0.5">吨</span>}</span>
                  </div>
                  <div className="col-span-2 flex items-center justify-center">
                    <span className="text-sm font-semibold tabular-nums" style={{ color: item.stock_after_ship > 0 ? (toColor(item.brand_color, "#6366f1")) : "#94a3b8" }}>{fmtQty(item.stock_after_ship)}{item.stock_after_ship > 0 && <span className="text-xs font-normal ml-0.5">吨</span>}</span>
                  </div>
                  <div className="col-span-1 text-center tabular-nums text-slate-500">{fmtQty(item.shipped_this_month)}</div>
                  <div className="col-span-1 text-center tabular-nums text-slate-400">{fmtQty(item.shipped_last_month)}</div>
                  <div className="col-span-1 text-center tabular-nums text-slate-500">{fmtQty(item.shipped_this_quarter)}</div>
                  <div className="col-span-1 text-center tabular-nums text-slate-500">{fmtQty(item.shipped_this_year)}</div>
                  <div className="col-span-1 text-center tabular-nums text-slate-600">{fmtQty(item.shipped_qty)}</div>
                </div>
              </div>

              {/* ====== 仓库子行（展开时显示，关联画线） ====== */}
              {isOpen && whs.length > 0 && (
                <div className="border-b border-slate-50 bg-slate-50/30">
                  {whs.map((wh) => (
                    <div key={wh.warehouse_id} className="hidden sm:grid grid-cols-12 gap-1 items-center px-4 py-2 text-xs">
                      <div className="col-span-2 flex items-center gap-2 pl-8">
                        <span className="text-slate-500">{wh.warehouse_name}</span>
                      </div>
                      <div className="col-span-1 text-center tabular-nums text-slate-500">{fmtQty(wh.purchased_qty)}</div>
                      <div className="col-span-2 flex items-center justify-center">
                        <span className="tabular-nums font-medium" style={{ color: wh.stock_after_sale > 0 ? (toColor(wh.brand_color, "#10b981")) : "#94a3b8" }}>{fmtQty(wh.stock_after_sale)}</span>
                      </div>
                      <div className="col-span-2 flex items-center justify-center">
                        <span className="tabular-nums font-medium" style={{ color: wh.stock_after_ship > 0 ? (toColor(wh.brand_color, "#6366f1")) : "#94a3b8" }}>{fmtQty(wh.stock_after_ship)}</span>
                      </div>
                      <div className="col-span-1"></div>
                    </div>
                  ))}
                  {/* 移动端仓库子行 */}
                  <div className="sm:hidden">
                    {whs.map(wh => (
                      <div key={wh.warehouse_id} className="px-4 py-2 pl-8 border-t border-slate-100 flex items-center gap-3 text-xs">
                        <span className="text-slate-600 font-medium">{wh.warehouse_name}</span>
                        <span className="text-slate-400">采购{fmtQty(wh.purchased_qty)}</span>
                        <span style={{ color: toColor(wh.brand_color, "#10b981") }}>可售{fmtQty(wh.stock_after_sale)}</span>
                        <span style={{ color: toColor(wh.brand_color, "#6366f1") }}>可发{fmtQty(wh.stock_after_ship)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function MiniCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color: "blue" | "emerald" | "indigo" | "rose" | "amber" | "slate" }) {
  const colors: Record<string, string> = {
    blue: "border-l-blue-400", emerald: "border-l-emerald-400", indigo: "border-l-indigo-400",
    rose: "border-l-rose-400", amber: "border-l-amber-400", slate: "border-l-slate-400",
  }
  return (
    <div className={`bg-white border border-slate-200 rounded-lg px-4 py-3 border-l-[3px] ${colors[color]}`}>
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className="text-base font-bold tabular-nums text-slate-800">{value}</div>
      {sub ? <div className="text-xs text-slate-400 mt-0.5">{sub}</div> : null}
    </div>
  )
}
