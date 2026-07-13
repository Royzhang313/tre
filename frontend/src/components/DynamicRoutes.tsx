import { useMemo } from "react"
import { Route } from "react-router-dom"
import { useMenu } from "../api/ui"
import { PageRenderer } from "./PageRenderer"

export function useDynamicRoutes() {
  const { data: menu } = useMenu()

  return useMemo(() => {
    const routes: { path: string; element: JSX.Element }[] = []
    const seen = new Set<string>()

    for (const item of menu ?? []) {
      for (const child of item.children ?? []) {
        if (child.route && child.route.startsWith("/")) {
          const segments = child.route.split("/")
          const module = segments[1] || ""

          // 基于 route 的 page_type 推断（来自菜单无此信息，简单后缀判断）
          const isDetail = segments.includes("detail")
          const routePattern = isDetail ? `${child.route}/:id` : child.route

          if (!seen.has(routePattern)) {
            seen.add(routePattern)
            routes.push({
              path: routePattern,
              element: <PageRenderer module={module} />,
            })
          }
        }
      }
    }
    return routes
  }, [menu])
}
