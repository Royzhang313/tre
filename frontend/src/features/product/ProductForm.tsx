/** 产品创建/编辑表单 */
import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiPut } from "../../api/client"
import { sysToast } from "../../components/shared/Dialog"

interface ProductFormData {
  product_code: string
  name: string
  brand_name: string
  model_type: string
  warehouse_name: string
  unit: string
  default_purchase_price: number
  default_sale_price: number
  description: string
}

const MODEL_TYPES = ["热料", "冷料", "蓝白片", "绿片", "3A白片"]

const emptyForm: ProductFormData = {
  product_code: "",
  name: "",
  brand_name: "",
  model_type: "",
  warehouse_name: "",
  unit: "吨",
  default_purchase_price: 0,
  default_sale_price: 0,
  description: "",
}

export function ProductForm() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const isEdit = Boolean(id)

  const [form, setForm] = useState<ProductFormData>(emptyForm)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [codeError, setCodeError] = useState("")

  // 编辑时加载现有数据
  const { data: existing } = useQuery({
    queryKey: ["product", id],
    queryFn: () => apiGet<{ id: string } & ProductFormData>(`/products/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (existing) {
      setForm({
        product_code: existing.product_code || "",
        name: existing.name || "",
        brand_name: existing.brand_name || "",
        model_type: existing.model_type || "",
        warehouse_name: existing.warehouse_name || "",
        unit: existing.unit || "吨",
        default_purchase_price: existing.default_purchase_price ?? 0,
        default_sale_price: existing.default_sale_price ?? 0,
        description: existing.description || "",
      })
    }
  }, [existing])

  // 产品编码唯一性校验
  const checkCode = async (code: string) => {
    if (!code || (isEdit && existing?.product_code === code)) return
    try {
      const res = await apiGet<{ exists: boolean }>(`/products/check-code/${encodeURIComponent(code)}`)
      setCodeError(res.exists ? "产品编码已存在" : "")
    } catch { /* ignore */ }
  }

  const createMutation = useMutation({
    mutationFn: (data: ProductFormData) => apiPost("/products", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
      sysToast("产品创建成功", "success")
      navigate("/products")
    },
    onError: (err: Error) => sysToast(err.message, "error"),
  })

  const updateMutation = useMutation({
    mutationFn: (data: ProductFormData) => apiPut(`/products/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
      sysToast("产品更新成功", "success")
      navigate("/products")
    },
    onError: (err: Error) => sysToast(err.message, "error"),
  })

  const validate = (): boolean => {
    const e: Record<string, string> = {}
    if (!form.product_code.trim()) e.product_code = "产品编码不能为空"
    if (!form.name.trim()) e.name = "产品名称不能为空"
    if (form.default_purchase_price < 0) e.default_purchase_price = "采购价不能为负"
    if (form.default_sale_price < 0) e.default_sale_price = "销售价不能为负"
    setErrors(e)
    return Object.keys(e).length === 0 && !codeError
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    if (isEdit) {
      updateMutation.mutate(form)
    } else {
      createMutation.mutate(form)
    }
  }

  const set = (field: keyof ProductFormData, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }))
    if (field === "product_code") {
      setErrors(prev => { const n = { ...prev }; delete n.product_code; return n })
      checkCode(value as string)
    }
    if (field === "name") setErrors(prev => { const n = { ...prev }; delete n.name; return n })
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate("/products")} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
          <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h1 className="text-xl font-bold text-slate-800">{isEdit ? "编辑产品" : "新增产品"}</h1>
          <p className="text-sm text-slate-500 mt-0.5">{isEdit ? `编辑 ${form.name}` : "创建新的 PET 瓶片产品"}</p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5">
        {/* 产品编码 */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">产品编码 <span className="text-rose-500">*</span></label>
          <input
            type="text"
            value={form.product_code}
            onChange={e => set("product_code", e.target.value)}
            placeholder="例如: PRD-001"
            className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 ${errors.product_code || codeError ? "border-rose-300 focus:ring-rose-300" : "border-slate-200 focus:border-indigo-300 focus:ring-indigo-300"}`}
          />
          {(errors.product_code || codeError) && <p className="text-xs text-rose-500 mt-1">{errors.product_code || codeError}</p>}
        </div>

        {/* 产品名称 */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">产品名称 <span className="text-rose-500">*</span></label>
          <input
            type="text"
            value={form.name}
            onChange={e => set("name", e.target.value)}
            placeholder="例如: PET透明瓶片"
            className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 ${errors.name ? "border-rose-300 focus:ring-rose-300" : "border-slate-200 focus:border-indigo-300 focus:ring-indigo-300"}`}
          />
          {errors.name && <p className="text-xs text-rose-500 mt-1">{errors.name}</p>}
        </div>

        {/* 品牌 + 型号 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">品牌名称</label>
            <input
              type="text"
              value={form.brand_name}
              onChange={e => set("brand_name", e.target.value)}
              placeholder="例如: 中石化"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">型号类型</label>
            <select
              value={form.model_type}
              onChange={e => set("model_type", e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-300"
            >
              <option value="">请选择型号</option>
              {MODEL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>

        {/* 默认仓库 + 单位 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">默认发货仓库</label>
            <input
              type="text"
              value={form.warehouse_name}
              onChange={e => set("warehouse_name", e.target.value)}
              placeholder="例如: 上海仓"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">计量单位</label>
            <input
              type="text"
              value={form.unit}
              onChange={e => set("unit", e.target.value)}
              placeholder="吨"
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-300"
            />
          </div>
        </div>

        {/* 默认价格 */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">默认采购单价 (元/吨)</label>
            <input
              type="number"
              step="0.0001"
              min="0"
              value={form.default_purchase_price}
              onChange={e => set("default_purchase_price", parseFloat(e.target.value) || 0)}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 ${errors.default_purchase_price ? "border-rose-300 focus:ring-rose-300" : "border-slate-200 focus:border-indigo-300 focus:ring-indigo-300"}`}
            />
            {errors.default_purchase_price && <p className="text-xs text-rose-500 mt-1">{errors.default_purchase_price}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">默认销售单价 (元/吨)</label>
            <input
              type="number"
              step="0.0001"
              min="0"
              value={form.default_sale_price}
              onChange={e => set("default_sale_price", parseFloat(e.target.value) || 0)}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 ${errors.default_sale_price ? "border-rose-300 focus:ring-rose-300" : "border-slate-200 focus:border-indigo-300 focus:ring-indigo-300"}`}
            />
            {errors.default_sale_price && <p className="text-xs text-rose-500 mt-1">{errors.default_sale_price}</p>}
          </div>
        </div>

        {/* 描述 */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">产品描述</label>
          <textarea
            value={form.description}
            onChange={e => set("description", e.target.value)}
            rows={3}
            placeholder="可选的产品描述信息..."
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-300 focus:ring-1 focus:ring-indigo-300 resize-none"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={createMutation.isPending || updateMutation.isPending}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm disabled:opacity-50"
          >
            {createMutation.isPending || updateMutation.isPending ? "保存中..." : isEdit ? "保存修改" : "创建产品"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/products")}
            className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm hover:bg-slate-50 transition-colors"
          >
            取消
          </button>
        </div>
      </form>
    </div>
  )
}
