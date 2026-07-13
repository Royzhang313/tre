import { useState } from "react"
import { useQueryClient } from "@tanstack/react-query"

const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"
const TYPE_OPTS = [{ v: "trader", l: "贸易商" }, { v: "factory", l: "原料厂" }, { v: "end_customer", l: "终端客户" }]

/** 快速新增企业弹窗 —— 供方/客户表单统一使用 */
export function AddEnterpriseModal({ onAdded, defaultTypes, title }: {
  onAdded: (id: string) => void
  defaultTypes: string[]
  title: string
}) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState(""); const [sname, setSname] = useState(""); const [uscc, setUscc] = useState("")
  const [addr, setAddr] = useState(""); const [bank, setBank] = useState(""); const [bankAcct, setBankAcct] = useState("")
  const [types, setTypes] = useState<string[]>(defaultTypes)
  const [contacts, setContacts] = useState<{ name: string; mobile: string }[]>([])
  const qc = useQueryClient()

  const toggleType = (v: string) => setTypes(p => p.includes(v) ? p.filter(t => t !== v) : [...p, v])

  const save = async () => {
    if (!name) return
    const body = { name, short_name: sname || null, uscc: uscc || null, address: addr || null, bank_name: bank || null, bank_account: bankAcct || null, enterprise_type: types, contacts }
    const res = await fetch("/api/v1/basedata/enterprises", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
    const json = await res.json()
    if (json.data?.id) { qc.invalidateQueries({ queryKey: ["ents"] }); onAdded(json.data.id); setOpen(false); setName(""); setSname(""); setUscc(""); setAddr(""); setBank(""); setBankAcct(""); setTypes(defaultTypes); setContacts([]) }
  }

  const handleOpen = () => {
    setTypes(defaultTypes)
    setOpen(true)
  }

  return (
    <>
      <button type="button" onClick={handleOpen} className="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50 transition-all shrink-0" title={title}>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
      </button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/30 backdrop-blur-sm" onClick={() => setOpen(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-slate-100 px-6 py-4 flex items-center justify-between rounded-t-2xl z-10">
              <h2 className="text-base font-bold text-slate-900">{title}</h2>
              <button onClick={() => setOpen(false)} className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400">✕</button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">企业名称 {!name && <span className="text-rose-400">*</span>}</label>
                  <input value={name} onChange={e => setName(e.target.value)} className={INP} />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1.5">简称</label>
                  <input value={sname} onChange={e => setSname(e.target.value)} className={INP} />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">统一社会信用代码</label>
                <input value={uscc} onChange={e => setUscc(e.target.value)} className={INP} />
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">企业类型</label>
                <div className="flex flex-wrap gap-2">
                  {TYPE_OPTS.map(o => (
                    <label key={o.v} onClick={() => toggleType(o.v)} className={`px-3 py-1.5 rounded-lg border-2 cursor-pointer text-xs font-medium transition-all ${types.includes(o.v) ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"}`}>{o.l}</label>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1.5">地址</label>
                <input value={addr} onChange={e => setAddr(e.target.value)} className={INP} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs text-slate-500 mb-1.5">开户行</label><input value={bank} onChange={e => setBank(e.target.value)} className={INP} /></div>
                <div><label className="block text-xs text-slate-500 mb-1.5">对公账户</label><input value={bankAcct} onChange={e => setBankAcct(e.target.value)} className={INP} /></div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-slate-500">联系人</label>
                  <button onClick={() => setContacts(p => [...p, { name: "", mobile: "" }])} className="text-xs text-indigo-600 hover:text-indigo-800">+ 添加</button>
                </div>
                {contacts.map((c, i) => (
                  <div key={i} className="flex items-center gap-2 mb-2">
                    <input value={c.name} onChange={e => { const n = [...contacts]; n[i] = { ...n[i], name: e.target.value }; setContacts(n) }} className={INP + " w-28"} />
                    <input value={c.mobile} onChange={e => { const n = [...contacts]; n[i] = { ...n[i], mobile: e.target.value }; setContacts(n) }} className={INP + " w-36"} />
                    <button onClick={() => setContacts(p => p.filter((_, j) => j !== i))} className="text-slate-300 hover:text-rose-500">✕</button>
                  </div>
                ))}
              </div>
            </div>
            <div className="sticky bottom-0 bg-white/95 backdrop-blur-xl border-t border-slate-100 px-6 py-4 flex justify-end gap-3 rounded-b-2xl">
              <button onClick={() => setOpen(false)} className="px-5 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-600 hover:bg-slate-50">取消</button>
              <button onClick={save} disabled={!name} className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-40">保存</button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
