# M5 Shipment 模块 —— 架构设计

> 状态: Review V1 | 日期: 2026-07-07
> 基于: Supply Chain V3 Final Design

---

## 一、模块定位

Shipment 是**物流事实记录**模块。不负责库存计算，不直接修改 WarehouseStock。

| Shipment 做 | Shipment 不做 |
|-------------|---------------|
| 记录发运单（什么货、从哪发、发多少） | 修改 WarehouseStock.qty_on_hand |
| 管理发运状态（draft → delivered） | 管理 Allocation 状态（由 Inventory 负责） |
| 发布 Shipment 事件通知 Inventory | 直接 import Inventory Service |
| 引用 Allocation 作为发货源 | 引用 SalesContract 或 PurchaseOrder |

---

## 二、实体关系图

```
┌──────────────┐       ┌──────────────┐
│   Shipment   │←──────│ ShipmentLine │
│  (聚合根)     │ 1   N │              │
│  shipment_no │       │ allocation_id──→ Inventory.Allocation
│  status      │       │ batch_id ──────→ Inventory.Batch
│  warehouse_id│       │ qty_shipped   │
│  carrier     │       │ qty_delivered │
└──────────────┘       └──────────────┘
```

Shipment 只引用 Inventory 的数据（通过 FK），不通过 Service 调用。

---

## 三、表定义

### 3.1 Shipment（发运单 —— 聚合根）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| shipment_no | str(30) | UNIQUE, SH-YYYYMMDD-{seq} |
| warehouse_id | UUID | FK→Warehouse |
| customer_id | UUID | FK→BusinessPartner |
| carrier | str(100) | nullable, 承运人 |
| vehicle_no | str(30) | nullable, 车号 |
| container_no | str(30) | nullable, 柜号 |
| loading_date | str(10) | nullable, 装货日期 |
| delivery_address | str(255) | nullable, 送货地址 |
| tracking_no | str(50) | nullable, 运单号 |
| estimated_date | str(10) | nullable, 预计发运日期 |
| actual_date | str(10) | nullable, 实际发运日期 |
| status | str(20) | draft / confirmed / shipped / delivered / cancelled |
| total_qty | Decimal(18,4) | 发运总重量 |
| remark | str(500) | nullable |
| created_by | UUID | FK→User |
| confirmed_by | UUID | FK→User, nullable |
| created_at/updated_at | datetime | |

### 3.2 ShipmentLine（发运行）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| shipment_id | UUID | FK→Shipment |
| allocation_id | UUID | FK→Allocation, NOT NULL |
| batch_id | UUID | FK→Batch, nullable |
| warehouse_id | UUID | FK→Warehouse, NOT NULL |
| material_id | UUID | FK→Material |
| qty_shipped | Decimal(18,4) | 发运重量（吨） |
| qty_delivered | Decimal(18,4) | 实际送达重量（吨），初始 = qty_shipped |
| remark | str(255) | nullable |

**约束**: `(shipment_id, allocation_id)` 唯一 —— 同一发运单中对同一个 Allocation 不能重复发货。

---

## 四、状态流转

```
draft ──→ confirmed ──→ shipped ──→ delivered
  │          │            │
  └──────────┴────────────┘
          cancelled
```

| 状态 | 触发 | Event | Inventory 联动 |
|------|------|-------|---------------|
| draft | 创建 | - | - |
| confirmed | 物流确认 | `shipment.confirmed` | **无库存变化**——仅物流确认 |
| shipped | 实际发运 | `shipment.shipped` | ALLOCATED → COMMITTED |
| delivered | 送达确认 | `shipment.delivered` | COMMITTED → DELIVERED, WarehouseStock -qty |
| cancelled | 取消 | `shipment.cancelled` | 反向操作 |

---

## 五、EventBus 集成

### Shipment 发布事件

```
shipment.confirmed:
  → Inventory: Allocation.consumed（锁货进入交付流程）
  → Sales: SalesExecution.status = committed

shipment.shipped:
  → Inventory: WarehouseStock.on_hand -= qty, ContractStock.qty_shipped += qty
  → Inventory: Ledger DELIVERED +qty

shipment.cancelled:
  → Inventory: 反向（退回 WarehouseStock / 释放 Allocation）
```

### Inventory 不监听 Shipment 事件？

**否。** Shipment 发布事件，Inventory 消费。原因是 Shipment 是物流事实的发起方，Inventory 是被动的状态同步方。

```
Shipment.confirm()  →  publish(shipment.confirmed)  →  Inventory 监听
Shipment.ship()     →  publish(shipment.shipped)     →  Inventory 监听
```

---

## 六、业务场景

### 6.1 单次发货

```
SalesContract: 100t PET Clear Flake
Allocation: 100t (active)

Shipment: SH-001, 100t
  ShipmentLine: allocation_id=alloc-1, qty=100t

Shipment.confirm() → Allocation.consumed (100t)
Shipment.ship()    → WarehouseStock -100t, DELIVERED +100t
```

### 6.2 多次部分发货

```
SalesContract: 100t
Allocation: 100t (active)

Shipment SH-001: 60t
  → confirm + ship → 60t delivered, Allocation still 40t active

Shipment SH-002: 40t
  → confirm + ship → 40t delivered, Allocation fully consumed
```

### 6.3 多批次发货

```
Shipment SH-001:
  Line 1: allocation_id=alloc-1, batch_id=BATCH-A, qty=50t
  Line 2: allocation_id=alloc-2, batch_id=BATCH-B, qty=30t
```

---

## 七、权限

```
shipment.{create,read,update,confirm,ship,deliver,cancel}
shipment.line.{create,read,delete}
```

共 10 条。

---

## 八、模块结构

```
modules/shipment/
├── __init__.py
├── models.py
├── schemas.py
├── repository.py
├── service.py
├── router.py
└── events.py
```

---

## 九、API

```
POST   /api/v1/shipment/orders                    # 创建发运单
GET    /api/v1/shipment/orders                    # 发运单列表
GET    /api/v1/shipment/orders/{id}               # 详情（含 lines）
POST   /api/v1/shipment/orders/{id}/lines         # 添加行
POST   /api/v1/shipment/orders/{id}/confirm       # 确认
POST   /api/v1/shipment/orders/{id}/ship          # 发运
POST   /api/v1/shipment/orders/{id}/deliver       # 送达
POST   /api/v1/shipment/orders/{id}/cancel        # 取消
```

---

## 十、边界

| ✅ M5 | ❌ 不做 |
|-------|--------|
| 发运单 CRUD + 状态机 | 物流跟踪/轨迹 |
| 多批次/多次发货 | WMS 仓储管理 |
| EventBus 驱动 Inventory | 运费计算 |
| 10 条权限 + Seed | 发货通知/邮件 |

---

确认后进入 Coding。
