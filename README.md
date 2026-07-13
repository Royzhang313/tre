# ERP Builder

现代化、独立的 AI 驱动 ERP 系统。

## 特性

- 🏗️ **DDD Lite + Vertical Slice**: 模块独立，清晰的分层架构
- 🔄 **Event Bus**: 跨模块异步事件驱动，松耦合通信
- 📋 **Workflow Engine**: 可编程工作流引擎，状态转换与历史追踪
- 📊 **AG Grid**: 企业级数据表格，高性能大数据渲染
- 🎨 **shadcn/ui**: 现代可定制 UI 组件
- ⚡ **全栈 TypeScript + Python**: 前端 React 19 + 后端 FastAPI

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI (Python 3.12+) |
| **ORM** | SQLAlchemy 2.x (async) |
| **数据库** | PostgreSQL 16 |
| **迁移工具** | Alembic |
| **数据校验** | Pydantic v2 |
| **包管理** | uv |
| **前端框架** | React 19 + TypeScript |
| **路由** | TanStack Router |
| **数据请求** | TanStack Query |
| **样式** | TailwindCSS |
| **UI 组件** | shadcn/ui |
| **表格** | AG Grid Community |
| **构建工具** | Vite |
| **容器化** | Docker + Docker Compose |

## 快速开始

### 环境要求

- Python 3.12+
- PostgreSQL 16+
- Node.js 20+
- uv (Python 包管理器)

### 安装

```bash
# 安装后端依赖
cd backend && uv sync --dev

# 安装前端依赖
cd frontend && npm install
```

### 配置

```bash
# 从模板创建环境变量文件
cp .env.example .env
# 编辑 .env，填入数据库连接信息
```

### 运行

```bash
# 启动 PostgreSQL
docker compose up -d postgres

# 启动后端（backend/ 目录下）
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端（frontend/ 目录下，另一个终端）
cd frontend && npm run dev
```

访问 http://localhost:8000/docs 查看 API 文档（Swagger UI）。

访问 http://localhost:5173 打开前端页面。

## 项目结构

参见 [CLAUDE.md](CLAUDE.md) 了解详细架构和开发规范。
