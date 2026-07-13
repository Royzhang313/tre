/** 品牌管理 —— 拖拽排序 + 颜色必填 + 默认折叠 + 引用保护 */
import { useState, useEffect, useRef } from "react"
import { createPortal } from "react-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiGet, apiPost, apiDelete, apiPut, apiPatch } from "../../api/client"

interface B { id: string; name: string; color: string; sort_order: number; is_active: boolean }
interface BW { id: string; name: string; is_active: boolean }
interface BM { id: string; model_name: string; model_type: string; is_active: boolean }

const COLOR_PALETTE = [
  { key: 'red',     dot: 'bg-red-500' },       { key: 'orange',  dot: 'bg-orange-500' },
  { key: 'amber',   dot: 'bg-amber-500' },      { key: 'yellow',  dot: 'bg-yellow-500' },
  { key: 'lime',    dot: 'bg-lime-500' },       { key: 'green',   dot: 'bg-green-500' },
  { key: 'emerald', dot: 'bg-emerald-500' },    { key: 'teal',    dot: 'bg-teal-500' },
  { key: 'cyan',    dot: 'bg-cyan-500' },       { key: 'sky',     dot: 'bg-sky-500' },
  { key: 'blue',    dot: 'bg-blue-500' },       { key: 'indigo',  dot: 'bg-indigo-500' },
  { key: 'violet',  dot: 'bg-violet-500' },     { key: 'purple',  dot: 'bg-purple-500' },
  { key: 'fuchsia', dot: 'bg-fuchsia-500' },    { key: 'pink',    dot: 'bg-pink-500' },
  { key: 'rose',    dot: 'bg-rose-500' },       { key: 'slate',   dot: 'bg-slate-500' },
  { key: 'gray',    dot: 'bg-gray-500' },       { key: 'zinc',    dot: 'bg-zinc-500' },
  { key: 'neutral', dot: 'bg-neutral-500' },    { key: 'stone',   dot: 'bg-stone-500' },
  { key: 'warm',    dot: 'bg-stone-400' },      { key: 'cool',    dot: 'bg-slate-400' },
]

const CHIP_CLASS: Record<string, string> = {
  red:'bg-red-100 text-red-700',orange:'bg-orange-100 text-orange-700',amber:'bg-amber-100 text-amber-700',
  yellow:'bg-yellow-100 text-yellow-700',lime:'bg-lime-100 text-lime-700',green:'bg-green-100 text-green-700',
  emerald:'bg-emerald-100 text-emerald-700',teal:'bg-teal-100 text-teal-700',cyan:'bg-cyan-100 text-cyan-700',
  sky:'bg-sky-100 text-sky-700',blue:'bg-blue-100 text-blue-700',indigo:'bg-indigo-100 text-indigo-700',
  violet:'bg-violet-100 text-violet-700',purple:'bg-purple-100 text-purple-700',fuchsia:'bg-fuchsia-100 text-fuchsia-700',
  pink:'bg-pink-100 text-pink-700',rose:'bg-rose-100 text-rose-700',slate:'bg-slate-200 text-slate-700',
  gray:'bg-gray-200 text-gray-700',zinc:'bg-zinc-200 text-zinc-700',neutral:'bg-neutral-200 text-neutral-700',
  stone:'bg-stone-200 text-stone-700',warm:'bg-stone-100 text-stone-600',cool:'bg-slate-100 text-slate-600',
}

function colorChip(key: string) { return CHIP_CLASS[key] ?? CHIP_CLASS['slate'] }
function colorDot(key: string) { return COLOR_PALETTE.find(c => c.key === key)?.dot ?? 'bg-slate-500' }

const M_TYPES = ["热料", "水料", "油料", "碳酸料", "碳酸料(快速吸热)", "酒盒料", "桶料"]
const TYPE_COLOR: Record<string, string> = {
  "热料": "bg-red-50 text-red-700 border-red-200", "水料": "bg-blue-50 text-blue-700 border-blue-200",
  "油料": "bg-amber-50 text-amber-700 border-amber-200", "碳酸料": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "碳酸料(快速吸热)": "bg-teal-50 text-teal-700 border-teal-200", "酒盒料": "bg-purple-50 text-purple-700 border-purple-200",
  "桶料": "bg-slate-100 text-slate-600 border-slate-200",
}
const INP = "w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white transition-all"

