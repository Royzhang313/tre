/** 采购合同详情 V2 */
import { useState, useEffect, useRef } from "react"
import { useParams, Link, useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiDelete } from "../../api/client"
import { AuditTimeline } from "../../components/shared/AuditTimeline"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

interface E { id: string; name: string }
interface W { id: string; name: string }
interface Item { id: string; line_no: number; brand_id: string; model_id: string; shipping_warehouse_id: string; quantity: number; unit: string; purchase_price: number; amount: number; tax_rate: number; storage_fee_price: number; commission_fee_price: number; commission_fee: number }
interface Detail { id: string; contract_no: string; supplier_enterprise_id: string; contract_date: string; contract_start_date: string; contract_end_date: string; attachment_path: string | null; status: string; total_quantity: number; total_amount: number; delivery_progress: number; payment_progress: number; remark: string | null; created_at: string; items: Item[] }

const STATUS: Record<string, { l: string; c: string }> = {
  pending_execution: { l: "待执行", c: "bg-amber-50 text-amber-700 border-amber-200" },
  in_progress: { l: "执行中", c: "bg-blue-50 text-blue-700 border-blue-200" },
  completed: { l: "已完成", c: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  cancelled: { l: "已作废", c: "bg-slate-100 text-slate-400 border-slate-200" },
}

export function PurchaseContractDetail() {
  const { id } = useParams<{ id: string }>()
  const nav = useNavigate(); const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ["pc-detail", id], queryFn: () => apiGet<Detail>(`/purchase-contracts/${id}`), enabled: !!id })
  const { data: ents } = useQuery({ queryKey: ["ents"], queryFn: async () => { const r = await apiGet<{ items: E[] }>("/basedata/enterprises?page=1&page_size=100"); return r.items } })
  const { data: brands } = useQuery({ queryKey: ["brands"], queryFn: async () => { const r = await apiGet<{ items: { id: string; name: string }[] }>("/brand/brands?page=1&page_size=100"); return r.items } })

  // 按需加载品牌仓库和型号名称
  const [nameMap, setNameMap] = useState<{ warehouses: Record<string, string>; models: Record<string, string> }>({ warehouses: {}, models: {} })
  useEffect(() => {
    if (!data?.items) return
    const brandIds = [...new Set(data.items.map(it => it.brand_id).filter(Boolean))]
    brandIds.forEach(async (bid) => {
      const [wRes, mRes] = await Promise.all([
        fetch(`/api/v1/brand/brands/${bid}/warehouses?page=1&page_size=100`),
        fetch(`/api/v1/brand/brands/${bid}/models?page=1&page_size=100`),
      ])
      const [wJson, mJson] = await Promise.all([wRes.json(), mRes.json()])
      setNameMap(p => ({
        warehouses: { ...p.warehouses, ...Object.fromEntries((wJson?.data?.items ?? []).map((bw: any) => [bw.id, bw.name])) },
        models: { ...p.models, ...Object.fromEntries((mJson?.data?.items ?? []).map((bm: any) => [bm.id, bm.model_name])) },
      }))
    })
  }, [data])

  const en = (eid: string) => ents?.find(e => e.id === eid)?.name ?? ""
  const wn = (wid: string) => nameMap.warehouses[wid] ?? ""
  const mn = (mid: string) => nameMap.models[mid] ?? ""
  const bn = (bid: string) => brands?.find(b => b.id === bid)?.name ?? ""
  const del = useMutation({ mutationFn: () => apiDelete(`/purchase-contracts/${id!}`), onSuccess: () => { qc.invalidateQueries({ queryKey: ["pc"] }); nav("/purchase-contracts") } })
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!menuOpen) return
    const fn = (e: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false) }
    document.addEventListener("mousedown", fn)
    return () => document.removeEventListener("mousedown", fn)
  }, [menuOpen])

  if (isLoading) return <div className="flex items-center justify-center h-96"><svg className="animate-spin w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg></div>
  if (!data) return <div className="text-center py-24 text-slate-400">合同不存在</div>
  const s = STATUS[data.status] ?? { l: data.status, c: "bg-slate-100 text-slate-600 border-slate-200" }

  return (
    <div className="page-enter p-8 max-w-7xl mx-auto">
      <div className="flex items-center gap-2 text-slate-400 text-sm mb-2">
        <a onClick={() => nav("/")} className="hover:text-slate-600 cursor-pointer">首页</a><span>/</span>
        <a onClick={() => nav("/purchase-contracts")} className="hover:text-slate-600 cursor-pointer">采购合同</a><span>/</span>
        <span className="text-slate-700 font-medium">{data.contract_no}</span>
      </div>
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-slate-900">{data.contract_no}</h1>
          <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border ${s.c}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${data.status==="pending_execution"?"bg-amber-400":data.status==="in_progress"?"bg-blue-400":data.status==="completed"?"bg-emerald-400":"bg-slate-300"}`} />{s.l}
          </span>
        </div>
        <div className="flex items-center gap-2" ref={menuRef}>
          <Link to={`/purchase-contracts/${id}/edit`} className="px-4 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">编辑</Link>
          <div className="relative">
            <button onClick={() => setMenuOpen(p => !p)} className="w-9 h-9 flex items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/></svg>
            </button>
            {menuOpen && (
              <div className="absolute right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-xl z-50 py-1 min-w-[120px]">
                <button onClick={async () => { setMenuOpen(false); if (sysConfirm("确定作废？")) del.mutate() }} className="w-full text-left px-4 py-2.5 text-sm text-rose-600 hover:bg-rose-50 transition-colors">作废</button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="col-span-2 bg-white rounded-xl border border-slate-200/60 shadow-sm p-5">
          <h2 className="text-sm font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">基本信息</h2>
          <div className="grid grid-cols-2 gap-x-8 gap-y-3">
            {[["合同编号", data.contract_no], ["供方", en(data.supplier_enterprise_id)], ["签订日期", data.contract_date], ["合同期限", `${data.contract_start_date} ~ ${data.contract_end_date}`], ["备注", data.remark || ""], ["创建日期", data.created_at?.slice(0, 10)]].map(([l, v]) => (
              <div key={l as string} className="flex items-center gap-3">
                <span className="text-xs text-slate-400 w-16 shrink-0">{l}</span>
                <span className="text-sm font-medium text-slate-800">{v}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-5">
          <h2 className="text-sm font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">执行进度</h2>
          <div className="space-y-5">
            {[["发货进度", data.delivery_progress, "from-blue-500 to-indigo-500"], ["付款进度", data.payment_progress, "from-emerald-500 to-teal-500"]].map(([l, pct, g]) => (
              <div key={l as string}><div className="flex justify-between text-sm mb-1.5"><span className="text-slate-500">{l}</span><span className="font-semibold text-slate-700">{pct as number}%</span></div><div className="h-2 bg-slate-100 rounded-full overflow-hidden"><div className={`h-full bg-gradient-to-r ${g} rounded-full`} style={{ width: `${pct}%` }} /></div></div>
            ))}
          </div>
        </div>
      </div>

      {/* 商品明细 */}
      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-5 mb-8">
        <h2 className="text-sm font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">商品明细 <span className="text-xs text-slate-400 font-normal">{data.items.length} 项</span></h2>
        <table className="w-full text-sm">
          <thead><tr className="border-y border-slate-100">{["#", "品牌", "型号", "发货仓库", "数量(吨)", "单价", "金额", "税率", "库费单价", "撮合费单价", "撮合费"].map(h => (<th key={h} className={`px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider ${["数量(吨)","单价","金额","税率","库费单价","撮合费单价","撮合费"].includes(h)?"text-right":"text-left"}`}>{h}</th>))}</tr></thead>
          <tbody>
            {data.items.map(it => (
              <tr key={it.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                <td className="px-4 py-3.5 text-xs text-slate-400">{it.line_no}</td>
                <td className="px-4 py-3.5 font-semibold text-slate-800">{bn(it.brand_id)}</td>
                <td className="px-4 py-3.5 text-slate-600">{mn(it.model_id)}</td>
                <td className="px-4 py-3.5 text-slate-600">{wn(it.shipping_warehouse_id)}</td>
                <td className="px-4 py-3.5 text-right text-slate-700 tabular-nums">{it.quantity.toLocaleString()}</td>
                <td className="px-4 py-3.5 text-right text-slate-700 tabular-nums">¥{it.purchase_price.toLocaleString()}</td>
                <td className="px-4 py-3.5 text-right font-semibold text-slate-900 tabular-nums">¥{it.amount.toLocaleString()}</td>
                <td className="px-4 py-3.5 text-right text-slate-500">{it.tax_rate}%</td>
                <td className="px-4 py-3.5 text-right text-slate-500 tabular-nums">¥{it.storage_fee_price.toLocaleString()}</td>
                <td className="px-4 py-3.5 text-right text-slate-500 tabular-nums">¥{it.commission_fee_price.toLocaleString()}</td>
                <td className="px-4 py-3.5 text-right text-slate-500 tabular-nums">¥{it.commission_fee.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-5">
        <div className="flex items-center gap-12">
          <div><span className="text-xs text-slate-400">合计数量</span><p className="text-2xl font-bold text-slate-900 mt-1 tabular-nums">{data.total_quantity.toLocaleString()} <span className="text-sm font-normal text-slate-400">吨</span></p></div>
          <div><span className="text-xs text-slate-400">合计金额</span><p className="text-2xl font-bold text-rose-600 mt-1 tabular-nums">¥{data.total_amount.toLocaleString()}</p></div>
        </div>
      </div>

      <AuditTimeline entityType="purchase_contract" entityId={data.id} />
    </div>
  )
}
