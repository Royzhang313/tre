/** 自定义日期选择器 —— 系统 UI 风格 */
import { useState, useRef, useEffect } from "react"

const MONTHS = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"]
const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"]

interface Props { value: string; onChange: (v: string) => void; placeholder?: string }

export function DatePicker({ value, onChange, placeholder = "选择日期" }: Props) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const d = value ? new Date(value + "T00:00:00") : new Date()
  const [viewYear, setViewYear] = useState(d.getFullYear())
  const [viewMonth, setViewMonth] = useState(d.getMonth())

  useEffect(() => {
    const fn = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener("mousedown", fn); return () => document.removeEventListener("mousedown", fn)
  }, [])

  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()
  const firstDay = new Date(viewYear, viewMonth, 1).getDay()
  const today = new Date(); today.setHours(0, 0, 0, 0)

  const select = (day: number) => {
    const m = String(viewMonth + 1).padStart(2, "0")
    const dd = String(day).padStart(2, "0")
    onChange(`${viewYear}-${m}-${dd}`); setOpen(false)
  }

  const prevMonth = () => { if (viewMonth === 0) { setViewYear(viewYear - 1); setViewMonth(11) } else setViewMonth(viewMonth - 1) }
  const nextMonth = () => { if (viewMonth === 11) { setViewYear(viewYear + 1); setViewMonth(0) } else setViewMonth(viewMonth + 1) }

  const isSelected = (day: number) => {
    if (!value) return false
    const m = String(viewMonth + 1).padStart(2, "0")
    const dd = String(day).padStart(2, "0")
    return value === `${viewYear}-${m}-${dd}`
  }
  const isToday = (day: number) => {
    const m = String(viewMonth + 1).padStart(2, "0")
    const dd = String(day).padStart(2, "0")
    const target = new Date(`${viewYear}-${m}-${dd}T00:00:00`)
    return target.getTime() === today.getTime()
  }

  return (
    <div ref={ref} className="relative">
      <button type="button" onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-1.5 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-left focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all">
        <svg className="w-4 h-4 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
        <span className={value ? "text-slate-700" : "text-slate-300"}>{value || ""}</span>
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1.5 bg-white rounded-xl border border-slate-200 shadow-xl shadow-slate-200/50 z-[9999] p-3 w-64 animate-in fade-in slide-in-from-top-2 duration-150">
          {/* 月份切换 */}
          <div className="flex items-center justify-between mb-3">
            <button onClick={prevMonth} className="w-7 h-7 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-500"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg></button>
            <span className="text-sm font-semibold text-slate-800">{viewYear}年 {MONTHS[viewMonth]}</span>
            <button onClick={nextMonth} className="w-7 h-7 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-500"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg></button>
          </div>

          {/* 星期 */}
          <div className="grid grid-cols-7 mb-1">
            {WEEKDAYS.map(w => <div key={w} className="text-center text-xs text-slate-400 py-1 font-medium">{w}</div>)}
          </div>

          {/* 日期 */}
          <div className="grid grid-cols-7 gap-0.5">
            {Array.from({ length: firstDay }, (_, i) => <div key={`e${i}`} />)}
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map(day => {
              const sel = isSelected(day); const tdy = isToday(day)
              return (
                <button key={day} onClick={() => select(day)}
                  className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors
                    ${sel ? "bg-indigo-600 text-white shadow-sm shadow-indigo-200" :
                      tdy ? "bg-indigo-50 text-indigo-600" :
                      "text-slate-600 hover:bg-slate-100"}`}>
                  {day}
                </button>
              )
            })}
          </div>

          {/* 快捷操作 */}
          <div className="flex gap-2 mt-3 pt-3 border-t border-slate-100">
            <button onClick={() => { onChange(""); setOpen(false) }}
              className="flex-1 px-3 py-1.5 text-xs font-medium text-slate-500 hover:bg-slate-100 rounded-lg transition-colors">清除</button>
            <button onClick={() => { const t = new Date(); const m = String(t.getMonth()+1).padStart(2,"0"); const d = String(t.getDate()).padStart(2,"0"); onChange(`${t.getFullYear()}-${m}-${d}`); setOpen(false) }}
              className="flex-1 px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors">今天</button>
          </div>
        </div>
      )}
    </div>
  )
}