/** 色板选择器 —— Portal 到 body，6列网格 + 颜色名标签 */
function ColorPicker({ value, onChange }: { value: string; onChange: (c: string) => void }) {
  const [open, setOpen] = useState(false)
  const btnRef = useRef<HTMLButtonElement>(null)
  const [pos, setPos] = useState({ top: 0, left: 0 })

  const handleOpen = () => {
    if (!open && btnRef.current) {
      const r = btnRef.current.getBoundingClientRect()
      setPos({ top: r.bottom + 4, left: r.left })
    }
    setOpen(!open)
  }

  return (
    <div className="inline-flex items-center gap-2">
      <button ref={btnRef} onClick={handleOpen} className={`w-8 h-8 rounded-full ${colorDot(value)} border-2 border-white shadow-sm hover:scale-110 transition-transform ring-1 ring-slate-200 shrink-0`} title="选择颜色" />
      <span className="text-xs text-slate-500 font-medium">{value}</span>
      {open && createPortal(
        <div className="fixed inset-0 z-[9999]" onClick={() => setOpen(false)}>
          <div className="absolute bg-white border border-slate-200 rounded-xl shadow-xl p-2.5" style={{ top: pos.top, left: pos.left }} onMouseDown={e => e.preventDefault()}>
            <div className="grid grid-cols-6 gap-1.5 w-[208px]">
              {COLOR_PALETTE.map(p => (
                <button key={p.key} onMouseDown={e => { e.preventDefault(); onChange(p.key); setOpen(false) }}
                  className={`w-7 h-7 rounded-full ${p.dot} hover:scale-110 transition-transform ${value === p.key ? 'ring-2 ring-offset-2 ring-indigo-500' : ''}`} />
              ))}
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}

function BrandRow({ b, onDragStart, onDragOver, onDrop, onDragEnd }: {
  b: B; onDragStart: (id: string) => void; onDragOver: (e: React.DragEvent, id: string) => void;
  onDrop: (e: React.DragEvent, id: string) => void; onDragEnd: () => void
}) {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState(false); const [editName, setEditName] = useState(b.name); const [editColor, setEditColor] = useState(b.color); const inputRef = useRef<HTMLInputElement>(null)
  const [showWh, setShowWh] = useState(false); const [whName, setWhName] = useState(""); const [whErr, setWhErr] = useState("")
  const [showModel, setShowModel] = useState(false); const [mName, setMName] = useState(""); const [mType, setMType] = useState("热料"); const [mErr, setMErr] = useState("")
  const [editWh, setEditWh] = useState<{ id: string; name: string } | null>(null); const [editWhErr, setEditWhErr] = useState("")
  const [editM, setEditM] = useState<{ id: string; name: string; type: string } | null>(null); const [editMErr, setEditMErr] = useState("")
  const [delConfirm, setDelConfirm] = useState<{ type: string; id: string; name: string } | null>(null)
  const [whPage, setWhPage] = useState(1); const [mPage, setMPage] = useState(1)
  const [refMap, setRefMap] = useState<Record<string, boolean>>({})
  const [whDragId, setWhDragId] = useState<string | null>(null)
  const [mDragId, setMDragId] = useState<string | null>(null)

  useEffect(() => { if (editing) inputRef.current?.focus() }, [editing])

  const { data: whData } = useQuery({ queryKey: ["bw", b.id, whPage], queryFn: () => apiGet<{ items: BW[]; total: number; pages: number }>(`/brand/brands/${b.id}/warehouses?page=${whPage}&page_size=5`), enabled: open })
  const { data: mData } = useQuery({ queryKey: ["bm", b.id, mPage], queryFn: () => apiGet<{ items: BM[]; total: number; pages: number }>(`/brand/brands/${b.id}/models?page=${mPage}&page_size=5`), enabled: open })

  // 检查引用（品牌 + 子仓库 + 子型号）
  useEffect(() => {
    if (!open) return
    apiGet<{ referenced: boolean }>(`/brand/brands/${b.id}/check-references`).then(r => setRefMap(p => ({ ...p, [b.id]: r.referenced })))
    whData?.items.forEach(bw => { apiGet<{ referenced: boolean }>(`/brand/warehouses/${bw.id}/check-references`).then(r => setRefMap(p => ({ ...p, [bw.id]: r.referenced }))) })
    mData?.items.forEach(m => { apiGet<{ referenced: boolean }>(`/brand/models/${m.id}/check-references`).then(r => setRefMap(p => ({ ...p, [m.id]: r.referenced }))) })
  }, [open, whData, mData])

  const delBrand = useMutation({ mutationFn: () => apiDelete(`/brand/brands/${b.id}`), onSuccess: () => qc.invalidateQueries({ queryKey: ["brands"] }) })
  const updBrand = useMutation({ mutationFn: (data: { name: string; color: string }) => apiPut(`/brand/brands/${b.id}`, data), onSuccess: () => { qc.invalidateQueries({ queryKey: ["brands"] }); setEditing(false) } })
  const addWh = useMutation({ mutationFn: () => apiPost("/brand/warehouses", { brand_id: b.id, name: whName }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["bw", b.id] }); setShowWh(false); setWhName(""); setWhErr("") }, onError: (e: any) => setWhErr(e.message?.includes("已存在") ? e.message : "添加失败") })
  const addM = useMutation({ mutationFn: () => apiPost("/brand/models", { brand_id: b.id, model_name: mName, model_type: mType }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["bm", b.id] }); setShowModel(false); setMName(""); setMType("热料"); setMErr("") }, onError: (e: any) => setMErr(e.message?.includes("已存在") ? e.message : "添加失败") })
  const delWh = useMutation({ mutationFn: (id: string) => apiDelete(`/brand/warehouses/${id}`), onSuccess: () => qc.invalidateQueries({ queryKey: ["bw", b.id] }) })
  const delM = useMutation({ mutationFn: (id: string) => apiDelete(`/brand/models/${id}`), onSuccess: () => qc.invalidateQueries({ queryKey: ["bm", b.id] }) })
  const updWh = useMutation({ mutationFn: ({ id, name }: { id: string; name: string }) => apiPut(`/brand/warehouses/${id}`, { name }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["bw", b.id] }); setEditWh(null) } })
  const updM = useMutation({ mutationFn: ({ id, name, type }: { id: string; name: string; type: string }) => apiPut(`/brand/models/${id}`, { model_name: name, model_type: type }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["bm", b.id] }); setEditM(null) } })
  const reorderWh = useMutation({ mutationFn: (items: { id: string; sort_order: number }[]) => apiPatch("/brand/warehouses/reorder", { brand_id: b.id, items }) })
  const reorderM = useMutation({ mutationFn: (items: { id: string; sort_order: number }[]) => apiPatch("/brand/models/reorder", { brand_id: b.id, items }) })

  // 仓库拖拽处理
  const handleWhDragStart = (id: string) => setWhDragId(id)
  const handleWhDragOver = (e: React.DragEvent) => { e.preventDefault(); e.dataTransfer.dropEffect = "move" }
  const handleWhDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault()
    if (!whDragId || whDragId === targetId || !whData) return
    const list = [...whData.items]
    const fromIdx = list.findIndex(bw => bw.id === whDragId)
    const toIdx = list.findIndex(bw => bw.id === targetId)
    if (fromIdx === -1 || toIdx === -1) return
    const [moved] = list.splice(fromIdx, 1)
    list.splice(toIdx, 0, moved)
    qc.setQueryData(["bw", b.id, whPage], { ...whData, items: list })
    reorderWh.mutate(list.map((bw, i) => ({ id: bw.id, sort_order: (i + 1) * 10 })))
    setWhDragId(null)
  }
  const handleWhDragEnd = () => setWhDragId(null)

  // 型号拖拽处理
  const handleMDragStart = (id: string) => setMDragId(id)
  const handleMDragOver = (e: React.DragEvent) => { e.preventDefault(); e.dataTransfer.dropEffect = "move" }
  const handleMDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault()
    if (!mDragId || mDragId === targetId || !mData) return
    const list = [...mData.items]
    const fromIdx = list.findIndex(bm => bm.id === mDragId)
    const toIdx = list.findIndex(bm => bm.id === targetId)
    if (fromIdx === -1 || toIdx === -1) return
    const [moved] = list.splice(fromIdx, 1)
    list.splice(toIdx, 0, moved)
    qc.setQueryData(["bm", b.id, mPage], { ...mData, items: list })
    reorderM.mutate(list.map((bm, i) => ({ id: bm.id, sort_order: (i + 1) * 10 })))
    setMDragId(null)
  }
  const handleMDragEnd = () => setMDragId(null)

  return (
    <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden" draggable
      onDragStart={() => onDragStart(b.id)} onDragOver={e => onDragOver(e, b.id)} onDrop={e => onDrop(e, b.id)} onDragEnd={onDragEnd}>
      <div className="flex items-center justify-between p-5 hover:bg-slate-50/50">
        <div className="flex items-center gap-3">
          {/* 拖拽手柄 */}
          <span className="cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 select-none" title="拖拽排序">⠿</span>
          <button onClick={() => setOpen(!open)} className="p-1"><svg className={`w-5 h-5 text-slate-400 transition-transform ${open ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg></button>
          {editing ? (
            <div className="flex items-center gap-2">
              <ColorPicker value={editColor} onChange={setEditColor} />
              <input ref={inputRef} value={editName} onChange={e => setEditName(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") updBrand.mutate({ name: editName.trim(), color: editColor }); if (e.key === "Escape") setEditing(false) }}
                className="px-3 py-1.5 border border-indigo-300 rounded-lg text-lg font-semibold w-48 focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
              <button onClick={() => updBrand.mutate({ name: editName.trim(), color: editColor })} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium">保存</button>
              <button onClick={() => setEditing(false)} className="px-3 py-1.5 border rounded-lg text-xs">取消</button>
            </div>
          ) : (
            <div className="flex items-center gap-3 group/name" onClick={e => e.stopPropagation()}>
              <span className={`w-3 h-3 rounded-full ${colorDot(b.color)} shrink-0`} />
              <span className="font-semibold text-slate-800 text-lg">{b.name}</span>
              <button onClick={() => { setEditName(b.name); setEditColor(b.color); setEditing(true) }}
                className="opacity-0 group-hover/name:opacity-100 text-slate-300 hover:text-indigo-500 transition-all p-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
              </button>
            </div>
          )}
        </div>
        {!refMap[b.id] && (
          <button onClick={() => setDelConfirm({ type: "brand", id: b.id, name: b.name })} className="text-xs text-rose-400 hover:text-rose-600 px-2.5 py-1.5 hover:bg-rose-50 rounded-lg">删除</button>
        )}
      </div>

      {open && (
        <div className="border-t border-slate-100 bg-slate-50/30">
          <div className="grid grid-cols-2 divide-x divide-slate-200">
            <div className="p-5">
              <div className="flex items-center justify-between mb-4"><h3 className="text-sm font-semibold text-slate-700">发货仓库</h3><button onClick={() => setShowWh(true)} className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-100">+ 添加</button></div>
              <table className="w-full text-sm"><tbody>
                {(!whData || whData.items.length === 0) ? <tr><td className="px-3 py-8 text-center text-slate-300 text-sm">暂无</td></tr> :
                  whData.items.map(bw => (
                    <tr key={bw.id} className="border-b border-slate-100 hover:bg-white/60 group" draggable
                      onDragStart={() => handleWhDragStart(bw.id)} onDragOver={handleWhDragOver}
                      onDrop={e => handleWhDrop(e, bw.id)} onDragEnd={handleWhDragEnd}>
                      <td className="px-1 py-2.5 w-6"><span className="cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 select-none text-xs" title="拖拽排序">⠿</span></td>
                      <td className="px-1 py-2.5 text-slate-700">{bw.name}</td>
                      <td className="w-16 text-right">
                        <div className="flex items-center justify-end gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => setEditWh({ id: bw.id, name: bw.name })} className="p-1 text-slate-300 hover:text-indigo-500" title="编辑"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg></button>
                          {!refMap[bw.id] && <button onClick={() => setDelConfirm({ type: "warehouse", id: bw.id, name: bw.name })} className="p-1 text-slate-300 hover:text-rose-500" title="删除"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>}
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody></table>
              {whData && whData.pages > 1 && <Pager page={whPage} pages={whData.pages} total={whData.total} setPage={setWhPage} />}
            </div>
            <div className="p-5">
              <div className="flex items-center justify-between mb-4"><h3 className="text-sm font-semibold text-slate-700">品牌型号</h3><button onClick={() => setShowModel(true)} className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-medium hover:bg-emerald-100">+ 添加</button></div>
              <table className="w-full text-sm"><tbody>
                {(!mData || mData.items.length === 0) ? <tr><td className="px-3 py-8 text-center text-slate-300 text-sm">暂无</td></tr> :
                  mData.items.map(m => (
                    <tr key={m.id} className="border-b border-slate-100 hover:bg-white/60 group" draggable
                      onDragStart={() => handleMDragStart(m.id)} onDragOver={handleMDragOver}
                      onDrop={e => handleMDrop(e, m.id)} onDragEnd={handleMDragEnd}>
                      <td className="px-1 py-2.5 w-6"><span className="cursor-grab active:cursor-grabbing text-slate-300 hover:text-slate-500 select-none text-xs" title="拖拽排序">⠿</span></td>
                      <td className="px-1 py-2.5 text-slate-700 font-medium">{m.model_name}</td>
                      <td className="px-1 py-2.5"><span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium border ${TYPE_COLOR[m.model_type] ?? ""}`}>{m.model_type}</span></td>
                      <td className="w-16 text-right">
                        <div className="flex items-center justify-end gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => setEditM({ id: m.id, name: m.model_name, type: m.model_type })} className="p-1 text-slate-300 hover:text-indigo-500" title="编辑"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg></button>
                          {!refMap[m.id] && <button onClick={() => setDelConfirm({ type: "model", id: m.id, name: m.model_name })} className="p-1 text-slate-300 hover:text-rose-500" title="删除"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>}
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody></table>
              {mData && mData.pages > 1 && <Pager page={mPage} pages={mData.pages} total={mData.total} setPage={setMPage} />}
            </div>
          </div>
        </div>
      )}

      <Modal open={showWh} onClose={() => { setShowWh(false); setWhErr("") }} title="添加发货仓库">
        <div><label className="block text-sm font-medium text-slate-600 mb-1.5">仓库名称</label><input value={whName} onChange={e => { setWhName(e.target.value); setWhErr("") }} className={`${INP} ${whErr ? "border-rose-300" : ""}`} />{whErr && <p className="text-xs text-rose-500 mt-1.5">{whErr}</p>}</div>
        <div className="flex justify-end gap-3 mt-6"><BtnCancel onClick={() => setShowWh(false)} /><BtnSave onClick={() => addWh.mutate()} disabled={!whName} /></div>
      </Modal>
      <Modal open={!!editWh} onClose={() => { setEditWh(null); setEditWhErr("") }} title="编辑发货仓库">
        <div><label className="block text-sm font-medium text-slate-600 mb-1.5">仓库名称</label><input value={editWh?.name ?? ""} onChange={e => { setEditWh(p => p ? { ...p, name: e.target.value } : null); setEditWhErr("") }} className={`${INP} ${editWhErr ? "border-rose-300" : ""}`} />{editWhErr && <p className="text-xs text-rose-500 mt-1.5">{editWhErr}</p>}</div>
        <div className="flex justify-end gap-3 mt-6"><BtnCancel onClick={() => setEditWh(null)} /><BtnSave onClick={() => editWh && updWh.mutate({ id: editWh.id, name: editWh.name })} disabled={!editWh?.name} /></div>
      </Modal>

      <Modal open={showModel} onClose={() => { setShowModel(false); setMErr("") }} title="添加品牌型号">
        <div className="space-y-4">
          <div><label className="block text-sm font-medium text-slate-600 mb-1.5">型号名称</label><input value={mName} onChange={e => { setMName(e.target.value); setMErr("") }} className={`${INP} ${mErr ? "border-rose-300" : ""}`} />{mErr && <p className="text-xs text-rose-500 mt-1.5">{mErr}</p>}</div>
          <div><label className="block text-sm font-medium text-slate-600 mb-1.5">型号类型</label><div className="grid grid-cols-4 gap-2">{M_TYPES.map(t => <label key={t} onClick={() => setMType(t)} className={`px-3 py-2 rounded-xl border-2 cursor-pointer text-center text-sm font-medium transition-all ${mType===t?"border-indigo-500 bg-indigo-50 text-indigo-700":"border-slate-200 bg-white text-slate-600 hover:border-slate-300"}`}>{t}</label>)}</div></div>
        </div>
        <div className="flex justify-end gap-3 mt-6"><BtnCancel onClick={() => setShowModel(false)} /><BtnSave onClick={() => addM.mutate()} disabled={!mName} /></div>
      </Modal>
      <Modal open={!!editM} onClose={() => { setEditM(null); setEditMErr("") }} title="编辑品牌型号">
        <div className="space-y-4">
          <div><label className="block text-sm font-medium text-slate-600 mb-1.5">型号名称</label><input value={editM?.name ?? ""} onChange={e => { setEditM(p => p ? { ...p, name: e.target.value } : null); setEditMErr("") }} className={`${INP} ${editMErr ? "border-rose-300" : ""}`} />{editMErr && <p className="text-xs text-rose-500 mt-1.5">{editMErr}</p>}</div>
          <div><label className="block text-sm font-medium text-slate-600 mb-1.5">型号类型</label><div className="grid grid-cols-4 gap-2">{M_TYPES.map(t => <label key={t} onClick={() => setEditM(p => p ? { ...p, type: t } : null)} className={`px-3 py-2 rounded-xl border-2 cursor-pointer text-center text-sm font-medium transition-all ${(editM?.type??"")===t?"border-indigo-500 bg-indigo-50 text-indigo-700":"border-slate-200 bg-white text-slate-600 hover:border-slate-300"}`}>{t}</label>)}</div></div>
        </div>
        <div className="flex justify-end gap-3 mt-6"><BtnCancel onClick={() => setEditM(null)} /><BtnSave onClick={() => editM && updM.mutate({ id: editM.id, name: editM.name, type: editM.type })} disabled={!editM?.name} /></div>
      </Modal>

      <ConfirmModal open={!!delConfirm} onClose={() => setDelConfirm(null)} title="确认删除"
        message={delConfirm ? `确定要删除${delConfirm.type === "brand" ? "品牌" : delConfirm.type === "warehouse" ? "发货仓库" : "品牌型号"}「${delConfirm.name}」吗？` : ""}
        onConfirm={() => { if (!delConfirm) return; if (delConfirm.type === "brand") delBrand.mutate(); else if (delConfirm.type === "warehouse") delWh.mutate(delConfirm.id); else if (delConfirm.type === "model") delM.mutate(delConfirm.id); setDelConfirm(null) }}
      />
    </div>
  )
}

