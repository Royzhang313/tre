import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQueryClient } from "@tanstack/react-query"
import { apiPost } from "../api/client"
import type { PageSchema } from "../api/ui"

export function FormPage({ page }: { page: PageSchema }) {
  const fields = page.form_config?.fields ?? []
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  // 受控表单状态
  const [formData, setFormData] = useState<Record<string, string>>(() => {
    const init: Record<string, string> = {}
    for (const f of fields) init[f.field] = ""
    return init
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      // 构建 API 路径：/module/entitys
      const module = page.permission.split(".")[0]
      const entityPath = page.entity?.toLowerCase() + "s"
      const path = `/${module}/${entityPath}`

      // 转换字段类型（number → 数字）
      const body: Record<string, unknown> = {}
      for (const f of fields) {
        const val = formData[f.field]
        if (f.field_type === "number" && val !== "") {
          body[f.field] = Number(val)
        } else {
          body[f.field] = val || null
        }
      }

      await apiPost(path, body)

      // 刷新列表缓存并跳转回列表页
      queryClient.invalidateQueries({ queryKey: ["list"] })
      navigate(`/${module}/${entityPath}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-lg border border-slate-200 rounded-lg p-6 bg-white">
      <h2 className="text-base font-semibold text-slate-700 mb-4">{page.title}</h2>

      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="space-y-3">
        {fields.map(f => (
          <div key={f.field}>
            <label className="block text-sm text-slate-600 mb-0.5">
              {f.label}
            </label>
            {f.field_type === "textarea" ? (
              <textarea
                className="w-full border border-slate-300 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                rows={3}
                value={formData[f.field] ?? ""}
                onChange={e => setFormData(prev => ({ ...prev, [f.field]: e.target.value }))}
              />
            ) : f.field_type === "select" ? (
              <select
                className="w-full border border-slate-300 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={formData[f.field] ?? ""}
                onChange={e => setFormData(prev => ({ ...prev, [f.field]: e.target.value }))}
              >
                <option value="">请选择</option>
              </select>
            ) : f.field_type === "date" ? (
              <input
                type="date"
                className="w-full border border-slate-300 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={formData[f.field] ?? ""}
                onChange={e => setFormData(prev => ({ ...prev, [f.field]: e.target.value }))}
              />
            ) : (
              <input
                type={f.field_type === "number" ? "number" : "text"}
                className="w-full border border-slate-300 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={formData[f.field] ?? ""}
                onChange={e => setFormData(prev => ({ ...prev, [f.field]: e.target.value }))}
              />
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-2 mt-5">
        <button
          type="submit"
          disabled={submitting}
          className="bg-blue-600 text-white px-4 py-1.5 rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {submitting ? "提交中…" : "提交"}
        </button>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="border border-slate-300 text-slate-600 px-4 py-1.5 rounded-md text-sm hover:bg-slate-50 transition-colors"
        >
          取消
        </button>
      </div>
    </form>
  )
}
