/** 轻量 SVG 图标组件 —— 基于 Lucide Icon path（MIT） */

interface IconProps {
  name: string
  className?: string
  size?: number
}

/** Lucide SVG 路径数据 —— 仅包含 ERP Portal 所需图标 */
const ICON_SVG_PATHS: Record<string, string[]> = {
  // 导航
  Folder: ["M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"],
  FileText: ["M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z", "M14 2v4a2 2 0 0 0 2 2h4", "M10 9H8", "M16 13H8", "M16 17H8"],

  // 模块图标
  Users: ["M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", "M22 21v-2a4 4 0 0 0-3-3.87", "M16 3.13a4 4 0 0 1 0 7.75", "M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z"],
  Database: ["M12 3c4.97 0 9 1.51 9 4.5S16.97 12 12 12s-9-2.03-9-4.5S7.03 3 12 3Z", "M21 7.5v3", "M3 7.5v3", "M12 12v3", "M21 10.5v3c0 3-4.03 4.5-9 4.5S3 16.47 3 13.5V12"],
  Package: ["M12.89 1.45l8 4A2 2 0 0 1 22 7.24v9.53a2 2 0 0 1-1.11 1.79l-8 4a2 2 0 0 1-1.79 0l-8-4a2 2 0 0 1-1.1-1.8V7.24a2 2 0 0 1 1.11-1.79l8-4a2 2 0 0 1 1.78 0Z", "M2.32 6.16L12 11l9.68-4.84", "M12 22.76V11"],
  ShoppingCart: ["M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6", "M7 21a1 1 0 1 0 2 0 1 1 0 1 0-2 0", "M19 21a1 1 0 1 0 2 0 1 1 0 1 0-2 0"],
  Receipt: ["M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z", "M16 8H8", "M12 12H8"],
  Truck: ["M1 3h15v13H1z", "M16 8h4l3 3v5h-7V8z", "M5.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z", "M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z"],
  Bot: ["M12 8V4H8", "M12 2v2", "M2 14c0 2.8 2.2 5 5 5h10c2.8 0 5-2.2 5-5v-3.5A2.5 2.5 0 0 0 19.5 8h-15A2.5 2.5 0 0 0 2 10.5V14Z", "M2 14c0 2.8 2.2 5 5 5h10", "M9 18v4", "M15 18v4"],

  // Dashboard
  LayoutDashboard: ["M3 3h7v9H3z", "M14 3h7v5h-7z", "M14 12h7v9h-7z", "M3 16h7v5H3z"],
  Home: ["M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z", "M9 22V12h6v10"],

  // UI 操作
  ChevronDown: ["m6 9 6 6 6-6"],
  ChevronRight: ["m9 18 6-6-6-6"],
  Bell: ["M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9", "M10.3 21a1.94 1.94 0 0 0 3.4 0"],
  User: ["M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2", "M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z"],
  LogOut: ["M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4", "M16 17l5-5-5-5", "M21 12H9"],
  Menu: ["M4 12h16", "M4 6h16", "M4 18h16"],
  X: ["M18 6 6 18", "M6 6l12 12"],
  Plus: ["M5 12h14", "M12 5v14"],
  Clipboard: ["M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2", "M15 2H9a1 1 0 0 0-1 1v2a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1Z"],
  Activity: ["M22 12h-4l-3 9L9 3l-3 9H2"],
  Settings: ["M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2Z", "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"],
  AlertCircle: ["M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z", "M12 8v4", "M12 16h.01"],
}

export function Icon({ name, className = "", size = 16 }: IconProps) {
  const paths = ICON_SVG_PATHS[name]
  if (!paths) return null

  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths.map((d, i) => (
        <path key={i} d={d} />
      ))}
    </svg>
  )
}
