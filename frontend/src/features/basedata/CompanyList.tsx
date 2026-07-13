/** 主体公司管理 —— 行点击详情弹窗 */
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiPut, apiDelete } from "../../api/client"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

interface C { id: string; name: string; short_name: string | null; uscc: string | null; address: string | null; bank_name: string | null; bank_account: string | null; is_active: boolean }

const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"
const LBL = "block text-sm font-medium text-slate-600 mb-1.5"

export function CompanyList() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false); const [editId, setEditId] = useState<string | null>(null)
  const [detailId, setDetailId] = useState<string | null>(null); const [editing, setEditing] = useState(false)
  const [name, setName] = useState(""); const [sname, setSname] = useState(""); const [uscc, setUscc] = useState("")
  const [addr, setAddr] = useState(""); const [bank, setBank] = useState(""); const [bankAcct, setBankAcct] = useState("")

  const { data, isLoading } = useQuery({ queryKey: ["companies"], queryFn: async () => { const r = await apiGet<{ items: C[] }>("/basedata/companies"); return r.items } })
  const del = useMutation({ mutationFn: (id: string) => apiDelete(`/basedata/companies/${id}`), onSuccess: () => qc.invalidateQueries({ queryKey: ["companies"] }) })
  const save = useMutation({
    mutationFn: async () => {
      const body: any = { name, short_name: sname || null, uscc: uscc || null, address: addr || null, bank_name: bank || null, bank_account: bankAcct || null }
      return editId ? apiPut(`/basedata/companies/${editId}`, body) : apiPost("/basedata/companies", body)
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["companies"] }); closeModal() }
  })

  const closeModal = () => { setShow(false); setDetailId(null); setEditId(null); setEditing(false); setName(""); setSname(""); setUscc(""); setAddr(""); setBank(""); setBankAcct("") }
  const fillForm = (c: C) => { setName(c.name); setSname(c.short_name ?? ""); setUscc(c.uscc ?? ""); setAddr(c.address ?? ""); setBank(c.bank_name ?? ""); setBankAcct(c.bank_account ?? "") }
  const openEdit = (c: C) => { fillForm(c); setEditId(c.id); setEditing(true); setShow(true) }
  const openDetail = (c: C) => { fillForm(c); setDetailId(c.id); setEditing(false); setShow(true) }

  return (
    <div className="page-enter p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div><h1 className="text-2xl font-bold text-slate-900">主体公司</h1><p className="text-sm text-slate-500 mt-1">管理执行主体公司抬头</p></div>
        <button onClick={() => { closeModal(); setShow(true) }}
          className="px-5 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl hover:from-indigo-700 hover:to-blue-700 transition-all shadow-lg shadow-indigo-200 text-sm font-semibold">+ 新增公司</button>
      </div>

      {isLoading ? <div className="text-center py-20 text-slate-300">加载中...</div> : (
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm">
          <div className="overflow-x-auto -mx-4 sm:mx-0">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-slate-100 bg-slate-50/50">{["公司名称", "简称", "信用代码", "地址", "开户行", "银行账号", ""].map(h => <th key={h} className="px-4 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider text-left">{h}</th>)}</tr></thead>
            <tbody>
              {data?.map(c => (
                <tr key={c.id} className="border-b border-slate-50 hover:bg-indigo-50/20 transition-colors group cursor-pointer" onClick={() => openDetail(c)}>
                  <td className="px-4 py-3.5 font-semibold text-slate-800">{c.name}</td>
                  <td className="px-4 py-3.5 text-slate-500">{c.short_name ?? ""}</td>
                  <td className="px-4 py-3.5 text-slate-500 text-xs font-mono">{c.uscc ?? ""}</td>
                  <td className="px-4 py-3.5 text-slate-500 text-xs max-w-[160px] truncate">{c.address ?? ""}</td>
                  <td className="px-4 py-3.5 text-slate-500">{c.bank_name ?? ""}</td>
                  <td className="px-4 py-3.5 text-slate-500 text-xs font-mono">{c.bank_account ?? ""}</td>
                  <td className="px-3 py-3.5"><div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={ev => ev.stopPropagation()}><button onClick={() => openEdit(c)} className="px-2.5 py-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg">编辑</button><button onClick={async () => { if (sysConfirm("确定删除？")) del.mutate(c.id) }} className="px-2.5 py-1.5 text-xs font-medium text-rose-500 hover:bg-rose-50 rounded-lg">删除</button></div></td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}

      {/* 弹窗 */}
      {show && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/30 backdrop-blur-sm" onClick={closeModal}>
          <div className="bg-white rounded-2xl shadow-2xl shadow-slate-500/20 w-full max-w-xl max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-slate-100 px-8 py-5 flex items-center justify-between rounded-t-2xl z-10">
              <h2 className="text-lg font-bold text-slate-900">{editId ? (editing ? "编辑公司" : "公司详情") : "新增公司"}</h2>
              <div className="flex items-center gap-2">
                {detailId && !editing && (
                  <button onClick={() => { setEditing(true); setEditId(detailId) }} className="px-4 py-2 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">编辑</button>
                )}
                <button onClick={closeModal} className="w-9 h-9 rounded-xl hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>

            <div className="p-8 space-y-5">
              <div className="grid grid-cols-2 gap-4">
                <div><label className={LBL}>公司名称 {!name && <span className="text-rose-400">*</span>}</label>
                  {editing || !detailId ? <input value={name} onChange={e => setName(e.target.value)} className={INP} /> : <p className="text-sm font-medium text-slate-800 pt-2">{name}</p>}
                </div>
                <div><label className={LBL}>简称</label>
                  {editing || !detailId ? <input value={sname} onChange={e => setSname(e.target.value)} className={INP} /> : <p className="text-sm text-slate-600 pt-2">{sname || ""}</p>}
                </div>
                <div className="col-span-2"><label className={LBL}>统一社会信用代码</label>
                  {editing || !detailId ? <input value={uscc} onChange={e => setUscc(e.target.value)} className={INP} /> : <p className="text-sm text-slate-600 pt-2 font-mono">{uscc || ""}</p>}
                </div>
                <div className="col-span-2"><label className={LBL}>地址</label>
                  {editing || !detailId ? <input value={addr} onChange={e => setAddr(e.target.value)} className={INP} /> : <p className="text-sm text-slate-600 pt-2">{addr || ""}</p>}
                </div>
                <div><label className={LBL}>开户行</label>
                  {editing || !detailId ? <input value={bank} onChange={e => setBank(e.target.value)} className={INP} /> : <p className="text-sm text-slate-600 pt-2">{bank || ""}</p>}
                </div>
                <div><label className={LBL}>对公账户</label>
                  {editing || !detailId ? <input value={bankAcct} onChange={e => setBankAcct(e.target.value)} className={INP} /> : <p className="text-sm text-slate-600 pt-2 font-mono">{bankAcct || ""}</p>}
                </div>
              </div>
            </div>

            {(editing || !detailId) && (
              <div className="sticky bottom-0 bg-white/95 backdrop-blur-xl border-t border-slate-100 px-8 py-4 flex justify-end gap-3 rounded-b-2xl">
                <button onClick={closeModal} className="px-5 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">取消</button>
                <button onClick={() => save.mutate()} disabled={!name}
                  className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-xl text-sm font-semibold hover:from-indigo-700 hover:to-blue-700 disabled:opacity-40 transition-all shadow-lg shadow-indigo-200">保存</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
