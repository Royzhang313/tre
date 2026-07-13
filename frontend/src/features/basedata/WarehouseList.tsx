/** 仓库管理 */
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiPut, apiDelete } from "../../api/client"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

interface W { id: string; name: string; is_active: boolean }
const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"

export function WarehouseList() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false); const [editId, setEditId] = useState<string | null>(null); const [name, setName] = useState("")
  const { data, isLoading } = useQuery({ queryKey: ["whs"], queryFn: async () => { const r = await apiGet<{ items: W[] }>("/basedata/warehouses?page=1&page_size=200"); return r.items } })
  const del = useMutation({ mutationFn: (id: string) => apiDelete(`/basedata/warehouses/${id}`), onSuccess: () => qc.invalidateQueries({ queryKey: ["whs"] }) })
  const save = useMutation({ mutationFn: async () => { return editId ? apiPut(`/basedata/warehouses/${editId}`, { name }) : apiPost("/basedata/warehouses", { name }) }, onSuccess: () => { qc.invalidateQueries({ queryKey: ["whs"] }); setShow(false); setName(""); setEditId(null) } })
  const edit = (w: W) => { setEditId(w.id); setName(w.name); setShow(true) }

  return (
    <div className="page-enter p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div><h1 className="text-2xl font-bold text-slate-900">仓库管理</h1><p className="text-sm text-slate-500 mt-1">管理提货/发货仓库</p></div>
        <button onClick={() => { setName(""); setEditId(null); setShow(true) }} className="px-5 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl hover:from-indigo-700 hover:to-blue-700 transition-all shadow-lg shadow-indigo-200 text-sm font-semibold">+ 新增仓库</button>
      </div>
      {show && (
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6 mb-6">
          <h3 className="font-semibold text-slate-800 mb-4">{editId ? "编辑仓库" : "新增仓库"}</h3>
          <div className="flex gap-3 items-end">
            <div className="flex-1"><label className="block text-sm font-medium text-slate-600 mb-1.5">仓库名称</label><input value={name} onChange={e => setName(e.target.value)} className={INP} /></div>
            <button onClick={() => save.mutate()} disabled={!name} className="px-5 py-3 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-40">保存</button>
            <button onClick={() => setShow(false)} className="px-5 py-3 border rounded-xl text-sm">取消</button>
          </div>
        </div>
      )}
      {isLoading ? <div className="text-center py-20 text-slate-300">加载中...</div> : (
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-slate-100">{["仓库名称", "状态", ""].map(h => <th key={h} className="px-5 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider text-left">{h}</th>)}</tr></thead>
            <tbody>
              {data?.map(w => (
                <tr key={w.id} className="border-b border-slate-50 hover:bg-slate-50/50 group">
                  <td className="px-5 py-3.5 font-semibold text-slate-800">{w.name}</td>
                  <td className="px-5 py-3.5"><span className={`text-xs font-medium ${w.is_active?"text-emerald-600":"text-slate-400"}`}>{w.is_active?"启用":"停用"}</span></td>
                  <td className="px-5 py-3.5"><div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"><button onClick={() => edit(w)} className="px-2.5 py-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg">编辑</button><button onClick={async () => { if (sysConfirm("删除？")) del.mutate(w.id) }} className="px-2.5 py-1.5 text-xs font-medium text-rose-500 hover:bg-rose-50 rounded-lg">删除</button></div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
