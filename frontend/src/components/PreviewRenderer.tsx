import { useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { apiGet } from "../api/client"
import { ListPage } from "./ListPage"
import type { PageSchema } from "../api/ui"

export function PreviewRenderer() {
  const { sandboxId } = useParams<{ sandboxId: string }>()

  const { data: schema } = useQuery({
    queryKey: ["preview-schema", sandboxId],
    queryFn: () => apiGet<{ pages: PageSchema[]; module_display: string }>(`/ui/preview/${sandboxId}/:module/schema`),
    enabled: !!sandboxId,
  })

  if (!schema) return <div className="p-6 text-slate-500">加载预览...</div>

  return (
    <div className="p-6">
      <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 mb-4 text-sm text-amber-800">
        Sandbox 预览模式 —— {schema.module_display}
      </div>
      <div className="space-y-6">
        {schema.pages.map((page: PageSchema, i: number) => {
          if (page.page_type === "list") return <ListPage key={i} page={page} />
          return null
        })}
      </div>
    </div>
  )
}
