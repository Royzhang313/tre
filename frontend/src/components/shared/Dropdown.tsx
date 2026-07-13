/** 自定义下拉选择 —— Portal 渲染选项到 body，不受父级 overflow 影响 */
import { useState, useRef, useEffect, useCallback } from "react"
import { createPortal } from "react-dom"

interface Option { id: string; name: string; model_name?: string }
interface Props {
  value: string
  onChange: (v: string) => void
  options: Option[]
  className?: string
  placeholder?: string
}

export function Dropdown({ value, onChange, options, className, placeholder }: Props) {
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState({ top: 0, left: 0, width: 0 })
  const btnRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const selected = options.find(o => o.id === value)

  const updatePos = useCallback(() => {
    if (!btnRef.current) return
    const r = btnRef.current.getBoundingClientRect()
    setPos({ top: r.bottom + 2, left: r.left, width: Math.max(r.width, 120) })
  }, [])

  useEffect(() => { if (open) updatePos() }, [open, updatePos])

  useEffect(() => {
    const fn = (e: MouseEvent) => {
      if (panelRef.current?.contains(e.target as Node)) return
      if (btnRef.current?.contains(e.target as Node)) return
      setOpen(false)
    }
    document.addEventListener("mousedown", fn)
    return () => document.removeEventListener("mousedown", fn)
  }, [])

  return (
    <>
      <button ref={btnRef} type="button"
        onClick={() => { updatePos(); setOpen(p => !p) }}
        className={`w-full text-left text-[10px] border border-slate-200 rounded px-1 py-0.5 bg-white hover:border-slate-300 truncate ${className || ""}`}>
        {selected ? (selected.name || selected.model_name || selected.id?.slice(0, 8)) : (placeholder || "选择...")}
      </button>
      {open && createPortal(
        <div ref={panelRef}
          className="fixed bg-white border border-slate-200 rounded-lg shadow-xl z-[9999] max-h-40 overflow-y-auto"
          style={{ top: pos.top, left: pos.left, width: pos.width }}>
          {options.map(o => (
            <button key={o.id} type="button"
              onClick={() => { onChange(o.id); setOpen(false) }}
              className={`w-full text-left px-2 py-1.5 text-[10px] hover:bg-indigo-50 transition-colors ${o.id === value ? "bg-indigo-50 text-indigo-700 font-medium" : "text-slate-700"}`}>
              {o.name || o.model_name || o.id.slice(0, 8)}
            </button>
          ))}
        </div>,
        document.body
      )}
    </>
  )
}
