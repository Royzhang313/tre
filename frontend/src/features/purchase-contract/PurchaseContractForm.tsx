/** 采购合同表单 V2 —— 品牌/仓库/型号联动 */
import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate, useParams } from "react-router-dom"
import { apiGet, apiPost, apiPut } from "../../api/client"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"
import { AttachmentField, type AttachFile } from "../../components/shared/AttachmentField"
import { DatePicker } from "../../components/shared/DatePicker"
import { SearchableSelect } from "../../components/shared/SearchableSelect"
import { AddEnterpriseModal } from "../../components/shared/AddEnterpriseModal"
import { AddCommissionPlatformModal } from "../../components/shared/AddCommissionPlatformModal"

interface E { id: string; name: string; enterprise_type: string }
interface B { id: string; name: string; code: string }
interface Item { brand_id: string; model_id: string; shipping_warehouse_id: string; quantity: number; unit: string; purchase_price: number; amount: number; tax_rate: number; storage_fee_price: number; commission_fee_price: number; commission_fee: number }

const EMPTY: Item = { brand_id: "", model_id: "", shipping_warehouse_id: "", quantity: 0, unit: "吨", purchase_price: 0, amount: 0, tax_rate: 13, storage_fee_price: 0, commission_fee_price: 0, commission_fee: 0 }
const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"

