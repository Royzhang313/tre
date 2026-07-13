/** 计划看板 V3 —— 按明细项显示 + 日期滚动 */
import { useState, useEffect, useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { apiGet, apiPost, apiPut, apiPatch, apiDelete } from "../../api/client"
import { SearchableSelect } from "../../components/shared/SearchableSelect"
import { Cascader } from "../../components/shared/Cascader"
import { Dropdown } from "../../components/shared/Dropdown"
import { AuditTimeline } from "../../components/shared/AuditTimeline"
import type { CascaderOption } from "../../components/shared/Cascader"
import { fmtQty } from "../../lib/utils"
import {
  DndContext, DragOverlay, closestCorners,
  PointerSensor, useSensor, useSensors,
  useDroppable,
  type DragStartEvent, type DragEndEvent,
} from "@dnd-kit/core"
import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { sysToast, sysConfirm } from "../../components/shared/Dialog"

const INP = "px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400"

interface PlanItem { id: string; line_no: number; customer_enterprise_id: string; sales_contract_id: string; model_id: string; warehouse_id: string; planned_quantity: number; shipped_quantity: number; surcharge_type: string | null; surcharge_amount: number; purchase_price: number; sale_price: number }
interface Plan { id: string; brand_id: string; supplier_enterprise_id: string; purchase_contract_id: string; planned_date: string; delivery_method: string; status: string; total_planned_quantity: number; remark: string | null; items: PlanItem[]; created_at: string }
interface BrandInfo { [id: string]: { name: string; color: string; warehouses?: { id: string; name: string }[]; models?: { id: string; model_name: string }[] } }
interface NameMap { [id: string]: string }

const STATUS_MAP: Record<string, { label: string; dot: string }> = {
  pending: { label: "待执行", dot: "bg-slate-400" },
  in_progress: { label: "进行中", dot: "bg-blue-500" },
  partially_shipped: { label: "部分发货", dot: "bg-amber-500" },
  completed: { label: "已完成", dot: "bg-emerald-500" },
  cancelled: { label: "已取消", dot: "bg-red-500" },
}

const DL_MAP: Record<string, string> = { ZT: "自提", SH: "送货" }

// ============================================================
// PlanItemBar —— 横条展示：客户 | 品牌 | 仓库 | 型号 | 计划数量
// ============================================================
function PlanItemBar({ item, plan, brandName, brandColor, ents, models, whs, onClick }: {
  item: PlanItem; plan: Plan; brandName: string; brandColor: string
  ents: NameMap; models: NameMap; whs: NameMap
  onClick: () => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: item.id })
  const style = { transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.5 : 1 }
  const entName = ents[item.customer_enterprise_id] ?? item.customer_enterprise_id.slice(0, 8)
  const whName = whs[item.warehouse_id] ?? item.warehouse_id.slice(0, 8)
  const mdlName = models[item.model_id] ?? item.model_id.slice(0, 10)
  const isDone = plan.status === "completed" || plan.status === "cancelled"
  const dlLabel = plan.delivery_method === "ZT" ? "自提" : "送货"
  const dlBg = plan.delivery_method === "ZT" ? "bg-amber-100 text-amber-600" : "bg-sky-100 text-sky-600"

  return (
    <div ref={setNodeRef} style={style} onClick={onClick}
      className={`group flex items-center rounded-lg border px-3 py-2 hover:shadow-md transition-shadow cursor-pointer select-none min-h-[36px] gap-2 ${isDone ? "bg-slate-50 border-slate-200 opacity-65" : "bg-white border-slate-200 hover:border-indigo-300"}`}
      {...attributes} {...listeners}>
      {/* 客户 */}
      <span className={`text-xs font-medium truncate min-w-[60px] max-w-[120px] ${isDone ? "text-slate-400" : "text-slate-700"}`}>{entName}</span>
      {/* 分隔 */}
      <span className="text-slate-200">|</span>
      {/* 品牌 */}
      <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium text-white shrink-0 min-w-[40px] text-center" style={{ backgroundColor: isDone ? "#cbd5e1" : (brandColor || "#6366f1") }}>{brandName.slice(0, 8) || "—"}</span>
      {/* 仓库 */}
      <span className={`text-xs truncate min-w-[50px] max-w-[100px] ${isDone ? "text-slate-400" : "text-slate-600"}`}>{whName}</span>
      <span className="text-slate-200">|</span>
      {/* 型号 */}
      <span className={`text-xs truncate min-w-[50px] max-w-[100px] ${isDone ? "text-slate-400" : "text-slate-500"}`}>{mdlName}</span>
      {/* 分隔 */}
      <span className="text-slate-200">|</span>
      {/* 计划数量 */}
      <span className={`text-xs font-semibold shrink-0 tabular-nums min-w-[56px] text-right ${isDone ? "text-slate-400" : "text-slate-800"}`}>{fmtQty(item.planned_quantity)}吨</span>
      {/* 已发量 */}
      {item.shipped_quantity > 0 && <span className={`text-[10px] shrink-0 ${isDone ? "text-slate-400" : "text-slate-400"}`}>(已发{fmtQty(item.shipped_quantity)})</span>}
      {/* 调货标记 */}
      {item.surcharge_type === "carbonate_transfer" && <span className="text-[10px] text-purple-500 shrink-0">碳酸料</span>}
      {item.surcharge_type === "brand_transfer" && <span className="text-[10px] text-orange-500 shrink-0">品牌调货</span>}
      {/* 配送方式 */}
      <span className={`text-[10px] px-1 py-0.5 rounded font-medium shrink-0 ml-auto ${isDone ? "bg-slate-200 text-slate-400" : dlBg}`}>{dlLabel}</span>
    </div>
  )
}

