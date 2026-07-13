import { useState, useCallback, useEffect, useRef } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiPut, apiPatch, apiDelete } from "../api/client"
import type { PageSchema, ActionDef, PageResponse } from "../api/ui"
import { sysToast, sysConfirm } from "./shared/Dialog"

/** 搜索防抖 hook —— 300ms 延迟 */
function useDebounce<T>(value: T, delay: number = 300): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

// ============================================================
// 可执行操作按钮
// ============================================================

function ActionButton({ action, rowId, onSuccess }: {
  action: ActionDef
  rowId?: string
  onSuccess: () => void
}) {
  const [loading, setLoading] = useState(false)

  const handleClick = async () => {
    if (action.confirm_dialog && !window.sysConfirm(action.confirm_dialog)) return
    setLoading(true)
    try {
      let path = action.http_path ?? ""
      if (rowId) path = path.replace("{id}", rowId)
      const method = action.http_method?.toUpperCase() ?? "POST"
      if (method === "POST") await apiPost(path)
      else if (method === "PUT") await apiPut?.(path) ?? apiPost(path)
      else if (method === "PATCH") await apiPatch(path)
      else if (method === "DELETE") await apiDelete(path)
      else await apiPost(path)
      onSuccess()
    } catch (err) {
      sysToast(err instanceof Error ? err.message : "操作失败")
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="px-2 py-0.5 text-xs rounded border border-slate-300 text-slate-600 hover:bg-slate-100 hover:border-slate-400 disabled:opacity-50 transition-colors"
      title={action.capability}
    >
      {loading ? "…" : action.label}
    </button>
  )
}

// ============================================================
// 分页控件
// ============================================================

function Pagination({ page, pages, total, onChange }: {
  page: number; pages: number; total: number; onChange: (p: number) => void
}) {
  if (pages <= 1) return null

  // 页码按钮范围: current +/- 2
  const start = Math.max(1, page - 2)
  const end = Math.min(pages, page + 2)
  const nums: number[] = []
  for (let i = start; i <= end; i++) nums.push(i)

  return (
    <div className="flex items-center justify-between mt-3 text-sm text-slate-500">
      <span>共 {total} 条，第 {page}/{pages} 页</span>
      <div className="flex gap-0.5">
        <PageBtn disabled={page <= 1} onClick={() => onChange(1)}>首页</PageBtn>
        <PageBtn disabled={page <= 1} onClick={() => onChange(page - 1)}>上页</PageBtn>
        {nums.map(n => (
          <PageBtn key={n} active={n === page} onClick={() => onChange(n)}>{n}</PageBtn>
        ))}
        <PageBtn disabled={page >= pages} onClick={() => onChange(page + 1)}>下页</PageBtn>
        <PageBtn disabled={page >= pages} onClick={() => onChange(pages)}>末页</PageBtn>
      </div>
    </div>
  )
}

function PageBtn({ active, disabled, onClick, children }: {
  active?: boolean; disabled?: boolean; onClick: () => void; children: import("react").ReactNode
}) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={`px-2 py-0.5 rounded text-xs border transition-colors
        ${active ? "bg-blue-600 text-white border-blue-600" : "border-slate-200 hover:bg-slate-50"}
        ${disabled ? "opacity-30 cursor-not-allowed" : ""}`}
    >
      {children}
    </button>
  )
}

// ============================================================
// ListPage
// ============================================================

