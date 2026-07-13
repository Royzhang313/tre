# M3-3 Purchase V2 —— 架构设计

> 状态: Review V2 | 日期: 2026-07-07
> 基于: SupplyChain Flow Design

---

## 一、设计原则

Purchase V2 **不修旧模型，完全重建**。

核心变更：
- Purchase **不直接调用 Inventory Service**
- 所有库存变更通过 **EventBus + InventoryTransaction + Ledger** 完成
- PO 确认 → 发布事件 → Inventory 创建货权
- Receipt 确认 → 发布事件 → Inventory 在途转在仓
- Purchase 只管理自己的数据（PO / Receipt）

---

## 二、实体

### 2.1 PurchaseOrder

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| po_no | str(30) | UNIQUE, 自动: PO-YYYYMMDD-{seq} |
| supplier_id | UUID | FK→BusinessPartner |
| order_date | str(10) | |
| expected_date | str(10) | nullable |
| currency_id | UUID | FK→Currency |
| total_amount | Decimal(18,2) | |
| status | str(20) | draft / confirmed / partial / complete / cancelled / closed |
| remark | str(500) | nullable |
| created_by | UUID | FK→User |
| confirmed_by | UUID | FK→User, nullable |
| confirmed_at | datetime | nullable |
| created_at/updated_at | datetime | |

### 2.2 PurchaseLine

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| po_id | UUID | FK→PurchaseOrder |
| line_no | int | |
| material_id | UUID | FK→Material |
| qty_ordered | Decimal(18,4) | 订购重量（吨） |
| qty_received | Decimal(18,4) | 已收重量 |
| unit_id | UUID | FK→Unit |
| unit_price | Decimal(18,4) | |
| currency_id | UUID | FK→Currency |
| amount | Decimal(18,2) | |
| expected_date | str(10) | nullable |
| status | str(20) | open / partial / complete / cancelled |
| remark | str(255) | nullable |

### 2.3 GoodsReceipt

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| receipt_no | str(30) | UNIQUE, GR-YYYYMMDD-{seq} |
| po_id | UUID | FK→PurchaseOrder |
| warehouse_id | UUID | FK→Warehouse |
| receipt_date | str(10) | |
| status | str(20) | draft / confirmed / reversed / cancelled |
| total_qty | Decimal(18,4) | |
| remark | str(500) | nullable |
| received_by | UUID | FK→User |

### 2.4 GoodsReceiptLine

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| receipt_id | UUID | FK→GoodsReceipt |
| po_line_id | UUID | FK→PurchaseLine |
| material_id | UUID | FK→Material |
| qty_received | Decimal(18,4) | 申报收货量 |
| actual_qty | Decimal(18,4) | 实际收货量（过磅） |
| unit_price | Decimal(18,4) | PO 原始单价 |
| actual_unit_price | Decimal(18,4) | 实际单价 |
| warehouse_id | UUID | FK→Warehouse |
| location_id | UUID | nullable |
| remark | str(255) | nullable |

**不再有 batch_id 字段** —— Inventory 管理 Batch，Purchase 不持有 Batch 引用。

---

## 三、Purchase → EventBus → Inventory

### 3.1 PO 确认

```
PO.confirm()
    │
    ├── PO.status = confirmed
    └── publish(POConfirmed):
        {
          po_id, supplier_id,
          lines: [{material_id, qty_ordered, unit_price, currency_id}]
        }
            │
            ▼ (Inventory 监听)
        ContractStockService.on_po_confirmed()
            │
            ├── ContractStock 创建 (qty_in_transit = qty_ordered)
            ├── InventoryTransaction (tx_type=receive)
            └── Ledger: IN_TRANSIT +qty
```

### 3.2 Receipt 确认

```
Receipt.confirm()
    │
    ├── Receipt.status = confirmed
    ├── 更新 PO Line.qty_received
    ├── 更新 PO 状态
    └── publish(GoodsReceived):
        {
          receipt_id, po_id,
          lines: [{material_id, qty, warehouse_id, location_id, ...}]
        }
            │
            ▼ (Inventory 监听)
        BatchService.on_goods_received()
            │
            ├── ContractStock: in_transit -qty, in_warehouse +qty
            ├── Batch + BatchSource 创建
            ├── WarehouseStock 创建
            ├── InventoryTransaction (tx_type=receive)
            └── Ledger: IN_WAREHOUSE +qty, IN_TRANSIT -qty
```

---

## 四、Service 设计

### PurchaseOrderService
- create / add_line / confirm / cancel / close / update_price
- confirm() → 更新状态 + **发布 POConfirmed 事件**
- cancel() → 检查无收货后可取消

### GoodsReceiptService
- create / add_line / confirm / reverse
- confirm() → 更新 PO Line + **发布 GoodsReceived 事件**
- reverse() → 发布 GoodsReversed 事件（Inventory 监听后反向记账）
- **不调用 BatchService.receive()**

---

## 五、权限

```
purchase.order.{create,read,update,confirm,cancel,close}
purchase.line.{create,read,delete}
purchase.receipt.{create,read,confirm,reverse}
purchase.receipt-line.{create,read}
purchase.price.{read,update}
```

共 17 条。

---

## 六、模块结构

```
modules/purchase/
├── __init__.py
├── models.py            # PO / POLine / GoodsReceipt / ReceiptLine
├── schemas.py
├── repository.py
├── service.py           # 不含 Inventory 调用
├── router.py
└── events.py            # 领域事件定义 + 发布
```

---

## 七、与 V1 的核心差异

| V1 | V2 |
|----|----|
| GoodsReceiptLine.batch_id | ❌ 移除（Inventory 管理 Batch） |
| Receipt.confirm() → BatchService.receive() | Receipt.confirm() → publish(GoodsReceived) |
| Purchase 直接 import Inventory Service | Purchase 只发布 Event |
| PO.confirm() 只改状态 | PO.confirm() + publish(POConfirmed) |

---

确认后进入 Coding。
