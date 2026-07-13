/** AuthContext —— 存储当前用户信息 + token */
import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react"
import { apiGet } from "../api/client"

interface UserInfo {
  id: string; username: string; email: string | null; display_name: string | null
  status: string; roles: string[]; permissions: string[]
}

interface AuthState {
  user: UserInfo | null
  token: string | null
  login: (token: string) => Promise<void>
  logout: () => void
  hasPermission: (code: string) => boolean
  isAuthenticated: boolean
}

const AuthCtx = createContext<AuthState>({
  user: null, token: null,
  login: async () => {}, logout: () => {},
  hasPermission: () => false, isAuthenticated: false,
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("auth_token"))

  const fetchUser = useCallback(async (t: string) => {
    // 确保 token 已设置以便 /auth/me 能通过鉴权
    localStorage.setItem("auth_token", t)
    const data = await apiGet<any>("/auth/me")
    setUser({
      id: data.id, username: data.username, email: data.email,
      display_name: data.display_name, status: data.status,
      roles: data.roles ?? [], permissions: data.permissions ?? [],
    })
  }, [])

  const login = useCallback(async (t: string) => {
    localStorage.setItem("auth_token", t)
    setToken(t)
    await fetchUser(t)
  }, [fetchUser])

  const logout = useCallback(() => {
    localStorage.removeItem("auth_token")
    setToken(null); setUser(null)
  }, [])

  const hasPermission = useCallback((code: string) => {
    return user?.permissions?.includes(code) ?? false
  }, [user])

  // 启动时如果有 token 就加载用户
  useEffect(() => {
    if (token) fetchUser(token).catch(() => { setUser(null); localStorage.removeItem("auth_token"); setToken(null) })
  }, [])  // eslint-disable-line

  return (
    <AuthCtx.Provider value={{ user, token, login, logout, hasPermission, isAuthenticated: !!user }}>
      {children}
    </AuthCtx.Provider>
  )
}

export function useAuth() { return useContext(AuthCtx) }
