/** 计划表单 —— 品牌→供方→采购合同(含明细)，明细：客户→销售合同(含明细)→仓库/型号/吨数 */
import { useState, useEffect, useRef } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { apiGet, apiPost } from "../../api/client"
import { SearchableSelect } from "../../components/shared/SearchableSelect"
import { fmtQty } from "../../lib/utils"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"
const INP_SM = "w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400"

interface E { id: string; name: string }
interface B { id: string; name: string; color: string }
interface BM { id: string; model_name: string; model_type: string }
interface BW { id: string; name: string }
interface PCI { brand_id: string; model_id: string; shipping_warehouse_id: string; quantity: number; purchase_price: number }
interface PC { id: string; contract_no: string; supplier_enterprise_id: string; total_quantity: number; items: PCI[] }
interface SCI { id: string; brand_id: string; model_id: string; shipping_warehouse_id: string; quantity: number; sale_price: number }
interface SC { id: string; contract_no: string; customer_enterprise_id: string; status: string; items: SCI[] }

interface PlanRow {
  customer_enterprise_id: string; sales_contract_id: string
  model_id: string; warehouse_id: string; planned_quantity: number
  purchase_price: number; sale_price: number
  surcharge_type: string | null; surcharge_amount: number
}

const DL_OPTS = [
  { key: "SH", label: "送货", color: "border-sky-400 bg-sky-50 text-sky-700", active: "border-sky-500 bg-sky-100 text-sky-800 ring-2 ring-sky-200" },
  { key: "ZT", label: "自提", color: "border-amber-400 bg-amber-50 text-amber-700", active: "border-amber-500 bg-amber-100 text-amber-800 ring-2 ring-amber-200" },
]

