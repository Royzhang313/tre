/** OCR 银行回单上传识别组件 —— 支持拖拽、点击、截图粘贴 */
import { useState, useRef, useEffect } from "react"

interface OCRResult {
  success: boolean
  amount: number | null; bank_name: string | null; bank_account: string | null
  payer_name: string | null; receiver_name: string | null; date: string | null
  remark: string | null; summary: string | null
}

interface Props {
  onResult: (result: OCRResult) => void
  label?: string
}

export function OCRUpload({ onResult, label = "银行回单" }: Props) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState("")
  const [preview, setPreview] = useState<string | null>(null)
  const [fullPreview, setFullPreview] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const onResultRef = useRef(onResult)
  onResultRef.current = onResult  // 始终保持最新

  const handleFile = async (file: File) => {
    setError(""); setUploading(true)
    const reader = new FileReader()
    reader.onload = () => setPreview(reader.result as string)
    reader.readAsDataURL(file)

    try {
      const fd = new FormData(); fd.append("file", file)
      const res = await fetch("/api/v1/system/ocr/recognize", { method: "POST", body: fd })
      const json = await res.json()
      if (json.data?.success) {
        onResultRef.current(json.data)
      } else {
        setError(json.data?.remark || "识别失败，请手动填写")
      }
    } catch (e: any) {
      setError("上传失败: " + e.message)
    }
    setUploading(false)
  }

  // 截图粘贴
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items
      if (!items) return
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith("image/")) {
          e.preventDefault()
          const blob = items[i].getAsFile()
          if (blob) {
            const ext = items[i].type.split("/")[1] || "png"
            handleFile(new File([blob], `receipt-${Date.now()}.${ext}`, { type: items[i].type }))
          }
          break
        }
      }
    }
    document.addEventListener("paste", onPaste)
    return () => document.removeEventListener("paste", onPaste)
  }, [])

  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1.5">{label}</label>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={e => { e.preventDefault() }}
        onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}
        className="flex items-center gap-3 p-4 border-2 border-dashed border-slate-200 rounded-xl cursor-pointer hover:border-indigo-300 hover:bg-indigo-50/20 transition-all"
      >
        {preview ? (
          <img src={preview} className="w-12 h-12 rounded-lg object-cover cursor-pointer hover:ring-2 hover:ring-indigo-400 transition-all" alt="preview" onClick={(e) => { e.stopPropagation(); setFullPreview(true) }} />
        ) : (
          <svg className="w-8 h-8 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
        )}
        <div className="text-xs">
          <p className="text-slate-500">{uploading ? "识别中..." : "上传回单自动识别"}</p>
          <p className="text-slate-400 text-[10px]">Ctrl+V 截图粘贴 / 点击上传 / 拖拽，支持 JPG/PNG</p>
        </div>
        <input ref={inputRef} type="file" className="hidden" accept="image/*" onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />
      </div>
      {error && <p className="text-xs text-amber-600 mt-1">{error}</p>}

      {/* 全屏图片预览 */}
      {fullPreview && preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={() => setFullPreview(false)}>
          <img src={preview} alt="回单预览" className="max-w-[90vw] max-h-[90vh] rounded-2xl shadow-2xl" onClick={e => e.stopPropagation()} />
          <button onClick={() => setFullPreview(false)} className="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/20 hover:bg-white/40 flex items-center justify-center text-white transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      )}
    </div>
  )
}
