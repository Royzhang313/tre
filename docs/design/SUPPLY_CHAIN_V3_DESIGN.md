# Supply Chain V3 Final Design —— PET 瓶片贸易 ERP

> 状态: Review V3 | 日期: 2026-07-07

---

## 一、Bounded Context 边界

```
┌──────────────────────────────────────────────────────────────────┐
│                        PET 瓶片贸易 ERP                           │
│                                                                  │
│  ┌──────────┐    EventBus    ┌───────────┐    EventBus    ┌──────┐
│  │ Purchase │──────────────→│ Inventory  │←──────────────│Sales │
│  │          │               │           │               │      │
│  │ PO       │               │ContractStk│               │SC    │
│  │ Receipt  │               │WarehouseStk│              │SCLine│
│  │          │               │ Batch      │               │SCExec│
│  └──────────┘               │ Allocation │               └──────┘
│                              │ Transaction│                      │
│                              │ Ledger     │                      │
│                              └───────────┘                      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Shared Kernel                           │   │
│  │  EventBus │ NumberEngine │ AuditEngine │ WorkflowEngine  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     BaseData                              │   │
│  │  Company │ BP │ Warehouse │ Unit │ Currency │ Category    │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## 二、上下文决策

### 2.1 SalesExecution 归属

**选择: Sales 模块内部（SalesExecution 是 SalesContractLine 的执行状态视图）**

| 层 | 职责 | 所属模块 |
|----|------|---------|
| SalesContract | 合同 CRUD + 确认/取消/关闭 | Sales |
| SalesContractLine | 合同行内容 | Sales |
| SalesExecution (执行状态) | 每行 allocated/committed/shipped 进度 | Sales (监听 Inventory 事件更新) |
| Allocation | 库存承诺（货权占用） | Inventory |
| InventoryLedger | 每次变动的快照 | Inventory |

**交互方式**: Inventory 发布事件 → Sales 监听更新 SalesExecution 状态。Inventory 不 import Sales。

```
SalesContract.confirm()
    │
    └── publish(SalesContractConfirmed)
            │
            ▼ (Inventory 监听)
        AllocationService.allocate()
            │
            └── publish(InventoryAllocated)
                    │
                    ▼ (Sales 监听)
                SalesExecution.status = allocated
```

### 2.2 Allocation V3 泛化

**选择: 泛化为 allocation_type + source_type + source_id**

Inventory 核心不依赖 Sales 模块。

```python
class Allocation(BaseModel):
    contract_stock_id       # FK → ContractStock
    batch_id               # FK → Batch (nullable)
    customer_id            # FK → BusinessPartner
    allocation_type        # "sales" | "customer_hold" | "internal_reserve" | "consignment"
    source_type            # "SalesContract" | "PurchaseContract" | "Manual"
    source_id              # 来源单据 UUID
    source_line_id         # 来源行 UUID
    qty / status / ...
```

**示例**:
```
销售锁货: allocation_type="sales", source_type="SalesContract", source_id=<sc.id>
客户暂存: allocation_type="customer_hold", source_type="Manual", source_id=<user.id>
寄售:     allocation_type="consignment", source_type="ConsignmentContract", source_id=<cc.id>
```

---

## 三、实体关系（V3 Final）

### Purchase（V3 增强）

```
PurchaseOrder
├── incoterm: str(10)        # 🆕 FOB / CIF / CFR
├── payment_term: str(30)    # 🆕 TT 30d / LC at sight
├── loading_port: str(50)    # 🆕
├── discharge_port: str(50)  # 🆕
├── quality_spec: JSON       # 🆕 PET 质量约定
├── origin_country: str(50)  # 🆕

PurchaseLine (保持)
├── material_id → Material
├── qty_ordered / unit_price / currency_id
```

### Inventory（Allocation V3 泛化 + Ledger 保持）

```
Allocation (V3)
├── allocation_type          # 🆕
├── source_type              # 🆕
├── source_id                # 🆕
├── source_line_id           # 🆕
├── (移除 sales_contract_id) # ❌

