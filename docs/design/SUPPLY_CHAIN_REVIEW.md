# Supply Chain Domain Review —— PET 瓶片贸易 ERP

> 状态: Review V1 | 日期: 2026-07-07
> 基于: M0/M1/M3/M4 已完成代码 + Supply Chain Flow Design

---

## 一、当前状态总览

### 模块交付状态

| 模块 | 状态 | 实体数 | 事件数 | 权限数 |
|------|------|--------|--------|--------|
| M3-2 Inventory V2.3 | ✅ | 8 (Material/Account/ContractStock/WarehouseStock/Batch/BatchSource/Allocation/Transaction/Ledger) | 0 (消费者) | 16 |
| M3-3 Purchase V2 | ✅ | 4 (PO/Line/Receipt/Line) | 4 (发布方) | 17 |
| M4 Sales V1 | ✅ | 2 (Contract/Line) | 1 (发布方) | 12 |
| M3.5 Shared Kernel | ✅ | EventLog/ConsumerLog/NumberSequence/NumberRule/AuditLog/WorkflowInstance | - | - |

### 已形成的闭环

```
Purchase V2                    Inventory V2.3                  Sales V1
──────────                     ──────────────                  ────────
PO.confirm()                   ContractStock(IN_TRANSIT)       SC.confirm()
  │ publish(POConfirmed)           ▲                              │ publish(SCConfirmed)
  │                                │                              │
Receipt.confirm()                  │                              ▼
  │ publish(GoodsReceived)         │                          Allocation(ACTIVE)
  │                                │
  ▼                                │
Batch + WarehouseStock             │
  (IN_TRANSIT→IN_WAREHOUSE)        │
```

✅ 采购→入库→锁货→销售 链路已贯通（EventBus 驱动）

---

## 二、问题分析

### 2.1 SalesContract 状态模型 —— 合同状态 vs 执行状态混在一起

**当前**:

```
draft → confirmed → allocated → committed → partial_shipped → delivered → closed
```

**问题**: 合同生命周期（draft/confirmed/cancelled）和物流执行（allocated/committed/shipped）混在同一个状态机中。这导致：
- `allocated` 依赖 Inventory 回调才能进入（跨模块耦合）
- `committed` 不是合同概念，是库存承诺概念
- `partial_shipped` 是发货状态，不是合同状态
- 状态转换依赖外部系统（Inventory、Shipment），Sales 模块不可独立测试

**建议 V3**:

```
SalesContract (合同状态)
  draft → confirmed → completed → closed
                │
                └──→ cancelled

SalesExecution (执行状态 - 新增，由 Inventory 管理)
  pending → allocated → committed → partial_delivered → delivered
```

| 层 | 实体 | 职责 |
|----|------|------|
| 合同层 | SalesContract | 合同本身的 CRUD + 确认/关闭 |
| 执行层 | SalesExecution (Inventory 侧) | 锁货状态、承诺状态、交付进度 |

**影响**: Sales 模块和 Inventory 模块各管各自的状态，通过 EventBus 同步而非等待回调。

---

### 2.2 Allocation 泛化 —— 当前绑定 SalesContract

**当前**:

```python
class Allocation(BaseModel):
    contract_stock_id  # FK → ContractStock
    sales_contract_id  # FK → SalesContract  ← 硬绑定
    sales_contract_line_id
```

**问题**: Inventory 核心实体的字段耦合了 Sales 模块概念。未来需要支持：
- 销售锁货
- 客户暂存（customer hold）
- 临时预留（internal reserve）
- 三方贸易（寄售）

**建议 V3**:

```python
class Allocation(BaseModel):
    contract_stock_id     # FK → ContractStock (货权源)
    batch_id              # FK → Batch (nullable)
    customer_id           # FK → BusinessPartner
    allocation_type       # "sales_contract" | "customer_hold" | "internal_reserve" | "consignment"
    source_type           # "SalesContract" | "Manual" | "Transfer"
    source_id             # 来源单据 UUID (可以是 SalesContract.id)
    source_line_id        # 来源行 UUID
    qty / status / ...
```

**核心变更**: `sales_contract_id` → `allocation_type + source_type + source_id` 三元组。Inventory 不 import Sales 模块，通过 source_type 字符串区分来源。

