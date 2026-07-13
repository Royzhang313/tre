/** 角色管理 —— 含权限配置弹窗 */
import { useState, useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiPatch, apiDelete } from "../../api/client"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

interface R { id: string; code: string; name: string; description: string | null; is_system: boolean }
interface P { id: string; code: string; name: string; module: string; resource: string; action: string }

const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"
const LBL = "block text-sm font-medium text-slate-600 mb-1.5"

export function RoleList() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false); const [editId, setEditId] = useState<string | null>(null)
  const [detailId, setDetailId] = useState<string | null>(null); const [editing, setEditing] = useState(false)
  const [code, setCode] = useState(""); const [name, setName] = useState(""); const [desc, setDesc] = useState("")
  // 权限配置弹窗
  const [permModal, setPermModal] = useState(false); const [permRoleId, setPermRoleId] = useState(""); const [permRoleName, setPermRoleName] = useState("")
  const [selectedPerms, setSelectedPerms] = useState<string[]>([])

  const { data: roles } = useQuery({ queryKey: ["roles"], queryFn: async () => { const r = await apiGet<R[]>("/auth/roles"); return Array.isArray(r) ? r : (r as any).items ?? [] } })
  const { data: allPerms } = useQuery({ queryKey: ["perms"], queryFn: async () => { const r = await apiGet<P[]>("/auth/permissions"); return Array.isArray(r) ? r : (r as any).items ?? [] } })

  // 按模块分组权限
  const permGroups = useMemo(() => {
    const groups: Record<string, P[]> = {}
    for (const p of (allPerms ?? [])) {
      const m = p.module || "其他"
      if (!groups[m]) groups[m] = []
      groups[m].push(p)
    }
    return groups
  }, [allPerms])

  const saveRole = useMutation({
    mutationFn: async () => {
      const body: any = { code, name, description: desc || null }
      return editId ? apiPatch(`/auth/roles/${editId}`, body) : apiPost("/auth/roles", body)
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["roles"] }); closeModal() }
  })

  const delRole = useMutation({
    mutationFn: (id: string) => apiDelete(`/auth/roles/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] })
  })

  const assignPerms = useMutation({
    mutationFn: ({ roleId, permIds }: { roleId: string; permIds: string[] }) =>
      apiPatch(`/auth/roles/${roleId}/permissions`, { permission_ids: permIds }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["roles"] }); setPermModal(false) }
  })

  const closeModal = () => { setShow(false); setDetailId(null); setEditId(null); setEditing(false); setCode(""); setName(""); setDesc("") }
  const openEdit = (r: R) => { setEditId(r.id); fillForm(r); setEditing(true); setShow(true) }
  const openDetail = (r: R) => { fillForm(r); setDetailId(r.id); setEditing(false); setShow(true) }
  const fillForm = (r: R) => { setCode(r.code); setName(r.name); setDesc(r.description ?? "") }

  const openPermModal = async (r: R) => {
    setPermRoleId(r.id); setPermRoleName(r.name)
    try {
      const d = await apiGet<{ permissions: P[] }>(`/auth/roles/${r.id}`)
      setSelectedPerms(((d as any).permissions ?? []).map((p: P) => p.id))
    } catch { setSelectedPerms([]) }
    setPermModal(true)
  }

  return (
    <div className="page-enter p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div><h1 className="text-2xl font-bold text-slate-900">角色管理</h1><p className="text-sm text-slate-500 mt-1">管理角色与权限分配</p></div>
        <button onClick={() => { closeModal(); setShow(true) }} className="px-5 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl hover:from-indigo-700 hover:to-blue-700 transition-all shadow-lg shadow-indigo-200 text-sm font-semibold">+ 新增角色</button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm">
        <div className="overflow-x-auto -mx-4 sm:mx-0">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-100 bg-slate-50/50">{["角色编码", "名称", "描述", "系统", "权限", ""].map(h => <th key={h} className="px-4 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider text-left">{h}</th>)}</tr></thead>
          <tbody>
            {roles?.map(r => (
              <tr key={r.id} className="border-b border-slate-50 hover:bg-indigo-50/20 transition-colors group cursor-pointer" onClick={() => openDetail(r)}>
                <td className="px-4 py-3.5 font-semibold text-slate-800 font-mono text-xs">{r.code}</td>
                <td className="px-4 py-3.5 text-slate-700">{r.name}</td>
                <td className="px-4 py-3.5 text-slate-500 text-xs max-w-[200px] truncate">{r.description ?? ""}</td>
                <td className="px-4 py-3.5">{r.is_system ? <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700">系统</span> : ""}</td>
                <td className="px-4 py-3.5">
                  <button onClick={ev => { ev.stopPropagation(); openPermModal(r) }} className="text-xs text-purple-600 hover:text-purple-800 font-medium">配置权限</button>
                </td>
                <td className="px-3 py-3.5"><div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={ev => ev.stopPropagation()}>
                  <button onClick={() => openEdit(r)} className="px-2.5 py-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg">编辑</button>
                  {!r.is_system && <button onClick={async () => { if (sysConfirm("确定删除？")) delRole.mutate(r.id) }} className="px-2.5 py-1.5 text-xs font-medium text-rose-500 hover:bg-rose-50 rounded-lg">删除</button>}
                </div></td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>

      {/* 详情/编辑弹窗 */}
      {show && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/30 backdrop-blur-sm" onClick={closeModal}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-slate-100 px-8 py-5 flex items-center justify-between rounded-t-2xl z-10">
              <h2 className="text-lg font-bold text-slate-900">{editId ? (editing ? "编辑角色" : "角色详情") : "新增角色"}</h2>
              <div className="flex items-center gap-2">
                {detailId && !editing && <button onClick={() => { setEditing(true); setEditId(detailId) }} className="px-4 py-2 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">编辑</button>}
                <button onClick={closeModal} className="w-9 h-9 rounded-xl hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors">✕</button>
              </div>
            </div>
            <div className="p-8 space-y-4">
              <div><label className={LBL}>角色编码 {!code && <span className="text-rose-400">*</span>}</label>
                {editing || !detailId ? <input value={code} onChange={e => setCode(e.target.value)} className={INP} disabled={!!editId} /> : <p className="text-sm font-mono font-medium text-slate-800 pt-2">{code}</p>}
              </div>
              <div><label className={LBL}>名称 {!name && <span className="text-rose-400">*</span>}</label>
                {editing || !detailId ? <input value={name} onChange={e => setName(e.target.value)} className={INP} /> : <p className="text-sm font-medium text-slate-800 pt-2">{name}</p>}
              </div>
              <div><label className={LBL}>描述</label>
                {editing || !detailId ? <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={2} className={INP + " resize-none"} /> : <p className="text-sm text-slate-600 pt-2">{desc || ""}</p>}
              </div>
            </div>
            {(editing || !detailId) && (
              <div className="sticky bottom-0 bg-white/95 backdrop-blur-xl border-t border-slate-100 px-8 py-4 flex justify-end gap-3 rounded-b-2xl">
                <button onClick={closeModal} className="px-5 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">取消</button>
                <button onClick={() => saveRole.mutate()} disabled={!code || !name} className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-xl text-sm font-semibold hover:from-indigo-700 hover:to-blue-700 disabled:opacity-40 transition-all shadow-lg shadow-indigo-200">保存</button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 权限配置弹窗 */}
      {permModal && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[6vh] bg-black/30 backdrop-blur-sm" onClick={() => setPermModal(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-slate-100 px-6 py-4 flex items-center justify-between rounded-t-2xl z-10">
              <div><h2 className="text-lg font-bold text-slate-900">配置权限 —— {permRoleName}</h2><p className="text-xs text-slate-400 mt-0.5">勾选该角色拥有的权限</p></div>
              <button onClick={() => setPermModal(false)} className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400">✕</button>
            </div>
            <div className="p-6 space-y-6">
              {Object.entries(permGroups).map(([module, perms]) => (
                <div key={module}>
                  <h3 className="text-sm font-semibold text-slate-600 mb-2 px-1 uppercase">{module}</h3>
                  <div className="space-y-1">
                    {perms.map(p => (
                      <label key={p.id} onClick={() => setSelectedPerms(prev => prev.includes(p.id) ? prev.filter(x => x !== p.id) : [...prev, p.id])}
                        className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm
                          ${selectedPerms.includes(p.id) ? "bg-indigo-50 text-indigo-700" : "hover:bg-slate-50 text-slate-600"}`}>
                        <span className={`w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 ${selectedPerms.includes(p.id) ? "border-indigo-500 bg-indigo-500" : "border-slate-300"}`}>
                          {selectedPerms.includes(p.id) && <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                        </span>
                        <div className="flex-1"><p className="font-medium">{p.name}</p><p className="text-xs text-slate-400">{p.code}</p></div>
                        <span className="text-xs text-slate-300">{p.action}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="sticky bottom-0 bg-white/95 backdrop-blur-xl border-t border-slate-100 px-6 py-4 flex justify-end gap-3 rounded-b-2xl">
              <button onClick={() => setPermModal(false)} className="px-5 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-600 hover:bg-slate-50">取消</button>
              <button onClick={() => assignPerms.mutate({ roleId: permRoleId, permIds: selectedPerms })} className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700">保存权限</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
