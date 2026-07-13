# Technical Decisions

## 2026-07-07: ERP Builder 独立核心架构

**决策**: ERP Builder 不依赖 NocoBase 作为核心 Runtime。

NocoBase 可以作为：
- 原型验证工具
- 外部集成平台
- 辅助管理后台

但业务模型、权限、流程由 ERP Builder 自己实现。

**原因**: 保证 ERP Builder 长期可控。

**影响**:
- 删除 `plugins/` 目录
- 前端从 Vue 3 切换为 React 19
- 不再维护 NocoBase 兼容代码

## 2026-07-07: 技术栈终选

**Backend**: Python 3.12+ / FastAPI / SQLAlchemy 2.x / Alembic / Pydantic v2 / uv
**Frontend**: React 19 / Vite / TypeScript / TanStack Router / TanStack Query / TailwindCSS / shadcn/ui / AG Grid
**Infra**: Docker + Docker Compose / PostgreSQL 16

## 2026-07-07: 架构原则冻结（9 条）

1. Vertical Slice 模块结构
2. EventBus 跨模块解耦
3. Repository 不互相依赖
4. BaseData 纯 Master Data
5. Business Partner 拆表
6. Brand 独立模块
7. Auth RBAC
8. BaseData 无 Workflow
9. 逐模块交付

## 2026-07-07: Shared Layer 设计

- Workflow / Audit / Attachment / SerialNumber 使用 `typing.Protocol` 定义接口
- 具体实现在业务模块中通过依赖注入接入
- Workflow Definition 代码注册，不存数据库

## 2026-07-07: 文档体系建立

CLAUDE.md 分为 5 层 + docs/ 目录：
- CLAUDE.md: 项目身份 / 当前状态 / 架构规则 / 开发规范 / 技术架构 / 命令
- docs/ARCHITECTURE.md: 详细架构说明
- docs/PROJECT_STATUS.md: 进度追踪
- docs/TODO.md: 待办清单
- docs/DECISIONS.md: 决策记录

## 2026-07-07: AI Builder 生成原则

**核心能力**: 用户描述业务需求 → AI 自动生成完整模块。

**生成物**（按顺序）:
1. Domain Model
2. Database Schema
3. API
4. UI Schema
5. Menu
6. Permission
7. Workflow

**生成流程**:
```
业务分析 → 领域模型 → 数据模型 → API → UI → 权限 → 测试
```

**禁止**: 直接根据一句需求生成大量代码。必须先分析、建模，再逐层生成。
