# 项目说明

## 1. 项目身份

**ERP Builder V18** —— AI 驱动的企业管理系统生成平台。

通过自然语言描述，自动生成：
- 数据模型（SQLAlchemy + Alembic）
- CRUD API（FastAPI）
- 页面 UI（React 19 + shadcn/ui）
- 菜单配置
- 权限配置（RBAC）

---

## 2. 当前状态（AI Context）

### 当前任务

V18 自动 UI + 菜单 + 表生成

### 开发阶段

| 阶段 | 状态 |
|------|------|
| M0 Project Skeleton | ✅ 完成 |
| M1 Shared Kernel | ✅ 完成 |
| M2 Auth / BaseData / Brand | ✅ 完成 |
| M3 Purchase / Inventory | ✅ 完成 |
| M4 Sales / Shipping | ✅ 完成 |
| M5 Finance | 🔄 设计中 |

### 已完成

- Python Agent 基础框架
- FastAPI Backend 骨架
- DDD Lite + Vertical Slice 目录结构
- EventBus 基础
- Shared Kernel（BaseModel, BaseRepository, BaseService, Workflow/Audit/Attachment 接口）
- React 19 前端骨架（TanStack Router + TanStack Query + TailwindCSS + shadcn/ui + AG Grid）
- 采购合同 / 销售合同 / 发货 / 执行计划 / 基础资料 / 品牌管理

### 待完成

- M5: Finance（AR/AP 台账 + 收付款 + 票据）
- M6: Settlement + Logistics
- M7: 报表

---

## 3. 架构规则（稳定）

### 核心原则

- **DDD Lite + Vertical Slice**: 每个业务模块独立目录，包含 models / schemas / repository / service / router / events
- **Event Bus**: 跨模块通信必须通过事件总线，禁止模块间直接调用 Service
- **Shared Kernel**: 共享基础类（BaseModel, BaseRepository, Workflow/Audit/Attachment Protocol 等）放在 `app/shared/`
- **Business Partner**: 联系人、地址、银行等拆分独立表

### 模块结构（Vertical Slice）

```
modules/finance/
├── models.py
├── schemas.py
├── repository.py
├── service.py
├── router.py
└── events.py
```

### 模块间通信

```
Module A → EventBus → Module B   ✅
Module A → Module B.Service      ❌
```

---

## 4. 开发规范（稳定）

- 所有回复和交互使用**中文**
- 所有代码注释使用**中文**
- 严格遵循 **SOLID** 原则
- 优先使用异步（`async/await`）
- 所有结构变更必须通过 **Alembic** 迁移
- 每个文件写完立即 mypy 类型检查
- 禁止大范围重构、一次开发多个模块、为未来需求提前实现功能（YAGNI）

### 技术架构

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.x async, Alembic, Pydantic v2, uv
- **Frontend**: React 19, TypeScript, Vite, TanStack Router, TanStack Query, TailwindCSS, shadcn/ui
- **Database**: PostgreSQL 16+, SQLite (dev)
- **Infrastructure**: Docker + Docker Compose

### 项目结构

```
erp-builder/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/         # config, database, events, exceptions, di
│   │   ├── shared/       # base_model, base_repository, base_schema, workflow, audit, attachment, serial_number
│   │   ├── modules/      # Vertical Slices
│   │   ├── api/v1/       # 路由聚合
│   │   └── migrations/   # Alembic
│   └── tests/
├── frontend/
│   └── src/
│       ├── features/     # 功能模块
│       ├── components/   # ui/ + shared/
│       ├── routes/       # TanStack Router
│       ├── api/          # API client
│       └── lib/          # utils
├── docs/
├── docker-compose.yml
└── .env.example
```
