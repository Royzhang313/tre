# ERP Builder —— Domain Boundary V3

> M8.5.1 Domain Alignment Review
>
> ERP Builder 不是固定贸易 ERP，而是 **AI 可生成 ERP 平台**。
> 所有模块通过 Capability + Domain Event 通信，禁止 Service 级直接调用。

---

## 1. Module Boundaries (7 Modules)

```
┌─────────────────────────────────────────────────────────────┐
│                      EventBus (Domain Events)                │
│  purchase.contract.effective  ────→  inventory/listeners     │
│  purchase.contract.closed     ────→  inventory/listeners     │
│  sales.contract.confirmed     ────→  inventory/listeners     │
│  inventory.allocation.created ────→  sales/listeners         │
│  inventory.allocation.released───→  sales/listeners          │
│  inventory.allocation.consumed───→  sales/listeners          │
│  shipment.shipped             ────→  (待注册)                 │
│  shipment.delivered           ────→  (待注册)                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Purchase (采购合同)

| 维度 | 内容 |
|------|------|
| **聚合根** | PurchaseOrder (采购合同) |
| **实体** | PurchaseLine (合同明细) |
| **状态机** | draft → effective → closed |
| **发布事件** | `purchase.contract.effective`、`purchase.contract.closed` |
| **消费事件** | 无 |
| **依赖** | basedata (BP/Currency)、auth (User) |

**合同生效 = 货权转移。** 合同生效时发布 `purchase.contract.effective`，由 Inventory 监听生成 ContractStock。Purchase 不直接调用 Inventory Service。

### 1.2 Inventory (库存管理)

| 维度 | 内容 |
|------|------|
| **聚合根** | ContractStock (货权库存)、WarehouseStock (实物库存)、Batch (批次) |
| **实体** | InventoryTransaction、InventoryLedger、Allocation |
| **发布事件** | `inventory.stock.received`、`inventory.allocation.created/released/consumed` |
| **消费事件** | `purchase.contract.effective`、`purchase.contract.closed`、`sales.contract.confirmed` |
| **依赖** | basedata (Material/Warehouse) |

**Ledger Driven:** 所有库存变化以 InventoryLedger 为唯一真实来源。ContractStock/WarehouseStock 为高性能缓存。

### 1.3 Sales (销售管理)

| 维度 | 内容 |
|------|------|
| **聚合根** | SalesContract (销售合同) |
| **实体** | SalesContractLine、SalesExecution |
| **状态机** | draft → confirmed → completed → closed |
| **发布事件** | `sales.contract.confirmed`、`sales.execution.updated` |
| **消费事件** | `inventory.allocation.created/released/consumed` |
| **依赖** | basedata (BP)、inventory (Material via Event) |

### 1.4 Shipment (发运管理)

| 维度 | 内容 |
|------|------|
| **聚合根** | Shipment (发运单) |
| **实体** | ShipmentLine |
| **状态机** | draft → confirmed → shipped → delivered |
| **发布事件** | `shipment.shipped`、`shipment.delivered` |
| **消费事件** | 无 |
| **依赖** | basedata、inventory (via Event) |

### 1.5 Auth (系统管理)

| 维度 | 内容 |
|------|------|
| **实体** | User、Role、Permission |
| **发布事件** | 无 |
| **消费事件** | 无 |

### 1.6 BaseData (基础资料)

| 维度 | 内容 |
|------|------|
| **实体** | Company、Department、Employee、Warehouse、BP、Currency、Unit、Category |
| **发布事件** | 无 |
| **消费事件** | 无 |

### 1.7 Portal (工作台)

纯 UI 元数据模块。无后端 Service/Router。Dashboard 配置来自 Metadata。

---

## 2. Communication Rules

### 允许 ✅

```
Module A ──EventBus──→ Module B     (Domain Event)
Module A ──API──────→ Module A      (同模块内 Router→Service→Repository)
Module A ──Metadata──→ UI Renderer  (Capability/Workflow 注册)
```

### 禁止 ❌

```
Module A.Service ──→ Module B.Service    (禁止直接 Service 调用)
Module A.Repository ──→ Module B.Model   (禁止跨模块 ORM 引用)
Module A ──→ Module B 的数据库表          (禁止绕过 API/Event 直接读写)
```

---

## 3. Workflow Engine (纯引擎)

Workflow Engine **不包含任何业务状态**。业务状态由各模块在 `__init__.py` 中定义。

### 当前数据结构

```
WorkflowDefinition
 ├── name: str                    # "purchase_contract_lifecycle"
 ├── states: list[WorkflowState]  # [{code, name, terminal}]
 ├── transitions: list[WorkflowTransition]
 │    ├── name: str               # "生效"
 │    ├── from_state: str         # "draft"
 │    ├── to_state: str           # "effective"
 │    └── api_action: str         # "effect" (API 动作名)
 └── initial_state: str
