/** 货运模块 —— 按发货明细行展示 */
import { useState, useMemo, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { apiGet } from "../../api/client"
import { SearchableSelect } from "../../components/shared/SearchableSelect"
import { Cascader } from "../../components/shared/Cascader"
import type { CascaderOption } from "../../components/shared/Cascader"
import { Pagination } from "../../components/shared/Pagination"
import { AuditTimeline } from "../../components/shared/AuditTimeline"
import { fmtQty } from "../../lib/utils"

const INP = "px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400"

interface ShipmentItem {
  id: string; plan_item_id: string; shipped_quantity: number; unit: string
  model_id?: string; warehouse_id?: string
  customer_enterprise_id?: string; sales_contract_id?: string
}
interface PlanBrief { id: string; brand_id: string; planned_date: string; delivery_method: string; total_planned_quantity: number; supplier_enterprise_id: string; purchase_contract_id: string }
interface Shipment {
  id: string; shipment_no: string; shipped_date: string; plan_id: string
  driver_name: string | null; driver_phone: string | null; driver_license_plate: string | null
  driver_id_card: string | null
  freight_total: number | null; freight_unit_price: number | null
  status: string; remark: string | null; created_at: string
  plan?: PlanBrief; items: ShipmentItem[]
}

/** 扁平化行：一个发货明细 = 一行 */
interface FlatRow {
  shipmentId: string; itemId: string
  shipmentNo: string; shippedDate: string
  customerId: string; brandId: string
  modelId: string; warehouseId: string
  quantity: number
  purchaseContractId: string; salesContractId: string
  driverName: string; driverPhone: string; driverPlate: string; driverIdCard: string
  remark: string
}

export function FreightLedger() {
  const [fDateFrom, setFDateFrom] = useState("")
  const [fDateTo, setFDateTo] = useState("")
  const [searchNo, setSearchNo] = useState("")
  const [fCustomerId, setFCustomerId] = useState("")
  const [detailShipmentId, setDetailShipmentId] = useState<string | null>(null)
  const detailShipment = shipments.find(s => s.id === detailShipmentId)
  const [brandFilter, setBrandFilter] = useState<string[]>([])
  const [whFilter, setWhFilter] = useState<string[]>([])
  const [cascaderOpen, setCascaderOpen] = useState(false)
  const [fPcId, setFPcId] = useState("")
  const [fScId, setFScId] = useState("")
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
    queryKey: ["freight-ledger", fDateFrom, fDateTo, page, pageSize],
    queryFn: async () => {
      const r = await apiGet<{ items: Shipment[]; total: number; pages: number }>(buildUrl())
      return r
    },
  })
  const shipments = shipmentData?.items ?? []
  const total = shipmentData?.total ?? 0
  const pages = shipmentData?.pages ?? 0

  // 品牌名称 + 仓库列表（级联用）
  interface BrandInfo { name: string; warehouses: { id: string; name: string }[]; color?: string }
  const [brandInfo, setBrandInfo] = useState<Record<string, BrandInfo>>({})
  const brandMap = useMemo(() => {
    const m: Record<string, string> = {}
    for (const [id, b] of Object.entries(brandInfo)) m[id] = b.name
    return m
  }, [brandInfo])

  useEffect(() => {
    (async () => {
      const r = await apiGet<{ items: { id: string; name: string; color: string }[] }>("/brand/brands?page=1&page_size=200")
      const map: Record<string, BrandInfo> = {}
      for (const b of r.items ?? []) map[b.id] = { name: b.name, color: b.color, warehouses: [] }
      // 并行加载每个品牌的仓库列表
      await Promise.all((r.items ?? []).map(async (b) => {
        try {
          const wr = await apiGet<{ items: { id: string; name: string }[] }>(`/brand/brands/${b.id}/warehouses?page=1&page_size=100`)
          if (map[b.id]) map[b.id].warehouses = wr.items ?? []
        } catch { /* skip */ }
      }))
      setBrandInfo(map)
    })()
  }, [])

  // 企业名称
  const { data: entMap = {} } = useQuery({
    queryKey: ["ents-freight"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/enterprises?page=1&page_size=200")
      const m: Record<string, string> = {}
      for (const e of r.items ?? []) m[e.id] = e.name
      return m
    },
  })

  // 采购/销售合同名称
  const { data: pcMap = {} } = useQuery({
    queryKey: ["pcs-freight"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; contract_no: string }[] }>("/purchase-contracts?page=1&page_size=100")
      const m: Record<string, string> = {}
      for (const pc of r.items ?? []) m[pc.id] = pc.contract_no
      return m
    },
  })
  const { data: scMap = {} } = useQuery({
    queryKey: ["scs-freight"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; contract_no: string }[] }>("/sales-contracts?page=1&page_size=100")
      const m: Record<string, string> = {}
      for (const sc of r.items ?? []) m[sc.id] = sc.contract_no
      return m
    },
  })

  // 所有品牌型号和仓库名称映射
  const [nameMap, setNameMap] = useState<{ models: Record<string, string>; whs: Record<string, string> }>({ models: {}, whs: {} })
  useEffect(() => {
    const brandIds = [...new Set(shipments.map(s => s.plan?.brand_id).filter(Boolean))]
    if (brandIds.length === 0) return
    let cancelled = false
    ;(async () => {
      const models: Record<string, string> = {}
      const whs: Record<string, string> = {}
      // 并行加载所有品牌的型号和仓库
      await Promise.all(brandIds.map(async (bid) => {
        try {
          const [mRes, wRes] = await Promise.all([
            fetch(`/api/v1/brand/brands/${bid}/models?page=1&page_size=100`),
            fetch(`/api/v1/brand/brands/${bid}/warehouses?page=1&page_size=100`),
          ])
          const [mJson, wJson] = await Promise.all([mRes.json(), wRes.json()])
          for (const bm of mJson?.data?.items ?? []) models[bm.id] = bm.model_name
          for (const bw of wJson?.data?.items ?? []) whs[bw.id] = bw.name
        } catch { /* skip */ }
      }))
      if (!cancelled) setNameMap({ models, whs })
    })()
    return () => { cancelled = true }
  }, [shipments])

  // 扁平化为明细行
  const flatRows = useMemo(() => {
    const rows: FlatRow[] = []
    for (const s of shipments) {
      for (const it of s.items) {
        rows.push({
          shipmentId: s.id, itemId: it.id,
          shipmentNo: s.shipment_no, shippedDate: s.shipped_date,
          customerId: it.customer_enterprise_id ?? "",
          brandId: s.plan?.brand_id ?? "",
          modelId: it.model_id ?? "", warehouseId: it.warehouse_id ?? "",
          quantity: it.shipped_quantity,
          purchaseContractId: s.plan?.purchase_contract_id ?? "",
          salesContractId: it.sales_contract_id ?? "",
          driverName: s.driver_name ?? "", driverPhone: s.driver_phone ?? "",
          driverPlate: s.driver_license_plate ?? "", driverIdCard: s.driver_id_card ?? "",
          remark: s.remark ?? "",
        })
      }
    }
    return rows
  }, [shipments])

  // 筛选选项
  const cascaderOptions: CascaderOption[] = useMemo(() => {
    return Object.entries(brandInfo).map(([id, b]) => ({
      value: id, label: b.name,
      children: b.warehouses.map(w => ({ value: w.id, label: w.name })),
    }))
  }, [brandInfo])
  const customerOptions = useMemo(() => {
    const seen = new Set<string>()
    const opts: { id: string; name: string }[] = []
    for (const r of flatRows) {
      if (r.customerId && !seen.has(r.customerId)) {
        seen.add(r.customerId)
        opts.push({ id: r.customerId, name: entMap[r.customerId] ?? r.customerId.slice(0, 6) })
      }
    }
    return opts
  }, [flatRows, entMap])
  const pcOptions = useMemo(() => Object.entries(pcMap).map(([id, name]) => ({ id, name })), [pcMap])
  const scOptions = useMemo(() => Object.entries(scMap).map(([id, name]) => ({ id, name })), [scMap])

  const toggleCascader = (val: string) => {
    // 判断是品牌还是仓库
    const isBrand = brandInfo[val] !== undefined
    if (isBrand) {
      if (brandFilter.includes(val)) {
        // 取消品牌 → 同时取消其下所有仓库
        const whIds = (brandInfo[val]?.warehouses ?? []).map(w => w.id)
        setBrandFilter(p => p.filter(v => v !== val))
        setWhFilter(p => p.filter(v => !whIds.includes(v)))
      } else {
        // 勾选品牌 → 同时全选其下所有仓库
        const whIds = (brandInfo[val]?.warehouses ?? []).map(w => w.id)
        setBrandFilter(p => [...p, val])
        setWhFilter(p => [...new Set([...p, ...whIds])])
      }
    } else {
      setWhFilter(p => p.includes(val) ? p.filter(v => v !== val) : [...p, val])
    }
  }

  const filtered = useMemo(() => {
    let rows = flatRows
    if (searchNo) { const q = searchNo.toLowerCase(); rows = rows.filter(r => r.shipmentNo.toLowerCase().includes(q)) }
    if (fCustomerId) rows = rows.filter(r => r.customerId === fCustomerId)
    if (brandFilter.length > 0) rows = rows.filter(r => brandFilter.includes(r.brandId))
    if (whFilter.length > 0) rows = rows.filter(r => whFilter.includes(r.warehouseId))
    if (fPcId) rows = rows.filter(r => r.purchaseContractId === fPcId)
    if (fScId) rows = rows.filter(r => r.salesContractId === fScId)
    return rows
  }, [flatRows, searchNo, fCustomerId, brandFilter, whFilter, fPcId, fScId])

  return (
    <div className="page-enter p-4 sm:p-6 lg:p-8">
      <h1 className="text-xl font-bold text-slate-900 mb-4">🚚 货运台账</h1>

      {/* 筛选栏 */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <input type="date" value={fDateFrom} onChange={e => setFDateFrom(e.target.value)} className={`${INP} w-34`} />
        <span className="text-slate-300">~</span>
        <input type="date" value={fDateTo} onChange={e => setFDateTo(e.target.value)} className={`${INP} w-34`} />
        <input value={searchNo} onChange={e => setSearchNo(e.target.value)} className={`${INP} w-40 text-xs`} />
        <SearchableSelect value={fCustomerId} onChange={setFCustomerId} options={customerOptions} className={`${INP} w-28 text-xs`} />
        <Cascader label="品牌/仓库" options={cascaderOptions} selected={[...brandFilter, ...whFilter]} onChange={toggleCascader} isOpen={cascaderOpen} onToggle={() => setCascaderOpen(p => !p)} />
        <SearchableSelect value={fPcId} onChange={setFPcId} options={pcOptions} className={`${INP} w-32 text-xs`} />
        <SearchableSelect value={fScId} onChange={setFScId} options={scOptions} className={`${INP} w-32 text-xs`} />
        {(fDateFrom || fDateTo || searchNo || fCustomerId || brandFilter.length > 0 || whFilter.length > 0 || fPcId || fScId) && (
          <button onClick={() => { setFDateFrom(""); setFDateTo(""); setSearchNo(""); setFCustomerId(""); setBrandFilter([]); setWhFilter([]); setFPcId(""); setFScId("") }}
            className="text-xs text-indigo-500 hover:text-indigo-700 px-2">清除</button>
        )}
      </div>

      {/* 表格 */}
      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-x-auto -mx-4 sm:mx-0">
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
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">客户</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">品牌</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">仓库</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">型号</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-right">数量</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">采购合同</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">销售合同</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">车牌</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">司机</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">手机</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">身份证</th>
                <th className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">备注</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r, idx) => (
                <tr key={`${r.shipmentId}-${r.itemId}`}
                  onClick={() => setDetailShipmentId(r.shipmentId)}
                  className={`border-b border-slate-50 hover:bg-indigo-50/30 transition-colors cursor-pointer ${idx > 0 && filtered[idx - 1].shipmentId === r.shipmentId ? "" : "border-t-slate-200"}`}>
                  <td className="px-3 py-2.5 text-xs font-semibold text-indigo-600">{r.shipmentNo}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-700">{r.shippedDate}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-700">{entMap[r.customerId] ?? r.customerId.slice(0, 6)}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-700 font-medium">{brandMap[r.brandId] ?? r.brandId.slice(0, 6)}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-600">{nameMap.whs[r.warehouseId] ?? r.warehouseId.slice(0, 6)}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-600">{nameMap.models[r.modelId] ?? r.modelId.slice(0, 8)}</td>
                  <td className="px-3 py-2.5 text-xs text-right font-semibold text-slate-800">{fmtQty(r.quantity)}吨</td>
                  <td className="px-3 py-2.5 text-xs text-slate-500">{pcMap[r.purchaseContractId] ?? r.purchaseContractId.slice(0, 8)}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-500">{scMap[r.salesContractId] ?? r.salesContractId.slice(0, 8)}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-600 font-mono">{r.driverPlate || ""}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-600">{r.driverName || ""}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-500 font-mono">{r.driverPhone || ""}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-400 font-mono">{r.driverIdCard || ""}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-400 max-w-[80px] truncate" title={r.remark}>{r.remark}</td>
                </tr>
              ))}
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

      {detailShipment && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/20" onClick={() => setDetailShipmentId(null)} />
          <div className="relative w-[480px] bg-white shadow-2xl h-full overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
              <div><h2 className="text-lg font-bold">{detailShipment.shipment_no}</h2><span className="text-xs text-slate-400">{detailShipment.shipped_date}</span></div>
              <button onClick={() => setDetailShipmentId(null)} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button>
            </div>
            <div className="p-6 space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div><span className="text-slate-400 text-xs">发货日期</span><div className="text-slate-800">{detailShipment.shipped_date}</div></div>
                <div><span className="text-slate-400 text-xs">司机</span><div className="text-slate-800">{detailShipment.driver_name || "—"}</div></div>
                <div><span className="text-slate-400 text-xs">手机</span><div className="text-slate-800">{detailShipment.driver_phone || "—"}</div></div>
                <div><span className="text-slate-400 text-xs">车牌</span><div className="text-slate-800">{detailShipment.driver_license_plate || "—"}</div></div>
              </div>
              <div><span className="text-slate-400 text-xs">运费</span><div className="text-slate-800 font-semibold">{detailShipment.freight_total ? `¥${Number(detailShipment.freight_total).toFixed(2)}` : "—"}</div></div>
              {detailShipment.remark && <div><span className="text-slate-400 text-xs">备注</span><div className="text-slate-600">{detailShipment.remark}</div></div>}
              <AuditTimeline entityType="shipment" entityId={detailShipment.id} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
