/** 登录页面 */
import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../../contexts/AuthContext"
import { apiPost } from "../../api/client"

export function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const nav = useNavigate()

  const handleLogin = async () => {
    if (!username || !password) { setError("请输入用户名和密码"); return }
    setLoading(true); setError("")
    try {
      const res = await apiPost<{ access_token: string }>("/auth/login", { username, password })
      await login(res.access_token)
      nav("/")
    } catch (e: any) {
      setError(e.message || "登录失败")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200">
      <div className="bg-white rounded-3xl shadow-2xl shadow-slate-300/50 w-full max-w-md p-10">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 text-white flex items-center justify-center mx-auto mb-4 shadow-lg shadow-indigo-200">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">ERP Builder</h1>
          <p className="text-sm text-slate-500 mt-1">PET 瓶片贸易管理系统</p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1.5">用户名</label>
            <input value={username} onChange={e => setUsername(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleLogin()}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1.5">密码</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleLogin()}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all" />
          </div>

          {error && <p className="text-sm text-rose-500 bg-rose-50 px-4 py-2.5 rounded-xl">{error}</p>}

          <button onClick={handleLogin} disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-xl text-sm font-semibold hover:from-indigo-700 hover:to-blue-700 disabled:opacity-50 transition-all shadow-lg shadow-indigo-200">
            {loading ? "登录中..." : "登 录"}
          </button>
        </div>

        <p className="text-xs text-slate-400 text-center mt-6">默认账号 admin · 密码通过环境变量 ERP_ADMIN_PASSWORD 设置</p>
      </div>
    </div>
  )
}
