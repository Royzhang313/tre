/** AR 应收账款台账 */
import { useState, useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiDelete } from "../../api/client"
import { Pagination } from "../../components/shared/Pagination"
import { SearchableSelect } from "../../components/shared/SearchableSelect"
import { AuditTimeline } from "../../components/shared/AuditTimeline"
import { fmtMoney } from "../../lib/utils"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

interface Receipt { id: string; receipt_no: string; bp_id: string; type: string; amount: number; receipt_date: string; method: string; status: string; remark: string | null }

const TYPE_LABELS: Record<string, string> = {
  deposit: "定金", goods: "货款", balance: "尾款", prepay: "预付款",
  guarantee: "保证金", bank_acceptance: "银行承兑", com_acceptance: "商业承兑",
}
const STATUS_LABELS: Record<string, string> = { pending: "待确认", confirmed: "已确认", voided: "已作废" }

export function ARLedger() {
  const [page, setPage] = useState(1); const [pageSize, setPageSize] = useState(50)
  const [fBpId, setFBpId] = useState(""); const [fStatus, setFStatus] = useState("")
  const [detail, setDetail] = useState<Receipt | null>(null)
  const qc = useQueryClient()

  const { data: receipts, isLoading } = useQuery({
    queryKey: ["ar-receipts", page, pageSize],
    queryFn: async () => apiGet<{ items: Receipt[]; total: number; pages: number }>(`/finance/ar/receipts?page=${page}&page_size=${pageSize}`),
  })
  const { data: enterprises } = useQuery({
    queryKey: ["ents-ar"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/enterprises?page=1&page_size=200")
      const m: Record<string, string> = {}; for (const e of r.items ?? []) m[e.id] = e.name; return m
    },
  })

  const bpOptions = useMemo(() => {
    const seen = new Set<string>()
    return (receipts?.items ?? []).filter(r => { if (seen.has(r.bp_id)) return false; seen.add(r.bp_id); return true }).map(r => ({ id: r.bp_id, name: (enterprises ?? {})[r.bp_id] ?? r.bp_id.slice(0, 6) }))
  }, [receipts, enterprises])

  /** 确认收款 */
  const confirmMut = useMutation({
    mutationFn: (id: string) => apiPost(`/finance/ar/receipts/${id}/confirm`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["ar-receipts"] }); setDetail(null) },
  })

  /** 作废收款 */
  const voidMut = useMutation({
    mutationFn: (id: string) => apiDelete(`/finance/ar/receipts/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["ar-receipts"] }); setDetail(null) },
  })

  const filtered = useMemo(() => {
    let items = receipts?.items ?? []
    if (fBpId) items = items.filter(r => r.bp_id === fBpId)
    if (fStatus) items = items.filter(r => r.status === fStatus)
    return items
  }, [receipts, fBpId, fStatus])

  const totalAmount = filtered.reduce((s, r) => s + r.amount, 0)
  const items = receipts?.items ?? []; const total = receipts?.total ?? 0; const pages = receipts?.pages ?? 0

  return (
    <div className="page-enter p-4 sm:p-6 lg:p-8">
      <h1 className="text-xl font-bold text-slate-900 mb-4">应收账款</h1>
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <SearchableSelect value={fBpId} onChange={setFBpId} options={bpOptions} className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs w-40" />
        <select value={fStatus} onChange={e => setFStatus(e.target.value)} className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs w-28">
          <option value="">全部状态</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <div className="text-sm text-slate-500 ml-auto">合计 <b className="text-slate-800">¥{fmtMoney(totalAmount)}</b></div>
      </div>
      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm overflow-x-auto -mx-4 sm:mx-0">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-100 bg-slate-50/50">
            {["编号","客户","类型","金额","日期","方式","状态","备注"].map(h => <th key={h} className="px-3 py-2.5 text-xs font-semibold text-slate-400 text-left">{h}</th>)}
          </tr></thead>
          <tbody>
            {items.map(r => (
              <tr key={r.id} className="border-b border-slate-50 hover:bg-indigo-50/30 cursor-pointer" onClick={() => setDetail(r)}>
                <td className="px-3 py-2.5 text-xs font-semibold text-indigo-600">{r.receipt_no}</td>
                <td className="px-3 py-2.5 text-xs text-slate-700">{(enterprises ?? {})[r.bp_id] ?? r.bp_id.slice(0, 8)}</td>
                <td className="px-3 py-2.5 text-xs text-slate-600">{TYPE_LABELS[r.type] ?? r.type}</td>
                <td className="px-3 py-2.5 text-xs font-semibold text-slate-800">¥{fmtMoney(r.amount)}</td>
                <td className="px-3 py-2.5 text-xs text-slate-600">{r.receipt_date}</td>
                <td className="px-3 py-2.5 text-xs text-slate-500">{r.method === "transfer" ? "转账" : r.method === "cash" ? "现金" : "承兑"}</td>
                <td className="px-3 py-2.5 text-xs"><span className={`px-1.5 py-0.5 rounded-full text-xs ${r.status === "confirmed" ? "bg-emerald-50 text-emerald-600" : r.status === "voided" ? "bg-red-50 text-red-400" : "bg-amber-50 text-amber-600"}`}>{STATUS_LABELS[r.status]}</span></td>
                <td className="px-3 py-2.5 text-xs text-slate-400 max-w-[120px] truncate">{r.remark || ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={pageSize} total={total} pages={pages} onPageChange={setPage} onPageSizeChange={s => { setPageSize(s); setPage(1) }} />

      {/* 详情抽屉 */}
      {detail && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/20" onClick={() => setDetail(null)} />
          <div className="relative w-[480px] bg-white shadow-2xl h-full overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
              <div>
                <h2 className="text-lg font-bold">{detail.receipt_no}</h2>
                <span className="text-xs text-slate-400">{STATUS_LABELS[detail.status]}</span>
              </div>
              <div className="flex items-center gap-2">
                {detail.status === "pending" && (
                  <>
                    <button
                      onClick={() => confirmMut.mutate(detail.id)}
                      disabled={confirmMut.isPending}
                      className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 disabled:opacity-40"
                    >
                      {confirmMut.isPending ? "确认中..." : "确认"}
                    </button>
                    <button
                      onClick={async () => { if (sysConfirm("确定作废此收款？")) voidMut.mutate(detail.id) }}
                      disabled={voidMut.isPending}
                      className="px-3 py-1.5 border border-rose-200 text-rose-600 rounded-lg text-xs font-medium hover:bg-rose-50 disabled:opacity-40"
                    >
                      {voidMut.isPending ? "作废中..." : "作废"}
                    </button>
                  </>
                )}
                {detail.status === "confirmed" && (
                  <button
                    onClick={async () => { if (sysConfirm("确定作废此收款？")) voidMut.mutate(detail.id) }}
                    disabled={voidMut.isPending}
                    className="px-3 py-1.5 border border-rose-200 text-rose-600 rounded-lg text-xs font-medium hover:bg-rose-50 disabled:opacity-40"
                  >
                    {voidMut.isPending ? "作废中..." : "作废"}
                  </button>
                )}
                <button onClick={() => setDetail(null)} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button>
              </div>
            </div>
            <div className="p-6 space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div><span className="text-slate-400 text-xs">客户</span><div className="text-slate-800">{(enterprises ?? {})[detail.bp_id] ?? "—"}</div></div>
                <div><span className="text-slate-400 text-xs">类型</span><div className="text-slate-800">{TYPE_LABELS[detail.type] ?? detail.type}</div></div>
                <div><span className="text-slate-400 text-xs">金额</span><div className="text-slate-800 font-semibold">¥{fmtMoney(detail.amount)}</div></div>
                <div><span className="text-slate-400 text-xs">日期</span><div className="text-slate-800">{detail.receipt_date}</div></div>
                <div><span className="text-slate-400 text-xs">方式</span><div className="text-slate-800">{detail.method === "transfer" ? "转账" : detail.method === "cash" ? "现金" : "承兑"}</div></div>
              </div>
              {detail.remark && <div><span className="text-slate-400 text-xs">备注</span><div className="text-slate-600">{detail.remark}</div></div>}
              <AuditTimeline entityType="ar_receipt" entityId={detail.id} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
