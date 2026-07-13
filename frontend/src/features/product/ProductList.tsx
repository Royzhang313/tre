/** 产品管理列表 */
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate } from "react-router-dom"
import { apiGet, apiDelete, apiPatch } from "../../api/client"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

interface Product {
  id: string
  product_code: string
  name: string
  brand_name: string | null
  model_type: string | null
  warehouse_name: string | null
  unit: string
  default_purchase_price: number
  default_sale_price: number
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

const MODEL_TYPE_LABELS: Record<string, string> = {
  "热料": "热料",
  "冷料": "冷料",
  "蓝白片": "蓝白片",
  "绿片": "绿片",
  "3A白片": "3A白片",
}

function StatusBadge({ active }: { active: boolean }) {
  return active
    ? <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">启用</span>
    : <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-400 border border-slate-200">停用</span>
}

export function ProductList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState("")
  const [modelType, setModelType] = useState("")
  const [page, setPage] = useState(1)
  const pageSize = 20

  const params = new URLSearchParams()
  params.set("page", String(page))
  params.set("page_size", String(pageSize))
  if (search) params.set("search", search)
  if (modelType) params.set("model_type", modelType)

  const { data, isLoading } = useQuery({
    queryKey: ["products", search, modelType, page],
    queryFn: () => apiGet<{ items: Product[]; total: number; page: number; page_size: number }>(
      `/products?${params.toString()}`
    ),
  })

  const toggleActive = useMutation({
    mutationFn: (id: string) => apiPatch(`/products/${id}/toggle-active`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["products"] }); sysToast("操作成功", "success") },
  })

  const deleteProduct = useMutation({
    mutationFn: (id: string) => apiDelete(`/products/${id}`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["products"] }); sysToast("已停用", "success") },
  })

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-800">产品管理</h1>
          <p className="text-sm text-slate-500 mt-0.5">管理 PET 瓶片贸易产品目录</p>
        </div>
        <button
          onClick={() => navigate("/products/new")}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm"
        >
          + 新增产品
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <input
          type="text"
          placeholder="搜索产品名称/编码/品牌..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm w-64 focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-300"
        />
        <select
          value={modelType}
          onChange={e => { setModelType(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:border-indigo-300"
        >
          <option value="">全部型号</option>
          {Object.entries(MODEL_TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <div className="text-4xl mb-3">📦</div>
          <div>暂无产品数据</div>
          <button onClick={() => navigate("/products/new")} className="mt-2 text-indigo-600 text-sm hover:underline">创建第一个产品</button>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">编码</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">产品名称</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">品牌</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">型号</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">默认仓库</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase">采购价</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase">销售价</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase">状态</th>
                <th className="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody>
              {items.map(p => (
                <tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                  <td className="px-4 py-3 text-sm font-mono text-indigo-600">{p.product_code}</td>
                  <td className="px-4 py-3 text-sm font-medium text-slate-800">{p.name}</td>
                  <td className="px-4 py-3 text-sm text-slate-600">{p.brand_name || "-"}</td>
                  <td className="px-4 py-3 text-sm">
                    {p.model_type ? (
                      <span className="inline-flex px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-xs font-medium">{p.model_type}</span>
                    ) : "-"}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">{p.warehouse_name || "-"}</td>
                  <td className="px-4 py-3 text-sm text-right text-slate-700">¥{p.default_purchase_price?.toLocaleString()}</td>
                  <td className="px-4 py-3 text-sm text-right text-slate-700">¥{p.default_sale_price?.toLocaleString()}</td>
                  <td className="px-4 py-3 text-center"><StatusBadge active={p.is_active} /></td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() => navigate(`/products/${p.id}/edit`)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                      >
                        编辑
                      </button>
                      <button
                        onClick={async () => {
                          const ok = await sysConfirm(`确定要${p.is_active ? "停用" : "启用"}产品 "${p.name}" 吗？`)
                          if (ok) toggleActive.mutate(p.id)
                        }}
                        className={`text-xs font-medium ${p.is_active ? "text-rose-600 hover:text-rose-800" : "text-emerald-600 hover:text-emerald-800"}`}
                      >
                        {p.is_active ? "停用" : "启用"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
              <div className="text-sm text-slate-500">共 {total} 条</div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1 border border-slate-200 rounded text-sm disabled:opacity-40 hover:bg-slate-50"
                >
                  上一页
                </button>
                {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                  const start = Math.max(1, Math.min(page - 3, totalPages - 6))
                  const pn = start + i
                  if (pn > totalPages) return null
                  return (
                    <button
                      key={pn}
                      onClick={() => setPage(pn)}
                      className={`w-8 h-8 rounded text-sm ${pn === page ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}
                    >
                      {pn}
                    </button>
                  )
                })}
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1 border border-slate-200 rounded text-sm disabled:opacity-40 hover:bg-slate-50"
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
