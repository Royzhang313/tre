/** 通用单选下拉框 —— 支持取消选择（点击已选项清空 + 清除按钮） */
import { useState, useRef, useEffect } from "react"

export function SearchableSelect({ value, onChange, options, disabled, className }: {
  value: string; onChange: (v: string) => void; options: { id: string; name: string }[]
  disabled?: boolean; className: string
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // 点击外部关闭
  useEffect(() => {
    if (!open) return
    const fn = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", fn)
    return () => document.removeEventListener("mousedown", fn)
  }, [open])

  const selected = options.find(o => o.id === value)

  const handleSelect = (id: string) => {
    // 点击已选项 → 取消选择
    if (id === value) {
      onChange("")
    } else {
      onChange(id)
    }
    setOpen(false)
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => { if (!disabled) setOpen(p => !p) }}
        disabled={disabled}
        className={`${className} text-left flex items-center justify-between gap-1 ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
      >
        <span className={selected ? "text-slate-700 truncate" : "text-slate-300"}>{selected ? selected.name : ""}</span>
        <span className="flex items-center gap-1 shrink-0">
          {/* 清除按钮 — 有值时显示 */}
          {selected && !disabled && (
            <span
              onClick={e => { e.stopPropagation(); onChange("") }}
              className="text-slate-400 hover:text-slate-600 leading-none text-sm"
              title="取消选择"
            >×</span>
          )}
          <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
        </span>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-max min-w-[100px] bg-white border border-slate-200 rounded-xl shadow-2xl z-[9999] max-h-56 overflow-y-auto" onMouseDown={e => e.stopPropagation()}>
          {options.length === 0 && <div className="px-3 py-4 text-xs text-slate-400 whitespace-nowrap text-center">暂无数据</div>}
          {options.map(o => (
            <button
              key={o.id}
              onClick={() => handleSelect(o.id)}
              className={`block w-full text-left px-3 py-2 text-xs hover:bg-indigo-50 transition-colors whitespace-nowrap ${value === o.id ? "bg-indigo-50 text-indigo-700 font-medium" : "text-slate-700"}`}
            >{o.name}{value === o.id && <span className="ml-1 text-indigo-400 text-[10px]">✓</span>}</button>
          ))}
        </div>
      )}
    </div>
  )
}
