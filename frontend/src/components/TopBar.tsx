/** 顶部导航栏 —— Premium Design */
import { Link, useLocation, useNavigate } from "react-router-dom"
import { useState, useRef, useEffect } from "react"
import { useAuth } from "../contexts/AuthContext"

interface NavItem { label: string; route?: string; children?: { label: string; route: string; desc?: string }[] }

const NAV: NavItem[] = [
  { label: "首页", route: "/" },
  { label: "采购", route: "/purchase-contracts" },
  { label: "销售", route: "/sales-contracts" },
  { label: "计划", route: "/shipping/plans" },
  { label: "财务", route: "/finance" },
  {
    label: "基础资料",
    children: [
      { label: "主体公司", route: "/basedata/companies", desc: "执行主体公司抬头" },
      { label: "企业管理", route: "/basedata/enterprises", desc: "供应商/客户企业信息" },
      { label: "撮合平台", route: "/basedata/commission-platforms", desc: "撮合平台管理" },
      { label: "品牌管理", route: "/brand", desc: "品牌、仓库、型号" },
    ],
  },
  {
    label: "系统",
    children: [
      { label: "用户管理", route: "/auth/users", desc: "用户账号与角色分配" },
      { label: "角色管理", route: "/auth/roles", desc: "角色与权限配置" },
      { label: "OCR 配置", route: "/system/ocr", desc: "银行回单 OCR 识别配置" },
    ],
  },
  { label: "回收站", route: "/recycle-bin" },
]

function UserMenu() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const fn = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener("mousedown", fn)
    return () => document.removeEventListener("mousedown", fn)
  }, [open])

  const initial = (user?.display_name || user?.username || "U")[0].toUpperCase()
  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(p => !p)} className="flex items-center gap-2 pl-3 border-l border-slate-200 hover:opacity-80 transition-opacity">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center text-sm font-bold shadow-sm">{initial}</div>
        <span className="text-sm font-medium text-slate-700 hidden sm:block">{user?.display_name || user?.username || "未登录"}</span>
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-2 bg-white border border-slate-200 rounded-xl shadow-xl z-50 py-1 min-w-[140px]">
          <div className="px-4 py-2 border-b border-slate-100">
            <p className="text-sm font-medium text-slate-800">{user?.username}</p>
            <p className="text-xs text-slate-400">{user?.roles?.join(", ") || ""}</p>
          </div>
          <button onClick={() => { setOpen(false); logout(); nav("/login") }} className="w-full text-left px-4 py-2 text-sm text-slate-600 hover:bg-slate-50 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
            退出登录
          </button>
        </div>
      )}
    </div>
  )
}