```

### 待完善 (M8.6+)

按用户要求，WorkflowTransition 应补充：

| 字段 | 类型 | 说明 |
|------|------|------|
| `permission` | str | 执行该转换需要的权限，如 `"purchase.order.confirm"` |
| `event_hook` | str | 转换完成后发布的事件名，如 `"purchase.contract.effective"` |

当前 `permission` 由 Capability 注册承担，`event_hook` 由 Service 层手动发布。补充这两个字段后，WorkflowDefinition 成为完整的声明式状态机描述。

### 理想声明式模型

```python
PURCHASE_CONTRACT_WORKFLOW = WorkflowDefinition(
    name="purchase_contract_lifecycle",
    states=[
        WorkflowState("draft", "草稿"),
        WorkflowState("effective", "已生效"),
        WorkflowState("closed", "已关闭", terminal=True),
    ],
    transitions=[
        WorkflowTransition("生效", "draft", "effective",
            api_action="effect",
            permission="purchase.order.confirm",
            event_hook="purchase.contract.effective"),
        WorkflowTransition("关闭", "draft", "closed",
            api_action="close",
            permission="purchase.order.cancel",
            event_hook="purchase.contract.closed"),
        WorkflowTransition("关闭", "effective", "closed",
            api_action="close",
            permission="purchase.order.cancel",
            event_hook="purchase.contract.closed"),
    ],
    initial_state="draft",
)
```

这样 WorkflowDefinition 完全描述了一个实体的：
- **状态** (State)
- **转换** (Transition)
- **权限** (Permission)
- **事件钩子** (Event Hook)

---

## 4. Capability Registry

每个模块的操作能力在 `__init__.py` 中注册到 `CapabilityRegistry`：

```python
Capability(
    name="purchase.order.effect",       # 唯一标识
    display_name="合同生效",             # 展示名
    module="purchase",                   # 所属模块
    http_method="POST",                  # HTTP 方法
    http_path="/api/v1/purchase/orders/{id}/effect",  # API 路径
    required_permissions=["purchase.order.confirm"],   # 所需权限
    events_published=["purchase.contract.effective"],  # 发布事件
    preconditions=["status=draft"],      # 前置条件
)
```

Capability Registry 是 **AI Agent 发现系统能力的目录**，也是前端动态按钮的元数据来源。

---

## 5. Event Timeline

所有领域事件通过 `EventBus.publish()` 发布，同时写入 `EventLog` 表。

```
EventLog
 ├── event_id: UUID
 ├── event_type: str          # "purchase.contract.effective"
 ├── aggregate_type: str      # "PurchaseOrder"
 ├── aggregate_id: UUID       # 实体 ID
 ├── payload: JSON             # 事件载荷
 ├── status: str               # pending/processing/completed/failed
 └── created_at: datetime
```

前端 DetailPage 通过 `GET /api/v1/events/{entity_type}/{entity_id}` 拉取事件时间线。

---

## 6. Audit Findings (本次 Review)

### 6.1 已修正

| 项 | 状态 |
|----|------|
| PurchaseOrder → PurchaseContract 语义 | ✅ V3 已改 |
| POStatus: 6 状态 → 3 状态 (draft/effective/closed) | ✅ V3 已改 |
| 删除 GoodsReceipt 作为入库前置 | ✅ V3 已改 |
| 删除 Receipt 相关事件 | ✅ V3 已改 |
| 跨模块 Service 调用审计 | ✅ 0 违规 |

### 6.2 待修正 (优先级排序)

| 优先级 | 项 | 说明 |
|--------|-----|------|
| **P0** | `inventory/__init__.py` events_consumed 声明过时 | 声明 `purchase.order.confirmed` → 应为 `purchase.contract.effective` |
| **P1** | WorkflowTransition 缺 `permission` 字段 | 权限信息目前由 Capability 承担，Workflow 应在声明层对齐 |
| **P1** | WorkflowTransition 缺 `event_hook` 字段 | Service 层手动发布事件，改为 Workflow Engine 自动触发更声明式 |
| **P2** | Sales 模块缺 WorkflowDefinition | 只有 purchase 注册了 Workflow，sales/shipment 应补充 |
| **P2** | EventLog 写入未启用 | EventBus.publish() 当前不自动写 EventLog 表 |

### 6.3 P0 立即修正

`inventory/__init__.py` Line 38:
```python
# 当前 (过时):
events_consumed=["purchase.order.confirmed", "purchase.receipt.confirmed", "sales.contract.confirmed"],

# 应为:
events_consumed=["purchase.contract.effective", "purchase.contract.closed", "sales.contract.confirmed"],
```

---

## 7. Next Steps

1. **P0**: 修正 inventory events_consumed 声明
2. **M8.5.1 收尾**: 等待 Review 确认后，P1/P2 进入 M8.6
3. **M8.6**: WorkflowTransition 扩展 + EventBus 自动写 EventLog
