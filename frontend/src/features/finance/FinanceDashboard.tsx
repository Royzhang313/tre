/** 资金总览 + 统一台账 */
import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link, useNavigate } from "react-router-dom"
import { apiGet } from "../../api/client"
import { Pagination } from "../../components/shared/Pagination"
import { fmtMoney } from "../../lib/utils"

interface LedgerRow {
  id: string; _direction: "ar" | "ap"; _label: string; _date: string; _no: string
  _counterparty_id: string; type: string; amount: number; method: string
  status: string; remark: string | null; summary: string | null
  bank_name: string | null; bank_account: string | null
  company_id: string | null
}

const TYPE_LABELS: Record<string, string> = {
  deposit: "定金", goods: "货款", balance: "尾款", prepay: "预付款",
  guarantee: "保证金", bank_acceptance: "银行承兑", com_acceptance: "商业承兑",
  warehouse_surcharge: "库费", commission: "撮合费", freight: "运费",
}
const STATUS_LABELS: Record<string, string> = { pending: "待确认", confirmed: "已确认", voided: "已作废" }

export function FinanceDashboard() {
  const nav = useNavigate()
  const [page, setPage] = useState(1); const [pageSize, setPageSize] = useState(50)
  const [fDirection, setFDirection] = useState(""); const [fStatus, setFStatus] = useState("")

  const params = new URLSearchParams()
  params.set("page", String(page)); params.set("page_size", String(pageSize))
  if (fDirection) params.set("direction", fDirection)
  if (fStatus) params.set("status", fStatus)

  const { data, isLoading } = useQuery({
    queryKey: ["ledger", page, pageSize, fDirection, fStatus],
    queryFn: async () => apiGet<{
      items: LedgerRow[]; total: number; page: number; pages: number
      ar_total: number; ap_total: number
    }>(`/finance/ledger?${params.toString()}`),
  })

  const { data: enterpriseMap } = useQuery({
    queryKey: ["ents-ledger"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/enterprises?page=1&page_size=200")
      const m: Record<string, string> = {}; for (const e of r.items ?? []) m[e.id] = e.name; return m
    },
  })

  const { data: companyMap } = useQuery({
    queryKey: ["companies-ledger"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/companies")
      const m: Record<string, string> = {}; for (const c of r.items ?? []) m[c.id] = c.name; return m
    },
  })

  const items = data?.items ?? []
  const arTotal = data?.ar_total ?? 0
  const apTotal = data?.ap_total ?? 0

  const bpName = (id: string) => (enterpriseMap ?? {})[id] ?? id.slice(0, 8)
  const coName = (id: string | null) => id ? ((companyMap ?? {})[id] ?? id.slice(0, 8)) : ""

  return (
    <div className="page-enter p-4 max-w-full mx-2">
      {/* KPI 卡片 + 操作按钮 */}
      <div className="flex items-start justify-between mb-3 gap-4 flex-wrap">
        <div className="flex gap-3 flex-wrap">
          <div className="bg-white rounded-lg border border-slate-200/60 px-4 py-2.5">
            <p className="text-xs text-slate-400">收款合计 (AR)</p>
            <p className="text-xl font-bold text-emerald-600">¥{fmtMoney(arTotal)}</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200/60 px-4 py-2.5">
            <p className="text-xs text-slate-400">付款合计 (AP)</p>
            <p className="text-xl font-bold text-rose-600">¥{fmtMoney(apTotal)}</p>
          </div>
          <div className="bg-white rounded-lg border border-slate-200/60 px-4 py-2.5">
            <p className="text-xs text-slate-400">净额</p>
            <p className={`text-xl font-bold ${arTotal >= apTotal ? "text-emerald-600" : "text-rose-600"}`}>¥{fmtMoney(arTotal - apTotal)}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Link to="/finance/ar/new" className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700">+ 收款</Link>
          <Link to="/finance/ap/new" className="px-3 py-1.5 bg-rose-600 text-white rounded-lg text-xs font-medium hover:bg-rose-700">+ 付款</Link>
        </div>
      </div>

      {/* 筛选 */}
      <div className="flex items-center gap-3 mb-3 flex-wrap">
        <select value={fDirection} onChange={e => { setFDirection(e.target.value); setPage(1) }} className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs">
          <option value="">全部方向</option>
          <option value="ar">收款</option>
          <option value="ap">付款</option>
        </select>
        <select value={fStatus} onChange={e => { setFStatus(e.target.value); setPage(1) }} className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs">
          <option value="">全部状态</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <div className="text-xs text-slate-400 ml-auto">共 <b className="text-slate-700">{data?.total ?? 0}</b> 条</div>
      </div>

      {/* 台账表格 */}
      <div className="bg-white rounded-lg border border-slate-200/60 shadow-sm overflow-x-auto">
        {isLoading ? (
          <div className="p-16 text-center text-slate-300">加载中...</div>
        ) : items.length === 0 ? (
          <div className="py-16 text-center text-slate-400">暂无资金记录，点击上方按钮新增收款/付款</div>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="border-b border-slate-100 bg-slate-50/50">
              {["方向","编号","对方","主体公司","类型","金额","日期","方式","银行","状态","摘要","备注"].map(h => (
                <th key={h} className={`px-3 py-2.5 text-xs font-semibold text-slate-400 ${h === "金额" ? "text-right" : "text-left"}`}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {items.map(r => (
                <tr
                  key={`${r._direction}-${r.id}`}
                  className="border-b border-slate-50 hover:bg-indigo-50/30 cursor-pointer"
                  onClick={() => nav(r._direction === "ar" ? "/finance/ar" : "/finance/ap")}
                >
                  <td className="px-3 py-2.5">
                    <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold ${r._direction === "ar" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>{r._label}</span>
                  </td>
                  <td className="px-3 py-2.5 text-xs font-semibold text-indigo-600">{r._no}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-700">{bpName(r._counterparty_id)}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-500">{coName(r.company_id)}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-600">{TYPE_LABELS[r.type] ?? r.type}</td>
                  <td className="px-3 py-2.5 text-xs font-semibold text-right tabular-nums">
                    <span className={r._direction === "ar" ? "text-emerald-700" : "text-rose-700"}>
                      {r._direction === "ar" ? "+" : "-"}¥{fmtMoney(r.amount)}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-xs text-slate-600">{r._date}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-500">{r.method === "transfer" ? "转账" : r.method === "cash" ? "现金" : r.method === "acceptance" ? "承兑" : r.method}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-400 max-w-[100px] truncate" title={r.bank_name ?? ""}>{r.bank_name || ""}</td>
                  <td className="px-3 py-2.5 text-xs">
                    <span className={`px-1.5 py-0.5 rounded-full text-xs ${r.status === "confirmed" ? "bg-emerald-50 text-emerald-600" : r.status === "voided" ? "bg-red-50 text-red-400" : "bg-amber-50 text-amber-600"}`}>{STATUS_LABELS[r.status] ?? r.status}</span>
                  </td>
                  <td className="px-3 py-2.5 text-xs text-slate-400 max-w-[100px] truncate" title={r.summary ?? ""}>{r.summary || ""}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-400 max-w-[120px] truncate" title={r.remark ?? ""}>{r.remark || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && data.pages > 1 && (
        <Pagination page={page} pageSize={pageSize} total={data.total} pages={data.pages}
          onPageChange={setPage} onPageSizeChange={s => { setPageSize(s); setPage(1) }} />
      )}
    </div>
  )
}
