import { useNavigate } from "react-router-dom"
import { usePortal } from "../contexts/PortalContext"

export function TabBar() {
  const { openTabs, activeTabPath, closeTab } = usePortal()
  const navigate = useNavigate()

  if (openTabs.length <= 1) return null

  return (
    <div className="flex border-b border-slate-200 bg-white/80 backdrop-blur shrink-0 overflow-x-auto">
      {openTabs.map((tab) => {
        const isActive = activeTabPath === tab.path
        return (
          <div
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className={`
              flex items-center gap-1.5 px-4 py-2 text-sm cursor-pointer select-none
              border-r border-slate-100 transition-all whitespace-nowrap
              ${isActive
                ? "text-blue-600 bg-blue-50/60 border-b-2 border-b-blue-500 -mb-px font-medium"
                : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
              }
            `}
          >
            <span className="max-w-40 truncate">{tab.title}</span>
            {tab.path !== "/" && (
              <button
                className="ml-1 p-0.5 rounded hover:bg-slate-200 hover:text-slate-700 shrink-0 transition-colors"
                onClick={(e) => { e.stopPropagation(); closeTab(tab.path) }}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}