export function BrandManage() {
  const [showBrand, setShowBrand] = useState(false); const [bName, setBName] = useState(""); const [bColor, setBColor] = useState("indigo")
  const [dragId, setDragId] = useState<string | null>(null)
  const qc = useQueryClient()
  const { data: brands } = useQuery({ queryKey: ["brands"], queryFn: async () => { const r = await apiGet<{ items: B[] }>("/brand/brands"); return r.items } })
  const [brandErr, setBrandErr] = useState("")
  const saveBrand = useMutation({ mutationFn: async () => apiPost("/brand/brands", { name: bName, color: bColor }), onSuccess: () => { qc.invalidateQueries({ queryKey: ["brands"] }); setShowBrand(false); setBName(""); setBColor("indigo"); setBrandErr("") }, onError: (e: any) => setBrandErr(e.message?.includes("已存在") ? e.message : "添加失败") })

  // 拖拽排序
  const reorder = useMutation({ mutationFn: (items: { id: string; sort_order: number }[]) => apiPatch("/brand/brands/reorder", { items }) })
  const handleDragStart = (id: string) => setDragId(id)
  const handleDragOver = (e: React.DragEvent, id: string) => { e.preventDefault(); e.dataTransfer.dropEffect = "move" }
  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault()
    if (!dragId || dragId === targetId || !brands) return
    const list = [...brands]
    const fromIdx = list.findIndex(b => b.id === dragId)
    const toIdx = list.findIndex(b => b.id === targetId)
    if (fromIdx === -1 || toIdx === -1) return
    const [moved] = list.splice(fromIdx, 1)
    list.splice(toIdx, 0, moved)
    const updates = list.map((b, i) => ({ id: b.id, sort_order: (i + 1) * 10 }))
    qc.setQueryData(["brands"], list)
    reorder.mutate(updates)
    setDragId(null)
  }
  const handleDragEnd = () => setDragId(null)

  return (
    <div className="page-enter p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div><h1 className="text-2xl font-bold text-slate-900">品牌管理</h1><p className="text-sm text-slate-500 mt-1">拖拽排序 · 管理 PET 品牌、发货仓库与型号</p></div>
        <button onClick={() => setShowBrand(true)} className="px-5 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-2xl hover:from-indigo-700 hover:to-blue-700 transition-all shadow-lg shadow-indigo-200 text-sm font-semibold">+ 新增品牌</button>
      </div>
      <div className="space-y-3">
        {brands?.map(b => (
          <BrandRow key={b.id} b={b}
            onDragStart={handleDragStart} onDragOver={handleDragOver} onDrop={handleDrop} onDragEnd={handleDragEnd} />
        ))}
        {(!brands || brands.length === 0) && <div className="text-center py-20 bg-white rounded-2xl border border-slate-200/60"><p className="text-slate-400 font-medium">暂无品牌</p></div>}
      </div>
      <Modal open={showBrand} onClose={() => { setShowBrand(false); setBrandErr("") }} title="新增品牌">
        <div className="space-y-4">
          <div><label className="block text-sm font-medium text-slate-600 mb-1.5">品牌名称 {!bName && <span className="text-rose-400">*</span>}</label><input value={bName} onChange={e => { setBName(e.target.value); setBrandErr("") }} className={`${INP} ${brandErr ? "border-rose-300" : ""}`} />{brandErr && <p className="text-xs text-rose-500 mt-1.5">{brandErr}</p>}</div>
          <div><label className="block text-sm font-medium text-slate-600 mb-1.5">品牌颜色 {!bColor && <span className="text-rose-400">*</span>}</label><ColorPicker value={bColor} onChange={setBColor} /></div>
        </div>
        <div className="flex justify-end gap-3 mt-6"><BtnCancel onClick={() => setShowBrand(false)} /><BtnSave onClick={() => saveBrand.mutate()} disabled={!bName} /></div>
      </Modal>
    </div>
  )
}

