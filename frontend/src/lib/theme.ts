/** 共享样式常量 —— 所有表单/列表统一使用 */

/** 通用输入框样式 */
export const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"

/** 小号输入框 */
export const INP_SM = "w-full px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-[10px] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400"

/** 表单标签样式 */
export const LBL = "block text-sm font-medium text-slate-600 mb-1.5"

/** 品牌颜色映射 —— 统一使用 */
export const BRAND_CHIP: Record<string, string> = {
  red:'bg-red-100 text-red-700',orange:'bg-orange-100 text-orange-700',amber:'bg-amber-100 text-amber-700',
  yellow:'bg-yellow-100 text-yellow-700',lime:'bg-lime-100 text-lime-700',green:'bg-green-100 text-green-700',
  emerald:'bg-emerald-100 text-emerald-700',teal:'bg-teal-100 text-teal-700',cyan:'bg-cyan-100 text-cyan-700',
  sky:'bg-sky-100 text-sky-700',blue:'bg-blue-100 text-blue-700',indigo:'bg-indigo-100 text-indigo-700',
  violet:'bg-violet-100 text-violet-700',purple:'bg-purple-100 text-purple-700',fuchsia:'bg-fuchsia-100 text-fuchsia-700',
  pink:'bg-pink-100 text-pink-700',rose:'bg-rose-100 text-rose-700',slate:'bg-slate-200 text-slate-700',
  gray:'bg-gray-200 text-gray-700',zinc:'bg-zinc-200 text-zinc-700',neutral:'bg-neutral-200 text-neutral-700',
  stone:'bg-stone-200 text-stone-700',warm:'bg-stone-100 text-stone-600',cool:'bg-slate-100 text-slate-600',
}

/** 标签色板 */
export const TAG_PALETTE = [
  { key: 'slate', dot: 'bg-slate-300', chip: 'bg-slate-50 text-slate-600 border-slate-200' },
  { key: 'red', dot: 'bg-red-400', chip: 'bg-red-50 text-red-600 border-red-200' },
  { key: 'orange', dot: 'bg-orange-400', chip: 'bg-orange-50 text-orange-600 border-orange-200' },
  { key: 'amber', dot: 'bg-amber-400', chip: 'bg-amber-50 text-amber-600 border-amber-200' },
  { key: 'yellow', dot: 'bg-yellow-400', chip: 'bg-yellow-50 text-yellow-600 border-yellow-200' },
  { key: 'lime', dot: 'bg-lime-400', chip: 'bg-lime-50 text-lime-600 border-lime-200' },
  { key: 'green', dot: 'bg-green-400', chip: 'bg-green-50 text-green-600 border-green-200' },
  { key: 'emerald', dot: 'bg-emerald-400', chip: 'bg-emerald-50 text-emerald-600 border-emerald-200' },
  { key: 'teal', dot: 'bg-teal-400', chip: 'bg-teal-50 text-teal-600 border-teal-200' },
  { key: 'cyan', dot: 'bg-cyan-400', chip: 'bg-cyan-50 text-cyan-600 border-cyan-200' },
  { key: 'sky', dot: 'bg-sky-400', chip: 'bg-sky-50 text-sky-600 border-sky-200' },
  { key: 'blue', dot: 'bg-blue-400', chip: 'bg-blue-50 text-blue-600 border-blue-200' },
  { key: 'indigo', dot: 'bg-indigo-400', chip: 'bg-indigo-50 text-indigo-600 border-indigo-200' },
  { key: 'violet', dot: 'bg-violet-400', chip: 'bg-violet-50 text-violet-600 border-violet-200' },
  { key: 'purple', dot: 'bg-purple-400', chip: 'bg-purple-50 text-purple-600 border-purple-200' },
  { key: 'fuchsia', dot: 'bg-fuchsia-400', chip: 'bg-fuchsia-50 text-fuchsia-600 border-fuchsia-200' },
  { key: 'pink', dot: 'bg-pink-400', chip: 'bg-pink-50 text-pink-600 border-pink-200' },
  { key: 'rose', dot: 'bg-rose-400', chip: 'bg-rose-50 text-rose-600 border-rose-200' },
]
