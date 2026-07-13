/** 用户管理 */
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiPatch, apiDelete } from "../../api/client"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

interface U { id: string; username: string; phone: string | null; email: string | null; display_name: string | null; status: string; last_login_at: string | null; created_at: string }
interface R { id: string; code: string; name: string; is_system: boolean }

const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"
const LBL = "block text-sm font-medium text-slate-600 mb-1.5"

export function UserList() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false); const [editId, setEditId] = useState<string | null>(null)
  const [detailId, setDetailId] = useState<string | null>(null); const [editing, setEditing] = useState(false)
  const [username, setUsername] = useState(""); const [phone, setPhone] = useState(""); const [email, setEmail] = useState(""); const [displayName, setDisplayName] = useState("")
  const [password, setPassword] = useState("")
  const [createRoles, setCreateRoles] = useState<string[]>([])
  const [roleModal, setRoleModal] = useState(false); const [roleUserId, setRoleUserId] = useState(""); const [selectedRoles, setSelectedRoles] = useState<string[]>([])

  const { data: users, isLoading, error, refetch } = useQuery({ queryKey: ["users"], queryFn: async () => { const r = await apiGet<{ items: U[] }>("/auth/users?page_size=100"); return r.items }, staleTime: 0 })
  const { data: allRoles } = useQuery({ queryKey: ["roles-all"], queryFn: async () => { const r = await apiGet<R[]>("/auth/roles"); return Array.isArray(r) ? r : (r as any).items ?? [] } })

  const doSave = async () => {
    const body: any = {
      username: username,
      phone: phone || null,
      email: email || `${username}@local`,
      display_name: displayName || username,
    }
    if (!editId) {
      body.password = password
      body.role_ids = createRoles
    }
    console.log("SAVING BODY:", JSON.stringify(body))
    if (editId) return apiPatch(`/auth/users/${editId}`, body)
    return apiPost("/auth/users", body)
  }

  const saveUser = useMutation({
    mutationFn: doSave,
    onSuccess: () => { refetch(); closeModal() },
    onError: (err: any) => { sysToast("失败: " + (err.message || "未知")) },
  })

  const toggleStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => apiPatch(`/auth/users/${id}/status`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] })
  })

  const assignRoles = useMutation({
    mutationFn: ({ userId, roleIds }: { userId: string; roleIds: string[] }) => apiPatch(`/auth/users/${userId}/roles`, { role_ids: roleIds }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["users"] }); setRoleModal(false) }
  })

  const delUser = useMutation({
    mutationFn: (id: string) => apiDelete(`/auth/users/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] })
  })

  const closeModal = () => { setShow(false); setDetailId(null); setEditId(null); setEditing(false); setUsername(""); setPhone(""); setEmail(""); setDisplayName(""); setPassword(""); setCreateRoles([]) }
  const openEdit = (u: U) => { setEditId(u.id); fillForm(u); setEditing(true); setShow(true) }
  const openDetail = (u: U) => { fillForm(u); setDetailId(u.id); setEditing(false); setShow(true) }
  const fillForm = (u: U) => { setUsername(u.username); setPhone(u.phone ?? ""); setEmail(u.email ?? ""); setDisplayName(u.display_name ?? "") }

  const openRoleAssign = (u: U) => {
    setRoleUserId(u.id)
    apiGet<{ roles: R[] }>(`/auth/users/${u.id}`).then(d => {
      setSelectedRoles(((d as any).roles ?? []).map((r: R) => r.id))
    })
    setRoleModal(true)
  }

  return (
    <div className="page-enter p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div><h1 className="text-2xl font-bold text-slate-900">用户管理</h1><p className="text-sm text-slate-500 mt-1">管理用户账号与角色分配</p></div>
        <button onClick={() => { closeModal(); setShow(true) }} className="px-5 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl hover:from-indigo-700 hover:to-blue-700 transition-all shadow-lg shadow-indigo-200 text-sm font-semibold">+ 新增用户</button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm">
        {error ? <div className="p-8 text-center text-rose-500 text-sm">加载失败: {(error as any).message}</div> :
        isLoading ? <div className="p-8 text-center text-slate-300">加载中...</div> :
        <div className="overflow-x-auto -mx-4 sm:mx-0">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-100 bg-slate-50/50">{["用户名","手机号","显示名","状态","角色","最后登录",""].map(h => <th key={h} className="px-4 py-3.5 text-xs font-semibold text-slate-400 uppercase tracking-wider text-left">{h}</th>)}</tr></thead>
          <tbody>
            {users?.map(u => (
              <tr key={u.id} className="border-b border-slate-50 hover:bg-indigo-50/20 transition-colors group cursor-pointer" onClick={() => openDetail(u)}>
                <td className="px-4 py-3.5 font-semibold text-slate-800">{u.username}</td>
                <td className="px-4 py-3.5 text-slate-500 font-mono text-xs">{u.phone ?? ""}</td>
                <td className="px-4 py-3.5 text-slate-600">{u.display_name ?? ""}</td>
                <td className="px-4 py-3.5"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${u.status === "active" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-400"}`}>{u.status === "active" ? "启用" : "停用"}</span></td>
                <td className="px-4 py-3.5"><span className="text-xs text-slate-400">点击查看</span></td>
                <td className="px-4 py-3.5 text-slate-400 text-xs">{u.last_login_at?.slice(0, 10) ?? ""}</td>
                <td className="px-3 py-3.5"><div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={ev => ev.stopPropagation()}>
                  <button onClick={() => openEdit(u)} className="px-2.5 py-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg">编辑</button>
                  <button onClick={() => toggleStatus.mutate({ id: u.id, status: u.status === "active" ? "inactive" : "active" })} className={`px-2.5 py-1.5 text-xs font-medium rounded-lg ${u.status === "active" ? "text-amber-600 hover:bg-amber-50" : "text-emerald-600 hover:bg-emerald-50"}`}>{u.status === "active" ? "停用" : "启用"}</button>
                  <button onClick={() => openRoleAssign(u)} className="px-2.5 py-1.5 text-xs font-medium text-purple-600 hover:bg-purple-50 rounded-lg">角色</button>
                  <button onClick={async () => { if (sysConfirm("确定删除该用户？")) delUser.mutate(u.id) }} className="px-2.5 py-1.5 text-xs font-medium text-rose-500 hover:bg-rose-50 rounded-lg">删除</button>
                </div></td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>}
      </div>

      {show && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/30 backdrop-blur-sm" onClick={closeModal}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-slate-100 px-8 py-5 flex items-center justify-between rounded-t-2xl z-10">
              <h2 className="text-lg font-bold text-slate-900">{editId ? (editing ? "编辑用户" : "用户详情") : "新增用户"}</h2>
              <div className="flex items-center gap-2">
                {detailId && !editing && <button onClick={() => { setEditing(true); setEditId(detailId) }} className="px-4 py-2 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">编辑</button>}
                <button onClick={closeModal} className="w-9 h-9 rounded-xl hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors">✕</button>
              </div>
            </div>
            <div className="p-8 space-y-4">
              <div>
                <label className={LBL}>用户名 {!username && <span className="text-rose-400">*</span>}</label>
                {editing || !detailId ? <input value={username} onChange={e => setUsername(e.target.value)} className={INP} disabled={!!editId} /> : <p className="text-sm font-medium text-slate-800 pt-2">{username}</p>}
              </div>
              {(!detailId || editing) && !editId && (
                <div><label className={LBL}>密码 {!password && <span className="text-rose-400">*</span>}</label><input type="password" value={password} onChange={e => setPassword(e.target.value)} className={INP} /></div>
              )}
              <div>
                <label className={LBL}>手机号</label>
                {editing || !detailId ? <input value={phone} onChange={e => setPhone(e.target.value)} className={INP} /> : <p className="text-sm text-slate-600 pt-2">{phone || ""}</p>}
              </div>
              <div>
                <label className={LBL}>邮箱</label>
                {editing || !detailId ? <input value={email} onChange={e => setEmail(e.target.value)} className={INP} /> : <p className="text-sm text-slate-600 pt-2">{email || ""}</p>}
              </div>
              <div>
                <label className={LBL}>显示名 {!displayName && <span className="text-rose-400">*</span>}</label>
                {editing || !detailId ? <input value={displayName} onChange={e => setDisplayName(e.target.value)} className={INP} /> : <p className="text-sm font-medium text-slate-800 pt-2">{displayName || ""}</p>}
              </div>
              {!detailId && !editId && (
                <div>
                  <label className={LBL}>角色</label>
                  <div className="flex flex-wrap gap-2">
                    {(allRoles ?? []).map(r => (
                      <label key={r.id} onClick={() => setCreateRoles(p => p.includes(r.id) ? p.filter(x => x !== r.id) : [...p, r.id])}
                        className={`px-3 py-1.5 rounded-lg border text-xs font-medium cursor-pointer transition-colors ${createRoles.includes(r.id) ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"}`}>
                        {r.name}
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {(editing || !detailId) && (
              <div className="sticky bottom-0 bg-white/95 backdrop-blur-xl border-t border-slate-100 px-8 py-4 flex justify-end gap-3 rounded-b-2xl">
                <button onClick={closeModal} className="px-5 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">取消</button>
                <button onClick={() => saveUser.mutate()} disabled={!username || (!editId && !password)} className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-xl text-sm font-semibold hover:from-indigo-700 hover:to-blue-700 disabled:opacity-40 transition-all shadow-lg shadow-indigo-200">保存</button>
              </div>
            )}
          </div>
        </div>
      )}

      {roleModal && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[12vh] bg-black/30 backdrop-blur-sm" onClick={() => setRoleModal(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900">分配角色</h2>
              <button onClick={() => setRoleModal(false)} className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400">✕</button>
            </div>
            <div className="p-6 space-y-2">
              {(allRoles ?? []).map(r => (
                <label key={r.id} onClick={() => setSelectedRoles(p => p.includes(r.id) ? p.filter(x => x !== r.id) : [...p, r.id])}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border-2 cursor-pointer transition-all text-sm font-medium ${selectedRoles.includes(r.id) ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"}`}>
                  <span className={`w-4 h-4 rounded border-2 flex items-center justify-center ${selectedRoles.includes(r.id) ? "border-indigo-500 bg-indigo-500" : "border-slate-300"}`}>
                    {selectedRoles.includes(r.id) && <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                  </span>
                  <div><p>{r.name}</p><p className="text-xs text-slate-400">{r.code}</p></div>
                </label>
              ))}
            </div>
            <div className="border-t border-slate-100 px-6 py-4 flex justify-end gap-3">
              <button onClick={() => setRoleModal(false)} className="px-4 py-2 border border-slate-200 rounded-xl text-sm text-slate-600 hover:bg-slate-50">取消</button>
              <button onClick={() => assignRoles.mutate({ userId: roleUserId, roleIds: selectedRoles })} className="px-5 py-2 bg-indigo-600 text-white rounded-xl text-sm font-semibold hover:bg-indigo-700">保存</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