/* ===== 复用组件 ===== */
function Modal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl shadow-slate-500/20 w-full max-w-lg" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100"><h2 className="text-lg font-bold text-slate-900">{title}</h2><button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button></div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}
function ConfirmModal({ open, onClose, title, message, onConfirm }: { open: boolean; onClose: () => void; title: string; message: string; onConfirm: () => void }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl shadow-slate-500/20 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100"><h2 className="text-lg font-bold text-slate-900">{title}</h2><button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button></div>
        <div className="p-6">
          <div className="flex items-start gap-4"><div className="w-10 h-10 rounded-full bg-rose-100 text-rose-500 flex items-center justify-center shrink-0"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg></div><p className="text-sm text-slate-700 pt-1.5">{message}</p></div>
          <div className="flex justify-end gap-3 mt-6"><button onClick={onClose} className="px-5 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-600 hover:bg-slate-50 transition-colors">取消</button><button onClick={onConfirm} className="px-5 py-2.5 bg-rose-500 text-white rounded-xl text-sm font-medium hover:bg-rose-600 transition-colors shadow-sm shadow-rose-200">确定删除</button></div>
        </div>
      </div>
    </div>
  )
}
function Pager({ page, pages, total, setPage }: { page: number; pages: number; total: number; setPage: (p: number) => void }) {
  return (
    <div className="flex items-center justify-between mt-3 text-xs"><span className="text-slate-400">共 {total} 条</span>
      <div className="flex gap-1"><button onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1} className="px-2 py-1 border rounded-md disabled:opacity-30">‹</button><span className="px-2 py-1 text-slate-500">{page}/{pages}</span><button onClick={() => setPage(Math.min(pages, page + 1))} disabled={page >= pages} className="px-2 py-1 border rounded-md disabled:opacity-30">›</button></div>
    </div>
  )
}
function BtnCancel({ onClick }: { onClick: () => void }) { return <button onClick={onClick} className="px-5 py-2.5 border border-slate-200 rounded-xl text-sm text-slate-600 hover:bg-slate-50 transition-colors">取消</button> }
function BtnSave({ onClick, disabled }: { onClick: () => void; disabled?: boolean }) { return <button onClick={onClick} disabled={disabled} className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-xl text-sm font-semibold hover:from-indigo-700 hover:to-blue-700 disabled:opacity-40 transition-all shadow-lg shadow-indigo-200">保存</button> }
