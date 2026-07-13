/** 通用分页组件 —— 默认 50 条/页，支持选择每页条数 */
export interface PaginationProps {
  page: number
  pageSize: number
  total: number
  pages: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
  pageSizeOptions?: number[]
}

const DEFAULT_SIZES = [10, 20, 50, 100]

export function Pagination({ page, pageSize, total, pages, onPageChange, onPageSizeChange, pageSizeOptions = DEFAULT_SIZES }: PaginationProps) {
  if (total === 0 && pages <= 1) return null

  // 页码按钮范围：当前页前后各 2 页，最多 7 个按钮
  const start = Math.max(1, page - 2)
  const end = Math.min(pages, page + 2)
  const nums: number[] = []
  for (let i = start; i <= end; i++) nums.push(i)

  return (
    <div className="flex items-center justify-between pt-3 text-xs text-slate-500">
      <div className="flex items-center gap-2">
        <span>共 <b className="text-slate-700">{total}</b> 条</span>
        <span className="text-slate-300">|</span>
        <select
          value={pageSize}
          onChange={e => onPageSizeChange(Number(e.target.value))}
          className="border border-slate-200 rounded-md px-2 py-1 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
        >
          {pageSizeOptions.map(s => (
            <option key={s} value={s}>{s} 条/页</option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-1">
        <button
          disabled={page <= 1}
          onClick={() => onPageChange(1)}
          className="px-2 py-1 rounded hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
          title="首页"
        >«</button>
        <button
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          className="px-2 py-1 rounded hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
        >‹</button>

        {start > 1 && (
          <>
            <button onClick={() => onPageChange(1)} className="px-2.5 py-1 rounded hover:bg-slate-100 text-slate-400">1</button>
            {start > 2 && <span className="px-1 text-slate-300">…</span>}
          </>
        )}

        {nums.map(n => (
          <button
            key={n}
            onClick={() => onPageChange(n)}
            className={`px-2.5 py-1 rounded ${n === page ? "bg-indigo-600 text-white font-medium" : "hover:bg-slate-100 text-slate-600"}`}
          >{n}</button>
        ))}

        {end < pages && (
          <>
            {end < pages - 1 && <span className="px-1 text-slate-300">…</span>}
            <button onClick={() => onPageChange(pages)} className="px-2.5 py-1 rounded hover:bg-slate-100 text-slate-400">{pages}</button>
          </>
        )}

        <button
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
          className="px-2 py-1 rounded hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
        >›</button>
        <button
          disabled={page >= pages}
          onClick={() => onPageChange(pages)}
          className="px-2 py-1 rounded hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
          title="末页"
        >»</button>
      </div>
    </div>
  )
}
