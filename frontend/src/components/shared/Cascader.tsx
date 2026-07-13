/** 通用级联多选组件 —— 悬停展开子级，点击外部自动关闭 */
import { useState, useEffect, useRef } from "react"

export interface CascaderOption {
  value: string; label: string; children?: CascaderOption[]
}

export function Cascader({ label, options, selected, onChange, isOpen, onToggle }: {
  label: string; options: CascaderOption[]; selected: string[]; onChange: (v: string) => void
  isOpen: boolean; onToggle: () => void
}) {
  const [hovered, setHovered] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const hoverOpt = options.find(o => o.value === hovered)
  const children = hoverOpt?.children ?? []

  // 点击外部区域自动关闭
  useEffect(() => {
    if (!isOpen) return
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onToggle()
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [isOpen, onToggle])

  return (
    <div className="relative" ref={containerRef}>
      <button
        onMouseDown={e => { e.stopPropagation(); onToggle() }}
        className={`px-3 py-1.5 border rounded-lg text-xs flex items-center gap-1 whitespace-nowrap ${selected.length > 0 ? "border-indigo-300 bg-indigo-50 text-indigo-700" : "border-slate-200 bg-white text-slate-600"}`}
      >
        {label}
        {selected.length > 0 && <span className="bg-indigo-600 text-white w-4 h-4 rounded-full text-[10px] flex items-center justify-center">{selected.length}</span>}
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
      </button>
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 flex bg-white border border-slate-200 rounded-lg shadow-xl z-50" onMouseDown={e => e.stopPropagation()}>
          <div className="w-40 max-h-56 overflow-y-auto p-2">
            {options.map(o => (
              <label
                key={o.value} onClick={e => { e.stopPropagation(); onChange(o.value) }}
                onMouseEnter={() => setHovered(o.value)}
                className={`flex items-center gap-2 px-2 py-1.5 rounded text-xs cursor-pointer hover:bg-slate-50 ${selected.includes(o.value) ? "text-indigo-700 font-medium bg-indigo-50" : "text-slate-600"}`}
              >
                <CheckMark checked={selected.includes(o.value)} />
                <span className="flex-1 truncate">{o.label}</span>
                {(o.children?.length ?? 0) > 0 && <svg className="w-3 h-3 text-slate-300 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>}
              </label>
            ))}
          </div>
          {hoverOpt && children.length > 0 && (
            <div className="w-40 max-h-56 overflow-y-auto p-2 border-l border-slate-100">
                {children.map(c => (
                <label
                  key={c.value} onClick={e => { e.stopPropagation(); onChange(c.value) }}
                  className={`flex items-center gap-2 px-2 py-1.5 rounded text-xs cursor-pointer hover:bg-slate-50 ${selected.includes(c.value) ? "text-indigo-700 font-medium bg-indigo-50" : "text-slate-600"}`}
                >
                  <CheckMark checked={selected.includes(c.value)} />
                  <span className="truncate">{c.label}</span>
                </label>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function CheckMark({ checked }: { checked: boolean }) {
  return (
    <span className={`w-3 h-3 rounded border-2 flex items-center justify-center shrink-0 ${checked ? "border-indigo-500 bg-indigo-500" : "border-slate-300"}`}>
      {checked && <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
    </span>
  )
}