InventoryLedger (保持)
├── before_qty / change_qty / after_qty  # 快照模型

InventoryTransaction (保持)
├── source_type / source_id / source_line_id
```

### Sales（增加 SalesExecution）

```
SalesContract
├── status: ContractStatus    # draft / confirmed / completed / cancelled / closed

SalesContractLine
├── status: LineStatus        # open / partial / complete / cancelled
├── SalesExecution (执行状态)  # 🆕

SalesExecution (新增 - Sales 模块内的执行追踪)
├── contract_line_id          # FK → SalesContractLine
├── allocated_qty             # 已锁重量
├── committed_qty             # 已承诺重量
├── shipped_qty               # 已发运重量
├── status: ExecutionStatus   # pending / allocated / committed / partial / delivered
```

---

## 四、状态机

### 4.1 SalesContract（合同状态）

```
draft ──→ confirmed ──→ completed ──→ closed
  │           │
  └──→ cancelled
```

| 状态 | 触发 | 说明 |
|------|------|------|
| draft | 创建 | 编辑中 |
| confirmed | 确认 | 合同生效，发布 SalesContractConfirmed |
| completed | 全部执行完成 | 自动（监听 Inventory 事件） |
| cancelled | 取消 | 未发运前可取消 |
| closed | 关结 | 手动 |

### 4.2 SalesExecution（执行状态 - 独立跟踪）

```
pending ──→ allocated ──→ committed ──→ partial ──→ delivered
  │             │            │            │
  └─────────────┴────────────┴────────────┘
                 cancelled
```

| 状态 | 触发事件 | 来源 |
|------|---------|------|
| pending | 合同确认 | Sales |
| allocated | InventoryAllocated | Inventory (EventBus) |
| committed | SalesExecutionCommitted | Sales (手动/自动) |
| partial | InventoryPartiallyDelivered | Inventory (EventBus) |
| delivered | InventoryDelivered | Inventory (EventBus) |

### 4.3 PurchaseOrder（保持）

```
draft → confirmed → partial → complete → closed
  │        │
  └──→ cancelled
```

---

## 五、Event Catalog（完整）

```
┌──────────────────────────────┬──────────┬──────────────┬─────────────────────────┐
│ Event                        │ 发布方   │ 消费方       │ 描述                     │
├──────────────────────────────┼──────────┼──────────────┼─────────────────────────┤
│ purchase.order.confirmed     │ Purchase │ Inventory    │ PO确认→ContractStock创建 │
│ purchase.order.cancelled     │ Purchase │ Inventory    │ PO取消→ContractStock释放 │
│ purchase.receipt.confirmed   │ Purchase │ Inventory    │ 收货→IN_WAREHOUSE+Batch  │
│ purchase.receipt.reversed    │ Purchase │ Inventory    │ 冲销→反向记账            │
│ sales.contract.confirmed     │ Sales    │ Inventory    │ SC确认→Allocation创建    │
│ sales.contract.cancelled     │ Sales    │ Inventory    │ SC取消→Allocation释放    │
│ inventory.allocated          │ Inventory│ Sales        │ 锁货完成→更新Execution   │
│ inventory.allocation.released│ Inventory│ Sales        │ 锁货释放→更新Execution   │
│ inventory.delivered          │ Inventory│ Sales        │ 发运完成→更新Execution   │
│ inventory.stock.changed      │ Inventory│ Audit        │ 库存变动→审计记录        │
└──────────────────────────────┴──────────┴──────────────┴─────────────────────────┘
```

**关键**: Inventory 不监听 Sales 事件（改为 Sales 监听 Inventory 事件）。Inventory 是所有库存状态的权威来源。

---

## 六、EventBus V3

### EventLog 增强

```python
class EventLog(BaseModel):
    # ... 现有字段
    status: str = "pending"       # pending / processing / success / failed / dead
    retry_count: int = 0
    max_retries: int = 3
    last_error: str | None
    next_retry_at: str | None    # ISO datetime
