# AI Context Layer Design

> 状态: Review V1 | 日期: 2026-07-08
> 目标: 为 AI Builder 提供结构化系统上下文，实现自然语言 → 代码生成

---

## 一、架构总览

```
┌──────────────────────────────────────────────────┐
│                  AI Builder                       │
│   (自然语言 → 理解系统 → 生成代码)                  │
└────────────────────┬─────────────────────────────┘
                     │ 消费
                     ▼
┌──────────────────────────────────────────────────┐
│              AI Context Layer                     │
│                                                   │
│  ModuleManifest (版本/命令/UI)                      │
│  EntityContext  (命令/工作流/事件)                    │
│  AllocationHold (独立暂挂实体)                       │
│  ContextBuilder (快照生成器)                         │
└────────────────────┬─────────────────────────────┘
                     │ 读取
                     ▼
┌──────────────────────────────────────────────────┐
│            Module Registry + Entity Metadata      │
│            (M6 Core Hardening)                    │
└──────────────────────────────────────────────────┘
```

---

## 二、ModuleManifest 增强

### 2.1 新增字段

```python
@dataclass
class ModuleManifest:
    # === M6 已有 ===
    name: str
    display_name: str
    version: str
    entities: list[EntityMeta]
    events_published: list[str]
    events_consumed: list[str]
    permissions: list[str]
    dependencies: list[str]

    # === M6.1 新增 ===
    commands: list[ModuleCommand]       # 🆕 模块支持的命令
    ui_pages: list[UIPageMeta]          # 🆕 前端页面描述
    workflows: list[WorkflowRef]        # 🆕 模块使用的工作流
```

### 2.2 ModuleCommand（模块命令）

```python
@dataclass
class ModuleCommand:
    """模块对外暴露的业务命令 —— AI 可据此生成 API 和 UI"""
    name: str                    # "create_purchase_order"
    display_name: str            # "创建采购订单"
    description: str             # "创建 PET 瓶片采购订单，支持多品种多币种"
    http_method: str             # "POST"
    http_path: str               # "/api/v1/purchase/orders"
    request_schema: str          # "POCreate"
    response_schema: str         # "POResponse"
    required_permission: str     # "purchase.order.create"
    side_effects: list[str]      # ["publish: purchase.order.confirmed"]
```

### 2.3 UIPageMeta（UI 页面元数据）

```python
@dataclass
class UIPageMeta:
    """前端页面描述 —— AI 可据此生成 React 页面"""
    route: str                   # "/purchase/orders"
    title: str                   # "采购订单"
    page_type: str               # "list" | "form" | "detail" | "dashboard"
    entity: str                  # "PurchaseOrder"
    columns: list[str]           # 列表页显示的列
    filters: list[str]           # 支持的筛选字段
    actions: list[str]           # 行操作: ["view", "edit", "confirm", "cancel"]
```

### 2.4 WorkflowRef（工作流引用）

```python
@dataclass
class WorkflowRef:
    """模块使用的工作流 —— 关联到 shared/workflow 中的定义"""
    workflow_name: str           # "purchase_order_approval"
    entity: str                  # "PurchaseOrder"
    trigger_command: str         # "confirm"  → 触发状态转换
```

---

## 三、EntityContext 增强

### 3.1 新增字段

```python
@dataclass
class EntityContext(EntityMeta):
    """增强实体元数据 —— 包含命令、工作流、事件绑定"""

    # === M6 EntityMeta 已有字段 ===
    name / display_name / table_name / module / is_aggregate_root
    fields: list[FieldMeta]
    relationships: list[RelationMeta]

    # === M6.1 新增 ===
    commands: list[EntityCommand]        # 🆕 此实体的业务命令
    lifecycle_workflow: str | None       # 🆕 关联的工作流名称
    events_emitted: list[str]            # 🆕 此实体变更时发出的事件
    state_field: str | None              # 🆕 状态字段名（如 "status"）
    state_values: list[str]              # 🆕 状态枚举值
    searchable_fields: list[str]         # 🆕 可搜索字段
    sortable_fields: list[str]           # 🆕 可排序字段
```

### 3.2 EntityCommand（实体命令）

```python
@dataclass
class EntityCommand:
    """实体级别的命令 —— 比 ModuleCommand 更细粒度"""
    name: str                    # "confirm"
    description: str             # "确认采购订单"
    pre_state: str | None        # "draft" (前置状态)
    post_state: str | None       # "confirmed" (后置状态)
    validation_rules: list[str]  # ["status_must_be: draft", "lines_not_empty"]
    event_emitted: str | None    # "purchase.order.confirmed"
```

---

## 四、AllocationHold —— 独立暂挂实体

### 4.1 设计理由

