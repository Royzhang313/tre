/** 通用附件上传组件 —— 多文件 + 截图粘贴 + 预览 */
import { useState, useRef, useEffect, useCallback } from "react"

export interface AttachFile { path: string; filename: string }

interface Props {
  files: AttachFile[]
  onChange: (files: AttachFile[]) => void
}

function getFileType(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase() || ""
  if (/pdf/i.test(ext)) return { label: "PDF", bg: "bg-red-100", text: "text-red-600" }
  if (/docx?/i.test(ext)) return { label: "DOC", bg: "bg-blue-100", text: "text-blue-600" }
  if (/xlsx?/i.test(ext)) return { label: "XLS", bg: "bg-emerald-100", text: "text-emerald-600" }
  if (/png|jpg|jpeg|gif|webp|bmp/i.test(ext)) return { label: "IMG", bg: "bg-purple-100", text: "text-purple-600" }
  return { label: ext.slice(0, 3).toUpperCase() || "FILE", bg: "bg-slate-100", text: "text-slate-500" }
}

export function AttachmentField({ files, onChange }: Props) {
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState<AttachFile | null>(null)
  const dropRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const uploadFile = async (file: File): Promise<AttachFile | null> => {
    const fd = new FormData(); fd.append("file", file)
    try {
      const r = await fetch("/api/v1/system/upload", { method: "POST", body: fd })
      const j = await r.json()
      if (j.data?.path) return { path: j.data.path, filename: file.name }
    } catch { /* ignore */ }
    return null
  }

  const handleFiles = async (fileList: FileList | File[]) => {
    setUploading(true)
    const arr = Array.from(fileList)
    const results: AttachFile[] = []
    for (const f of arr) {
      const r = await uploadFile(f)
      if (r) results.push(r)
    }
    onChange([...files, ...results])
    setUploading(false)
  }

  // 截图粘贴
  const handlePaste = useCallback(async (e: ClipboardEvent) => {
    const items = e.clipboardData?.items
    if (!items) return
    const imageItems: File[] = []
    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (item.type.startsWith("image/")) {
        const blob = item.getAsFile()
        if (blob) {
          const ext = item.type.split("/")[1] || "png"
          imageItems.push(new File([blob], `screenshot-${Date.now()}.${ext}`, { type: item.type }))
        }
      }
    }
    if (imageItems.length > 0) {
      setUploading(true)
      const results: AttachFile[] = []
      for (const f of imageItems) {
        const r = await uploadFile(f)
        if (r) results.push(r)
      }
      onChange([...files, ...results])
      setUploading(false)
    }
  }, [files, onChange])

  useEffect(() => {
    const el = dropRef.current
    if (!el) return
    el.addEventListener("paste", handlePaste as any)
    return () => el.removeEventListener("paste", handlePaste as any)
  }, [handlePaste])

  // 拖拽
  const [dragOver, setDragOver] = useState(false)
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false)
    if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files)
  }

  const remove = (idx: number) => onChange(files.filter((_, i) => i !== idx))

  const isImage = (f: AttachFile) => /\.(png|jpg|jpeg|gif|webp|bmp)$/i.test(f.filename)

  return (
    <div ref={dropRef} className="flex items-start gap-3 flex-wrap">
      {/* 已上传文件列表 */}
      {files.map((f, i) => (
        <div key={i} className="group relative w-20 h-20 rounded-xl border border-slate-200 overflow-hidden bg-slate-50 shrink-0 cursor-pointer" onClick={() => { if (isImage(f)) setPreview(f); else window.open(f.path, "_blank") }}>
          {isImage(f) ? (
            <img src={f.path} alt={f.filename} className="w-full h-full object-cover" />
          ) : (
            <FileThumb file={f} type={getFileType(f.filename)} />
          )}
          <button onClick={e => { e.stopPropagation(); remove(i) }}
            className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/50 hover:bg-rose-500 text-white flex items-center justify-center transition-colors">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      ))}

      {/* 上传按钮 */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`shrink-0 flex items-center justify-center gap-1.5 px-3 py-4 border-2 border-dashed rounded-xl cursor-pointer transition-all text-xs
          ${dragOver ? "border-indigo-400 bg-indigo-50 text-indigo-600" : "border-slate-200 bg-slate-50/50 text-slate-400 hover:border-indigo-300 hover:bg-indigo-50/20"}
          ${uploading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
        <span>{uploading ? "上传中..." : "上传"}</span>
        <input ref={inputRef} type="file" className="hidden" multiple onChange={e => e.target.files && handleFiles(e.target.files)} accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.bmp,.doc,.docx,.xls,.xlsx" />
      </div>

      {/* 图片预览弹窗 */}
      {preview && isImage(preview) && (
        <ImagePreview file={preview} onClose={() => setPreview(null)} />
      )}
    </div>
  )
}

/** 文件类型缩略图 */
function FileThumb({ file, type }: { file: AttachFile; type: ReturnType<typeof getFileType> }) {
  return (
    <div className={`w-full h-full flex flex-col items-center justify-center ${type.bg}`}>
      <span className={`text-xs font-extrabold ${type.text}`}>{type.label}</span>
      <span className="text-[8px] text-slate-400 mt-0.5 text-center leading-tight px-1 truncate w-full">
        {file.filename.length > 10 ? file.filename.slice(0, 8) + ".." : file.filename}
      </span>
    </div>
  )
}

/** 图片预览弹窗 */
function ImagePreview({ file, onClose }: { file: AttachFile; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <img src={file.path} alt={file.filename} className="max-w-[90vw] max-h-[90vh] rounded-2xl shadow-2xl" onClick={e => e.stopPropagation()} />
      <button onClick={onClose} className="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/20 hover:bg-white/40 flex items-center justify-center text-white transition-colors"><svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
    </div>
  )
}