export function ShippingPlanForm() {
  const nav = useNavigate()
  const [companyId, setCompanyId] = useState("")
  const [brandId, setBrandId] = useState("")
  const [supplierId, setSupplierId] = useState("")
  const [purchaseContractId, setPurchaseContractId] = useState("")
  const [plannedDate, setPlannedDate] = useState(new Date().toISOString().slice(0, 10))
  const [deliveryMethod, setDeliveryMethod] = useState("SH")
  const [remark, setRemark] = useState("")
  const emptyRow = (price: number) => ({ customer_enterprise_id: "", sales_contract_id: "", model_id: "", warehouse_id: "", planned_quantity: 0, purchase_price: price, sale_price: 0, surcharge_type: null, surcharge_amount: 0 })
  const [rows, setRows] = useState<PlanRow[]>([emptyRow(0)])
  const [brandData, setBrandData] = useState<{ models: BM[]; warehouses: BW[] }>({ models: [], warehouses: [] })
  // 仓库名称映射（品牌级仓库在 loadBrandData 中追加）
  const [whNames, setWhNames] = useState<Record<string, string>>({})

  const { data: companies } = useQuery({ queryKey: ["co"], queryFn: async () => { const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/companies"); return r.items ?? [] } })
  const { data: brands } = useQuery({ queryKey: ["brands-all"], queryFn: async () => { const r = await apiGet<{ items: B[] }>("/brand/brands?page=1&page_size=200"); return r.items ?? [] } })
  // 品牌名直接从 React Query 数据派生（避免异步加载时序问题）
  const brandNames: Record<string, string> = {}
  for (const b of brands ?? []) brandNames[b.id] = b.name
  const { data: allEnts } = useQuery({ queryKey: ["ents-all"], queryFn: async () => { const r = await apiGet<{ items: E[] }>("/basedata/enterprises?page=1&page_size=200"); return r.items ?? [] } })
  const { data: allPCs, isLoading: pcsLoading } = useQuery({ queryKey: ["pcs-all"], queryFn: async () => { const r = await apiGet<{ items: PC[] }>("/purchase-contracts?page=1&page_size=100"); return r.items?.filter(pc => (pc as any).status !== "cancelled") ?? [] } })
  const { data: allSCs, isLoading: scsLoading } = useQuery({ queryKey: ["scs-all"], queryFn: async () => { const r = await apiGet<{ items: SC[] }>("/sales-contracts?page=1&page_size=100"); return r.items?.filter(sc => sc.status !== "cancelled") ?? [] } })

  // 加载合同已计划用量（用于计算可发/可提）
  const { data: usage } = useQuery({ queryKey: ["contract-usage"], queryFn: async () => { const r = await apiGet<{ purchase_usage: Record<string, number>; sales_usage: Record<string, number> }>("/shipping/contract-usage"); return r } })
  const pcUsed: Record<string, number> = usage?.purchase_usage ?? {}
  const scUsed: Record<string, number> = usage?.sales_usage ?? {}

  // 预加载所有品牌的仓库和型号名称映射（挂载即加载，确保选择器始终有名称数据）
  useEffect(() => {
    const loadAll = async () => {
      // 先获取全部品牌ID
      let ids: string[] = (brands ?? []).map(b => b.id)
      for (const sc of (allSCs ?? [])) for (const it of (sc.items ?? [])) if (it.brand_id) ids.push(it.brand_id)
      ids = [...new Set(ids)]
      // 如果还没有品牌数据，主动拉取
      if (ids.length === 0) {
        try { const r = await apiGet<{ items: { id: string }[] }>("/brand/brands?page_size=200"); ids = (r.items ?? []).map(b => b.id) } catch { return }
      }
      if (ids.length === 0) return
      const whMap: Record<string, string> = {}
      const mdlMap: Record<string, string> = {}
      await Promise.all(ids.map(async (bid) => {
        try {
          const [wResp, mResp] = await Promise.all([
            apiGet<{ items: { id: string; name: string }[] }>(`/brand/brands/${bid}/warehouses?page_size=100`).catch(() => ({ items: [] })),
            apiGet<{ items: { id: string; model_name: string }[] }>(`/brand/brands/${bid}/models?page_size=100`).catch(() => ({ items: [] })),
          ])
          for (const w of wResp.items ?? []) whMap[w.id] = w.name
          for (const m of mResp.items ?? []) mdlMap[m.id] = m.model_name
        } catch { /* skip */ }
      }))
      setWhNames(p => ({ ...whMap, ...p }))
      setAllModels(p => ({ ...mdlMap, ...p }))
    }
    loadAll()
  }, [brands, allSCs])

  const [allModels, setAllModels] = useState<Record<string, string>>({})

  // 品牌/仓库/型号名称（多层回退确保解析成功）
  const getBrandName = (bid: string) => brandNames[bid] ?? brands?.find(b => b.id === bid)?.name ?? (bid ? bid.slice(0, 8) : "—")
  const getWhName = (wid: string) => whNames[wid] ?? (wid ? wid.slice(0, 8) : "—")
  const getModelName = (mid: string) => allModels[mid] ?? (mid ? mid.slice(0, 8) : "—")

  const getEntName = (eid: string) => allEnts?.find(e => e.id === eid)?.name ?? eid.slice(0, 8)

  // 按品牌筛选采购合同 —— 只保留该品牌明细可发数量 > 0 的合同
  const pcsByBrand = brandId ? (allPCs ?? []).filter(pc => {
    const brandQty = pc.items.filter(it => it.brand_id === brandId).reduce((s, it) => s + it.quantity, 0)
    return brandQty - (pcUsed[pc.id] ?? 0) > 0
  }) : (allPCs ?? [])
  // 供方下拉 —— 只显示有可发货合同的供方
  const availableSupplierIds = brandId ? [...new Set(pcsByBrand.map(pc => pc.supplier_enterprise_id))] : (allEnts ?? []).map(e => e.id)
  const suppliers = (allEnts ?? []).filter(e => availableSupplierIds.includes(e.id))
  const filteredPCs = supplierId ? pcsByBrand.filter(pc => pc.supplier_enterprise_id === supplierId) : pcsByBrand
  const selectedPC = allPCs?.find(pc => pc.id === purchaseContractId)
  const pcAvailQty = selectedPC ? Math.max(0, selectedPC.items.filter(it => brandId ? it.brand_id === brandId : true).reduce((s, it) => s + it.quantity, 0) - (pcUsed[selectedPC.id] ?? 0)) : 0

  const loadBrandData = async (bid: string) => {
    if (!bid) { setBrandData({ models: [], warehouses: [] }); return }
    try {
      const [mData, wData] = await Promise.all([
        apiGet<{ items: BM[] }>(`/brand/brands/${bid}/models?page=1&page_size=100`),
        apiGet<{ items: BW[] }>(`/brand/brands/${bid}/warehouses?page=1&page_size=100`),
      ])
      const whs: BW[] = wData.items ?? []
      setBrandData({ models: mData.items ?? [], warehouses: whs })
      // 将品牌级仓库名也汇总进全局映射（解决 picker 中仓库名不显示的问题）
      if (whs.length > 0) setWhNames(p => { const n = { ...p }; for (const w of whs) n[w.id] = w.name; return n })
    } catch (e) { console.error("loadBrandData", e) }
  }
  useEffect(() => { loadBrandData(brandId) }, [brandId])

  useEffect(() => { if (selectedPC?.items?.[0]) setRows(prev => prev.map(r => ({ ...r, purchase_price: selectedPC.items[0].purchase_price }))) }, [purchaseContractId])

  const updRow = (i: number, f: keyof PlanRow, v: any) => {
    setRows(prev => {
      const next = [...prev]; const row = { ...next[i], [f]: v }
      if (f === "customer_enterprise_id") { row.sales_contract_id = ""; row.sale_price = 0 }
      if (f === "sales_contract_id" && v) { const sc = allSCs?.find(s => s.id === v); if (sc?.items?.length) { const it = sc.items.find(it => brandId ? it.brand_id === brandId : true) ?? sc.items[0]; row.sale_price = it.sale_price; row.model_id = it.model_id; row.warehouse_id = it.shipping_warehouse_id } }
      if (f === "model_id" && v) { const m = brandData.models.find(m => m.id === v); if (m?.model_type === "碳酸料") { row.surcharge_type = "carbonate_transfer"; row.surcharge_amount = 100 } else { row.surcharge_type = null; row.surcharge_amount = 0 } }
      next[i] = row; return next
    })
  }
  const addRow = () => setRows(prev => [...prev, emptyRow(selectedPC?.items?.[0]?.purchase_price ?? 0)])
  const delRow = (i: number) => { if (rows.length > 1) setRows(prev => prev.filter((_, idx) => idx !== i)) }

  const totalQty = rows.reduce((s, r) => s + (r.planned_quantity || 0), 0)
  const overAvail = pcAvailQty > 0 && totalQty > pcAvailQty
  const ok = companyId && brandId && supplierId && purchaseContractId && !overAvail && rows.every(r => r.customer_enterprise_id && r.sales_contract_id && r.model_id && r.warehouse_id && r.planned_quantity > 0)

  const mut = useMutation({
    mutationFn: async () => {
      return apiPost("/shipping/plans", {
        company_id: companyId, brand_id: brandId, supplier_enterprise_id: supplierId, purchase_contract_id: purchaseContractId,
        planned_date: plannedDate, delivery_method: deliveryMethod, remark: remark || null,
        items: rows.map(r => ({ customer_enterprise_id: r.customer_enterprise_id, sales_contract_id: r.sales_contract_id, model_id: r.model_id, warehouse_id: r.warehouse_id, planned_quantity: r.planned_quantity, unit: "吨", purchase_price: r.purchase_price, sale_price: r.sale_price, surcharge_type: r.surcharge_type, surcharge_amount: r.surcharge_amount })),
      })
    },
    onSuccess: () => nav("/shipping/plans"),
    onError: (err: any) => sysToast("提交失败: " + (err.message || "")),
  })

  return (
    <div className="page-enter p-8 max-w-6xl mx-auto">
      <div className="flex items-center gap-2 text-slate-400 text-sm mb-6">
        <a onClick={() => nav("/shipping/plans")} className="hover:text-slate-600 cursor-pointer">计划看板</a><span>/</span>
        <span className="text-slate-700 font-medium">新建计划</span>
      </div>
      <h2 className="text-xl font-bold text-slate-800 mb-6">新建计划</h2>
      <div className="space-y-6">
        <div className="grid grid-cols-4 gap-4">
          <div><label className="text-xs text-slate-500 mb-1 block">执行主体</label><SearchableSelect value={companyId} onChange={setCompanyId} options={companies ?? []} className={INP + " !min-w-[200px]"} /></div>
          <div><label className="text-xs text-slate-500 mb-1 block">发货品牌 <span className="text-indigo-500">(主维度)</span></label><SearchableSelect value={brandId} onChange={v => { setBrandId(v); setSupplierId(""); setPurchaseContractId("") }} options={brands?.map(b => ({ id: b.id, name: b.name })) ?? []} className={INP + " !min-w-[200px]"} /></div>
          <div><label className="text-xs text-slate-500 mb-1 block">供方</label><SearchableSelect value={supplierId} onChange={v => { setSupplierId(v); setPurchaseContractId("") }} options={suppliers} disabled={!brandId} className={INP + " !min-w-[200px]"} /></div>
          <div><label className="text-xs text-slate-500 mb-1 block">计划日期</label><input type="date" value={plannedDate} onChange={e => setPlannedDate(e.target.value)} className={INP + " !w-[120px]"} /></div>
        </div>

        <div className="flex items-start gap-4">
          <div className="flex-1">
            <label className="text-xs text-slate-500 mb-1 block">货源采购合同 {brandId && supplierId && <span className="text-slate-400">({filteredPCs.length}个可选, 可发{fmtQty(pcAvailQty)}吨)</span>}</label>
            <PurchaseContractPicker brandId={brandId} supplierId={supplierId} value={purchaseContractId} onChange={v => setPurchaseContractId(v)} allPCs={allPCs ?? []} filteredPCs={filteredPCs} getEntName={getEntName} getBrandName={getBrandName} getWhName={getWhName} getModelName={getModelName} pcUsed={pcUsed} loading={pcsLoading} />
          </div>
          <div><label className="text-xs text-slate-500 mb-1 block">配送方式</label><div className="flex gap-2">{DL_OPTS.map(opt => (<button key={opt.key} onClick={() => setDeliveryMethod(opt.key)} className={`px-4 py-2 rounded-lg text-sm border transition-all ${deliveryMethod === opt.key ? opt.active : opt.color}`}>{opt.label}</button>))}</div></div>
        </div>

        {pcAvailQty > 0 && (
          <div className={`text-xs flex items-center gap-2 px-3 py-2 rounded-lg ${overAvail ? "bg-red-50 text-red-600" : totalQty > 0 ? "bg-emerald-50 text-emerald-600" : "bg-slate-50 text-slate-400"}`}>
            {overAvail ? `⚠️ 计划总量 ${fmtQty(totalQty)}吨 超出合同可发量 ${fmtQty(pcAvailQty)}吨` : `合同可发: ${fmtQty(pcAvailQty)}吨 | 已计划: ${fmtQty(totalQty)}吨 | 剩余: ${fmtQty(Math.max(0, pcAvailQty - totalQty))}吨`}
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-3"><label className="text-sm font-semibold text-slate-700">计划明细（{rows.length}条）</label><button onClick={addRow} className="px-3 py-1.5 text-xs border border-indigo-200 text-indigo-600 rounded-lg hover:bg-indigo-50">+ 添加明细</button></div>
          <div className="space-y-3">
            {rows.map((row, i) => (
              <PlanItemRow key={i} index={i} row={row} updRow={updRow} delRow={delRow} brandData={brandData} brandId={brandId} allEnts={allEnts ?? []} allSCs={allSCs ?? []} scsLoading={scsLoading} getEntName={getEntName} getBrandName={getBrandName} getWhName={getWhName} getModelName={getModelName} rowsCount={rows.length} scUsed={scUsed} />
            ))}
          </div>
        </div>

        <div><label className="text-xs text-slate-500 mb-1 block">备注</label><textarea rows={3} value={remark} onChange={e => setRemark(e.target.value)} className={INP + " !w-4/5"} /></div>

        <div className="sticky bottom-0 bg-white border-t border-slate-200 p-4 -mx-8 -mb-8 flex items-center justify-between">
          <div className="text-sm text-slate-500">计划总量: <span className={`font-bold text-lg ${overAvail ? "text-red-600" : "text-slate-800"}`}>{fmtQty(totalQty)}吨</span>{pcAvailQty > 0 && <span className="text-slate-400 ml-1">/ {fmtQty(pcAvailQty)}吨</span>}<span className="mx-2">|</span>{rows.length}条明细<span className="mx-2">|</span>{brands?.find(b => b.id === brandId)?.name ?? ""}{supplierId && <span className="text-slate-400 ml-1">→ {getEntName(supplierId)}</span>}{selectedPC && <span className="text-slate-400 ml-1">→ {selectedPC.contract_no}</span>}</div>
          <div className="flex gap-3"><button onClick={() => nav("/shipping/plans")} className="px-6 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm hover:bg-slate-50">取消</button><button onClick={() => mut.mutate()} disabled={!ok || mut.isPending} className={`px-6 py-2.5 rounded-xl text-sm font-medium transition-all ${ok ? "bg-indigo-600 text-white hover:bg-indigo-700" : "bg-slate-200 text-slate-400 cursor-not-allowed"}`}>{mut.isPending ? "提交中..." : "提交创建计划"}</button></div>
        </div>
      </div>
    </div>
  )
}


/** 采购合同选择器 —— 显示每条明细的品牌/仓库/可发数量 */
function PurchaseContractPicker({ brandId, supplierId, value, onChange, allPCs, filteredPCs, getEntName, getBrandName, getWhName, getModelName, pcUsed, loading }: {
  brandId: string; supplierId: string; value: string; onChange: (v: string) => void;
  allPCs: PC[]; filteredPCs: PC[]; getEntName: (id: string) => string;
  getBrandName: (id: string) => string; getWhName: (id: string) => string;
  getModelName: (id: string) => string;
  pcUsed: Record<string, number>; loading: boolean
}) {
  const [open, setOpen] = useState(false); const [search, setSearch] = useState(""); const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { const fn = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }; document.addEventListener("mousedown", fn); return () => document.removeEventListener("mousedown", fn) }, [])
  const selected = allPCs.find(pc => pc.id === value)
  const filtered = search ? filteredPCs.filter(pc => pc.contract_no.toLowerCase().includes(search.toLowerCase())) : filteredPCs

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(p => !p)} disabled={!brandId || !supplierId} className={`${INP} text-left flex items-center justify-between ${!brandId || !supplierId ? "text-slate-300" : ""}`}>
        <span className={selected ? "text-slate-700" : "text-slate-400"}>{(loading ? "加载中..." : selected ? (() => { const it = selected.items.find(i => !brandId || i.brand_id === brandId); const used = pcUsed[selected.id] ?? 0; const avail = it ? Math.max(0, it.quantity - used) : 0; return `${selected.contract_no} | ${getBrandName(it?.brand_id ?? "")} | ${getWhName(it?.shipping_warehouse_id ?? "")} | ${getModelName(it?.model_id ?? "")} | 可发${fmtQty(avail)}吨` })() : (brandId && supplierId ? `点击选择 (${filteredPCs.length}个合同)...` : "请先选品牌+供方"))}</span>
        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-[520px] bg-white border border-slate-200 rounded-xl shadow-2xl z-50 max-h-80 overflow-hidden flex flex-col">
          <div className="p-3 border-b border-slate-100"><input value={search} onChange={e => setSearch(e.target.value)} className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20" autoFocus onClick={e => e.stopPropagation()} /></div>
          <div className="overflow-y-auto flex-1">
            {filtered.length === 0 && <div className="px-4 py-8 text-sm text-slate-400 text-center">{search ? `未找到包含"${search}"的合同` : "该品牌+供方下无可发采购合同"}</div>}
            {filtered.map(pc => (
              <button key={pc.id} onClick={() => { onChange(pc.id); setOpen(false); setSearch("") }} className={`w-full text-left px-4 py-3 text-xs hover:bg-indigo-50 transition-colors border-b border-slate-100 ${value === pc.id ? "bg-indigo-50 text-indigo-700" : "text-slate-700"}`}>
                <div className="font-semibold text-sm mb-1.5">{pc.contract_no}</div>
                <div className="space-y-0.5">
                  {pc.items.filter(it => !brandId || it.brand_id === brandId).map((it, idx) => {
                    const used = pcUsed[pc.id] ?? 0
                    const avail = Math.max(0, it.quantity - used)
                    return (
                    <div key={idx} className="flex items-center gap-2 text-slate-500 bg-slate-50 rounded px-2 py-1">
                      <span className="px-1 py-0.5 rounded font-medium text-white" style={{ backgroundColor: "#6366f1" }}>{getBrandName(it.brand_id)}</span>
                      <span className="text-slate-400 text-[10px]">型号</span><span>{getModelName(it.model_id)}</span>
                      <span className="text-slate-400 text-[10px]">仓库</span><span>{getWhName(it.shipping_warehouse_id)}</span>
                      <span className="text-slate-400 text-[10px]">可发</span><span className={`font-semibold ${avail > 0 ? "text-emerald-600" : "text-red-400"}`}>{fmtQty(avail)}</span>
                      <span className="flex-1 text-right text-slate-400">¥{it.purchase_price}/吨</span>
                    </div>
                  )})}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}


/** 计划明细行 */
function PlanItemRow({ index, row, updRow, delRow, brandData, brandId, allEnts, allSCs, scsLoading, getEntName, getBrandName, getWhName, getModelName, rowsCount, scUsed }: {
  index: number; row: PlanRow; updRow: (i: number, f: keyof PlanRow, v: any) => void; delRow: (i: number) => void
  brandData: { models: BM[]; warehouses: BW[] }; brandId: string; allEnts: E[]; allSCs: SC[]; scsLoading: boolean
  getEntName: (id: string) => string; getBrandName: (id: string) => string; getWhName: (id: string) => string; getModelName: (id: string) => string; rowsCount: number
  scUsed: Record<string, number>
}) {
  const models = brandData.models; const warehouses = brandData.warehouses
  const scList = row.customer_enterprise_id ? allSCs.filter(sc => sc.customer_enterprise_id === row.customer_enterprise_id) : []

  return (
    <div className="border border-slate-200 rounded-xl p-4 bg-white">
      <div className="flex items-center gap-2 mb-3"><span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">#{index + 1}</span>{row.surcharge_type === "carbonate_transfer" && <span className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded">⚠️碳酸料 +100</span>}<div className="flex-1" />{rowsCount > 1 && <button onClick={() => delRow(index)} className="text-xs text-red-400 hover:text-red-600">删除</button>}</div>
      <div className="grid grid-cols-5 gap-3">
        <div><label className="text-[10px] text-slate-400 mb-0.5 block">客户</label><SearchableSelect value={row.customer_enterprise_id} onChange={v => updRow(index, "customer_enterprise_id", v)} options={allEnts} className={INP_SM} /></div>
        <div>
          <label className="text-[10px] text-slate-400 mb-0.5 block">销售合同 {row.customer_enterprise_id && (scsLoading ? <span className="text-slate-300">...</span> : <span className="text-slate-300">({scList.length}个)</span>)}</label>
          <SalesContractPicker customerId={row.customer_enterprise_id} brandId={brandId} value={row.sales_contract_id} onChange={v => updRow(index, "sales_contract_id", v)} allSCs={allSCs} getEntName={getEntName} getBrandName={getBrandName} getWhName={getWhName} getModelName={getModelName} scUsed={scUsed} />
        </div>
        <div><label className="text-[10px] text-slate-400 mb-0.5 block">仓库</label><select value={row.warehouse_id} onChange={e => updRow(index, "warehouse_id", e.target.value)} className={INP_SM}><option value="">{brandId ? "选择仓库" : "请先选品牌"}</option>{warehouses.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}</select></div>
        <div><label className="text-[10px] text-slate-400 mb-0.5 block">型号</label><select value={row.model_id} onChange={e => updRow(index, "model_id", e.target.value)} className={INP_SM}><option value="">{brandId ? "选择型号" : "请先选品牌"}</option>{models.map(m => <option key={m.id} value={m.id}>{m.model_name} ({m.model_type})</option>)}</select></div>
        <div><label className="text-[10px] text-slate-400 mb-0.5 block">吨数</label><input type="number" step="0.01" min="0" value={row.planned_quantity || ""} onChange={e => updRow(index, "planned_quantity", Number(e.target.value))} className={INP_SM} /></div>
      </div>
      <div className="flex gap-4 mt-2 text-xs text-slate-400"><span>采购价: ¥{row.purchase_price}</span><span>销售价: ¥{row.sale_price}</span>{row.planned_quantity > 0 && <span>金额: ¥{(row.planned_quantity * row.sale_price).toFixed(2)}</span>}</div>
    </div>
  )
}


/** 销售合同选择器 —— 按客户筛选 + 显示明细品牌/仓库/可发数量 */
function SalesContractPicker({ customerId, brandId, value, onChange, allSCs, getEntName, getBrandName, getWhName, getModelName, scUsed }: {
  customerId: string; brandId: string; value: string; onChange: (v: string) => void;
  allSCs: SC[]; getEntName: (id: string) => string;
  getBrandName: (id: string) => string; getWhName: (id: string) => string;
  getModelName: (id: string) => string;
  scUsed: Record<string, number>
}) {
  const [open, setOpen] = useState(false); const [search, setSearch] = useState(""); const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { const fn = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }; document.addEventListener("mousedown", fn); return () => document.removeEventListener("mousedown", fn) }, [])
  // 按客户筛选
  const list = allSCs.filter(sc => {
    if (customerId && sc.customer_enterprise_id !== customerId) return false
    return true
  })
  const filtered = search ? list.filter(sc => sc.contract_no.toLowerCase().includes(search.toLowerCase())) : list
  const selected = allSCs.find(sc => sc.id === value)

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(p => !p)} disabled={!customerId} className={`${INP_SM} text-left flex items-center justify-between ${!customerId ? "text-slate-300" : ""}`}>
        <span className={selected ? "text-slate-700" : "text-slate-400"}>{selected ? selected.contract_no : (customerId ? "点击选择合同..." : "请先选客户")}</span>
        <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-[460px] bg-white border border-slate-200 rounded-xl shadow-2xl z-50 max-h-72 overflow-hidden flex flex-col">
          <div className="p-2 border-b border-slate-100"><input value={search} onChange={e => setSearch(e.target.value)} className="w-full px-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20" autoFocus onClick={e => e.stopPropagation()} /></div>
          <div className="overflow-y-auto flex-1">
            {filtered.length === 0 && <div className="px-4 py-6 text-xs text-slate-400 text-center">{search ? `未找到包含"${search}"的合同` : (customerId ? "该客户无可提销售合同" : "请先选择客户")}</div>}
            {filtered.map(sc => (
              <button key={sc.id} onClick={() => { onChange(sc.id); setOpen(false); setSearch("") }} className={`w-full text-left px-4 py-3 text-xs hover:bg-indigo-50 transition-colors border-b border-slate-100 ${value === sc.id ? "bg-indigo-50 text-indigo-700" : "text-slate-700"}`}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-semibold text-sm">{sc.contract_no}</span>
                  <span className="text-slate-500">{getEntName(sc.customer_enterprise_id)}</span>
                </div>
                <div className="space-y-0.5">
                  {sc.items.map((it, idx) => {
                    const used = scUsed[sc.id] ?? 0
                    const avail = Math.max(0, it.quantity - used)
                    return (
                    <div key={idx} className="flex items-center gap-2 text-slate-500 bg-slate-50 rounded px-2 py-1">
                      <span className="px-1 py-0.5 rounded font-medium text-white" style={{ backgroundColor: "#6366f1" }}>{getBrandName(it.brand_id)}</span>
                      <span className="text-slate-400">仓库:</span><span>{getWhName(it.shipping_warehouse_id)}</span>
                      <span className="text-slate-400">型号:</span><span>{getModelName(it.model_id)}</span>
                      <span className="text-slate-400 text-[10px]">可提:</span><span className={`font-semibold ${avail > 0 ? "text-emerald-600" : "text-red-400"}`}>{fmtQty(avail)}</span>
                      <span className="flex-1 text-right text-slate-700">{fmtQty(it.quantity)}吨</span>
                      <span className="text-slate-400">¥{it.sale_price}/吨</span>
                    </div>
                  )})}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