不修改 AllocationStatus 枚举（保持 active/released/consumed 简洁），改为独立实体表示"暂挂"状态。一个 Allocation 可以被多次 Hold（质检、争议、付款），每次 Hold 有独立的原因和处理人。

### 4.2 表定义

```python
class AllocationHold(BaseModel):
    """锁货暂挂 —— 独立实体，不污染 Allocation 状态机"""

    __tablename__ = "inventory_allocation_holds"

    allocation_id: UUID        # FK→Allocation
    hold_type: str             # "quality_inspection" | "customer_dispute" | "payment_pending" | "manual"
    hold_reason: str           # 暂挂原因描述
    held_by: UUID              # FK→User
    held_at: datetime
    released_by: UUID | None   # FK→User
    released_at: datetime | None
    status: str                # "active" | "released"
```

### 4.3 业务规则

```
Allocation(active) + AllocationHold(active) → 实际不可用
AllocationHold.release() → 恢复 Allocation(active) 可用
```

**约束**: 一个 Allocation 同时只能有一个 active 的 AllocationHold。

### 4.4 与 Allocation 关系

```
Allocation (1) ────── (N) AllocationHold
  status: active       status: active/released
                        hold_type: quality_inspection / ...
```

---

## 五、AI Context Builder

### 5.1 设计目标

`ContextBuilder` 在运行时汇总所有模块的 ModuleManifest + EntityContext，生成一份**完整系统快照**，供 AI 消费。

### 5.2 输出格式

```json
{
  "system": {
    "name": "ERP Builder",
    "version": "V3",
    "domain": "PET 瓶片贸易 ERP"
  },
  "modules": [
    {
      "name": "purchase",
      "display_name": "采购管理",
      "version": "V2",
      "commands": [
        {
          "name": "create_purchase_order",
          "http_method": "POST",
          "http_path": "/api/v1/purchase/orders",
          "request_schema": "POCreate"
        }
      ],
      "entities": [
        {
          "name": "PurchaseOrder",
          "table": "purchase_orders",
          "fields": [...],
          "state_field": "status",
          "state_values": ["draft", "confirmed", "partial", "complete", "cancelled", "closed"],
          "commands": [
            {"name": "confirm", "pre_state": "draft", "post_state": "confirmed"}
          ],
          "lifecycle_workflow": null,
          "events_emitted": ["purchase.order.confirmed"]
        }
      ],
      "ui_pages": [
        {"route": "/purchase/orders", "page_type": "list", "entity": "PurchaseOrder"}
      ],
      "events_published": ["purchase.order.confirmed", ...],
      "events_consumed": [],
      "permissions": ["purchase.order.create", ...]
    }
  ],
  "events": [
    {
      "event_type": "purchase.order.confirmed",
      "producer": "purchase",
      "consumers": ["inventory"],
      "payload_fields": ["po_id", "supplier_id", "lines"]
    }
  ]
}
```

### 5.3 API

```
GET /api/v1/system/ai-context     → 完整系统上下文快照 (JSON)
GET /api/v1/system/ai-context?module=purchase → 单模块快照
```

### 5.4 ContextBuilder 实现

```python
class ContextBuilder:
    """运行时汇总所有模块元数据，生成 AI 可消费的系统快照"""

    @staticmethod
    def build() -> dict:
        return {
            "system": {
                "name": "ERP Builder",
                "version": "V3",
                "domain": "PET 瓶片贸易 ERP",
            },
            "modules": [m.to_dict() for m in get_registered_modules()],
            "events": _build_event_catalog(),
        }

    @staticmethod
    def build_for_module(name: str) -> dict:
        manifest = get_manifest(name)
        return manifest.to_dict()
```

---

## 六、与 M6 Core Hardening 的分工

| 层 | M6 | M6.1 |
|----|-----|------|
| Outbox | ✅ OutboxMessage + Outbox | - |
| Module Registry | ✅ ModuleManifest 基础 | +version/commands/ui/workflows |
| Entity Metadata | ✅ EntityMeta.from_orm() | +commands/workflow/events/state |
| Allocation | ✅ Review 通过 | AllocationHold 独立实体 |
| AI Context | - | ✅ ContextBuilder + API |

---

## 七、Coding 范围

| 优先级 | 文件 | 说明 |
|--------|------|------|
| P0 | `shared/module_registry.py` | ModuleManifest + Command/UI/Workflow Meta dataclass |
| P0 | `shared/entity_context.py` | EntityContext + EntityCommand dataclass |
| P1 | `shared/context_builder.py` | ContextBuilder + API endpoint |
| P2 | `modules/inventory/models.py` | AllocationHold 实体 |
| P2 | 各模块 `__init__.py` | 注册 ModuleManifest |

---

确认后进入 M6 + M6.1 Coding。
