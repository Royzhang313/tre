/** 新增付款 */
import { useState } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { apiGet, apiPost } from "../../api/client"
import { SearchableSelect } from "../../components/shared/SearchableSelect"
import { OCRUpload } from "../../components/shared/OCRUpload"

const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400"
const TYPE_OPTS = [
  { v: "deposit", l: "定金" }, { v: "goods", l: "货款" }, { v: "balance", l: "尾款" },
  { v: "prepay", l: "预付款" }, { v: "guarantee", l: "保证金" },
  { v: "bank_acceptance", l: "银行承兑" }, { v: "com_acceptance", l: "商业承兑" },
  { v: "warehouse_surcharge", l: "库费" }, { v: "commission", l: "撮合费" }, { v: "freight", l: "运费" },
]

export function PaymentForm() {
  const nav = useNavigate()
  const [companyId, setCompanyId] = useState("")
  const [bpId, setBpId] = useState(""); const [type, setType] = useState("goods"); const [amount, setAmount] = useState("")
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10)); const [method, setMethod] = useState("transfer")
  const [bankName, setBankName] = useState(""); const [bankAccount, setBankAccount] = useState("")
  const [remark, setRemark] = useState(""); const [summary, setSummary] = useState("")

  const { data: companies } = useQuery({
    queryKey: ["companies-pf"], queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/companies"); return r.items ?? []
    },
  })

  const { data: enterprises } = useQuery({
    queryKey: ["ents-pf"], queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/enterprises?page=1&page_size=200"); return r.items ?? []
    },
  })

  const mut = useMutation({
    mutationFn: async () => apiPost("/finance/ap/payments", {
      company_id: companyId || null, bp_id: bpId, type, amount: Number(amount),
      payment_date: date, method, bank_name: bankName || null, bank_account: bankAccount || null,
      remark: remark || null, summary: summary || null,
    }),
    onSuccess: () => nav("/finance"),
  })

  const ok = bpId && type && Number(amount) > 0

  /** OCR 识别后自动匹配供方 */
  const handleOCR = (r: {
    amount: number | null; bank_name: string | null; bank_account: string | null
    receiver_name: string | null; payer_name: string | null; date: string | null
    remark: string | null; summary: string | null
  }) => {
    if (r.amount) setAmount(String(r.amount))
    if (r.bank_name) setBankName(r.bank_name)
    if (r.bank_account) setBankAccount(r.bank_account)
    if (r.date) setDate(r.date)
    if (r.remark) setRemark(r.remark)
    if (r.summary) setSummary(r.summary)
    // 自动匹配收款方 → 供方
    if (r.receiver_name && enterprises) {
      const name = r.receiver_name.trim()
      // 尝试精确匹配 / 模糊匹配
      let match = enterprises.find(e => e.name === name)
      if (!match) match = enterprises.find(e => e.name.includes(name) || name.includes(e.name))
      if (match) setBpId(match.id)
    }
  }

  return (
    <div className="page-enter p-6 max-w-xl mx-auto">
      <h1 className="text-xl font-bold text-slate-900 mb-6">新增付款</h1>
      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm p-6 space-y-4">
        <div>
          <label className="block text-xs text-slate-500 mb-1.5">主体公司</label>
          <SearchableSelect value={companyId} onChange={setCompanyId} options={companies ?? []} className={INP + " !min-w-[200px]"} />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1.5">供方 {!bpId && <span className="text-rose-400">*</span>}</label>
          <SearchableSelect value={bpId} onChange={setBpId} options={enterprises ?? []} className={INP + " !min-w-[200px]"} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">付款类型 {!type && <span className="text-rose-400">*</span>}</label>
            <select value={type} onChange={e => setType(e.target.value)} className={INP}>
              {TYPE_OPTS.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">金额 {!amount && <span className="text-rose-400">*</span>}</label>
            <input type="number" value={amount} onChange={e => setAmount(e.target.value)} className={INP} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">付款日期 {!date && <span className="text-rose-400">*</span>}</label>
            <input type="date" value={date} onChange={e => setDate(e.target.value)} className={INP} />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">付款方式</label>
            <select value={method} onChange={e => setMethod(e.target.value)} className={INP}>
              <option value="transfer">转账</option><option value="cash">现金</option><option value="acceptance">承兑</option>
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="block text-xs text-slate-500 mb-1.5">收款银行</label><input value={bankName} onChange={e => setBankName(e.target.value)} className={INP} /></div>
          <div><label className="block text-xs text-slate-500 mb-1.5">收款账号</label><input value={bankAccount} onChange={e => setBankAccount(e.target.value)} className={INP} /></div>
        </div>
        <OCRUpload onResult={handleOCR} />
        <div>
          <label className="block text-xs text-slate-500 mb-1.5">摘要</label>
          <input value={summary} onChange={e => setSummary(e.target.value)} className={INP} placeholder="OCR 识别摘要" />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1.5">备注</label>
          <textarea value={remark} onChange={e => setRemark(e.target.value)} rows={2} className={INP + " resize-none"} />
        </div>
        <div className="flex gap-3 pt-3">
          <button onClick={() => nav("/finance")} className="px-5 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-600 hover:bg-slate-50">取消</button>
          <button onClick={() => mut.mutate()} disabled={!ok || mut.isPending} className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-40">{mut.isPending ? "保存中..." : "保存"}</button>
        </div>
      </div>
    </div>
  )
}
