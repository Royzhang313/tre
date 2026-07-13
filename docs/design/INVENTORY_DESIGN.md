# M3-2 Inventory Core —— 架构设计 V2.2（最终）

> 状态: Review V2.3 (Final) | 日期: 2026-07-07
> 业务: PET 瓶片贸易 ERP —— 货权/实物双层 + 库存账户 + 复式台账

---

## 一、架构概览

```
Business Event (业务事件)
    │
    ▼
InventoryTransaction (业务事件记录)
    │
    ├── 更新 ContractStock / WarehouseStock / Allocation
    │
    └── 产生 InventoryLedger (复式记账)
            │
            ├── Debit:  Account A +qty
            └── Credit: Account B -qty
```

三层：
1. **业务事件层**: InventoryTransaction —— 记录"发生了什么"
2. **库存状态层**: ContractStock / WarehouseStock / Allocation —— 记录"现在是多少"
3. **台账层**: InventoryLedger —— 记录"每一笔记账"

---

## 二、库存账户体系

### 2.1 InventoryAccount（库存账户 —— 新增抽象）

不再直接绑定 `contract_stock` / `warehouse_stock` 字符串，改为系统定义的库存账户。

| code | 名称 | 类型 | 正常余额 | 说明 |
|------|------|------|----------|------|
| `IN_TRANSIT` | 在途库存 | Asset | Debit | 已采购未入库 |
| `IN_WAREHOUSE` | 在仓库存 | Asset | Debit | 已入库可用 |
| `ALLOCATED` | 已分配库存 | Contra | Credit | 承诺给客户（锁货） |
| `COMMITTED` | 已承诺库存 | Contra | Credit | 已承诺给销售合同，未发运（非财务收入确认） |
| `DELIVERED` | 已交付 | Settlement | Credit | 已发运给客户 |

### 2.2 账户记账规则

| 业务事件 | Debit (增加) | Credit (减少) | 说明 |
|----------|-------------|---------------|------|
| PO 确认 | IN_TRANSIT +qty | — | 货权增加 |
| 收货入库 | IN_WAREHOUSE +qty | IN_TRANSIT -qty | 在途转在仓 |
| 锁货 | IN_TRANSIT/IN_WAREHOUSE +qty (ALLOCATED) | — | 库存承诺 |
| 销售确认 | COMMITTED +qty | ALLOCATED -qty | 货权转移 |
| 发运 | DELIVERED +qty | COMMITTED -qty | 物理交付 |

---

## 三、实体关系图

```
┌──────────────────┐
│ InventoryAccount │  ← 系统账户定义（5 个固定账户）
│ code / name      │
└──────────────────┘

┌──────────────────┐       ┌──────────────────┐
│ ContractStock    │       │ WarehouseStock   │
│ material_id      │       │ batch_id         │
│ supplier_id      │       │ warehouse_id     │
│ qty_in_transit   │       │ qty_on_hand      │
│ qty_in_warehouse │       │ qty_allocated    │
│ qty_allocated    │       └──────────────────┘
│ qty_shipped      │               │
│ is_closed        │               │
└──────────────────┘               │
        │                           │
        └──────────┬────────────────┘
                   │
                   ▼
┌──────────────────┐       ┌──────────────────┐
│InventoryTransaction│────→│ InventoryLedger  │
│ (业务事件)         │ 1  N │ (记账条目)        │
│ tx_type           │       │ account_code     │
│ qty               │       │ entry_type       │
│ reference_type/id │       │ debit_qty        │
│ batch_id          │       │ credit_qty       │
│ idempotency_key   │       │ balance_qty      │
└──────────────────┘       └──────────────────┘

┌──────────────────┐       ┌──────────────────┐
│     Batch        │←──────│   BatchSource    │
│ batch_no         │ 1   N │ source_type      │
│ material_id      │       │ source_id        │
│ contract_stock_id│       │ qty              │
└──────────────────┘       └──────────────────┘

┌──────────────────┐
│   Allocation     │
│ contract_stock_id│
│ batch_id         │
│ customer_id → BP │
│ qty / status     │
└──────────────────┘
```

7 个实体。

---

## 四、表定义

### 4.1 InventoryAccount（库存账户）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(30) | UNIQUE, NOT NULL | IN_TRANSIT / IN_WAREHOUSE / ALLOCATED / COMMITTED / DELIVERED |
| name | str(50) | NOT NULL | 中文名 |
| normal_balance | str(6) | NOT NULL | debit / credit |
| description | str(255) | nullable | |

**Seed 数据**: 5 个固定账户，系统启动时自动创建，不提供 API 增删。

---

