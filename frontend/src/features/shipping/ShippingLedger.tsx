/** 货运台账 —— 发货记录列表 */
import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { apiGet } from "../../api/client"
import { Pagination } from "../../components/shared/Pagination"
import { fmtQty, fmtMoney } from "../../lib/utils"

const INP = "px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400"

interface ShipmentItem { id: string; line_no: number; plan_item_id: string; shipped_quantity: number; unit: string }
interface PlanBrief { id: string; brand_id: string; planned_date: string; delivery_method: string; total_planned_quantity: number; supplier_enterprise_id: string; purchase_contract_id: string }
interface Shipment {
  id: string; shipment_no: string; shipped_date: string; plan_id: string
  driver_name: string | null; driver_phone: string | null; driver_license_plate: string | null
  freight_total: number | null; freight_unit_price: number | null
  status: string; remark: string | null; created_at: string
  plan?: PlanBrief; items: ShipmentItem[]
}

const DL_MAP: Record<string, string> = { ZT: "自提", SH: "送货" }

export function ShippingLedger() {
  const [fDateFrom, setFDateFrom] = useState("")
  const [fDateTo, setFDateTo] = useState("")
  const [searchNo, setSearchNo] = useState("")
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  const buildUrl = () => {
    const p = new URLSearchParams()
    p.set("page", String(page))
    p.set("page_size", String(pageSize))
    if (fDateFrom) p.set("start_date", fDateFrom)
    if (fDateTo) p.set("end_date", fDateTo)
    return `/shipping/shipments?${p.toString()}`
  }

  const { data: shipmentData, isLoading } = useQuery({
    queryKey: ["shipments-ledger", fDateFrom, fDateTo, page, pageSize],
    queryFn: async () => {
      const r = await apiGet<{ items: Shipment[]; total: number; pages: number }>(buildUrl())
      return r
    },
  })
  const shipments = shipmentData?.items ?? []
  const total = shipmentData?.total ?? 0
  const pages = shipmentData?.pages ?? 0

  // 品牌/企业名称
  const { data: brandMap = {} } = useQuery({
    queryKey: ["brands-ledger"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string }[] }>("/brand/brands?page=1&page_size=200")
      const m: Record<string, string> = {}
      for (const b of r.items ?? []) m[b.id] = b.name
      return m
    },
  })
  const { data: entMap = {} } = useQuery({
    queryKey: ["ents-ledger"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/enterprises?page=1&page_size=200")
      const m: Record<string, string> = {}
      for (const e of r.items ?? []) m[e.id] = e.name
      return m
    },
  })
  const { data: pcMap = {} } = useQuery({
    queryKey: ["pcs-ledger"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; contract_no: string }[] }>("/purchase-contracts?page=1&page_size=100")
      const m: Record<string, string> = {}
      for (const pc of r.items ?? []) m[pc.id] = pc.contract_no
      return m
    },
  })

  const filtered = useMemo(() => {
    return searchNo ? shipments.filter(s => s.shipment_no.toLowerCase().includes(searchNo.toLowerCase())) : shipments
  }, [shipments, searchNo])

  const totalQty = filtered.reduce((s, sh) => s + sh.items.reduce((ss, i) => ss + i.shipped_quantity, 0), 0)
  const totalFreight = filtered.reduce((s, sh) => s + (sh.freight_total ? Number(sh.freight_total) : 0), 0)

  return (
    <div className="page-enter p-6">
      <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
        <Link to="/shipping/plans" className="hover:text-slate-600">计划看板</Link><span>/</span>
        <span className="text-slate-700 font-medium">货运台账</span>
      </div>
      <h1 className="text-xl font-bold text-slate-900 mb-4">货运台账</h1>

      {/* 筛选栏 */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <input type="date" value={fDateFrom} onChange={e => setFDateFrom(e.target.value)} className={`${INP} w-34`} />
        <span className="text-slate-300">~</span>
        <input type="date" value={fDateTo} onChange={e => setFDateTo(e.target.value)} className={`${INP} w-34`} />
        <input value={searchNo} onChange={e => setSearchNo(e.target.value)} className={`${INP} w-48`} />
        <div className="flex-1" />
        <div className="text-sm text-slate-500">
          共 <b className="text-slate-800">{total}</b> 条发货
          <span className="mx-3">|</span>
          发货总量 <b className="text-slate-800">{fmtQty(totalQty)}</b> 吨
          <span className="mx-3">|</span>
          运费合计 <b className="text-indigo-600">¥{fmtMoney(totalFreight)}</b>
        </div>
      </div>

      {/* 表格 */}
      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-x-auto">
        {isLoading ? (
          <div className="p-16 text-center text-slate-300">加载中...</div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-slate-400">暂无发货记录</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">发货编号</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">发货日期</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">品牌</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">供方</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">采购合同</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">配送方式</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-right">发货吨数</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-right">运费</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">司机/车辆</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">计划日期</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">备注</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(s => {
                const plan = s.plan
                const shippedQty = s.items.reduce((sum, i) => sum + i.shipped_quantity, 0)
                return (
                  <tr key={s.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="px-3 py-2.5 text-xs font-semibold text-indigo-600">{s.shipment_no}</td>
                    <td className="px-3 py-2.5 text-xs text-slate-700">{s.shipped_date}</td>
                    <td className="px-3 py-2.5 text-xs text-slate-600">
                      {plan ? brandMap[plan.brand_id] ?? plan.brand_id.slice(0, 6) : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-600">
                      {plan ? entMap[plan.supplier_enterprise_id] ?? plan.supplier_enterprise_id.slice(0, 6) : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-500">
                      {plan ? pcMap[plan.purchase_contract_id] ?? plan.purchase_contract_id.slice(0, 8) : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-600">
                      {plan ? DL_MAP[plan.delivery_method] ?? plan.delivery_method : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-right font-medium text-slate-700">{fmtQty(shippedQty)}吨</td>
                    <td className="px-3 py-2.5 text-xs text-right text-slate-600">
                      {s.freight_total ? <>¥{fmtMoney(s.freight_total)}<br /><span className="text-slate-400">¥{fmtMoney(s.freight_unit_price)}/吨</span></> : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-500">
                      {s.driver_name || s.driver_license_plate ? <>{s.driver_name ?? "—"}<br /><span className="text-slate-400">{s.driver_license_plate ?? ""}</span></> : "—"}
                    </td>
                    <td className="px-3 py-2.5 text-xs text-slate-500">{plan?.planned_date ?? "—"}</td>
                    <td className="px-3 py-2.5 text-xs text-slate-500 max-w-[120px] truncate" title={s.remark ?? ""}>{s.remark || "—"}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* 分页 */}
      <Pagination
        page={page} pageSize={pageSize} total={total} pages={pages}
        onPageChange={(p) => setPage(p)}
        onPageSizeChange={(s) => { setPageSize(s); setPage(1) }}
      />
    </div>
  )
}
