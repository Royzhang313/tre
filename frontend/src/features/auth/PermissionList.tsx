/** 权限列表 —— 只读，按模块分组 */
import { useState, useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { apiGet } from "../../api/client"

interface P { id: string; code: string; name: string; module: string; resource: string; action: string }

export function PermissionList() {
  const [filter, setFilter] = useState("")
  const { data: perms } = useQuery({
    queryKey: ["perms-list"],
    queryFn: async () => { const r = await apiGet<P[]>("/auth/permissions"); return Array.isArray(r) ? r : (r as any).items ?? [] }
  })

  const modules = useMemo(() => [...new Set((perms ?? []).map(p => p.module || "其他"))].sort(), [perms])
  const filtered = useMemo(() => filter ? (perms ?? []).filter(p => (p.module || "其他") === filter) : (perms ?? []), [perms, filter])

  return (
    <div className="page-enter p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div><h1 className="text-2xl font-bold text-slate-900">权限管理</h1><p className="text-sm text-slate-500 mt-1">查看系统中所有权限定义</p></div>
      </div>

      {/* 模块筛选 */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button onClick={() => setFilter("")} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${!filter ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>全部</button>
        {modules.map(m => (
          <button key={m} onClick={() => setFilter(m)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === m ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}>{m}</button>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-100 bg-slate-50/50">{["权限编码", "名称", "模块", "资源", "操作"].map(h => <th key={h} className="px-4 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider text-left">{h}</th>)}</tr></thead>
          <tbody>
            {filtered.map(p => (
              <tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                <td className="px-4 py-3.5 font-mono text-xs text-indigo-600">{p.code}</td>
                <td className="px-4 py-3.5 font-medium text-slate-800">{p.name}</td>
                <td className="px-4 py-3.5"><span className="px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-600">{p.module}</span></td>
                <td className="px-4 py-3.5 text-slate-500">{p.resource}</td>
                <td className="px-4 py-3.5 text-slate-500">{p.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