### 4.2 ContractStock（货权库存）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| material_id | UUID | FK→Material |
| supplier_id | UUID | FK→BusinessPartner |
| po_id | UUID | FK→PurchaseOrder |
| qty_contracted | Decimal(18,4) | 合同总量 |
| qty_in_transit | Decimal(18,4) | 在途量 |
| qty_in_warehouse | Decimal(18,4) | 在仓量 |
| qty_allocated | Decimal(18,4) | 已分配量 |
| qty_shipped | Decimal(18,4) | 已出库量 |
| is_closed | bool | default=False，手动关结 |

**唯一约束**: `(material_id, po_id)`

**数量状态计算**（不存 status 字段）:

| 状态 | 条件 |
|------|------|
| in_transit | qty_in_transit > 0, qty_in_warehouse == 0, qty_shipped == 0 |
| in_warehouse | qty_in_warehouse > 0, qty_shipped == 0 |
| partial_shipped | qty_shipped > 0, qty_shipped < qty_contracted |
| complete | qty_shipped == qty_contracted |

---

### 4.3 WarehouseStock（实物库存）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| material_id | UUID | 冗余 |
| batch_id | UUID | FK→Batch |
| warehouse_id | UUID | FK→Warehouse |
| location_id | UUID | nullable |
| qty_on_hand | Decimal(18,4) | 在手量 |
| qty_allocated | Decimal(18,4) | 已分配量 |
| last_tx_id | UUID | nullable |

**唯一约束**: `(batch_id, warehouse_id, location_id)`

---

### 4.4 Batch（贸易批次）

保持 V2 设计，`contract_stock_id` 关联货权源。

---

### 4.5 BatchSource（批次来源 —— 一对多）

一个 Batch 可以有多个来源（分次收货、调拨补货等）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| batch_id | UUID | FK→Batch, NOT NULL |
| source_type | str(30) | NOT NULL | purchase_receipt / transfer / manual / adjustment |
| source_id | UUID | NOT NULL | 来源单据 ID |
| source_line_id | UUID | nullable | 来源行 ID |
| ref_no | str(50) | nullable | 来源单据号 |
| qty | Decimal(18,4) | NOT NULL | 本次来源数量 |
| created_at | datetime | |

**不再 UNIQUE(batch_id)** —— 一个 Batch 可以有多个 Source。

---

### 4.6 Allocation（贸易锁货）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| contract_stock_id | UUID | FK→ContractStock, NOT NULL |
| batch_id | UUID | FK→Batch, nullable | 指定批次（null=不指定） |
| customer_id | UUID | FK→BusinessPartner, NOT NULL |
| sales_contract_id | UUID | nullable | FK→SalesContract(M4)，关联销售合同 |
| sales_contract_line_id | UUID | nullable | 销售合同行 ID，精确到行 |
| qty | Decimal(18,4) | NOT NULL |
| status | str(20) | NOT NULL | active / released / committed |
| operator_id | UUID | FK→User |
| released_at | str(10) | nullable |
| remark | str(255) | nullable |

**关联 SalesContract**: Allocation 必须关联销售合同（M4 Sales 模块实现前可为空）。不是简单的 sales_order_id —— SalesContract 是独立的合同实体。

---

### 4.7 InventoryTransaction（业务事件 —— 原 StockTransaction 重命名）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| tx_type | str(30) | NOT NULL | receive / ship / allocate / deallocate / sell / deliver / transfer_in / transfer_out / adjust / reverse |
| material_id | UUID | FK→Material |
| batch_id | UUID | FK→Batch, nullable |
| qty | Decimal(18,4) | NOT NULL |
| reference_type | str(50) | NOT NULL |
| reference_id | UUID | NOT NULL |
| source_type | str(50) | NOT NULL | 来源类型（purchase_receipt / sales_shipment / manual） |
| source_id | UUID | NOT NULL | 来源单据 ID |
| source_line_id | UUID | nullable | 来源行 ID |
| reference_line_id | UUID | nullable | 业务单据行 ID（与 source 区分：source=库存来源，reference=业务关联） |
| transfer_group | UUID | nullable |
| idempotency_key | str(100) | UNIQUE, NOT NULL |
| operator_id | UUID | FK→User |
| remark | str(255) | nullable |
| created_at | datetime | |

### 4.8 InventoryLedger（库存台账 —— 快照模型）

不做财务复式记账（debit/credit），只记录每次变动前后的**状态快照**。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| transaction_id | UUID | FK→InventoryTransaction, NOT NULL |
| account_code | str(30) | NOT NULL | IN_TRANSIT / IN_WAREHOUSE / ALLOCATED / COMMITTED / DELIVERED |
| material_id | UUID | FK→Material |
| batch_id | UUID | FK→Batch, nullable |
| before_qty | Decimal(18,4) | NOT NULL | 变动前数量 |
| change_qty | Decimal(18,4) | NOT NULL | 变动量（+入库/-出库） |
| after_qty | Decimal(18,4) | NOT NULL | 变动后数量 |
| reference_type | str(50) | NOT NULL |
| reference_id | UUID | NOT NULL |
| created_at | datetime | |

---

## 五、库存流转与记账

