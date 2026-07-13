/** 销售合同列表 */
import { useState, useEffect, useMemo, useRef } from "react"
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { apiGet, apiPatch, apiDelete } from "../../api/client"
import { Cascader } from "../../components/shared/Cascader"
import type { CascaderOption } from "../../components/shared/Cascader"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

const BRAND_CHIP: Record<string, string> = {
  red: 'bg-red-100 text-red-700', orange: 'bg-orange-100 text-orange-700',
  amber: 'bg-amber-100 text-amber-700', yellow: 'bg-yellow-100 text-yellow-700',
  lime: 'bg-lime-100 text-lime-700', green: 'bg-green-100 text-green-700',
  emerald: 'bg-emerald-100 text-emerald-700', teal: 'bg-teal-100 text-teal-700',
  cyan: 'bg-cyan-100 text-cyan-700', sky: 'bg-sky-100 text-sky-700',
  blue: 'bg-blue-100 text-blue-700', indigo: 'bg-indigo-100 text-indigo-700',
  violet: 'bg-violet-100 text-violet-700', purple: 'bg-purple-100 text-purple-700',
  fuchsia: 'bg-fuchsia-100 text-fuchsia-700', pink: 'bg-pink-100 text-pink-700',
  rose: 'bg-rose-100 text-rose-700', slate: 'bg-slate-200 text-slate-700',
  gray: 'bg-gray-200 text-gray-700', zinc: 'bg-zinc-200 text-zinc-700',
  neutral: 'bg-neutral-200 text-neutral-700', stone: 'bg-stone-200 text-stone-700',
  warm: 'bg-stone-100 text-stone-600', cool: 'bg-slate-100 text-slate-600',
}
function brandChipClass(color: string | null): string { return color && BRAND_CHIP[color] ? BRAND_CHIP[color] : 'bg-slate-100 text-slate-600' }

interface ItemL { brand_id: string; model_id: string; shipping_warehouse_id: string; quantity: number }
interface C { id: string; contract_no: string; customer_enterprise_id: string; contract_date: string; status: string; total_quantity: number; total_amount: number; pickup_progress: number; collection_progress: number; contract_start_date: string; contract_end_date: string; attachment_path: { path: string; filename: string }[] | null; items: ItemL[] | null; tags: Tag[] | null; remark: string | null }
interface E { id: string; name: string }