// ============================================================
// DateRow
// ============================================================
function DateRow({ date, plans, brands, ents, models, whs, isToday, isOverdue, onPlanClick, isDone }: {
  date: string; plans: Plan[]; brands: BrandInfo; ents: NameMap; models: NameMap; whs: NameMap
  isToday: boolean; isOverdue: boolean; onPlanClick: (p: Plan) => void; isDone?: boolean
}) {
  const colId = isDone ? `done-col-${date}` : `col-${date}`
  const { setNodeRef, isOver } = useDroppable({ id: colId })
  const totalQty = plans.reduce((s, p) => s + p.total_planned_quantity, 0)
  const dayLabel = new Date(date + "T00:00:00").toLocaleDateString("zh-CN", { weekday: "short", month: "numeric", day: "numeric" })

  return (
    <div className={`flex rounded-lg ${isDone ? "bg-white" : (isToday ? "bg-indigo-50/60 ring-2 ring-indigo-200" : isOverdue ? "bg-red-50/40" : "bg-slate-50")} ${isOver ? "ring-2 ring-indigo-400" : ""}`}>
      {/* 日期标签 - 紧凑 */}
      <div className="w-16 sm:w-20 shrink-0 flex flex-col items-center justify-center py-2 px-1 border-r border-white/60">
        <span className={`text-xs font-bold ${isDone ? "text-slate-400" : (isToday ? "text-indigo-700" : isOverdue ? "text-red-600" : "text-slate-500")}`}>{dayLabel}</span>
        {totalQty > 0 && <span className={`text-[10px] mt-0.5 ${isDone ? "text-slate-300" : "text-slate-400"}`}>{fmtQty(totalQty)}吨</span>}
        {isToday && <span className="text-[10px] text-indigo-500 font-medium mt-0.5">今天</span>}
      </div>
      {/* 横条列表 */}
      <div ref={setNodeRef} className="flex-1 py-1.5 px-2">
        {plans.length === 0 ? (
          <div className="flex items-center justify-center h-full text-xs text-slate-300 min-h-[32px]">{isDone ? "" : "拖拽至此"}</div>
        ) : (
          <div className="flex flex-col gap-1.5">
            {plans.flatMap(plan => {
              const brand = brands[plan.brand_id]
              return plan.items.map(item => (
                <PlanItemBar key={item.id} item={item} plan={plan}
                  brandName={brand?.name ?? "—"} brandColor={brand?.color ?? "#6366f1"}
                  ents={ents} models={models} whs={whs}
                  onClick={() => onPlanClick(plan)} />
              ))
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// ============================================================
// PlanningBoard V3
// ============================================================
export function ShippingPlanKanban() {
  const nav = useNavigate()
  const qc = useQueryClient()
  const [activeId, setActiveId] = useState<string | null>(null)
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null)
  const [showShipForm, setShowShipForm] = useState(false)

  const [brandFilter, setBrandFilter] = useState<string[]>([])
  const [whFilter, setWhFilter] = useState<string[]>([])
  const [cascaderOpen, setCascaderOpen] = useState(false)
  const [fCustomerId, setFCustomerId] = useState("")
  const [fSupplierId, setFSupplierId] = useState("")
  const [fPcId, setFPcId] = useState("")
  const [fScId, setFScId] = useState("")
  const [fStatus, setFStatus] = useState("")
  const [fDateFrom, setFDateFrom] = useState("")
  const [fDateTo, setFDateTo] = useState("")

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }))

  const buildUrl = () => {
    const p = new URLSearchParams(); p.set("page_size", "500")
    if (fDateFrom) p.set("start_date", fDateFrom)
    if (fDateTo) p.set("end_date", fDateTo)
    if (fCustomerId) p.set("customer_enterprise_id", fCustomerId)
    if (fSupplierId) p.set("supplier_enterprise_id", fSupplierId)
    if (fPcId) p.set("purchase_contract_id", fPcId)
    if (fScId) p.set("sales_contract_id", fScId)
    if (fStatus) p.set("status", fStatus)
    return `/shipping/plans?${p.toString()}`
  }

  const { data: plans = [], isLoading } = useQuery({
    queryKey: ["shipping-plans", fDateFrom, fDateTo, fCustomerId, fSupplierId, fPcId, fScId, fStatus],
    queryFn: async () => { const r = await apiGet<{ items: Plan[] }>(buildUrl()); return r.items ?? [] },
  })

  const { data: brands } = useQuery({
    queryKey: ["brands-board"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string; color: string }[] }>("/brand/brands?page=1&page_size=200")
      const map: BrandInfo = {}
      for (const b of r.items ?? []) map[b.id] = { name: b.name, color: b.color || "#6366f1" }
      // 并行加载所有品牌的仓库和型号
      await Promise.all((r.items ?? []).map(async (b) => {
        try {
          const wr = await apiGet<{ items: { id: string; name: string }[] }>(`/brand/brands/${b.id}/warehouses?page=1&page_size=100`)
          if (map[b.id]) map[b.id].warehouses = wr.items ?? []
        } catch { /* ignore */ }
        try {
          const mr = await apiGet<{ items: { id: string; model_name: string }[] }>(`/brand/brands/${b.id}/models?page=1&page_size=100`)
          if (map[b.id]) map[b.id].models = mr.items ?? []
        } catch { /* ignore */ }
      }))
      return map
    },
  })

  const { data: enterprises } = useQuery({
    queryKey: ["ents-board"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; name: string }[] }>("/basedata/enterprises?page=1&page_size=200")
      const m: NameMap = {}; for (const e of r.items ?? []) m[e.id] = e.name; return m
    },
  })

  const { data: pcs } = useQuery({
    queryKey: ["pcs-board"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; contract_no: string }[] }>("/purchase-contracts?page=1&page_size=100")
      const m: NameMap = {}; for (const pc of (r.items ?? []).filter((x: any) => x.status !== "cancelled")) m[pc.id] = pc.contract_no; return m
    },
  })

  const { data: scs } = useQuery({
    queryKey: ["scs-board"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; contract_no: string }[] }>("/sales-contracts?page=1&page_size=100")
      const m: NameMap = {}; for (const sc of (r.items ?? []).filter((x: any) => x.status !== "cancelled")) m[sc.id] = sc.contract_no; return m
    },
  })

  // 型号/仓库名称映射（与表单同款 useEffect 方案，已验证可行）
  const [itemNames, setItemNames] = useState<{ models: NameMap; whs: NameMap }>({ models: {}, whs: {} })
  useEffect(() => {
    const brandIds = [...new Set(plans.map(p => p.brand_id))]
    if (brandIds.length === 0) return
    let cancelled = false
    ;(async () => {
      const m: NameMap = {}; const w: NameMap = {}
      // 并行加载所有品牌的型号和仓库
      await Promise.all(brandIds.map(async (bid) => {
        try {
          const [wResp, mResp] = await Promise.all([
            apiGet<{ items: { id: string; name: string }[] }>(`/brand/brands/${bid}/warehouses?page=1&page_size=100`).catch(() => ({ items: [] })),
            apiGet<{ items: { id: string; model_name: string }[] }>(`/brand/brands/${bid}/models?page=1&page_size=100`).catch(() => ({ items: [] })),
          ])
          for (const bw of wResp.items ?? []) w[bw.id] = bw.name
          for (const bm of mResp.items ?? []) m[bm.id] = bm.model_name
        } catch { /* skip */ }
      }))
      if (!cancelled) setItemNames({ models: m, whs: w })
    })()
    return () => { cancelled = true }
  }, [plans])

  // 汇总名称（itemNames + brands + UUID 占位）
  const { models, whs: whNames } = useMemo(() => {
    const m: NameMap = {}; const w: NameMap = {}
    for (const [, b] of Object.entries(brands ?? {})) {
      for (const bw of b.warehouses ?? []) w[bw.id] = bw.name
      for (const bm of b.models ?? []) m[bm.id] = bm.model_name
    }
    // itemNames 覆盖（优先级更高——直接从品牌 API 获取）
    Object.assign(m, itemNames.models)
    Object.assign(w, itemNames.whs)
    // UUID 占位兜底
    for (const p of plans) for (const it of p.items) {
      if (it.model_id && !m[it.model_id]) m[it.model_id] = it.model_id.slice(0, 8)
      if (it.warehouse_id && !w[it.warehouse_id]) w[it.warehouse_id] = it.warehouse_id.slice(0, 8)
    }
    return { models: m, whs: w }
  }, [plans, brands, itemNames])

  // 筛选选项 —— 多选级联
  const cascaderOptions: CascaderOption[] = useMemo(() => {
    return Object.entries(brands ?? {}).map(([id, b]) => ({
      value: id, label: b.name,
      children: (b.warehouses ?? []).map(w => ({ value: w.id, label: w.name })),
    }))
  }, [brands])

  const handleCascader = (val: string) => {
    const isBrand = brands?.[val] !== undefined
    if (isBrand) {
      if (brandFilter.includes(val)) {
        // 取消品牌 → 同时取消其下所有仓库
        const whIds = (brands?.[val]?.warehouses ?? []).map(w => w.id)
        setBrandFilter(p => p.filter(v => v !== val))
        setWhFilter(p => p.filter(v => !whIds.includes(v)))
      } else {
        // 勾选品牌 → 同时全选其下所有仓库
        const whIds = (brands?.[val]?.warehouses ?? []).map(w => w.id)
        setBrandFilter(p => [...p, val])
        setWhFilter(p => [...new Set([...p, ...whIds])])
      }
    } else {
      setWhFilter(p => p.includes(val) ? p.filter(v => v !== val) : [...p, val])
    }
  }

  // 品牌/仓库客户端筛选
  const filteredPlans = useMemo(() => {
    let result = plans
    if (brandFilter.length > 0) result = result.filter(p => brandFilter.includes(p.brand_id))
    if (whFilter.length > 0) result = result.filter(p => p.items.some(it => whFilter.includes(it.warehouse_id)))
    return result
  }, [plans, brandFilter, whFilter])

  const { data: allPcs } = useQuery({
    queryKey: ["pcs-filter-board"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; contract_no: string }[] }>("/purchase-contracts?page=1&page_size=100")
      return (r.items ?? []).filter((pc: any) => pc.status !== "cancelled").map((pc: any) => ({ id: pc.id, name: pc.contract_no }))
    },
  })

  const { data: allScs } = useQuery({
    queryKey: ["scs-filter-board"],
    queryFn: async () => {
      const r = await apiGet<{ items: { id: string; contract_no: string }[] }>("/sales-contracts?page=1&page_size=100")
      return (r.items ?? []).filter((sc: any) => sc.status !== "cancelled").map((sc: any) => ({ id: sc.id, name: sc.contract_no }))
    },
  })

  // 周翻页
  const [weekOffset, setWeekOffset] = useState(0)

  // 当前周的 7 天（周一~周日）
  const weekDates = useMemo(() => {
    const now = new Date()
    const dayOfWeek = now.getDay() || 7 // 周日=7
    const monday = new Date(now)
    monday.setDate(now.getDate() - dayOfWeek + 1 + weekOffset * 7)
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(monday); d.setDate(monday.getDate() + i)
      return d.toISOString().slice(0, 10)
    })
  }, [weekOffset])

  const weekLabel = useMemo(() => `${weekDates[0]} ~ ${weekDates[6]}`, [weekDates])

  // 拆分：进行中 / 已完成
  const activePlans = useMemo(() => filteredPlans.filter(p => p.status !== "completed" && p.status !== "cancelled"), [filteredPlans])
  const donePlans = useMemo(() => filteredPlans.filter(p => p.status === "completed" || p.status === "cancelled"), [filteredPlans])

  const groupedActive = useMemo(() => {
    const g: Record<string, Plan[]> = {}; for (const d of weekDates) g[d] = []
    for (const p of activePlans) { if (weekDates.includes(p.planned_date)) { if (!g[p.planned_date]) g[p.planned_date] = []; g[p.planned_date].push(p) } }
    return g
  }, [activePlans, weekDates])

  const groupedDone = useMemo(() => {
    const g: Record<string, Plan[]> = {}; for (const d of weekDates) g[d] = []
    for (const p of donePlans) { if (weekDates.includes(p.planned_date)) { if (!g[p.planned_date]) g[p.planned_date] = []; g[p.planned_date].push(p) } }
    return g
  }, [donePlans, weekDates])

  const dateMut = useMutation({
    mutationFn: async ({ planId, date }: { planId: string; date: string }) => {
      await apiPatch(`/shipping/plans/${planId}/date`, { planned_date: date })
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shipping-plans"] }),
  })

  const handleDragStart = (e: DragStartEvent) => setActiveId(e.active.id as string)
  const handleDragEnd = (e: DragEndEvent) => {
    setActiveId(null)
    const { active, over } = e
    if (!over) return
    let targetDate = ""
    const overId = over.id as string
    if (overId.startsWith("col-")) { targetDate = overId.slice(4) }
    else if (overId.startsWith("done-col-")) { targetDate = overId.slice(9) }
    else { const tp = plans.find(p => p.id === overId || p.items.some(i => i.id === overId)); if (tp) targetDate = tp.planned_date }
    if (targetDate) {
      const plan = plans.find(p => p.items.some(i => i.id === active.id))
      if (plan) dateMut.mutate({ planId: plan.id, date: targetDate })
    }
  }

  const activePlan = activeId ? plans.find(p => p.items.some(i => i.id === activeId)) : undefined
  const today = new Date().toISOString().slice(0, 10)

  if (isLoading) return <div className="p-8 text-slate-400">加载中...</div>

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* 筛选栏 */}
      <div className="px-3 sm:px-4 py-2 bg-white border-b border-slate-200 flex flex-wrap items-center gap-2 shrink-0">
        <h1 className="text-lg font-bold text-slate-800 mr-1">计划</h1>
        <button onClick={() => nav("/shipping/plans/create")} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs hover:bg-indigo-700 whitespace-nowrap">+ 新建</button>
        <button onClick={() => nav("/freight")} className="px-3 py-1.5 border border-slate-200 text-slate-600 rounded-lg text-xs hover:bg-slate-50 whitespace-nowrap">📋 台账</button>
        <div className="w-px h-6 bg-slate-200 mx-1" />
        {/* 周翻页 */}
        <button onClick={() => setWeekOffset(p => p - 1)} className="px-2 py-1 border border-slate-200 rounded text-xs text-slate-600 hover:bg-slate-50">◀</button>
        <span className="text-xs text-slate-700 font-medium min-w-[160px] text-center">{weekLabel}</span>
        <button onClick={() => setWeekOffset(p => p + 1)} className="px-2 py-1 border border-slate-200 rounded text-xs text-slate-600 hover:bg-slate-50">▶</button>
        <button onClick={() => setWeekOffset(0)} className="px-2 py-1 text-xs text-indigo-500 hover:text-indigo-700">今天</button>
        <div className="w-px h-6 bg-slate-200 mx-1" />
        <Cascader label="品牌/仓库" options={cascaderOptions} selected={[...brandFilter, ...whFilter]} onChange={handleCascader} isOpen={cascaderOpen} onToggle={() => setCascaderOpen(p => !p)} />
        <SearchableSelect value={fCustomerId} onChange={setFCustomerId} options={Object.entries(enterprises ?? {}).map(([id, name]) => ({ id, name }))} className={`${INP} w-28 text-xs`} />
        <SearchableSelect value={fSupplierId} onChange={setFSupplierId} options={Object.entries(enterprises ?? {}).map(([id, name]) => ({ id, name }))} className={`${INP} w-28 text-xs`} />
        <SearchableSelect value={fPcId} onChange={setFPcId} options={allPcs ?? []} className={`${INP} w-28 text-xs`} />
        <SearchableSelect value={fScId} onChange={setFScId} options={allScs ?? []} className={`${INP} w-28 text-xs`} />
        <SearchableSelect value={fStatus} onChange={setFStatus} options={Object.entries(STATUS_MAP).map(([k, v]) => ({ id: k, name: v.label }))} className={`${INP} w-28 text-xs`} />
        {(brandFilter.length > 0 || whFilter.length > 0 || fCustomerId || fSupplierId || fPcId || fScId || fStatus) && (
          <button onClick={() => { setBrandFilter([]); setWhFilter([]); setFCustomerId(""); setFSupplierId(""); setFPcId(""); setFScId(""); setFStatus("") }}
            className="text-xs text-indigo-500 hover:text-indigo-700 px-2">清除</button>
        )}
        <span className="text-xs text-slate-400 ml-auto">{activePlans.length}进行中 · {donePlans.length}已完成</span>
      </div>

      {/* 看板 —— 左：每日计划(含已完成) | 右：货运明细 */}
      <DndContext sensors={sensors} collisionDetection={closestCorners} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          {/* 左侧：每日计划 */}
          <div className="flex-[2] overflow-y-auto p-2 sm:p-3 border-b lg:border-b-0 lg:border-r border-slate-200">
            <h3 className="text-sm font-semibold text-slate-600 mb-2 px-1">📋 每日计划</h3>
            <div className="flex flex-col gap-2">
              {weekDates.map(date => {
                const active = groupedActive[date] ?? []
                const done = groupedDone[date] ?? []
                if (active.length === 0 && done.length === 0) {
                  return <DateRow key={`day-${date}`} date={date} plans={[]}
                    brands={brands ?? {}} ents={enterprises ?? {}} models={models} whs={whNames}
                    isToday={date === today} isOverdue={date < today}
                    onPlanClick={setSelectedPlan} />
                }
                return (
                  <div key={`day-${date}`}>
                    <DateRow date={date} plans={active}
                      brands={brands ?? {}} ents={enterprises ?? {}} models={models} whs={whNames}
                      isToday={date === today} isOverdue={date < today}
                      onPlanClick={setSelectedPlan} />
                    {done.length > 0 && (
                      <div className="mt-1">
                        <div className="text-[10px] text-slate-400 mb-1">已完成</div>
                        {done.flatMap(plan => plan.items.map(item => (
                          <PlanItemBar key={item.id} item={item} plan={plan}
                            brandName={brands?.[plan.brand_id]?.name ?? "—"} brandColor={brands?.[plan.brand_id]?.color ?? "#6366f1"}
                            ents={enterprises ?? {}} models={models} whs={whNames}
                            onClick={() => setSelectedPlan(plan)} />
                        )))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
          {/* 右侧：货运明细 */}
          <div className="flex-1 overflow-y-auto p-2 sm:p-3 bg-slate-50/50">
            <h3 className="text-sm font-semibold text-slate-500 mb-2 px-1">🚚 货运明细</h3>
            <ShipmentList enterprises={enterprises ?? {}} />
          </div>
        </div>

        <DragOverlay>
          {activePlan ? (
            <div className="bg-white rounded-lg border-2 border-indigo-400 shadow-xl px-3 py-2 opacity-90">
              <span className="text-xs font-semibold text-slate-800">{brands?.[activePlan.brand_id]?.name ?? "—"}</span>
              <span className="text-xs text-slate-500 ml-2">{fmtQty(activePlan.total_planned_quantity)}吨</span>
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {selectedPlan && !showShipForm && (
        <PlanDetailDrawer plan={selectedPlan} brands={brands ?? {}} enterprises={enterprises ?? {}} pcs={pcs ?? {}} scs={scs ?? {}}
          models={models} whs={whNames}
          onClose={() => setSelectedPlan(null)} onShip={() => setShowShipForm(true)}
          onRefresh={() => qc.invalidateQueries({ queryKey: ["shipping-plans"] })} />
      )}

      {showShipForm && selectedPlan && (
        <ShipmentModal plan={selectedPlan} enterprises={enterprises ?? {}} whs={whNames} models={models} brands={brands ?? {}}
          onClose={() => { setShowShipForm(false); setSelectedPlan(null) }}
          onDone={() => { setShowShipForm(false); setSelectedPlan(null); qc.invalidateQueries({ queryKey: ["shipping-plans"] }) }} />
      )}
    </div>
  )
}


// ============================================================
// PlanDetailDrawer V3
// ============================================================
function PlanDetailDrawer({ plan, brands, enterprises, pcs, scs, models, whs, onClose, onShip, onRefresh }: {
  plan: Plan; brands: BrandInfo; enterprises: NameMap; pcs: NameMap; scs: NameMap; models: NameMap; whs: NameMap
  onClose: () => void; onShip: () => void; onRefresh: () => void
}) {
  const st = STATUS_MAP[plan.status] ?? { label: plan.status, dot: "bg-slate-400" }
  const [tab, setTab] = useState<"audit" | "detail" | "shipments">("detail")
  const [editMode, setEditMode] = useState(false)
  const [editDate, setEditDate] = useState(plan.planned_date)
  const [editDM, setEditDM] = useState(plan.delivery_method)
  const [editRemark, setEditRemark] = useState(plan.remark ?? "")
  const [editItems, setEditItems] = useState<Record<string, number>>(() => {
    const q: Record<string, number> = {}
    plan.items.forEach(it => { q[it.id] = it.planned_quantity })
    return q
  })
  const qc = useQueryClient()

  const cancelMut = useMutation({
    mutationFn: () => apiDelete(`/shipping/plans/${plan.id}`),
    onSuccess: () => { onClose(); onRefresh() },
  })

  /** 编辑保存 */
  const editMut = useMutation({
    mutationFn: async () => {
      const items = plan.items.map(it => ({
        id: it.id,
        planned_quantity: editItems[it.id] ?? it.planned_quantity,
      }))
      return apiPut(`/shipping/plans/${plan.id}`, {
        planned_date: editDate,
        delivery_method: editDM,
        remark: editRemark || null,
        items,
      })
    },
    onSuccess: () => { setEditMode(false); onRefresh(); },
    onError: (err: any) => sysToast("保存失败: " + (err.message || "")),
  })

  // 采购合同详情弹窗
  const [pcPopup, setPcPopup] = useState(false)
  const [pcDetail, setPcDetail] = useState<any>(null)
  const [pcLoading, setPcLoading] = useState(false)
  const openPcDetail = async () => {
    if (!plan.purchase_contract_id) return
    setPcPopup(true); setPcLoading(true)
    try {
      const d = await apiGet<any>(`/purchase-contracts/${plan.purchase_contract_id}`)
      setPcDetail(d)
    } catch { setPcDetail(null) }
    setPcLoading(false)
  }

  const pcNo = pcs[plan.purchase_contract_id] ?? (plan.purchase_contract_id ? plan.purchase_contract_id.slice(0, 8) : "—")

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-[560px] bg-white shadow-2xl h-full overflow-y-auto overflow-x-visible">
        <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-lg font-bold text-slate-800">计划详情</h2>
            <span className="text-xs text-slate-500">{pcNo}</span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl leading-none">&times;</button>
        </div>

        <div className="flex border-b border-slate-100 px-6">
          {(["detail", "shipments", "audit"] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 ${tab === t ? "border-indigo-500 text-indigo-700" : "border-transparent text-slate-500"}`}>
              {{ detail: "明细", shipments: "发货记录", audit: "操作记录" }[t]}
            </button>
          ))}
        </div>

        <div className="p-6">
          {tab === "detail" && (
            <div className="space-y-4">
              <div className="bg-indigo-50 rounded-xl p-4 flex items-center justify-between">
                <div>
                  <span className="text-xs text-indigo-400">计划发货日期</span>
                  {editMode ? (
                    <input type="date" value={editDate} onChange={e => setEditDate(e.target.value)}
                      className="text-xl font-bold text-indigo-700 bg-white border border-indigo-200 rounded-lg px-2 py-1 mt-1" />
                  ) : (
                    <div className="text-2xl font-bold text-indigo-700">{plan.planned_date}</div>
                  )}
                </div>
                <div className="text-right">
                  <span className="text-xs text-indigo-400">总计划量</span>
                  <div className="text-xl font-bold text-indigo-700">{fmtQty(plan.total_planned_quantity)}吨</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-slate-400 text-xs">品牌</span><div className="text-slate-800 font-medium">{brands[plan.brand_id]?.name ?? "—"}</div></div>
                <div>
                  <span className="text-slate-400 text-xs">配送方式</span>
                  {editMode ? (
                    <select value={editDM} onChange={e => setEditDM(e.target.value)}
                      className="text-slate-800 bg-white border border-slate-200 rounded px-2 py-1 text-sm mt-0.5 w-full">
                      <option value="SH">送货</option>
                      <option value="ZT">自提</option>
                    </select>
                  ) : (
                    <div className="text-slate-800">{DL_MAP[plan.delivery_method] ?? plan.delivery_method}</div>
                  )}
                </div>
                <div><span className="text-slate-400 text-xs">供方</span><div className="text-slate-800 text-xs">{enterprises[plan.supplier_enterprise_id] ?? "—"}</div></div>
                <div>
                  <span className="text-slate-400 text-xs">采购合同</span>
                  <div>
                    <button onClick={openPcDetail}
                      className="text-indigo-600 text-xs font-medium hover:text-indigo-800 hover:underline text-left truncate max-w-full">
                      {pcNo}
                    </button>
                  </div>
                </div>
              </div>
              <div>
                <span className="text-xs text-slate-400">备注</span>
                {editMode ? (
                  <input value={editRemark} onChange={e => setEditRemark(e.target.value)}
                    className="w-full text-sm text-slate-700 border border-slate-200 rounded px-2 py-1 mt-0.5" />
                ) : (
                  <div className="text-sm text-slate-500 mt-0.5">{plan.remark || ""}</div>
                )}
              </div>
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                <h4 className="text-sm font-semibold text-slate-800 mb-3">📋 计划明细</h4>
                <table className="w-full text-xs">
                  <thead><tr className="border-b border-slate-200 text-slate-500">
                    <th className="text-left py-2 font-semibold">客户</th><th className="text-left py-2 font-semibold">品牌</th><th className="text-left py-2 font-semibold">销售合同</th>
                    <th className="text-left py-2 font-semibold">仓库</th><th className="text-left py-2 font-semibold">型号</th>
                    <th className="text-right py-2 font-semibold">计划</th><th className="text-right py-2 font-semibold">已发</th><th className="text-right py-2 font-semibold">调货</th>
                  </tr></thead>
                  <tbody>
                    {plan.items.map(it => (
                      <tr key={it.id} className="border-b border-slate-100">
                        <td className="py-2 text-slate-800 font-medium">{enterprises[it.customer_enterprise_id] ?? "—"}</td>
                        <td className="py-2 text-slate-500 text-xs">{brands[plan.brand_id]?.name ?? "—"}</td>
                        <td className="py-2 text-slate-500 text-xs">{scs[it.sales_contract_id] ?? it.sales_contract_id.slice(0, 8)}</td>
                        <td className="py-2 text-slate-600">{whs[it.warehouse_id] ?? "—"}</td>
                        <td className="py-2 text-slate-600">{models[it.model_id] ?? "—"}</td>
                        <td className="py-2 text-right">
                          {editMode ? (
                            <input type="number" step="0.01" min={it.shipped_quantity} value={editItems[it.id] ?? it.planned_quantity}
                              onChange={e => setEditItems(p => ({ ...p, [it.id]: Number(e.target.value) }))}
                              className="w-20 text-right px-2 py-1 border border-slate-200 rounded text-xs" />
                          ) : (
                            <span className="font-semibold text-slate-800">{fmtQty(it.planned_quantity)}</span>
                          )}
                        </td>
                        <td className="py-2 text-right">{fmtQty(it.shipped_quantity)}</td>
                        <td className="py-2 text-right">
                          {it.surcharge_type === "carbonate_transfer" && <span className="text-purple-600">碳酸料</span>}
                          {it.surcharge_type === "brand_transfer" && <span className="text-orange-600">品牌调货</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {plan.status !== "cancelled" && plan.status !== "completed" && (
                <div className="flex gap-2 pt-2">
                  {editMode ? (
                    <>
                      <button onClick={() => editMut.mutate()} disabled={editMut.isPending}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm">
                        {editMut.isPending ? "保存中..." : "💾 保存"}
                      </button>
                      <button onClick={() => setEditMode(false)}
                        className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm">取消编辑</button>
                    </>
                  ) : (
                    <>
                      <button onClick={onShip} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm">🚚 发货</button>
                      <button onClick={() => { setEditMode(true); setEditDate(plan.planned_date); setEditDM(plan.delivery_method); setEditRemark(plan.remark ?? ""); const q: Record<string,number> = {}; plan.items.forEach(it => { q[it.id] = it.planned_quantity }); setEditItems(q) }}
                        className="px-4 py-2 border border-indigo-200 text-indigo-600 rounded-lg text-sm">✏️ 编辑</button>
                      <button onClick={async () => { if (sysConfirm("确认取消？")) cancelMut.mutate() }} className="px-4 py-2 border border-red-200 text-red-600 rounded-lg text-sm">取消</button>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
          {tab === "shipments" && <ShipmentHistory plan={plan} />}
          {tab === "audit" && (
            <AuditTimeline entityType="shipping_plan" entityId={plan.id} />
          )}
        </div>

        {/* 采购合同详情弹窗 */}
        {pcPopup && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center">
            <div className="absolute inset-0 bg-black/30" onClick={() => setPcPopup(false)} />
            <div className="relative bg-white rounded-2xl shadow-2xl w-[480px] max-h-[75vh] overflow-y-auto p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold text-slate-800">📄 采购合同</h3>
                <button onClick={() => setPcPopup(false)} className="text-slate-400 hover:text-slate-600 text-xl leading-none">&times;</button>
              </div>
              {pcLoading ? (
                <div className="text-slate-400 text-sm text-center py-8">加载中...</div>
              ) : pcDetail ? (
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between"><span className="text-slate-400">合同编号</span><span className="text-slate-800 font-semibold">{pcDetail.contract_no}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">供方</span><span className="text-slate-700">{enterprises[pcDetail.supplier_enterprise_id] ?? "—"}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">合同日期</span><span className="text-slate-700">{pcDetail.contract_date}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">履行期限</span><span className="text-slate-700">{pcDetail.contract_start_date} ~ {pcDetail.contract_end_date}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">状态</span><span className="text-slate-700">{STATUS_MAP[pcDetail.status]?.label ?? pcDetail.status}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">总数量</span><span className="text-slate-700 font-semibold">{fmtQty(pcDetail.total_quantity)}吨</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">总金额</span><span className="text-slate-700 font-semibold">¥{(pcDetail.total_amount ?? 0).toLocaleString()}</span></div>
                  {pcDetail.remark && <div className="pt-2 border-t border-slate-100"><span className="text-slate-400 text-xs">备注</span><div className="text-slate-500 mt-0.5">{pcDetail.remark}</div></div>}
                  {pcDetail.items?.length > 0 && (
                    <div className="pt-2 border-t border-slate-100">
                      <span className="text-slate-400 text-xs">合同明细</span>
                      <table className="w-full text-xs mt-1">
                        <thead><tr className="border-b border-slate-100 text-slate-400"><th className="text-left py-1">#</th><th className="text-left py-1">品牌</th><th className="text-left py-1">型号</th><th className="text-right py-1">数量</th><th className="text-right py-1">单价</th><th className="text-right py-1">金额</th></tr></thead>
                        <tbody>
                          {pcDetail.items.map((it: any) => (
                            <tr key={it.id} className="border-b border-slate-50">
                              <td className="py-1 text-slate-400">{it.line_no}</td>
                              <td className="py-1 text-slate-600">{brands[it.brand_id]?.name ?? it.brand_id?.slice(0, 8)}</td>
                              <td className="py-1 text-slate-600">{models[it.model_id] ?? it.model_id?.slice(0, 8)}</td>
                              <td className="py-1 text-right">{fmtQty(it.quantity)}</td>
                              <td className="py-1 text-right">¥{Number(it.purchase_price ?? 0).toFixed(2)}</td>
                              <td className="py-1 text-right">¥{Number(it.amount ?? 0).toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-slate-400 text-sm text-center py-8">加载失败</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


// ============================================================
// ShipmentHistory
// ============================================================
function ShipmentHistory({ plan }: { plan: Plan }) {
  const { data: shipments = [] } = useQuery({
    queryKey: ["shipments", plan.id],
    queryFn: async () => {
      try { const r = await apiGet<{ shipments: any[] }>(`/shipping/plans/${plan.id}`); return (r as any).shipments ?? [] } catch { return [] }
    },
  })
  return (
    <div className="space-y-3">
      {shipments.length === 0 && <div className="text-slate-400 text-sm text-center py-8">暂无发货记录</div>}
      {shipments.map((s: any) => (
        <div key={s.id} className="border border-slate-200 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-slate-700">{s.shipment_no}</span>
            <span className="text-xs text-slate-400">{s.shipped_date}</span>
          </div>
          <div className="text-xs text-slate-500 grid grid-cols-2 gap-1">
            <div>司机: {s.driver_name ?? "—"} {s.driver_phone ?? ""}</div>
            <div>车牌: {s.driver_license_plate ?? "—"}</div>
          </div>
          {s.freight_total && <div className="text-xs text-slate-500 mt-1">运费: ¥{Number(s.freight_total).toFixed(2)}</div>}
          <div className="text-xs text-slate-500 mt-1">{s.items?.map((si: any) => <span key={si.id} className="mr-3">{si.shipped_quantity}吨</span>)}</div>
        </div>
      ))}
    </div>
  )
}


// ============================================================
// ShipmentModal —— 按明细发货
// ============================================================
function ShipmentModal({ plan, enterprises, whs, models, brands, onClose, onDone }: {
  plan: Plan; enterprises: NameMap; whs: NameMap; models: NameMap; brands: BrandInfo; onClose: () => void; onDone: () => void
}) {
  const [shippedDate, setShippedDate] = useState(new Date().toISOString().slice(0, 10))
  const [driverName, setDriverName] = useState("")
  const [driverPhone, setDriverPhone] = useState("")
  const [driverPlate, setDriverPlate] = useState("")
  const [driverIdCard, setDriverIdCard] = useState("")
  const [freightTotal, setFreightTotal] = useState("")
  const [freightTaxRate, setFreightTaxRate] = useState("1.13")
  const [quickText, setQuickText] = useState("")

  /** 解析粘贴文本中的司机信息 */
  const parseQuickText = (text: string) => {
    setQuickText(text)
    // 先尝试带标签匹配
    const clean = (s: string) => s.replace(/[，,。、；;：:\s]+$/, "").trim()
    const plate = text.match(/(?:车牌|车号)[：:]\s*([^，,。、；;：:\s]+)/)
    const name = text.match(/(?:司机|姓名|名字)[：:]\s*([^，,。、；;：:\s]+)/)
    const idCard = text.match(/(?:身份证(?:号码)?|身份证号)[：:]\s*([^，,。、；;：:\s]+)/)
    const phone = text.match(/(?:电话(?:号码)?|手机(?:号码)?|手机号)[：:]\s*([^，,。、；;：:\s]+)/)

    if (plate || name || idCard || phone) {
      if (plate) setDriverPlate(clean(plate[1]))
      if (name) setDriverName(clean(name[1]))
      if (idCard) setDriverIdCard(clean(idCard[1]))
      if (phone) setDriverPhone(clean(phone[1]))
      return
    }

    // 按行或连续字符串中提取
    let t = text.replace(/[\n\r]+/g, " ").trim()
    if (!t) return
    // 车牌
    const p = t.match(/[一-龥]{1}[A-Z][A-Z0-9]{4,7}/)
    if (p) { setDriverPlate(p[0]); t = t.replace(p[0], "") }
    // 身份证
    const i = t.match(/\d{17}[\dXx]/)
    if (i) { setDriverIdCard(i[0]); t = t.replace(i[0], "") }
    // 手机号
    const ph = t.match(/1\d{10}/)
    if (ph) { setDriverPhone(ph[0]); t = t.replace(ph[0], "") }
    // 姓名（剩下的连续汉字中去掉已匹配的车牌首字）
    const remaining = t.replace(/[A-Z0-9\s]/gi, "")
    const n = remaining.match(/[一-龥]{2,4}/)
    if (n) setDriverName(n[0])
  }
  const [remark, setRemark] = useState("")
  const [quantities, setQuantities] = useState<Record<string, number>>(() => {
    const q: Record<string, number> = {}
    plan.items.forEach(it => { q[it.id] = it.planned_quantity - it.shipped_quantity })
    return q
  })
  // 编辑计划明细：仓库、型号、计划数量
  const [editPlanned, setEditPlanned] = useState<Record<string, number>>(() => {
    const q: Record<string, number> = {}
    plan.items.forEach(it => { q[it.id] = it.planned_quantity })
    return q
  })
  const [editWarehouse, setEditWarehouse] = useState<Record<string, string>>(() => {
    const q: Record<string, string> = {}
    plan.items.forEach(it => { q[it.id] = it.warehouse_id })
    return q
  })
  const [editModel, setEditModel] = useState<Record<string, string>>(() => {
    const q: Record<string, string> = {}
    plan.items.forEach(it => { q[it.id] = it.model_id })
    return q
  })

  const totalQty = Object.values(quantities).reduce((s, v) => s + (v || 0), 0)
  const freightUnitPrice = (() => {
    if (!(totalQty > 0 && freightTotal)) return "0"
    const base = Number(freightTotal) / totalQty
    return freightTaxRate ? (base * Number(freightTaxRate)).toFixed(2) : base.toFixed(2)
  })()

  const shipMut = useMutation({
    mutationFn: async () => {
      const items = Object.entries(quantities).filter(([, qty]) => qty > 0)
        .map(([plan_item_id, shipped_quantity]) => ({ plan_item_id, shipped_quantity, unit: "吨" }))
      if (items.length === 0) throw new Error("请至少输入一条发货数量")

      // 同步更新计划明细（仓库、型号、计划数量）
      const planItems = plan.items.map(it => ({
        id: it.id,
        planned_quantity: editPlanned[it.id] ?? it.planned_quantity,
        warehouse_id: editWarehouse[it.id] ?? it.warehouse_id,
        model_id: editModel[it.id] ?? it.model_id,
      }))
      const changed = planItems.some(it => {
        const orig = plan.items.find(o => o.id === it.id)
        return orig && (it.planned_quantity !== orig.planned_quantity || it.warehouse_id !== orig.warehouse_id || it.model_id !== orig.model_id)
      })
      if (changed) {
        await apiPut(`/shipping/plans/${plan.id}`, { items: planItems })
      }

      return apiPost(`/shipping/plans/${plan.id}/shipments`, {
        shipped_date: shippedDate, driver_name: driverName || null, driver_phone: driverPhone || null,
        driver_license_plate: driverPlate || null, driver_id_card: driverIdCard || null,
        freight_total: freightTotal ? Number(freightTotal) : null,
        freight_tax_rate: freightTaxRate ? Number(freightTaxRate) : null,
        remark: remark || null, items,
      })
    },
    onSuccess: () => { onDone(); sysToast("发货成功") },
    onError: (err: any) => sysToast("发货失败: " + (err.message || "")),
  })

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[5vh] overflow-y-auto">
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-[700px] p-6 mb-8" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-bold text-slate-800 mb-4">🚚 发货 · {plan.planned_date}</h3>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-slate-500 mb-1 block">发货日期</label>
            <input type="date" value={shippedDate} onChange={e => setShippedDate(e.target.value)} className={`${INP} w-full`} />
          </div>
          <div><label className="text-xs text-slate-500 mb-1 block">发货明细</label>
            <table className="w-full text-xs"><thead><tr className="border-b border-slate-100 text-slate-400">
              <th className="text-left py-1.5">#</th><th className="text-left py-1.5">客户</th><th className="text-left py-1.5">品牌</th>
              <th className="text-left py-1.5">仓库</th><th className="text-left py-1.5">型号</th><th className="text-right py-1.5">计划</th><th className="text-right py-1.5">已发</th>
              <th className="text-right py-1.5">可发</th><th className="text-right py-1.5">本次</th>
            </tr></thead><tbody>
              {plan.items.map(it => {
                const avail = it.planned_quantity - it.shipped_quantity
                const brandWhs = brands[plan.brand_id]?.warehouses ?? []
                const brandMdls = brands[plan.brand_id]?.models ?? []
                return (
                  <tr key={it.id} className="border-b border-slate-50">
                    <td className="py-1.5 text-slate-500">{it.line_no}</td>
                    <td className="py-1.5 text-slate-700 text-xs">{enterprises[it.customer_enterprise_id] ?? "—"}</td>
                    <td className="py-1.5 text-slate-500 text-[10px]">{brands[plan.brand_id]?.name ?? "—"}</td>
                    <td className="py-1">
                      <Dropdown value={editWarehouse[it.id] ?? it.warehouse_id} onChange={v => setEditWarehouse(p => ({ ...p, [it.id]: v }))}
                        options={brandWhs.map(w => ({ id: w.id, name: w.name }))} />
                    </td>
                    <td className="py-1">
                      <Dropdown value={editModel[it.id] ?? it.model_id} onChange={v => setEditModel(p => ({ ...p, [it.id]: v }))}
                        options={brandMdls.map(m => ({ id: m.id, name: m.model_name }))} />
                    </td>
                    <td className="py-1">
                      <input type="number" step="0.01" min={it.shipped_quantity} value={editPlanned[it.id] ?? it.planned_quantity}
                        onChange={e => setEditPlanned(p => ({ ...p, [it.id]: Number(e.target.value) }))}
                        className="w-16 text-right text-[10px] border border-slate-200 rounded px-1 py-0.5" />
                    </td>
                    <td className="py-1.5 text-right text-slate-400">{fmtQty(it.shipped_quantity)}</td>
                    <td className="py-1.5 text-right text-slate-500">{fmtQty(avail)}</td>
                    <td className="py-1.5 text-right">
                      <input type="number" step="0.01" min="0" max={avail} value={quantities[it.id] ?? 0}
                        onChange={e => setQuantities(p => ({ ...p, [it.id]: Number(e.target.value) }))}
                        className="w-20 text-right px-2 py-1 border border-slate-200 rounded text-xs" />
                    </td>
                  </tr>
                )
              })}
            </tbody></table>
          </div>
          <div><label className="text-xs text-slate-500 mb-1 block">快速识别</label>
            <textarea value={quickText} onChange={e => parseQuickText(e.target.value)}
              placeholder="粘贴司机信息，自动识别填充&#10;如：车牌：桂AAD229&#10;司机：覃新东&#10;身份证号码：452623197809150033&#10;电话号码：15778083523"
              rows={4} className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-400 focus:bg-white resize-none" />
          </div>
          <div><label className="text-xs text-slate-500 mb-1 block">司机信息</label>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-[10px] text-slate-400 mb-0.5 block">司机姓名</label><input value={driverName} onChange={e => setDriverName(e.target.value)} className={INP} /></div>
              <div><label className="text-[10px] text-slate-400 mb-0.5 block">电话号码</label><input value={driverPhone} onChange={e => setDriverPhone(e.target.value)} className={INP} /></div>
              <div><label className="text-[10px] text-slate-400 mb-0.5 block">车牌号</label><input value={driverPlate} onChange={e => setDriverPlate(e.target.value)} className={INP} /></div>
              <div><label className="text-[10px] text-slate-400 mb-0.5 block">身份证号</label><input value={driverIdCard} onChange={e => setDriverIdCard(e.target.value)} className={INP} /></div>
            </div>
          </div>
          <div><label className="text-xs text-slate-500 mb-1 block">运费</label>
            <div className="grid grid-cols-3 gap-2">
              <div><label className="text-[10px] text-slate-400 mb-0.5 block">运费总额</label><input type="number" step="0.01" value={freightTotal} onChange={e => setFreightTotal(e.target.value)} className={INP} /></div>
              <div><label className="text-[10px] text-slate-400 mb-0.5 block">税率</label><input type="number" step="0.01" value={freightTaxRate} onChange={e => setFreightTaxRate(e.target.value)} className="w-20 px-2 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20" /></div>
              <div className="flex items-end pb-2 text-sm text-slate-500">单价 ¥{freightUnitPrice}/吨</div>
            </div>
          </div>
          <div><label className="text-xs text-slate-500 mb-1 block">备注</label>
            <textarea value={remark} onChange={e => setRemark(e.target.value)} rows={3} className={`${INP} w-full resize-none`} />
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={onClose} className="flex-1 px-4 py-2.5 border border-slate-200 text-slate-600 rounded-xl text-sm">取消</button>
            <button onClick={() => shipMut.mutate()} disabled={shipMut.isPending}
              className="flex-1 px-4 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium disabled:opacity-50">
              {shipMut.isPending ? "提交中..." : `确认发货 · ${fmtQty(totalQty)}吨`}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

/** 右侧面板 —— 货运明细，按日期分组 */
function ShipmentList({ enterprises }: { enterprises: NameMap }) {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ["recent-shipments"],
    queryFn: async () => {
      const r = await apiGet<{ items: any[] }>("/shipping/shipments?page_size=100")
      return r.items ?? []
    },
    refetchInterval: 30000,
  })

  const entName = (id: string) => enterprises[id] ?? id.slice(0, 8)

  /** 按日期分组 */
  const grouped = useMemo(() => {
    if (!data) return {}
    const g: Record<string, any[]> = {}
    for (const s of data) {
      const d = s.shipped_date || "未知"
      if (!g[d]) g[d] = []
      g[d].push(s)
    }
    return g
  }, [data])

  if (isLoading) return <div className="text-xs text-slate-400 p-4">加载中...</div>
  if (!data || data.length === 0) return <div className="text-xs text-slate-400 p-4">暂无发货记录</div>

  const dates = Object.keys(grouped).sort((a, b) => b.localeCompare(a))

  return (
    <div className="flex flex-col gap-3">
      {dates.map(date => (
        <div key={date}>
          <div className="text-[10px] font-semibold text-slate-400 mb-1.5 px-1">{date}</div>
          <div className="space-y-1">
            {grouped[date].map((s: any) => (
              <div key={s.id} className="bg-white rounded-lg border border-slate-100 px-3 py-2 text-xs hover:shadow-sm transition-shadow">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-semibold text-slate-700">{s.shipment_no}</span>
                  <span className="text-slate-400">{s.shipped_date}</span>
                </div>
                {/* 客户 + 发货信息 */}
                <div className="grid grid-cols-2 gap-1 text-[11px]">
                  <div><span className="text-slate-400">吨数</span> <span className="text-slate-800 font-semibold">{s.items?.reduce((sum: number, i: any) => sum + (i.shipped_quantity || 0), 0).toFixed(2)}吨</span></div>
                  {s.plan && <div><span className="text-slate-400">方式</span> <span className="text-slate-600">{s.plan.delivery_method === "ZT" ? "自提" : "送货"}</span></div>}
                  {/* 客户名称 */}
                  {s.items?.[0]?.customer_enterprise_id && (
                    <div className="col-span-2"><span className="text-slate-400">客户</span> <span className="text-slate-800 font-medium">{entName(s.items[0].customer_enterprise_id)}</span></div>
                  )}
                  {/* 司机信息 */}
                  {(s.driver_name || s.driver_license_plate) && (
                    <div className="col-span-2 pt-1 border-t border-slate-50">
                      <span className="text-slate-400">司机</span>{" "}
                      <span className="text-slate-600">{[s.driver_name, s.driver_phone, s.driver_license_plate].filter(Boolean).join(" · ")}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