```

### Dead Letter

当 `retry_count >= max_retries` 时，事件进入 `status=dead`，不再重试。

```python
class DeadLetterEvent(BaseModel):
    """死信事件 —— 人工处理"""
    __tablename__ = "core_dead_letters"
    event_log_id: UUID
    event_type: str
    error_message: str
    payload: dict | None
    resolved: bool = False
```

---

## 七、数据流（完整）

### 采购入库流

```
1. PO.draft → 创建
2. PO.confirm()
   ├── PO.status = confirmed
   └── publish(purchase.order.confirmed)
           │
           ▼ Inventory 监听
       ContractStock: qty_in_transit += qty
       InventoryLedger: IN_TRANSIT +qty

3. Receipt.create() + add_line()
4. Receipt.confirm()
   ├── Receipt.status = confirmed
   ├── PO Line.qty_received += qty
   └── publish(purchase.receipt.confirmed)
           │
           ▼ Inventory 监听
       ContractStock: in_transit→in_warehouse
       Batch + WarehouseStock 创建
       InventoryLedger: IN_WAREHOUSE +qty, IN_TRANSIT -qty
```

### 销售出库流

```
1. SC.draft → 创建
2. SC.confirm()
   ├── SC.status = confirmed
   └── publish(sales.contract.confirmed)
           │
           ▼ Inventory 监听
       Allocation.create(allocation_type="sales", source_type="SalesContract", source_id=sc.id)
       InventoryLedger: ALLOCATED +qty
           │
           └── publish(inventory.allocated)
                   │
                   ▼ Sales 监听
               SalesExecution.status = allocated

3. SC.commit() (手动 or 自动)
   ├── publish(sales.execution.committed)
           │
           ▼ Inventory 监听
       Allocation.status = committed

4. Shipment.confirm() (M5)
   ├── publish(shipment.confirmed)
           │
           ▼ Inventory 监听
       WarehouseStock.qty_on_hand -= qty
       ContractStock.qty_shipped += qty
       InventoryLedger: DELIVERED +qty
           │
           └── publish(inventory.delivered)
                   │
                   ▼ Sales 监听
               SalesExecution.status = delivered
```

---

## 八、M5 Shipment 接入方式

```
┌──────────┐     publish(shipment.confirmed)     ┌───────────┐
│ Shipment │ ─────────────────────────────────→  │ Inventory │
│  (M5)    │                                      │           │
│          │                                      │ DELIVERED │
│  create  │                                      │ +qty      │
│  confirm │                                      │           │
└──────────┘                                      └───────────┘
                                                        │
                                               publish(inventory.delivered)
                                                        │
                                                        ▼
                                                   ┌──────────┐
                                                   │  Sales   │
                                                   │          │
                                                   │SalesExec │
                                                   │delivered │
                                                   └──────────┘
```

Shipment 模块职责：
- 发运单 CRUD
- 关联 SalesContract + Allocation
- confirm → publish `shipment.confirmed`
- 不操作 Inventory 表

---

## 九、V3 Coding 范围

| 优先级 | 变更 | 文件 |
|--------|------|------|
| P0 | Allocation 泛化 | `inventory/models.py` (sales_contract_id → allocation_type+source) |
| P0 | SalesExecution 新增 | `sales/models.py` + `sales/service.py` |
| P0 | SalesContract 状态收敛 | `sales/models.py` (ContractStatus 简化) |
| P1 | Purchase 贸易字段 | `purchase/models.py` (+incoterm/payment_term/port/quality_spec) |
| P1 | EventBus V3 retry | `core/event_log.py` (+status/retry/dead_letter) |
| P2 | Event 反转 (Inventory→Sales) | `inventory/events.py` + `sales/listeners.py` |

---

确认后进入 V3 Coding。