function CheckDropdown({ label, options, selected, onChange, isOpen, onToggle }: { label: string; options: {v:string;l:string}[]; selected: string[]; onChange: (v:string)=>void; isOpen: boolean; onToggle: ()=>void }) {
  return (
    <div className="relative">
      <button onMouseDown={e => { e.stopPropagation(); onToggle() }} className={`px-3 py-1.5 border rounded-lg text-xs flex items-center gap-1 whitespace-nowrap ${selected.length>0?"border-indigo-300 bg-indigo-50 text-indigo-700":"border-slate-200 bg-white text-slate-600"}`}>
        {label}{selected.length>0&&<span className="bg-indigo-600 text-white w-4 h-4 rounded-full text-[10px] flex items-center justify-center">{selected.length}</span>}
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/></svg>
      </button>
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-xl z-50 p-2 min-w-32 max-h-48 overflow-y-auto" onMouseDown={e=>e.stopPropagation()}>
          {options.map(o=>(<label key={o.v} onClick={e=>{e.stopPropagation();onChange(o.v)}} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs cursor-pointer hover:bg-slate-50 ${selected.includes(o.v)?"text-indigo-700 font-medium":"text-slate-600"}`}><span className={`w-3.5 h-3.5 rounded border-2 flex items-center justify-center ${selected.includes(o.v)?"border-indigo-500 bg-indigo-500":"border-slate-300"}`}>{selected.includes(o.v)&&<svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7"/></svg>}</span>{o.l}</label>))}
        </div>
      )}
    </div>
  )
}

function StatusBadge({ c }: { c: C }) { const s = getStatus(c); return <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold border ${s.c}`}>{s.l}</span> }

function getStatus(c: C) {
  const dp = c.pickup_progress ?? 0; const pp = c.collection_progress ?? 0
  if (c.status === "cancelled") return { l: "已作废", c: "bg-slate-100 text-slate-400 border-slate-200", k: "cancelled" }
  if (dp === 0 && pp === 0) return { l: "新", c: "bg-emerald-50 text-emerald-700 border-emerald-200", k: "new" }
  if (dp === 100 && pp === 100) return { l: "完成", c: "text-slate-400", k: "done" }
  if (dp > pp) return { l: "待回款", c: "bg-rose-50 text-rose-600 border-rose-200", k: "pending_collection" }
  if (pp > dp) return { l: "待提货", c: "bg-orange-50 text-orange-600 border-orange-200", k: "pending_delivery" }
  return { l: "待执行", c: "bg-blue-50 text-blue-700 border-blue-200", k: "pending" }
}

interface Tag { name: string; color: string }

const TAG_PALETTE = [
  { key: 'red',       bg: 'bg-red-100',       text: 'text-red-700',       border: 'border-red-200',       dot: 'bg-red-500' },
  { key: 'orange',    bg: 'bg-orange-100',    text: 'text-orange-700',    border: 'border-orange-200',    dot: 'bg-orange-500' },
  { key: 'amber',     bg: 'bg-amber-100',     text: 'text-amber-700',     border: 'border-amber-200',     dot: 'bg-amber-500' },
  { key: 'yellow',    bg: 'bg-yellow-100',    text: 'text-yellow-700',    border: 'border-yellow-200',    dot: 'bg-yellow-500' },
  { key: 'lime',      bg: 'bg-lime-100',      text: 'text-lime-700',      border: 'border-lime-200',      dot: 'bg-lime-500' },
  { key: 'green',     bg: 'bg-green-100',     text: 'text-green-700',     border: 'border-green-200',     dot: 'bg-green-500' },
  { key: 'emerald',   bg: 'bg-emerald-100',   text: 'text-emerald-700',   border: 'border-emerald-200',   dot: 'bg-emerald-500' },
  { key: 'teal',      bg: 'bg-teal-100',      text: 'text-teal-700',      border: 'border-teal-200',      dot: 'bg-teal-500' },
  { key: 'cyan',      bg: 'bg-cyan-100',      text: 'text-cyan-700',      border: 'border-cyan-200',      dot: 'bg-cyan-500' },
  { key: 'sky',       bg: 'bg-sky-100',       text: 'text-sky-700',       border: 'border-sky-200',       dot: 'bg-sky-500' },
  { key: 'blue',      bg: 'bg-blue-100',      text: 'text-blue-700',      border: 'border-blue-200',      dot: 'bg-blue-500' },
  { key: 'indigo',    bg: 'bg-indigo-100',    text: 'text-indigo-700',    border: 'border-indigo-200',    dot: 'bg-indigo-500' },
  { key: 'violet',    bg: 'bg-violet-100',    text: 'text-violet-700',    border: 'border-violet-200',    dot: 'bg-violet-500' },
  { key: 'purple',    bg: 'bg-purple-100',    text: 'text-purple-700',    border: 'border-purple-200',    dot: 'bg-purple-500' },
  { key: 'fuchsia',   bg: 'bg-fuchsia-100',   text: 'text-fuchsia-700',   border: 'border-fuchsia-200',   dot: 'bg-fuchsia-500' },
  { key: 'pink',      bg: 'bg-pink-100',      text: 'text-pink-700',      border: 'border-pink-200',      dot: 'bg-pink-500' },
  { key: 'rose',      bg: 'bg-rose-100',      text: 'text-rose-700',      border: 'border-rose-200',      dot: 'bg-rose-500' },
  { key: 'slate',     bg: 'bg-slate-200',     text: 'text-slate-700',     border: 'border-slate-300',     dot: 'bg-slate-500' },
  { key: 'gray',      bg: 'bg-gray-200',      text: 'text-gray-700',      border: 'border-gray-300',      dot: 'bg-gray-500' },
  { key: 'zinc',      bg: 'bg-zinc-200',      text: 'text-zinc-700',      border: 'border-zinc-300',      dot: 'bg-zinc-500' },
  { key: 'neutral',   bg: 'bg-neutral-200',   text: 'text-neutral-700',   border: 'border-neutral-300',   dot: 'bg-neutral-500' },
  { key: 'stone',     bg: 'bg-stone-200',     text: 'text-stone-700',     border: 'border-stone-300',     dot: 'bg-stone-500' },
  { key: 'warm',      bg: 'bg-stone-100',     text: 'text-stone-600',     border: 'border-stone-200',     dot: 'bg-stone-400' },
  { key: 'cool',      bg: 'bg-slate-100',     text: 'text-slate-600',     border: 'border-slate-200',     dot: 'bg-slate-400' },
]

/** 内联标签编辑器 —— 点击编辑，支持选择背景颜色 */
function TagCell({ contractId, tags: initialTags }: { contractId: string; tags: Tag[] | null }) {
  const [tags, setTags] = useState<Tag[]>(initialTags ?? [])
  const [editing, setEditing] = useState(false)
  const [input, setInput] = useState("")
  const [pickedColor, setPickedColor] = useState("indigo")
  const [showPalette, setShowPalette] = useState(false)
  const [palettePos, setPalettePos] = useState({ top: 0, left: 0 })
  const inputRef = useRef<HTMLInputElement>(null)
  const dotRef = useRef<HTMLButtonElement>(null)

  useEffect(() => { setTags(initialTags ?? []) }, [initialTags])

  const save = async (newTags: Tag[]) => {
    setTags(newTags)
    try { await apiPatch(`/sales-contracts/${contractId}/tags`, { tags: newTags }) } catch { /* 忽略 */ }
  }

  const addTag = () => {
    const name = input.trim()
    if (name && !tags.some(t => t.name === name)) { save([...tags, { name, color: pickedColor }]) }
    setInput(""); setEditing(false); setShowPalette(false)
  }

  const cancel = () => { setInput(""); setEditing(false); setShowPalette(false) }

  const removeTag = (name: string) => { save(tags.filter(t => t.name !== name)) }

  const openPalette = () => {
    if (dotRef.current) {
      const r = dotRef.current.getBoundingClientRect()
      setPalettePos({ top: r.bottom + 4, left: r.left })
    }
    setShowPalette(true)
  }

  const pickColor = (key: string) => {
    setPickedColor(key); setShowPalette(false)
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  const cur = TAG_PALETTE.find(p => p.key === pickedColor) ?? TAG_PALETTE[0]

  return (
    <div className="inline-flex flex-wrap items-center gap-1 justify-center" onClick={() => { if (!editing) { setEditing(true); setTimeout(() => inputRef.current?.focus(), 50) } }}>
      {tags.map(t => {
        const p = TAG_PALETTE.find(x => x.key === t.color) ?? TAG_PALETTE[0]
        return (
          <span key={t.name} className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium border ${p.bg} ${p.text} ${p.border}`}>
            {t.name}
            <button onClick={e => { e.stopPropagation(); removeTag(t.name) }} className="hover:opacity-50 ml-0.5 font-bold leading-none">&times;</button>
          </span>
        )
      })}
      {editing ? (
        <span className="inline-flex items-center gap-1" onClick={e => e.stopPropagation()}>
          <button ref={dotRef} onMouseDown={e => { e.stopPropagation(); e.preventDefault(); openPalette() }}
            className={`w-4 h-4 rounded-full ${cur.dot} hover:scale-110 transition-transform shrink-0`} title="选择颜色" />
          <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter") addTag(); if (e.key === "Escape") cancel() }}
            onBlur={() => setTimeout(() => { if (input.trim()) addTag(); else cancel() }, 200)}
            className="w-16 px-1.5 py-0.5 text-[10px] border border-indigo-300 rounded outline-none focus:ring-1 ring-indigo-400"
            />
        </span>
      ) : (
        <button className="text-[10px] text-slate-300 hover:text-indigo-400 px-1" title="添加标签">+</button>
      )}
      {showPalette && (
        <div className="fixed z-[9999] bg-white border border-slate-200 rounded-lg shadow-xl p-1.5 flex gap-1"
          style={{ top: palettePos.top, left: palettePos.left }}
          onMouseDown={e => { e.stopPropagation(); e.preventDefault() }}>
          {TAG_PALETTE.map(p => (
            <button key={p.key} onMouseDown={e => { e.stopPropagation(); e.preventDefault(); pickColor(p.key) }}
              className={`w-5 h-5 rounded-full ${p.dot} hover:scale-110 transition-transform ${pickedColor === p.key ? 'ring-2 ring-offset-1 ring-slate-800' : ''}`} />
          ))}
        </div>
      )}
    </div>
  )
}

export function SalesContractList() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string[]>([])
  const [searchNo, setSearchNo] = useState("")
  const [dateFrom, setDateFrom] = useState(""); const [dateTo, setDateTo] = useState("")
  const [brandFilter, setBrandFilter] = useState<string[]>([]); const [whFilter, setWhFilter] = useState<string[]>([])
  const [showFilterPanel, setShowFilterPanel] = useState("")
  const filterRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!showFilterPanel) return
    const fn = (e: MouseEvent) => { if (filterRef.current && !filterRef.current.contains(e.target as Node)) setShowFilterPanel("") }
    document.addEventListener("mousedown", fn)
    return () => document.removeEventListener("mousedown", fn)
  }, [showFilterPanel])

  const toggleFilter = (setter: any, val: string) => setter((p: string[]) => p.includes(val) ? p.filter(v => v !== val) : [...p, val])
  const statusOptions = [{v:"new",l:"新"},{v:"pending",l:"待执行"},{v:"pending_collection",l:"待回款"},{v:"pending_delivery",l:"待提货"},{v:"done",l:"完成"},{v:"cancelled",l:"已作废"}]

  const { data, isLoading } = useQuery({
    queryKey: ["sc", page],
    queryFn: () => apiGet<{ items: C[]; total: number; pages: number }>(`/sales-contracts?page=${page}&page_size=100`),
  })
  const { data: ents } = useQuery({ queryKey: ["ents"], queryFn: async () => { const r = await apiGet<{ items: E[] }>("/basedata/enterprises?page=1&page_size=200"); return r.items } })
  const { data: companies } = useQuery({ queryKey: ["companies-list"], queryFn: async () => { const r = await apiGet<{ items: {id:string;name:string}[] }>("/basedata/companies"); return r.items } })
  const nm = (id: string) => ents?.find(e => e.id === id)?.name ?? ""

  const [previewId, setPreviewId] = useState<string | null>(null)
  const [imgPreview, setImgPreview] = useState<{path:string;filename:string}|null>(null)

  const [idMap, setIdMap] = useState<{ wh: Record<string,string>; md: Record<string,string>; br: Record<string,string>; brColor: Record<string,string>; brWh: Record<string,string[]> }>({ wh:{}, md:{}, br:{}, brColor:{}, brWh:{} })
  const brandList = useMemo(() => Object.entries(idMap.br).map(([id, name]) => ({ id, name })), [idMap.br])
  const whList = useMemo(() => Object.entries(idMap.wh).map(([id, name]) => ({ id, name })), [idMap.wh])
  useEffect(() => {
    (async () => {
      const r = await fetch("/api/v1/brand/brands?page=1&page_size=100")
      const j = await r.json()
      const brands = j?.data?.items ?? []
      const brMap: Record<string,string> = {}
      const brColorMap: Record<string,string> = {}
      brands.forEach((b: any) => { brMap[b.id] = b.name; if (b.color) brColorMap[b.id] = b.color })
      // 并行加载所有品牌的仓库和型号
      const results = await Promise.all(brands.map((b: any) =>
        Promise.all([
          fetch(`/api/v1/brand/brands/${b.id}/warehouses?page=1&page_size=100`).then(r => r.json()),
          fetch(`/api/v1/brand/brands/${b.id}/models?page=1&page_size=100`).then(r => r.json()),
        ]).then(([w, m]) => ({ brandId: b.id, wItems: w?.data?.items ?? [], mItems: m?.data?.items ?? [] }))
      ))
      const whMap: Record<string,string> = {}
      const mdMap: Record<string,string> = {}
      const brWhMap: Record<string,string[]> = {}
      for (const { brandId, wItems, mItems } of results) {
        whMap[brandId] = whMap[brandId] || ""
        for (const bw of wItems) whMap[bw.id] = bw.name
        for (const bm of mItems) mdMap[bm.id] = bm.model_name
        brWhMap[brandId] = wItems.map((bw: any) => bw.id)
      }
      setIdMap(p => ({ ...p, br: brMap, brColor: brColorMap, wh: whMap, md: mdMap, brWh: brWhMap }))
    })()
  }, [])

  // 筛选
  const filtered = useMemo(() => {
    let items = data?.items ?? []
    if (statusFilter.length > 0) items = items.filter(c => statusFilter.includes(getStatus(c).k))
    if (searchNo) items = items.filter(c => c.contract_no.toLowerCase().includes(searchNo.toLowerCase()))
    if (dateFrom) items = items.filter(c => c.contract_date >= dateFrom)
    if (dateTo) items = items.filter(c => c.contract_date <= dateTo)
    if (brandFilter.length > 0 && whFilter.length > 0) {
      items = items.filter(c => (c.items ?? []).some(it => brandFilter.includes(it.brand_id) && whFilter.includes(it.shipping_warehouse_id)))
    } else if (brandFilter.length > 0) {
      items = items.filter(c => (c.items ?? []).some(it => brandFilter.includes(it.brand_id)))
    } else if (whFilter.length > 0) {
      items = items.filter(c => (c.items ?? []).some(it => whFilter.includes(it.shipping_warehouse_id)))
    }
    return items
  }, [data, statusFilter, searchNo, dateFrom, dateTo, brandFilter, whFilter])

  const stats = useMemo(() => {
    const s = { new: 0, pending_collection: 0, pending_delivery: 0, pending: 0, done: 0, cancelled: 0, total: filtered.length }
    filtered.forEach(c => { const k = getStatus(c).k; if (k in s) (s as any)[k]++ })
    return s
  }, [filtered])

  return (
    <div className="page-enter p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-bold text-slate-900">销售合同</h1>
        <Link to="/sales-contracts/create" className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all text-sm font-medium shadow-sm">+ 新增</Link>
      </div>

      {/* 筛选 + 统计 */}
      <div className="flex flex-wrap items-center gap-2 mb-3" ref={filterRef}>
        <Cascader label="品牌/仓库"
          options={useMemo(() => brandList.map(b => ({
            value: b.id, label: b.name,
            children: (idMap.brWh[b.id] ?? []).map(wid => ({ value: wid, label: whList.find(w => w.id === wid)?.name ?? wid.slice(0, 6) })),
          })), [brandList, whList, idMap.brWh])}
          selected={[...brandFilter, ...whFilter]}
          onChange={(v: string) => {
            if (brandList.some(b => b.id === v)) {
              if (brandFilter.includes(v)) {
                // 取消品牌 → 同时取消其下所有仓库
                setBrandFilter(p => p.filter(x => x !== v))
                setWhFilter(p => p.filter(wid => !(idMap.brWh[v] ?? []).includes(wid)))
              } else {
                // 勾选品牌 → 同时全选其下所有仓库
                setBrandFilter(p => [...p, v])
                setWhFilter(p => [...new Set([...p, ...(idMap.brWh[v] ?? [])])])
              }
            } else {
              toggleFilter(setWhFilter, v)
            }
          }}
          isOpen={showFilterPanel==="cascade"} onToggle={() => setShowFilterPanel(p=>p==="cascade"?"":"cascade")} />
        <CheckDropdown label="状态" options={statusOptions} selected={statusFilter} onChange={(v: string) => toggleFilter(setStatusFilter, v)} isOpen={showFilterPanel==="status"} onToggle={() => setShowFilterPanel(p=>p==="status"?"":"status")} />
        <input value={searchNo} onChange={e => setSearchNo(e.target.value)} className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs w-28" />
        <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs w-30" />
        <span className="text-xs text-slate-300">~</span>
        <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs w-30" />
        <span className="text-xs text-slate-400 ml-auto">共 <b className="text-slate-700">{filtered.length}</b> 条</span>
        {(brandFilter.length>0||whFilter.length>0||statusFilter.length>0) && <button onClick={() => { setBrandFilter([]); setWhFilter([]); setStatusFilter([]) }} className="text-xs text-indigo-500 hover:text-indigo-700 ml-1">清除筛选</button>}
      </div>
      <div className="flex gap-3 mb-3 text-xs">
        {[["全部", stats.total, "bg-slate-100 text-slate-600"], ["新", stats.new, "bg-emerald-50 text-emerald-700"], ["待执行", stats.pending, "bg-blue-50 text-blue-700"], ["待回款", stats.pending_collection, "bg-rose-50 text-rose-600"], ["待提货", stats.pending_delivery, "bg-orange-50 text-orange-600"], ["完成", stats.done, "text-slate-400"]].map(([l, v, c]) => (
          <span key={l as string} className={`${c} px-2.5 py-1 rounded-full font-medium`}>{l} {v as number}</span>
        ))}
      </div>

      {/* 表格 */}
      <div className="bg-white rounded-lg border border-slate-200/60 shadow-sm overflow-x-auto -mx-4 sm:mx-0">
        {isLoading ? <div className="p-16 text-center text-slate-300">加载中...</div> : filtered.length === 0 ? (
          <div className="py-16 text-center text-slate-400">暂无匹配数据</div>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="border-b border-slate-100 bg-slate-50/50">
              {["标签","状态","签订日期","合同编号","客户","明细","数量","金额","已提","可提","已回","待回","附件","备注"].map(h => (
                <th key={h} className={`px-3 py-2.5 text-xs font-semibold text-slate-400 ${["标签","状态","附件"].includes(h)?"text-center":["数量","金额","已提","可提","已回","待回"].includes(h)?"text-right":"text-left"}`}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                  {/* 标签 */}
                  <td className="px-2 py-2.5 text-center"><TagCell contractId={c.id} tags={c.tags} /></td>
                  {/* 状态 */}
                  <td className="px-3 py-2.5 text-center"><StatusBadge c={c} /></td>
                  {/* 签订日期 */}
                  <td className="px-3 py-2.5 text-xs text-slate-500">{c.contract_date}</td>
                  {/* 合同编号 */}
                  <td className="px-3 py-2.5"><button onClick={() => setPreviewId(c.id)} className="font-semibold text-indigo-600 hover:text-indigo-800 text-left text-xs">{c.contract_no}</button></td>
                  {/* 客户 */}
                  <td className="px-3 py-2.5 text-slate-700 font-medium text-xs">{nm(c.customer_enterprise_id)}</td>
                  {/* 明细 —— 多行换行显示 */}
                  <td className="px-3 py-2.5"><div className="flex flex-col gap-1.5">
                    {(c.items ?? []).map((it, idx) => (
                      <span key={idx} className="inline-flex items-center gap-2.5 text-xs">
                        <span className={`px-1.5 py-0.5 rounded font-medium ${brandChipClass(idMap.brColor?.[it.brand_id] ?? null)}`}>{idMap.br[it.brand_id]?.slice(0,6) ?? ""}</span>
                        <span className="text-slate-500">{idMap.wh[it.shipping_warehouse_id]?.slice(0,4) ?? ""}</span>
                        <span className="text-slate-500">{idMap.md[it.model_id]?.slice(0,8) ?? ""}</span>
                        <span className="text-slate-700 font-medium">{it.quantity}吨</span>
                      </span>
                    ))}
                  </div></td>
                  {/* 数量 */}
                  <td className="px-3 py-2.5 text-right text-slate-700 tabular-nums text-xs">{c.total_quantity?.toLocaleString()}</td>
                  {/* 金额 */}
                  <td className="px-3 py-2.5 text-right text-slate-700 tabular-nums text-xs">¥{c.total_amount?.toLocaleString()}</td>
                  {/* 已提 */}
                  <td className="px-2 py-2.5 text-right">
                    <span className="text-xs text-slate-500 font-medium tabular-nums">{Math.round(c.total_quantity * (c.pickup_progress ?? 0) / 100).toLocaleString()}</span>
                    <span className="text-[10px] text-slate-400 ml-0.5">吨</span>
                  </td>
                  {/* 可提 */}
                  <td className="px-2 py-2.5 text-right">
                    <span className="text-xs text-emerald-600 font-medium tabular-nums">{Math.round(c.total_quantity * (100 - (c.pickup_progress ?? 0)) / 100).toLocaleString()}</span>
                    <span className="text-[10px] text-slate-400 ml-0.5">吨</span>
                  </td>
                  {/* 已回 */}
                  <td className="px-2 py-2.5 text-right">
                    <span className="text-xs text-slate-500 font-medium tabular-nums">¥{Math.round(c.total_amount * (c.collection_progress ?? 0) / 100).toLocaleString()}</span>
                  </td>
                  {/* 待回 */}
                  <td className="px-2 py-2.5 text-right">
                    <span className="text-xs text-rose-400 font-medium tabular-nums">¥{Math.round(c.total_amount * (100 - (c.collection_progress ?? 0)) / 100).toLocaleString()}</span>
                  </td>
                  {/* 附件 */}
                  <td className="px-3 py-2.5 text-center">
                    {c.attachment_path && c.attachment_path.length > 0 ? (
                      <div className="flex justify-center gap-1">
                        {c.attachment_path.slice(0,3).map((f, i) => {
                          const isImg = /\.(png|jpg|jpeg|gif|webp|bmp)$/i.test(f.filename)
                          return isImg ? (
                            <button key={i} onClick={() => setImgPreview(f)} className="w-7 h-7 rounded border border-slate-200 overflow-hidden bg-slate-50 shrink-0"><img src={f.path} alt="" className="w-full h-full object-cover"/></button>
                          ) : (
                            <a key={i} href={f.path} target="_blank" className="w-7 h-7 rounded border border-slate-200 bg-slate-50 flex items-center justify-center shrink-0">
                              <svg className="w-3.5 h-3.5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                            </a>
                          )
                        })}
                        {c.attachment_path.length > 3 && <span className="text-xs text-slate-400 self-center">+{c.attachment_path.length-3}</span>}
                      </div>
                    ) : <span className="text-xs text-slate-300"></span>}
                  </td>
                  {/* 备注 */}
                  <td className="px-3 py-2.5 text-xs text-slate-500 max-w-[120px] truncate" title={c.remark ?? ""}>{c.remark || <span className="text-slate-300"></span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 bg-slate-50/50">
            <span className="text-xs text-slate-500">共 {data.total} 条</span>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page<=1} className="px-2.5 py-1.5 text-xs text-slate-600 hover:bg-white rounded disabled:opacity-30">←</button>
              {Array.from({length: Math.min(data.pages,5)}, (_, i) => i+1).map(p => <button key={p} onClick={() => setPage(p)} className={`w-7 h-7 rounded text-xs font-medium ${p===page?"bg-indigo-600 text-white":"text-slate-600 hover:bg-white"}`}>{p}</button>)}
              <button onClick={() => setPage(p => Math.min(data.pages, p+1))} disabled={page>=data.pages} className="px-2.5 py-1.5 text-xs text-slate-600 hover:bg-white rounded disabled:opacity-30">→</button>
            </div>
          </div>
        )}
      </div>
      {/* 详情弹窗 */}
      {previewId && <PreviewModal id={previewId} idMap={idMap} ents={ents} companies={companies} onClose={() => setPreviewId(null)} />}

      {imgPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={() => setImgPreview(null)}>
          <img src={imgPreview.path} alt={imgPreview.filename} className="max-w-[90vw] max-h-[90vh] rounded-2xl shadow-2xl" onClick={e => e.stopPropagation()} />
          <button onClick={() => setImgPreview(null)} className="absolute top-6 right-6 w-10 h-10 rounded-full bg-white/20 hover:bg-white/40 flex items-center justify-center text-white transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
      )}
    </div>
  )
}

function PreviewModal({ id, idMap, ents, companies, onClose }: { id: string; idMap: any; ents: any; companies: any; onClose: () => void }) {
  const qc = useQueryClient()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!menuOpen) return
    const fn = (e: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false) }
    document.addEventListener("mousedown", fn)
    return () => document.removeEventListener("mousedown", fn)
  }, [menuOpen])

  const { data, isLoading } = useQuery({
    queryKey: ["sc-preview", id],
    queryFn: () => apiGet<any>(`/sales-contracts/${id}`),
    enabled: !!id,
  })

  const cancelMut = useMutation({
    mutationFn: () => apiDelete(`/sales-contracts/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sc"] }); onClose() }
  })

  if (!data) return null
  const c = data as any
  const st = getStatus(c)
  const en = (eid: string) => ents?.find((e: any) => e.id === eid)?.name ?? ""
  const cn = (cid: string) => companies?.find((c: any) => c.id === cid)?.name ?? ""

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[4vh] bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[92vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-white/95 backdrop-blur-xl border-b border-slate-100 px-8 py-5 flex items-center justify-between rounded-t-2xl z-10">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold text-slate-900">{c.contract_no}</h2>
            <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold border ${st.c}`}>{st.l}</span>
          </div>
          <div className="flex items-center gap-2" ref={menuRef}>
            <Link to={`/sales-contracts/${id}/edit`} className="px-4 py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors" onClick={onClose}>编辑</Link>
            <div className="relative">
              <button onClick={() => setMenuOpen(p => !p)} className="w-9 h-9 flex items-center justify-center rounded-lg border border-slate-200 text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/></svg>
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-full mt-1 bg-white border border-slate-200 rounded-xl shadow-xl z-50 py-1 min-w-[100px]">
                  <button onClick={async () => { setMenuOpen(false); if (sysConfirm("确定作废？")) cancelMut.mutate() }} className="w-full text-left px-4 py-2.5 text-sm text-rose-600 hover:bg-rose-50 transition-colors">作废</button>
                </div>
              )}
            </div>
            <button onClick={onClose} className="w-9 h-9 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/></svg>
            </button>
          </div>
        </div>

        <div className="p-8 space-y-6">
          {/* 基本信息 + 进度 */}
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2 bg-white rounded-xl border border-slate-200/60 p-5">
              <h3 className="text-sm font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">基本信息</h3>
              <div className="grid grid-cols-2 gap-x-8 gap-y-3">
                <div className="flex items-center gap-3"><span className="text-xs text-slate-400 w-20 shrink-0">主体公司</span><span className="text-sm font-medium text-slate-800">{cn(c.company_id)}</span></div>
                <div className="flex items-center gap-3"><span className="text-xs text-slate-400 w-20 shrink-0">客户</span><span className="text-sm font-medium text-slate-800">{en(c.customer_enterprise_id)}</span></div>
                <div className="flex items-center gap-3"><span className="text-xs text-slate-400 w-20 shrink-0">合同编号</span><span className="text-sm font-medium text-slate-800">{c.contract_no}</span></div>
                <div className="flex items-center gap-3"><span className="text-xs text-slate-400 w-20 shrink-0">签订日期</span><span className="text-sm text-slate-700">{c.contract_date}</span></div>
                <div className="flex items-center gap-3"><span className="text-xs text-slate-400 w-20 shrink-0">开始日期</span><span className="text-sm text-slate-700">{c.contract_start_date}</span></div>
                <div className="flex items-center gap-3"><span className="text-xs text-slate-400 w-20 shrink-0">结束日期</span><span className="text-sm text-slate-700">{c.contract_end_date}</span></div>
                <div className="flex items-center gap-3 col-span-2"><span className="text-xs text-slate-400 w-20 shrink-0">备注</span><span className="text-sm text-slate-700">{c.remark || ""}</span></div>
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200/60 p-5">
              <h3 className="text-sm font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">执行进度</h3>
              <div className="space-y-5">
                <div>
                  <div className="flex justify-between text-xs mb-1.5"><span className="text-slate-500">提货进度</span><span className="font-semibold text-slate-700">{c.pickup_progress??0}%</span></div>
                  <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-emerald-500 rounded-full" style={{width:`${c.pickup_progress??0}%`}}/></div>
                  <div className="flex justify-between text-xs mt-1"><span className="text-slate-400">已提</span><span className="font-medium text-slate-600 tabular-nums">{Math.round(c.total_quantity * (c.pickup_progress ?? 0) / 100).toLocaleString()} 吨</span></div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1.5"><span className="text-slate-500">回款进度</span><span className="font-semibold text-slate-700">{c.collection_progress??0}%</span></div>
                  <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-blue-500 rounded-full" style={{width:`${c.collection_progress??0}%`}}/></div>
                  <div className="flex justify-between text-xs mt-1"><span className="text-slate-400">已回</span><span className="font-medium text-slate-600 tabular-nums">¥{Math.round(c.total_amount * (c.collection_progress ?? 0) / 100).toLocaleString()}</span></div>
                </div>
              </div>
            </div>
          </div>

          {/* 商品明细 */}
          <div className="bg-white rounded-xl border border-slate-200/60 p-5">
            <h3 className="text-sm font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">商品明细 <span className="text-xs text-slate-400 font-normal">{c.items?.length ?? 0} 项</span></h3>
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-100">
                <th className="px-3 py-2.5 text-xs text-slate-400 text-left">品牌</th><th className="px-3 py-2.5 text-xs text-slate-400 text-left">仓库</th><th className="px-3 py-2.5 text-xs text-slate-400 text-left">型号</th>
                <th className="px-3 py-2.5 text-xs text-slate-400 text-right w-20">数量</th><th className="px-3 py-2.5 text-xs text-slate-400 text-right w-24">单价</th><th className="px-3 py-2.5 text-xs text-slate-400 text-right w-24">金额</th>
              </tr></thead>
              <tbody>{(c.items??[]).map((it: any, i: number) => (
                <tr key={i} className="border-b border-slate-50">
                  <td className="px-3 py-2.5"><span className={`px-1.5 py-0.5 rounded font-medium text-xs ${brandChipClass(idMap.brColor?.[it.brand_id] ?? null)}`}>{idMap.br?.[it.brand_id] ?? ""}</span></td>
                  <td className="px-3 py-2.5 text-slate-600">{idMap.wh?.[it.shipping_warehouse_id] ?? ""}</td>
                  <td className="px-3 py-2.5 text-slate-600">{idMap.md?.[it.model_id] ?? ""}</td>
                  <td className="px-3 py-2.5 text-right text-slate-700">{it.quantity}吨</td>
                  <td className="px-3 py-2.5 text-right text-slate-700">¥{it.sale_price?.toLocaleString()}</td>
                  <td className="px-3 py-2.5 text-right font-semibold text-slate-900">¥{it.amount?.toLocaleString()}</td>
                </tr>
              ))}</tbody>
            </table>
            <div className="flex items-center gap-12 mt-4 pt-4 border-t border-slate-100">
              <div><span className="text-xs text-slate-400">合计数量</span><p className="text-xl font-bold text-slate-900 mt-0.5">{c.total_quantity?.toLocaleString()} <span className="text-sm font-normal text-slate-400">吨</span></p></div>
              <div><span className="text-xs text-slate-400">合计金额</span><p className="text-xl font-bold text-rose-600 mt-0.5">¥{c.total_amount?.toLocaleString()}</p></div>
            </div>
          </div>

          {/* 合同附件 */}
          <div className="bg-white rounded-xl border border-slate-200/60 p-5">
            <h3 className="text-sm font-semibold text-slate-800 mb-4 pb-3 border-b border-slate-100">合同附件</h3>
            {c.attachment_path && c.attachment_path.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {c.attachment_path.map((f: any, i: number) => (
                  <a key={i} href={f.path} target="_blank" className="flex items-center gap-2 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-indigo-600 hover:bg-indigo-50 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/></svg>
                    {f.filename}
                  </a>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">暂无附件</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
