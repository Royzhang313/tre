/** OCR 配置 —— 系统设置 */
import { useState, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPut } from "../../api/client"

const PROVIDERS = [
  { key: "smart", name: "Smart OCR（推荐）", desc: "PaddleOCR 取文字 + DeepSeek 智能解析，适配各种截图格式" },
  { key: "paddleocr", name: "PaddleOCR", desc: "本地 OCR，中文识别精准，无需网络" },
  { key: "deepseek", name: "DeepSeek Vision", desc: "大模型直接识图，理解能力强" },
  { key: "aliyun", name: "Tesseract OCR", desc: "本地备用，轻量级" },
  { key: "mock", name: "模拟（测试用）", desc: "开发测试，返回示例数据" },
]

interface OCRConfig {
  ocr_enabled?: string
  ocr_provider?: string
  ocr_api_key?: string
  ocr_api_secret?: string
  ocr_api_url?: string
}

export function OCRConfig() {
  const qc = useQueryClient()
  const [enabled, setEnabled] = useState(false)
  const [provider, setProvider] = useState("aliyun")
  const [apiKey, setApiKey] = useState("")
  const [apiSecret, setApiSecret] = useState("")
  const [apiUrl, setApiUrl] = useState("")
  const [saved, setSaved] = useState(false)

  const { data: configs } = useQuery({
    queryKey: ["sys-configs"],
    queryFn: async () => apiGet<OCRConfig>("/system/configs"),
  })

  useEffect(() => {
    if (!configs) return
    setEnabled(configs.ocr_enabled === "true")
    setProvider(configs.ocr_provider || "aliyun")
    setApiKey(configs.ocr_api_key || "")
    setApiSecret(configs.ocr_api_secret || "")
    setApiUrl(configs.ocr_api_url || "")
  }, [configs])

  const mut = useMutation({
    mutationFn: async () => {
      await apiPut("/system/configs", {
        configs: {
          ocr_enabled: String(enabled),
          ocr_provider: provider,
          ocr_api_key: apiKey || null,
          ocr_api_secret: apiSecret || null,
          ocr_api_url: apiUrl || null,
        },
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sys-configs"] })
      setSaved(true); setTimeout(() => setSaved(false), 2000)
    },
  })

  const sel = PROVIDERS.find(p => p.key === provider)

  return (
    <div className="page-enter p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-slate-900 mb-2">OCR 配置</h1>
      <p className="text-sm text-slate-500 mb-6">上传银行回单截图自动识别收款/付款信息</p>

      <div className="bg-white rounded-xl border border-slate-200/60 shadow-sm divide-y divide-slate-100">
        {/* 启用开关 */}
        <div className="p-5 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-800">启用 OCR</h3>
            <p className="text-xs text-slate-400 mt-0.5">开启后收款/付款表单支持上传回单自动填充</p>
          </div>
          <button onClick={() => setEnabled(!enabled)}
            className={`relative w-11 h-6 rounded-full transition-colors ${enabled ? "bg-indigo-600" : "bg-slate-300"}`}>
            <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${enabled ? "translate-x-5" : ""}`} />
          </button>
        </div>

        {/* 提供商选择 */}
        <div className="p-5">
          <h3 className="text-sm font-semibold text-slate-800 mb-3">识别引擎</h3>
          <div className="grid grid-cols-2 gap-3">
            {PROVIDERS.map(p => (
              <button key={p.key} onClick={() => setProvider(p.key)}
                className={`text-left p-3 rounded-xl border-2 transition-all ${provider === p.key ? "border-indigo-400 bg-indigo-50" : "border-slate-100 hover:border-slate-200"}`}>
                <div className={`text-sm font-semibold ${provider === p.key ? "text-indigo-700" : "text-slate-700"}`}>{p.name}</div>
                <div className="text-xs text-slate-400 mt-0.5">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* API 密钥 */}
        <div className="p-5 space-y-4">
          <h3 className="text-sm font-semibold text-slate-800">API 配置</h3>
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">AccessKey ID</label>
            <input type="text" value={apiKey} onChange={e => setApiKey(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400" />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">AccessKey Secret</label>
            <input type="text" value={apiSecret} onChange={e => setApiSecret(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400" />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1.5">自定义 API URL（可选，留空使用默认）</label>
            <input value={apiUrl} onChange={e => setApiUrl(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400" />
          </div>
        </div>

        {/* 当前选中提供商信息 */}
        <div className="p-5 bg-slate-50">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>当前：</span><span className="font-semibold text-slate-700">{sel?.name || "未选择"}</span>
            <span className="text-slate-300">|</span>
            <span>状态：<span className={enabled ? "text-emerald-600 font-semibold" : "text-slate-400"}>{enabled ? "已启用" : "已关闭"}</span></span>
          </div>
        </div>
      </div>

      <div className="flex gap-3 mt-6">
        <button onClick={() => mut.mutate()} disabled={mut.isPending}
          className="px-5 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 disabled:opacity-40">
          {mut.isPending ? "保存中..." : "保存配置"}
        </button>
        {saved && <span className="text-sm text-emerald-600 self-center">✅ 已保存</span>}
      </div>
    </div>
  )
}
