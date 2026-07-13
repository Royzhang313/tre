/** 企业管理 —— 行点击详情弹窗 + 全字段展示 */
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiPut, apiDelete } from "../../api/client"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

interface C { id?: string; name: string; mobile: string }
interface E { id: string; name: string; short_name: string | null; uscc: string | null; enterprise_type: string[]; address: string | null; bank_name: string | null; bank_account: string | null; is_active: boolean; contacts: C[] }

const TYPE_OPTIONS = [
  { value: "trader", label: "贸易商" },
  { value: "factory", label: "原料厂" },
  { value: "end_customer", label: "终端客户" },
]
const TYPE_LABELS: Record<string, string> = { trader: "贸易商", factory: "原料厂", end_customer: "终端客户" }

const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"
const LBL = "block text-sm font-medium text-slate-600 mb-1.5"

export function EnterpriseList() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false); const [editId, setEditId] = useState<string | null>(null)
  const [detailId, setDetailId] = useState<string | null>(null)  // 只读详情
  const [editing, setEditing] = useState(false)  // 详情弹窗中是否在编辑
  const [name, setName] = useState(""); const [sname, setSname] = useState(""); const [uscc, setUscc] = useState("")
  const [types, setTypes] = useState<string[]>(["trader"]); const [addr, setAddr] = useState("")
  const [bank, setBank] = useState(""); const [bankAcct, setBankAcct] = useState("")
  const [contacts, setContacts] = useState<C[]>([])

  const { data, isLoading } = useQuery({ queryKey: ["ents"], queryFn: async () => { const r = await apiGet<{ items: E[] }>("/basedata/enterprises"); return r.items } })
  const del = useMutation({ mutationFn: (id: string) => apiDelete(`/basedata/enterprises/${id}`), onSuccess: () => qc.invalidateQueries({ queryKey: ["ents"] }) })
  const save = useMutation({
    mutationFn: async () => {
      const body: any = { name, short_name: sname || null, uscc: uscc || null, enterprise_type: types, address: addr || null, bank_name: bank || null, bank_account: bankAcct || null, contacts: contacts.map(c => ({ name: c.name, mobile: c.mobile })) }
      return editId ? apiPut(`/basedata/enterprises/${editId}`, body) : apiPost("/basedata/enterprises", body)
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["ents"] }); closeModal() }
  })

  const closeModal = () => { setShow(false); setDetailId(null); setEditId(null); setEditing(false); setName(""); setSname(""); setUscc(""); setTypes(["trader"]); setAddr(""); setBank(""); setBankAcct(""); setContacts([]) }
  const openEdit = (e: E) => {
    fillForm(e); setEditId(e.id); setEditing(true); setShow(true)
  }
  const openDetail = (e: E) => {
    fillForm(e); setDetailId(e.id); setEditing(false); setShow(true)
  }
  const fillForm = (e: E) => {
    setName(e.name); setSname(e.short_name ?? ""); setUscc(e.uscc ?? "")
    setTypes(e.enterprise_type ?? ["trader"]); setAddr(e.address ?? ""); setBank(e.bank_name ?? ""); setBankAcct(e.bank_account ?? "")
    setContacts((e.contacts ?? []).map(c => ({ id: c.id, name: c.name, mobile: c.mobile })))
  }

  const toggleType = (v: string) => setTypes(p => p.includes(v) ? p.filter(t => t !== v) : [...p, v])

  return (
    <div className="page-enter p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div><h1 className="text-2xl font-bold text-slate-900">企业管理</h1><p className="text-sm text-slate-500 mt-1">管理供应商与客户企业信息</p></div>
        <button onClick={() => { closeModal(); setShow(true) }}
          className="px-5 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl hover:from-indigo-700 hover:to-blue-700 transition-all shadow-lg shadow-indigo-200 text-sm font-semibold">+ 新增企业</button>
      </div>

      {isLoading ? <div className="text-center py-20 text-slate-300">加载中...</div> : (
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm">
          <div className="overflow-x-auto -mx-4 sm:mx-0">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-slate-100 bg-slate-50/50">{["企业名称", "简称", "信用代码", "类型", "地址", "开户行", "银行账号", ""].map(h => <th key={h} className="px-4 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider text-left">{h}</th>)}</tr></thead>
            <tbody>
              {data?.map(e => (
                <tr key={e.id} className="border-b border-slate-50 hover:bg-indigo-50/20 transition-colors group cursor-pointer" onClick={() => openDetail(e)}>
                  <td className="px-4 py-3.5 font-semibold text-slate-800">{e.name}</td>
                  <td className="px-4 py-3.5 text-slate-500">{e.short_name ?? ""}</td>
                  <td className="px-4 py-3.5 text-slate-500 text-xs font-mono">{e.uscc ?? ""}</td>
                  <td className="px-4 py-3.5"><div className="flex flex-wrap gap-1">{(e.enterprise_type ?? []).map(t => <span key={t} className="px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">{TYPE_LABELS[t] ?? t}</span>)}</div></td>
                  <td className="px-4 py-3.5 text-slate-500 text-xs max-w-[140px] truncate">{e.address ?? ""}</td>
                  <td className="px-4 py-3.5 text-slate-500">{e.bank_name ?? ""}</td>
                  <td className="px-4 py-3.5 text-slate-500 text-xs font-mono">{e.bank_account ?? ""}</td>
                  <td className="px-3 py-3.5"><div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={ev => ev.stopPropagation()}><button onClick={() => openEdit(e)} className="px-2.5 py-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg">编辑</button><button onClick={async () => { if (sysConfirm("确定删除？")) del.mutate(e.id) }} className="px-2.5 py-1.5 text-xs font-medium text-rose-500 hover:bg-rose-50 rounded-lg">删除</button></div></td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}

      {/* 弹窗 —— 新增 / 只读详情 / 编辑 */}
      {show && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[6vh] bg-black/30 backdrop-blur-sm" onClick={closeModal}>
          <div className="bg-white rounded-2xl shadow-2xl shadow-slate-500/20 w-full max-w-2xl max-h-[88vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-slate-100 px-8 py-5 flex items-center justify-between rounded-t-2xl z-10">
              <h2 className="text-lg font-bold text-slate-900">{editId ? (editing ? "编辑企业" : "企业详情") : "新增企业"}</h2>
              <div className="flex items-center gap-2">
                {detailId && !editing && (
                  <button onClick={() => { setEditing(true); setEditId(detailId) }} className="px-4 py-2 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">编辑</button>
                )}
                <button onClick={closeModal} className="w-9 h-9 rounded-xl hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </div>

            <div className="p-8 space-y-6">
              {/* 基本信息 */}
              <div className="grid grid-cols-2 gap-4">
                <div><label className={LBL}>企业名称 {!name && <span className="text-rose-400">*</span>}</label>
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

              {/* 企业类型 */}
              <div>
                <label className={LBL}>企业类型</label>
                {editing || !detailId ? (
                  <div className="flex flex-wrap gap-3">
                    {TYPE_OPTIONS.map(opt => (
                      <label key={opt.value} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 cursor-pointer transition-all text-sm font-medium
                        ${types.includes(opt.value) ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"}`}>
                        <input type="checkbox" checked={types.includes(opt.value)} onChange={() => toggleType(opt.value)} className="sr-only" />
                        <span className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-colors ${types.includes(opt.value) ? "border-indigo-500 bg-indigo-500" : "border-slate-300"}`}>
                          {types.includes(opt.value) && <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                        </span>
                        {opt.label}
                      </label>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-1 pt-1">{(types ?? []).map(t => <span key={t} className="px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700">{TYPE_LABELS[t] ?? t}</span>)}</div>
                )}
              </div>

              {/* 联系人明细 */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className={LBL}>联系人</label>
                  {(editing || !detailId) && (
                    <button onClick={() => setContacts(p => [...p, { name: "", mobile: "" }])}
                      className="text-xs font-medium text-indigo-600 hover:text-indigo-800 px-3 py-1.5 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors">+ 添加</button>
                  )}
                </div>
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead><tr className="bg-slate-50 border-b border-slate-200">{["姓名", "手机", (editing || !detailId) ? "" : null].filter(Boolean).map(h => <th key={h} className="px-4 py-2.5 text-xs font-semibold text-slate-400 uppercase text-left">{h}</th>)}</tr></thead>
                    <tbody>
                      {contacts.length === 0 ? (
                        <tr><td colSpan={editing || !detailId ? 3 : 2} className="px-4 py-6 text-center text-slate-300 text-sm">暂无联系人</td></tr>
                      ) : contacts.map((c, i) => (
                        <tr key={i} className="border-b border-slate-100">
                          <td className="px-4 py-2">{(editing || !detailId) ? <input value={c.name} onChange={e => { const n = [...contacts]; n[i] = { ...n[i], name: e.target.value }; setContacts(n) }} className={`${INP} border-transparent bg-transparent`} /> : <span className="text-sm text-slate-700">{c.name}</span>}</td>
                          <td className="px-4 py-2">{(editing || !detailId) ? <input value={c.mobile} onChange={e => { const n = [...contacts]; n[i] = { ...n[i], mobile: e.target.value }; setContacts(n) }} className={`${INP} border-transparent bg-transparent`} /> : <span className="text-sm text-slate-600">{c.mobile}</span>}</td>
                          {(editing || !detailId) && <td className="px-4 py-2 w-8"><button onClick={() => setContacts(p => p.filter((_, j) => j !== i))} className="text-slate-300 hover:text-rose-500">×</button></td>}
                        </tr>
                      ))}
                    </tbody>
                  </table>
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
