import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    allowedHosts: ["6798285oupm1.vicp.fun", ".vicp.fun"],
    // API 代理 —— 增加超时防止后端慢响应导致断开
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        timeout: 120000,           // 代理请求超时 60s（OCR 需要较长时间）
      },
      "/uploads": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        timeout: 120000,
      },
    },
    // HMR WebSocket —— 添加超时和重连配置
    hmr: {
      overlay: false,
      timeout: 120000,             // WebSocket 超时 30s 后触发重连
    },
    // 文件监听 —— 使用轮询作为后备，避免 inotify 不可用时 HMR 失效
    watch: {
      usePolling: false,           // 默认不用轮询；如果 HMR 不生效可改为 true
      interval: 1000,              // 轮询间隔 1s（仅 usePolling=true 时生效）
    },
  },
})
