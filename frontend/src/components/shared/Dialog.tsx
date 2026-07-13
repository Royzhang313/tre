/** 系统级对话框 & 提示组件 —— 替换原生 alert/confirm */
import { createContext, useContext, useState, useCallback, type ReactNode } from "react"

// ============================================================
// Toast
// ============================================================
interface ToastCtx { show: (msg: string, type?: "success" | "error" | "info") => void }
const ToastCtx = createContext<ToastCtx>({ show: () => {} })
export const useToast = () => useContext(ToastCtx)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<{ id: number; msg: string; type: string }[]>([])
  const show = useCallback((msg: string, type = "info") => {
    const id = Date.now()
    setToasts(p => [...p, { id, msg, type }])
    setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 3000)
  }, [])
  // 挂载全局函数
  _toast = show
  return (
    <ToastCtx.Provider value={{ show }}>
      {children}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map(t => {
          const bg = t.type === "success" ? "bg-emerald-600" : t.type === "error" ? "bg-rose-600" : "bg-slate-800"
          return (
            <div key={t.id} className={`${bg} text-white text-sm px-4 py-2.5 rounded-xl shadow-lg pointer-events-auto animate-in slide-in-from-top-2 fade-in duration-200`}>
              {t.msg}
            </div>
          )
        })}
      </div>
    </ToastCtx.Provider>
  )
}

// ============================================================
// Confirm 对话框
// ============================================================
interface ConfirmOpts { title?: string; message: string; confirmLabel?: string; cancelLabel?: string; danger?: boolean }
const ConfirmCtx = createContext<{ confirm: (opts: ConfirmOpts) => Promise<boolean> }>({ confirm: async () => false })
export const useConfirm = () => useContext(ConfirmCtx)

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<{ opts: ConfirmOpts; resolve: (v: boolean) => void } | null>(null)
  const confirm = useCallback((opts: ConfirmOpts): Promise<boolean> => {
    return new Promise(resolve => setState({ opts, resolve }))
  }, [])
  // 挂载全局函数
  _confirm = confirm
  const close = (val: boolean) => {
    state?.resolve(val)
    setState(null)
  }
  return (
    <ConfirmCtx.Provider value={{ confirm }}>
      {children}
      {state && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center">
          <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => close(false)} />
          <div className="relative bg-white rounded-2xl shadow-2xl w-[400px] p-6 animate-in zoom-in-95 fade-in duration-200">
            <h3 className="text-base font-bold text-slate-800 mb-2">{state.opts.title || "确认操作"}</h3>
            <p className="text-sm text-slate-500 mb-6">{state.opts.message}</p>
            <div className="flex gap-3 justify-end">
              <button onClick={() => close(false)} className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm hover:bg-slate-50">
                {state.opts.cancelLabel || "取消"}
              </button>
              <button onClick={() => close(true)}
                className={`px-4 py-2 rounded-lg text-sm font-medium text-white ${state.opts.danger ? "bg-rose-600 hover:bg-rose-700" : "bg-indigo-600 hover:bg-indigo-700"}`}>
                {state.opts.confirmLabel || "确定"}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmCtx.Provider>
  )
}

// ============================================================
// 全局快捷函数（无需 hooks，可在任何地方调用）
// ============================================================
type ConfirmFn = (opts: ConfirmOpts) => Promise<boolean>
type ToastFn = (msg: string, type?: "success" | "error" | "info") => void

let _confirm: ConfirmFn = async (opts) => window.confirm(opts.message)
let _toast: ToastFn = (msg) => { /* noop until mounted */ }

/** 替代 window.confirm() */
export function sysConfirm(msg: string, danger?: boolean): Promise<boolean> {
  return _confirm({ message: msg, danger })
}

/** 替代 alert() */
export function sysToast(msg: string, type: "success" | "error" | "info" = "info"): void {
  _toast(msg, type)
}

/** Provider 内部挂载全局函数 */
function useMountGlobal({ confirm, toast }: { confirm: ConfirmFn; toast: ToastFn }) {
  _confirm = confirm
  _toast = toast
}