export function PurchaseContractForm() {
  const { id } = useParams<{ id: string }>()
  const nav = useNavigate()
  const qc = useQueryClient()
  const isEdit = Boolean(id)

  const [companyId, setCompanyId] = useState("")
  const [contractNo, setContractNo] = useState("")
  const [contractNoError, setContractNoError] = useState("")
  const [sid, setSid] = useState("")
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [remark, setRemark] = useState("")
  const [commissionPlatformId, setCommissionPlatformId] = useState("")
  const [deposit, setDeposit] = useState(0); const [paid, setPaid] = useState(0); const [shipped, setShipped] = useState(0)
  const [attach, setAttach] = useState<AttachFile[]>([])
  const [items, setItems] = useState<Item[]>([{ ...EMPTY }])

  const { data: companies } = useQuery({ queryKey: ["companies"], queryFn: async () => { const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/companies"); return r.items } })
  const { data: allEnts } = useQuery({ queryKey: ["ents"], queryFn: async () => { const r = await apiGet<{ items: E[] }>("/basedata/enterprises?page=1&page_size=200"); return r.items } })
  const { data: brands } = useQuery({ queryKey: ["brands"], queryFn: async () => { const r = await apiGet<{ items: B[] }>("/brand/brands?page=1&page_size=200"); return r.items } })
  const { data: platforms } = useQuery({ queryKey: ["cps"], queryFn: async () => { const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/commission-platforms?page=1&page_size=200"); return r.items } })
  const suppliers = allEnts?.filter(e => {
    const types: string[] = Array.isArray(e.enterprise_type) ? e.enterprise_type : [e.enterprise_type]
    return types.includes("trader") || types.includes("factory")
  }) ?? []

  const checkNo = async (no: string) => {
    if (!no || isEdit) return
    const r = await apiGet<{ exists: boolean }>(`/purchase-contracts/check-contract-no?contract_no=${encodeURIComponent(no)}`)
    setContractNoError(r.exists ? "合同编号已存在" : "")
  }

  useEffect(() => {
    if (!id) return
    apiGet<{ commission_platform_id: string | null; company_id: string; contract_no: string; supplier_enterprise_id: string; contract_date: string; contract_start_date: string; contract_end_date: string; attachment_path: string | null; remark: string | null; items: Item[] }>(`/purchase-contracts/${id}`).then(d => {
      setCommissionPlatformId(d.commission_platform_id ?? ""); setCompanyId(d.company_id ?? ""); setContractNo(d.contract_no); setSid(d.supplier_enterprise_id); setDate(d.contract_date)
      setStartDate(d.contract_start_date); setEndDate(d.contract_end_date)
      setAttach(Array.isArray(d.attachment_path) ? d.attachment_path : [])
      setRemark(d.remark ?? "")
      const its = d.items.map(i => ({ ...i, brand_id: i.brand_id ?? "", model_id: i.model_id ?? "", shipping_warehouse_id: i.shipping_warehouse_id ?? "" }))
      setItems(its)
      // 预加载所有品牌数据
      its.forEach(it => { if (it.brand_id) loadBrandData(it.brand_id) })
    })
  }, [id])

  const upd = (i: number, f: keyof Item, v: string | number) => {
    setItems(p => { const n = [...p]; const it = { ...n[i], [f]: v }; if (f === "quantity" || f === "purchase_price") it.amount = Number((it.quantity * it.purchase_price).toFixed(2)); n[i] = it; return n })
  }

  const tQty = items.reduce((s, i) => s + i.quantity, 0)
  const tAmt = items.reduce((s, i) => s + i.amount, 0)

  const mut = useMutation({
    mutationFn: async () => {
      const body = { company_id: companyId, contract_no: contractNo, supplier_enterprise_id: sid, commission_platform_id: commissionPlatformId || null, contract_date: date, contract_start_date: startDate, contract_end_date: endDate, attachment_path: attach.length > 0 ? attach : null, remark: remark || null, items }
      return isEdit ? apiPut(`/purchase-contracts/${id}`, body) : apiPost("/purchase-contracts", body)
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["pc-detail"] }); qc.invalidateQueries({ queryKey: ["purchase-contracts"] }); nav("/purchase-contracts") },
    onError: (err: any) => sysToast("保存失败: " + (err?.message || "未知错误"), "error"),
  })

  const ok = companyId && contractNo && !contractNoError && sid && startDate && endDate && !items.some(i => !i.brand_id || i.quantity <= 0)

  const [brandData, setBrandData] = useState<Record<string, { models: { id: string; model_name: string }[]; warehouses: { id: string; name: string }[] }>>({})
  const loadBrandData = async (brandId: string) => {
    if (!brandId || brandData[brandId]) return
    try {
      const [mResp, wResp] = await Promise.all([
        fetch(`/api/v1/brand/brands/${brandId}/models?page=1&page_size=100`),
        fetch(`/api/v1/brand/brands/${brandId}/warehouses?page=1&page_size=100`),
      ])
      const [mJson, wJson] = await Promise.all([mResp.json(), wResp.json()])
      const models = mJson?.data?.items ?? []
      const warehouses = wJson?.data?.items ?? []
      setBrandData(p => ({ ...p, [brandId]: { models, warehouses } }))
    } catch (e) { console.error("loadBrandData error", e) }
  }

  return (
    <div className="page-enter p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
        <a onClick={() => nav("/")} className="hover:text-slate-600 cursor-pointer">首页</a><span>/</span>
        <a onClick={() => nav("/purchase-contracts")} className="hover:text-slate-600 cursor-pointer">采购合同</a><span>/</span>
        <span className="text-slate-700 font-medium">{isEdit ? "编辑" : "新增"}</span>
      </div>
      <h1 className="text-xl font-bold text-slate-900 mb-5">{isEdit ? "编辑采购合同" : "新增采购合同"}</h1>

      {/* 基本信息 */}
      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-5 mb-4">
        <h2 className="text-sm font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">基本信息</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-3">
          <div className="flex items-center gap-3 col-span-2">
            <span className="text-xs text-slate-400 w-16 shrink-0">合同编号 {!contractNo && <span className="text-rose-400">*</span>}</span>
            <input value={contractNo} onChange={e => { setContractNo(e.target.value); checkNo(e.target.value) }} onBlur={e => checkNo(e.target.value)}
              disabled={isEdit} className={INP + " !w-60" + (contractNoError ? " border-rose-300" : "") + (isEdit ? " text-slate-400 cursor-not-allowed" : "")} />
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-16 shrink-0">主体公司 {!companyId && <span className="text-rose-400">*</span>}</span>
            <SearchableSelect value={companyId} onChange={setCompanyId} options={companies ?? []} className={INP + " !min-w-[200px]"} />
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-16 shrink-0">签订日期 {!date && <span className="text-rose-400">*</span>}</span>
            <div className="!w-[120px]"><DatePicker value={date} onChange={setDate} /></div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-16 shrink-0">供方 {!sid && <span className="text-rose-400">*</span>}</span>
            <SearchableSelect value={sid} onChange={v => setSid(v)} options={suppliers} className={INP + " !min-w-[200px]"} />
            <AddEnterpriseModal onAdded={(newId) => setSid(newId)} defaultTypes={["trader"]} title="新增供方" />
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-16 shrink-0">撮合</span>
            <SearchableSelect value={commissionPlatformId} onChange={setCommissionPlatformId} options={platforms ?? []} className={INP + " !min-w-[200px]"} />
            <AddCommissionPlatformModal onAdded={(newId) => setCommissionPlatformId(newId)} />
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-16 shrink-0">开始日期 {!startDate && <span className="text-rose-400">*</span>}</span>
            <div className="!w-[120px]"><DatePicker value={startDate} onChange={setStartDate} /></div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-16 shrink-0">结束日期 {!endDate && <span className="text-rose-400">*</span>}</span>
            <div className="!w-[120px]"><DatePicker value={endDate} onChange={setEndDate} /></div>
          </div>
        </div>

        <div className="flex items-start gap-8 mt-3 pt-3 border-t border-slate-100">
          <div className="flex items-start gap-3 flex-1">
            <span className="text-xs text-slate-400 w-16 shrink-0 pt-1.5">备注</span>
            <textarea value={remark} onChange={e => setRemark(e.target.value)} rows={3} className={INP + " flex-1 resize-none"} />
          </div>
          <div className="flex items-start gap-3 flex-1">
            <span className="text-xs text-slate-400 w-16 shrink-0 pt-1.5">合同附件</span>
            <AttachmentField files={attach} onChange={setAttach} />
          </div>
        </div>
      </div>

      {/* 商品明细 */}
      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-5 mb-4">
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-100">
          <h2 className="text-sm font-semibold text-slate-800">商品明细 <span className="text-xs text-slate-400 font-normal ml-1">{items.length} 项</span></h2>
          <button onClick={() => setItems(p => [...p, { ...EMPTY }])}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-colors">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>添加
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-y border-slate-100">
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-left w-6">#</th>
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-left">品牌 <span className="text-rose-400">*</span></th>
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-left">仓库</th>
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-left">型号</th>
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-right">数量(吨) <span className="text-rose-400">*</span></th>
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-right w-20">采购单价 <span className="text-rose-400">*</span></th>
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-right w-24">金额</th>
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-right w-20">库费单价</th>
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-right w-20">撮合费单价</th>
                <th className="px-2.5 py-2 text-xs font-semibold text-slate-400 text-right w-20">撮合费</th>
                <th className="px-2.5 py-2 w-8"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((it, i) => {
                const bd = brandData[it.brand_id]
                const availModels = bd?.models ?? []
                const availWhs = bd?.warehouses ?? []
                return (
                  <tr key={i} className="border-b border-slate-50 hover:bg-indigo-50/20 transition-colors group">
                    <td className="px-2.5 py-1.5 text-xs text-slate-400 font-medium">{i + 1}</td>
                    <td className="px-2.5 py-1.5 w-28">
                      <SearchableSelect value={it.brand_id} onChange={v => { upd(i, "brand_id", v); upd(i, "model_id", ""); if (v) loadBrandData(v) }} options={(brands ?? []).map(b => ({ id: b.id, name: b.name }))} className={INP} />
                    </td>
                    <td className="px-2.5 py-1.5 w-32">
                      <SearchableSelect value={it.shipping_warehouse_id} onChange={v => upd(i, "shipping_warehouse_id", v)} options={availWhs.map(w => ({ id: w.id, name: w.name }))} className={INP} />
                    </td>
                    <td className="px-2.5 py-1.5 w-28">
                      <SearchableSelect value={it.model_id} onChange={v => upd(i, "model_id", v)} options={availModels.map(m => ({ id: m.id, name: m.model_name }))} disabled={!it.brand_id} className={INP} />
                    </td>
                    <td className="px-2.5 py-1.5 w-20"><input type="number" step="0.01" value={it.quantity || ""} onChange={e => upd(i, "quantity", parseFloat(e.target.value) || 0)} className={INP + " text-right"} /></td>
                    <td className="px-2.5 py-1.5 w-24"><input type="number" step="0.01" value={it.purchase_price || ""} onChange={e => upd(i, "purchase_price", parseFloat(e.target.value) || 0)} className={INP + " text-right"} /></td>
                    <td className="px-2.5 py-1.5 w-24 text-right font-semibold text-slate-900 tabular-nums">{"¥"}{it.amount.toLocaleString()}</td>
                    <td className="px-2.5 py-1.5 w-20"><input type="number" step="0.01" value={it.storage_fee_price || ""} onChange={e => upd(i, "storage_fee_price", parseFloat(e.target.value) || 0)} className={INP + " text-right"} /></td>
                    <td className="px-2.5 py-1.5 w-20"><input type="number" step="0.01" value={it.commission_fee_price || ""} onChange={e => upd(i, "commission_fee_price", parseFloat(e.target.value) || 0)} className={INP + " text-right"} /></td>
                    <td className="px-2.5 py-1.5 w-20"><input type="number" step="0.01" value={it.commission_fee || ""} onChange={e => upd(i, "commission_fee", parseFloat(e.target.value) || 0)} className={INP + " text-right"} /></td>
                    <td className="px-2.5 py-1.5 w-6">
                      <button onClick={() => { if (items.length > 1) setItems(p => p.filter((_, j) => j !== i)) }}
                        className="w-6 h-6 rounded-md hover:bg-rose-50 text-slate-300 hover:text-rose-500 flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 底部操作栏 */}
      <div className="sticky bottom-4 bg-white/95 backdrop-blur-xl rounded-xl border border-slate-200/60 shadow-lg shadow-slate-200/30 p-5 flex items-center">
        <div className="flex items-center gap-8">
          <div><span className="text-xs text-slate-400">合计数量</span><p className="text-lg font-bold text-slate-900 tabular-nums">{tQty.toLocaleString()} <span className="text-sm font-normal text-slate-400">吨</span></p></div>
          <div><span className="text-xs text-slate-400">合计金额</span><p className="text-lg font-bold text-rose-600 tabular-nums">{"¥"}{tAmt.toLocaleString()}</p></div>
          <div className="w-px h-10 bg-slate-200" />
          <div><span className="text-xs text-slate-400">合同定金</span><p className="text-sm text-slate-700 tabular-nums">{deposit.toLocaleString()}</p></div>
          <div><span className="text-xs text-slate-400">已付</span><p className="text-sm text-slate-700 tabular-nums">{paid.toLocaleString()}</p></div>
          <div><span className="text-xs text-slate-400">已发</span><p className="text-sm text-slate-700 tabular-nums">{shipped.toLocaleString()}</p></div>
          <div className="w-28">
            <div className="flex justify-between text-xs mb-0.5"><span className="text-slate-400">付款比例</span><span className="text-slate-500">{tAmt > 0 ? Math.round(paid / tAmt * 100) : 0}%</span></div>
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full" style={{width: `${tAmt > 0 ? Math.min(paid / tAmt * 100, 100) : 0}%`}} /></div>
          </div>
          <div className="w-28">
            <div className="flex justify-between text-xs mb-0.5"><span className="text-slate-400">发货比例</span><span className="text-slate-500">{tQty > 0 ? Math.round(shipped / tQty * 100) : 0}%</span></div>
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full" style={{width: `${tQty > 0 ? Math.min(shipped / tQty * 100, 100) : 0}%`}} /></div>
          </div>
        </div>
        <div className="flex-1" />
        <button onClick={() => nav("/purchase-contracts")} className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors shrink-0">取消</button>
        <button onClick={() => mut.mutate()} disabled={!ok || mut.isPending}
          className="px-5 py-2 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-lg text-sm font-semibold hover:from-indigo-700 hover:to-blue-700 disabled:from-slate-300 disabled:to-slate-300 disabled:cursor-not-allowed transition-all shadow-sm shadow-indigo-200 shrink-0">
          {mut.isPending ? "保存中..." : isEdit ? "保存修改" : "保存合同"}
        </button>
      </div>
    </div>
  )
}