### 5.1 PO 确认 → 货权增加（通过 EventBus）

```
Purchase.PurchaseOrderConfirmed (Event)
    │
    ▼
Inventory 监听事件 → ContractStockService.create()
    │
    ├── ContractStock.qty_in_transit += qty
    └── InventoryLedger: IN_TRANSIT before=0 change=+qty after=qty
```

### 5.2 收货入库 → 在途转在仓（通过 EventBus）

```
Purchase.GoodsReceived (Event)
    │
    ▼
Inventory 监听事件 → BatchService.receive_from_event()
    │
    ├── ContractStock.qty_in_transit -= qty
    ├── ContractStock.qty_in_warehouse += qty
    ├── Batch + BatchSource 创建
    ├── WarehouseStock.qty_on_hand += qty
    └── InventoryLedger:
        IN_WAREHOUSE before=0 change=+qty after=qty
        IN_TRANSIT before=qty change=-qty after=0
```

### 5.3 锁货 → 库存承诺（直接调用）

```
AllocationService.allocate()
    │
    ├── ContractStock.qty_allocated += qty
    ├── WarehouseStock.qty_allocated += qty
    ├── Allocation 创建 (status=active, sales_contract_id)
    └── InventoryLedger: ALLOCATED change=+qty
```

### 5.4 销售合同确认 → 货权承诺（通过 EventBus）

```
Sales.SalesContractConfirmed (Event, M4)
    │
    ▼
Inventory 监听事件 → AllocationService.commit()
    │
    ├── Allocation.status = committed
    └── InventoryLedger: COMMITTED change=+qty
```

### 5.5 发运 → 物理交付（通过 EventBus）

```
Sales.ShipmentConfirmed (Event, M5)
    │
    ▼
Inventory 监听事件
    │
    ├── ContractStock.qty_shipped += qty
    ├── WarehouseStock.qty_on_hand -= qty
    ├── WarehouseStock.qty_allocated -= qty
    └── InventoryLedger:
        DELIVERED before=0 change=+qty after=qty
```

---

## 六、跨模块通信（EventBus）

**Purchase 不直接调用 Inventory Service。** 通过 EventBus 解耦：

```
Purchase Module                    Inventory Module
─────────────                      ────────────────
PO.confirm()
    │
    ├── 更新 PO 状态
    └── publish(PurchaseOrderConfirmed)
                                        │
                                        ▼
                                   ContractStockService
                                   .on_po_confirmed()
                                        │
                                        ├── ContractStock 创建
                                        └── InventoryLedger

Receipt.confirm()
    │
    ├── 更新 Receipt 状态
    └── publish(GoodsReceived)
                                        │
                                        ▼
                                   BatchService
                                   .on_goods_received()
                                        │
                                        ├── Batch + WarehouseStock
                                        └── InventoryLedger
```

| 事件 | 发布方 | 消费方 |
|------|--------|--------|
| `PurchaseOrderConfirmed` | Purchase | Inventory (创建 ContractStock) |
| `GoodsReceived` | Purchase | Inventory (在途→在仓 + Batch + Stock) |
| `SalesContractConfirmed` | Sales (M4) | Inventory (Allocation.commit) |
| `ShipmentConfirmed` | Sales (M5) | Inventory (DELIVERED + 实物扣减) |

---

## 七、M3-2 / M3-3 边界

| 模块 | 实体 |
|------|------|
| **M3-2 Inventory** | InventoryAccount / ContractStock / WarehouseStock / Batch / BatchSource / Allocation / InventoryTransaction / InventoryLedger |
| **M3-3 Purchase** | PurchaseOrder / PurchaseLine / GoodsReceipt / GoodsReceiptLine + 发布 Event（不直接调 Inventory Service） |

---

## 八、领域约束（最终）

**本系统为 PET 瓶片贸易 ERP。**

- ❌ 不设计 SKU / BOM / 生产工单 / 领料 / 制造属性
- ❌ Ledger 不做财务复式记账（debit/credit），只做数量快照（before/change/after）
- ❌ COMMITTED 不是财务收入确认，仅表示货权承诺
- ✅ 库存核心是**货权流转**（在途 → 在仓 → 承诺 → 交付）
- ✅ 所有后续模块必须基于此业务场景设计

---

## 九、V2.2 → V2.3 变更

| # | 变更 | 说明 |
|---|------|------|
| 1 | SOLD → COMMITTED | 避免与财务收入确认混淆，"已承诺"而非"已售" |
| 2 | Allocation 关联 SalesContract | 增加 `sales_contract_id`，不是简单 sales_order |
| 3 | Ledger 去复式记账 | before_qty / change_qty / after_qty 快照模型，不做 debit/credit |
| 4 | Purchase → EventBus → Inventory | Purchase 不直接调用 Inventory Service |
| 5 | 领域约束声明 | PET 瓶片贸易 ERP，货权流转模型 |

---

确认后进入 Coding。
