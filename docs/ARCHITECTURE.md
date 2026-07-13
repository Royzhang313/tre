# Architecture

## 架构风格

**DDD Lite + Vertical Slice Architecture**

每个业务模块是独立的 Vertical Slice，包含完整的 models / schemas / repository / service / router / events。模块之间通过 EventBus 通信，不直接调用对方的 Service。

## 模块结构

```
modules/{module}/
├── __init__.py
├── models.py          # SQLAlchemy ORM 模型
├── schemas.py         # Pydantic 请求/响应
├── repository.py      # 数据访问层
├── service.py         # 业务逻辑层
├── router.py          # FastAPI 路由
└── events.py          # 领域事件定义和处理器
```

## 跨模块通信

```
Module A ──publish──→ EventBus ──handle──→ Module B   ✅
Module A ──call──→ Module B.Service                     ❌
```

## 分层职责

| 层 | 职责 | 依赖方向 |
|------|------|---------|
| `router.py` | HTTP 端点，参数校验 | → Service |
| `service.py` | 业务逻辑编排 | → Repository, EventBus |
| `repository.py` | 数据访问，只操作自己的 Aggregate | → Model |
| `models.py` | ORM 实体定义 | → BaseModel |
| `schemas.py` | API Schema | 无 |
| `events.py` | 本模块发布/订阅的领域事件 | → DomainEvent |

## Shared Kernel

`app/shared/` 提供所有模块共享的基础能力：

- `base_model.py` — UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin, VersionMixin, BaseModel
- `base_repository.py` — 泛型 CRUD 仓储
- `base_schema.py` — APIResponse, PageRequest/Response, FilterSchema, SortSchema
- `base_service.py` — 服务基类
- `pagination.py` — 分页工具
- `workflow/` — WorkflowState, WorkflowTransition, WorkflowDefinition, WorkflowRegistry Protocol
- `audit/` — AuditOperator, AuditLogWriter Protocol
- `attachment/` — AttachmentMeta, AttachmentStorage Protocol
- `serial_number/` — SerialNumberGenerator Protocol

## Workflow Engine 设计

- Workflow Definition 通过代码注册，不存数据库
- 数据库仅保存：状态历史 + 少量元数据
- Workflow Engine 不执行业务逻辑，只管理：状态 / 转换 / 权限 / 历史
- 业务逻辑由 Service 或 EventHandler 执行

## 模块开发顺序

```
M0: Project Skeleton
M1: Shared Kernel
M2: Auth → BaseData → Brand
M3: Purchase / Inventory
M4: Template / Document / Sales
M5: Execution Plan / Shipment / Workflow
M6: Finance
M7: Settlement / Logistics
```

## BaseData 设计

纯 Master Data，无业务逻辑：
- Product / BusinessPartner / BPContact / BPAddress / BPBankAccount
- Category / Currency / Country / UOM / Warehouse

Business Partner 拆表：
- `bp` — 基础信息
- `bp_contact` — 联系人（唯一约束: bp_id + mobile）
- `bp_address` — 地址
- `bp_bank_account` — 银行账户
- ext_json 仅存真正不可预测的扩展字段

## Auth 设计

RBAC：User / Role / Permission / UserRole / RolePermission

## Brand 设计

独立模块，不并入 BaseData。采购/销售/产品均引用 Brand。
