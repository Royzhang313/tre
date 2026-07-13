import { useLocation } from "react-router-dom"
import { useModuleSchema } from "../api/ui"
import { ListPage } from "./ListPage"
import { FormPage } from "./FormPage"
import { DetailPage } from "./DetailPage"
import { DashboardPage } from "./DashboardPage"

/** 根据当前路由匹配对应的 PageSchema 并渲染 */
export function PageRenderer({ module }: { module?: string }) {
  const location = useLocation()
  const { data: schema, isLoading } = useModuleSchema(module ?? null)

  if (isLoading) return <div className="p-6 text-slate-500">加载中...</div>
  if (!schema) return <div className="p-6 text-red-500">模块 "{module}" 不存在</div>

  // 根据当前路径匹配页面 schema
  const currentPage = schema.pages.find(p => {
    // 去掉 :id 后缀做前缀匹配
    const routeBase = p.route.replace(/\/:id\??$/, "")
    return location.pathname.startsWith(routeBase)
  })

  if (!currentPage) {
    // 如果找不到匹配的 route，渲染所有页面（兼容旧行为）
    return (
      <div className="p-6">
        <h1 className="text-xl font-bold text-slate-800 mb-4">{schema.module_display}</h1>
        <div className="space-y-6">
          {schema.pages.map((page, i) => {
            if (page.page_type === "dashboard") return <DashboardPage key={i} page={page} />
            if (page.page_type === "list") return <ListPage key={i} page={page} />
            if (page.page_type === "form") return <FormPage key={i} page={page} />
            if (page.page_type === "detail") return <DetailPage key={i} page={page} />
            return null
          })}
        </div>
      </div>
    )
  }

  // 渲染匹配的单页面
  return (
    <div className="p-6">
      {currentPage.page_type === "dashboard" && <DashboardPage page={currentPage} />}
      {currentPage.page_type === "list" && <ListPage page={currentPage} />}
      {currentPage.page_type === "form" && <FormPage page={currentPage} />}
      {currentPage.page_type === "detail" && <DetailPage page={currentPage} />}
    </div>
  )
}