export function TopBar() {
  const loc = useLocation()
  const { hasPermission } = useAuth()
  const [open, setOpen] = useState<string | null>(null)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mobileSubOpen, setMobileSubOpen] = useState<string | null>(null)
  const ref = useRef<HTMLDivElement>(null)

  // 根据权限过滤菜单
  const navFiltered = NAV.filter(item => {
    if (item.label === "首页" || item.label === "回收站") return true
    if (item.label === "采购") return hasPermission("purchase-contract.contract.read")
    if (item.label === "销售") return true // 销售合同暂无独立权限
    if (item.label === "系统") return hasPermission("auth.user.read") || hasPermission("auth.role.manage")
    if (item.label === "基础资料") return hasPermission("basedata.enterprise.read")
    return true
  })

  useEffect(() => {
    const fn = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(null) }
    document.addEventListener("mousedown", fn)
    return () => document.removeEventListener("mousedown", fn)
  }, [])

  const active = (r?: string) => {
    if (!r) return false
    if (r === "/") return loc.pathname === "/"
    return loc.pathname.startsWith(r)
  }

  return (
    <>
      <header className="h-16 bg-white/80 backdrop-blur-xl border-b border-slate-200/60 flex items-center shrink-0 z-30 sticky top-0" ref={ref}>
      {/* Logo */}
      <Link to="/" className="flex items-center gap-3 pl-4 sm:pl-6 lg:pl-8 pr-3 sm:pr-4 lg:pr-6 h-full shrink-0 group">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 text-white flex items-center justify-center shadow-lg shadow-indigo-200 group-hover:scale-105 transition-transform">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>
        </div>
        <div>
          <span className="text-lg font-bold text-slate-900 tracking-tight">PET Trade</span>
          <span className="text-[10px] text-slate-400 font-medium block -mt-0.5 tracking-wide uppercase">Bottle Flake</span>
        </div>
      </Link>

      {/* 导航链接 */}
      <nav className="hidden lg:flex items-center h-full gap-1 ml-6">
        {navFiltered.map(item => {
          const isActive = active(item.route)
          if (item.children) {
            const isOpen = open === item.label
            return (
              <div key={item.label} className="relative h-full flex items-center">
                <button onClick={() => setOpen(isOpen ? null : item.label)}
                  className={`flex items-center gap-1.5 px-4 h-full text-sm font-medium transition-all duration-200 border-b-[3px] -mb-px
                    ${isActive || isOpen ? "text-indigo-600 border-indigo-500 bg-indigo-50/30" : "text-slate-600 border-transparent hover:text-slate-900 hover:bg-slate-50"}`}>
                  {item.label}
                  <svg className={`w-4 h-4 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </button>
                {isOpen && (
                  <div className="absolute top-full left-0 mt-2 w-56 bg-white rounded-2xl border border-slate-100 shadow-2xl shadow-slate-200/50 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                    {item.children.map(c => (
                      <Link key={c.route} to={c.route} onClick={() => setOpen(null)}
                        className={`block px-5 py-3 transition-colors ${loc.pathname.startsWith(c.route) ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-50"}`}>
                        <p className="text-sm font-semibold">{c.label}</p>
                        {c.desc && <p className="text-xs text-slate-400 mt-0.5">{c.desc}</p>}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )
          }
          return (
            <Link key={item.label} to={item.route!}
              className={`flex items-center px-4 h-full text-sm font-medium transition-all duration-200 border-b-[3px] -mb-px
                ${isActive ? "text-indigo-600 border-indigo-500 bg-indigo-50/30" : "text-slate-600 border-transparent hover:text-slate-900 hover:bg-slate-50"}`}>
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="flex-1" />

      {/* 汉堡菜单按钮 - 仅移动端显示 */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden p-2 mr-1 rounded-lg hover:bg-slate-100 transition-colors"
        aria-label="切换菜单"
      >
        {mobileOpen ? (
          <svg className="w-6 h-6 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>

      {/* 右侧 */}
      <div className="flex items-center gap-3 pr-4 sm:pr-6 lg:pr-8">
        <UserMenu />
      </div>
    </header>

      {/* 移动端导航菜单 */}
      {mobileOpen && (
        <div className="lg:hidden bg-white border-b border-slate-200 shadow-lg z-20">
          <nav className="flex flex-col p-2">
            {navFiltered.map(item => {
              const isActive = active(item.route)
              if (item.children) {
                const isSubOpen = mobileSubOpen === item.label
                return (
                  <div key={item.label}>
                    <button
                      onClick={() => setMobileSubOpen(isSubOpen ? null : item.label)}
                      className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium ${isActive ? "text-indigo-600 bg-indigo-50" : "text-slate-700 hover:bg-slate-50"}`}
                    >
                      {item.label}
                      <svg className={`w-4 h-4 transition-transform duration-200 ${isSubOpen ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {isSubOpen && (
                      <div className="ml-4 border-l-2 border-slate-100 pl-2 mt-1">
                        {item.children.map(c => (
                          <Link key={c.route} to={c.route} onClick={() => { setMobileOpen(false); setMobileSubOpen(null) }}
                            className={`block px-3 py-2 rounded-lg text-sm ${loc.pathname.startsWith(c.route) ? "text-indigo-600 bg-indigo-50 font-medium" : "text-slate-600 hover:bg-slate-50"}`}>
                            {c.label}
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                )
              }
              return (
                <Link key={item.label} to={item.route!} onClick={() => setMobileOpen(false)}
                  className={`px-3 py-2.5 rounded-lg text-sm font-medium ${isActive ? "text-indigo-600 bg-indigo-50" : "text-slate-700 hover:bg-slate-50"}`}>
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>
      )}
    </>
  )
}