---

### 2.3 Purchase 模型 —— 缺少贸易合同属性

**当前**: PurchaseOrder 缺少 PET 瓶片贸易特有的合同属性。

**缺失字段**:
- `incoterm`: FOB / CIF / CFR
- `payment_term`: TT / LC / DP
- `quality_spec`: PET 质量要求（IV 值、水分等）
- `origin_country`: 原产国
- `loading_port`: 装运港
- `discharge_port`: 卸货港

**建议 V3**: PurchaseOrder 增加贸易字段：

```
incoterm         str(10)      FOB / CIF / CFR
payment_term     str(20)      TT 30d / LC at sight
quality_spec     JSON         PET 质量约定
origin_country   str(50)      原产国
loading_port     str(50)      装运港
```

**注意**: Batch 是收货后产生的实物批次，不应承担合同属性（供应商、价格已在 Batch 上有冗余但合理）。

---

### 2.4 Inventory Ledger —— 保持快照模型

**当前**: `before_qty / change_qty / after_qty` 快照模型。

**确认**: 不引入财务复式记账（debit/credit）。保持当前设计。

**补充**: Ledger 增加 `account_code` 已满足按账户维度查询的需求。

---

### 2.5 EventBus —— 补充 retry / dead letter

**当前**:

```
DomainEvent (event_id, event_type, aggregate_type, aggregate_id, version, trace_id)
EventLog (持久化)
EventConsumerLog (消费者追踪)
EventBus (publish, subscribe, 幂等)
```

**缺失**:

- **Event retry**: 消费者失败后自动重试
- **Dead letter**: 超过最大重试次数的事件进入死信队列
- **Event status**: 事件自身的处理状态（pending / processed / failed）

**建议 V3**:

```python
# EventLog 增加字段:
status: str = "pending"  # pending / processed / failed / dead
retry_count: int = 0
max_retries: int = 3
last_error: str | None

# EventBus 增加:
async def publish_with_persistence(event) → EventLog
async def retry_failed() → None
```

**当前可用**: 已有的 EventLog + EventConsumerLog 表结构可以支撑这些能力，只需增加字段和方法。

---

## 三、V3 调整建议汇总

| # | 问题 | 当前 | V3 建议 | 影响模块 |
|---|------|------|---------|---------|
| 1 | SalesContract 状态混在一起 | 8 状态合一 | 拆分为 Contract 状态 + Execution 状态 | Sales, Inventory |
| 2 | Allocation 绑定 SalesContract | sales_contract_id | allocation_type + source_type + source_id | Inventory |
| 3 | Purchase 缺贸易属性 | 基础字段 | +incoterm/payment_term/quality_spec/port | Purchase |
| 4 | Ledger 快照模型 | before/change/after | 保持，不增加 | - |
| 5 | EventBus 缺 retry | publish 即完成 | +status/retry_count/dead_letter | Core |

---

## 四、修正后的实体关系（V3）

```
┌──────────────┐     EventBus     ┌───────────────┐     EventBus     ┌──────────────┐
│   Purchase   │ ───────────────→ │   Inventory   │ ←─────────────── │    Sales     │
│              │                  │               │                  │              │
│ PurchaseOrder│                  │ ContractStock │                  │ SalesContract│
│ (贸易属性)    │                  │ WarehouseStock│                  │ (合同状态)    │
│ PurchaseLine │                  │ Batch         │                  │ SCLine       │
│ GoodsReceipt │                  │ BatchSource   │                  │              │
│              │                  │ Allocation    │                  │              │
│              │                  │ (泛化)        │← source_type/id  │              │
│              │                  │ InvTransaction│                  │              │
│              │                  │ InvLedger     │                  │              │
└──────────────┘                  └───────────────┘                  └──────────────┘
```

---

## 五、M5 Shipment 前置条件

M5 Shipment 需要在 V3 调整后进入：

1. ✅ Allocation 泛化完成（Shipment 作为 source_type="shipment" 的消费者）
2. ✅ SalesContract 状态收敛（Shipment 更新 Execution 状态而非 Contract 状态）
3. ✅ EventBus 可靠（retry/dead letter 确保事件不丢失）

---

确认后按 V3 建议逐一修正。
