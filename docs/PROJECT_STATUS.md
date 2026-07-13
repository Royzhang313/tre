# Project Status

## 当前版本: V18 M2 (部分 M3/M4 提前完成)

## 开发进度

| 阶段 | 状态 | 内容 |
|------|------|------|
| M0 | ✅ 完成 | Project Skeleton —— backend/ + frontend/ 骨架 |
| M1 | ✅ 完成 | Shared Kernel —— BaseModel, Repository, Schema, Workflow/Audit/Attachment/SerialNumber 接口 |
| M2 | ✅ 完成 | Auth (RBAC) → BaseData (Enterprise/Company/Warehouse) → Brand |
| M3 | ✅ 提前完成 | Purchase Contract（采购合同台账）→ Inventory ⬜ 待开始 |
| M4 | 🔄 部分完成 | Sales Contract（销售合同台账）已完成 → Template / Document ⬜ 待开始 |
| M5 | ⬜ 待开始 | Execution Plan / Shipment / Workflow Engine |
| M6 | ⬜ 待开始 | Finance |
| M7 | ⬜ 待开始 | Settlement / Logistics |

## M0 交付物

- FastAPI 入口 + 生命周期管理
- 配置层（Pydantic Settings）
- 数据库层（Async Engine + Session）
- DDD 目录结构（core/ shared/ common/ modules/ api/）
- 领域异常体系（6 种异常）
- EventBus（内存异步）
- DI 容器（轻量）
- Alembic 异步迁移配置
- React 19 前端骨架（Vite + TanStack Router/Query + TailwindCSS + shadcn/ui + AG Grid）
- Docker Compose（PostgreSQL 16）

## M1 交付物

- BaseModel: +SoftDeleteMixin +VersionMixin
- BaseRepository: +filters +get_by_id_or_raise +exists
- BaseSchema: +FilterSchema +SortSchema
- Workflow: WorkflowState / Transition / Definition + Registry Protocol + Exceptions
- Audit: AuditOperator(+trace_id) + AuditLogWriter Protocol
- Attachment: AttachmentMeta(+storage_provider/storage_key) + AttachmentStorage Protocol
- SerialNumber: SerialNumberGenerator Protocol
- 测试: 59 条全部通过

## M2 交付物

### Auth 模块（RBAC）
- User/Role/Permission ORM 模型 + CRUD API
- 登录（用户名/手机号 + bcrypt + JWT）
- 角色-权限分配（替换式）
- 用户-角色分配（替换式，支持创建时分配）
- Dev 模式鉴权绕过（admin + "*" 通配符权限）
- 前端：登录页 / 用户管理 / 角色管理（含权限配置）/ 权限列表
- AuthGuard 权限守卫 + TopBar 权限过滤菜单

### BaseData 模块
- Enterprise（企业）CRUD + 软删除 + 联系人
- Company（执行主体公司）CRUD + 软删除
- Warehouse（仓库）CRUD + 软删除
- 前端：EnterpriseList / CompanyList / WarehouseList（行点击详情弹窗）

### Brand 模块
- Brand（品牌）/ BrandModel（型号）/ BrandWarehouse（品牌仓库） CRUD
- 前端：BrandManage（品牌管理页）

### Recycle Bin（回收站）
- 通用回收站：聚合所有模块已删除记录
- 恢复 / 永久删除
- 前端：RecycleBin 页面

### Audit（审计日志）
- 审计记录 API（按目标实体查询）
- 前端：AuditTimeline 共享组件（详情页底部时间线）

### 基础设施
- `_auto_migrate()` 启动时自动添加缺失列（SQLite 开发用）
- `--reload` 热重载
- 全局空值显示空白（非 "—"）

## M3/M4 提前交付物

### Purchase Contract（采购合同）
- 采购合同主表 + 明细表（品牌/型号/发货仓库）
- 合同编号自动生成 + 状态机（待执行/执行中/已完成/已作废）
- 前端：台账 / 表单 / 详情 / 预览弹窗（含作废按钮）

### Sales Contract（销售合同）
- 从采购合同镜像，术语调整（供方→客户、发货→提货、付款→回款）
- 合同类型：送货(SH) / 自提(ZT) / 还货(HH)
- 销售人员引用 + 合同编号自动生成
- 前端：台账 / 表单 / 详情 / 预览弹窗（含作废按钮）

## 测试
- 161 条全部通过（mypy ✅ / tsc ✅）
