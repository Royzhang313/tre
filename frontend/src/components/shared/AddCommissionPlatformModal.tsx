import { useState } from "react"
import { useQueryClient } from "@tanstack/react-query"

/** 快速新增撮合平台弹窗 */
export function AddCommissionPlatformModal({ onAdded }: { onAdded: (id: string) => void }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [errMsg, setErrMsg] = useState("")
  const qc = useQueryClient()

  const save = async () => {
    if (!name) return
    const res = await fetch("/api/v1/basedata/commission-platforms", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    })
    const json = await res.json()
    if (json.data?.id) {
      qc.invalidateQueries({ queryKey: ["cps"] })
      onAdded(json.data.id)
      setOpen(false)
      setName("")
      setErrMsg("")
    } else {
      setErrMsg(json?.message || "保存失败")
    }
  }

  return (
    <>
      <button type="button" onClick={() => { setOpen(true); setErrMsg("") }}
        className="w-8 h-8 flex items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50 transition-all shrink-0" title="新增撮合平台">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
      </button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/30 backdrop-blur-sm" onClick={() => setOpen(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900">新增撮合平台</h2>
              <button onClick={() => setOpen(false)} className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400">✕</button>
            </div>
            <div className="p-6">
              <label className="block text-xs text-slate-500 mb-1.5">撮合平台 {!name && <span className="text-rose-400">*</span>}</label>
              <input value={name} onChange={e => { setName(e.target.value); setErrMsg("") }} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400" />
              {errMsg && <p className="text-xs text-red-500 mt-2">{errMsg}</p>}
            </div>
            <div className="px-6 py-4 border-t border-slate-100 flex justify-end gap-3">
              <button onClick={() => setOpen(false)} className="px-5 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-600 hover:bg-slate-50">取消</button>
              <button onClick={save} disabled={!name} className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-40">保存</button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