export function ListPage({ page }: { page: PageSchema }) {
  const columns = page.list_config?.columns ?? []
  const filters = page.list_config?.filters ?? []
  const queryClient = useQueryClient()

  // 状态
  const [pageNum, setPageNum] = useState(1)
  const [search, setSearch] = useState("")
  const debouncedSearch = useDebounce(search, 300)   // 搜索防抖
  const [filterValues, setFilterValues] = useState<Record<string, string>>({})
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")

  // 构建查询参数 —— 使用防抖后的搜索值
  const buildQuery = useCallback(() => {
    const qp = new URLSearchParams()
    qp.set("page", String(pageNum))
    qp.set("page_size", "20")
    if (debouncedSearch) qp.set("search", debouncedSearch)
    if (sortBy) {
      qp.set("sort_by", sortBy)
      qp.set("sort_order", sortOrder)
    }
    Object.entries(filterValues).forEach(([k, v]) => { if (v) qp.set(k, v) })
    return qp.toString()
  }, [pageNum, debouncedSearch, filterValues, sortBy, sortOrder])

  // 数据获取
  const module = page.permission.split(".")[0]
  const entityPath = page.entity?.toLowerCase() + "s"
  const { data } = useQuery({
    queryKey: ["list", page.entity, pageNum, debouncedSearch, filterValues, sortBy, sortOrder],
    queryFn: () => apiGet<PageResponse>(`/${module}/${entityPath}?${buildQuery()}`),
    enabled: !!page.entity,
  })

  const items: Record<string, unknown>[] = data?.items ?? []
  const total = data?.total ?? 0
  const pages = data?.pages ?? 1

  // Action 分类
  const headerActions = page.actions.filter(a => a.name === "create")
  const rowActions = page.actions.filter(a => a.name !== "create")

  // 刷新回调
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["list", page.entity] })

  // 列排序
  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(prev => prev === "desc" ? "asc" : "desc")
    } else {
      setSortBy(field)
      setSortOrder("desc")
    }
    setPageNum(1)
  }

  return (
    <div>
      {/* 标题 + 搜索 + 新建按钮 */}
      <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
        <h2 className="text-base font-semibold text-slate-700">{page.title}</h2>
        <div className="flex items-center gap-2">
          {/* 搜索 */}
          <input
            type="text"
            value={search}
            onChange={e => { setSearch(e.target.value); setPageNum(1) }}
           
            className="border border-slate-300 rounded-md px-2.5 py-1 text-sm w-48 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-300"
          />
          {/* 新建操作 */}
          {headerActions.map((a, i) => (
            <ActionButton key={i} action={a} onSuccess={refresh} />
          ))}
        </div>
      </div>

      {/* 过滤栏 */}
      {filters.length > 0 && (
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          {filters.map(f => (
            <div key={f.field} className="flex items-center gap-1">
              <label className="text-xs text-slate-500">{f.label}:</label>
              {f.filter_type === "select" && f.options ? (
                <select
                  value={filterValues[f.field] ?? ""}
                  onChange={e => {
                    setFilterValues(prev => ({ ...prev, [f.field]: e.target.value }))
                    setPageNum(1)
                  }}
                  className="border border-slate-300 rounded px-1.5 py-0.5 text-xs"
                >
                  <option value="">全部</option>
                  {f.options.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={filterValues[f.field] ?? ""}
                  onChange={e => {
                    setFilterValues(prev => ({ ...prev, [f.field]: e.target.value }))
                    setPageNum(1)
                  }}
                 
                  className="border border-slate-300 rounded px-1.5 py-0.5 text-xs w-20"
                />
              )}
            </div>
          ))}
          {/* 清除过滤 */}
          {Object.values(filterValues).some(v => v) && (
            <button
              onClick={() => setFilterValues({})}
              className="text-xs text-blue-600 hover:underline"
            >
              清除
            </button>
          )}
        </div>
      )}

      {/* 表格 */}
      <div className="overflow-x-auto border border-slate-200 rounded-lg">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              {columns.map(c => (
                <th
                  key={c.field}
                  onClick={() => handleSort(c.field)}
                  className="text-left px-3 py-2 font-medium text-slate-600 cursor-pointer hover:bg-slate-100 select-none transition-colors"
                >
                  {c.header}
                  {sortBy === c.field && (
                    <span className="ml-1 text-blue-600">{sortOrder === "desc" ? "▾" : "▴"}</span>
                  )}
                </th>
              ))}
              {rowActions.length > 0 && <th className="px-3 py-2 w-24 text-left font-medium text-slate-600">操作</th>}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (rowActions.length > 0 ? 1 : 0)} className="px-3 py-8 text-center text-slate-400">
                  暂无数据
                </td>
              </tr>
            ) : items.map((row, i) => (
              <tr key={i} className="border-t border-slate-100 hover:bg-slate-50 transition-colors">
                {columns.map(c => (
                  <td key={c.field} className="px-3 py-2 text-slate-700">
                    {String(row[c.field] ?? "-")}
                  </td>
                ))}
                {rowActions.length > 0 && (
                  <td className="px-3 py-2">
                    <div className="flex gap-1">
                      {rowActions.map((a, j) => (
                        <ActionButton
                          key={j}
                          action={a}
                          rowId={String(row.id ?? "")}
                          onSuccess={refresh}
                        />
                      ))}
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      <Pagination page={data?.page ?? 1} pages={pages} total={total} onChange={p => setPageNum(p)} />
    </div>
  )
}
