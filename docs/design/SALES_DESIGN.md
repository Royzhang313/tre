# M4 Sales 模块 —— 架构设计

> 状态: Review V1 | 日期: 2026-07-07
> 业务: PET 瓶片贸易 ERP

---

## 一、模块定位

Sales 是贸易销售管理。通过 EventBus 驱动 Inventory（锁货/出库）。

**原则**：Sales 不操作 Inventory 表。Supplier/Customer 统一引用 BP。

---

## 二、实体

### 2.1 SalesContract（销售合同 —— 聚合根）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| contract_no | str(30) | UNIQUE, SC-YYYYMMDD-{seq} |
| customer_id | UUID | FK→BusinessPartner |
| contract_date | str(10) | |
| currency_id | UUID | FK→Currency |
| total_amount | Decimal(18,2) | |
| status | str(20) | draft/confirmed/allocated/committed/partial_shipped/delivered/cancelled/closed |
| remark | str(500) | nullable |
| created_by / confirmed_by | UUID | FK→User |
| created_at/updated_at | datetime | |

### 2.2 SalesContractLine

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | PK |
| contract_id | UUID | FK→SalesContract |
| line_no | int | |
| material_id | UUID | FK→Material |
| qty_ordered | Decimal(18,4) | 销售重量（吨） |
| qty_allocated | Decimal(18,4) | 已锁重量 |
| qty_shipped | Decimal(18,4) | 已发运重量 |
| unit_price | Decimal(18,4) | |
| currency_id | UUID | FK→Currency |
| amount | Decimal(18,2) | |
| status | str(20) | open/partial/complete/cancelled |

---

## 三、状态流转

```
draft → confirmed → allocated → committed → partial_shipped → delivered → closed
  │        │           │            │              │
  └────────┴───────────┴────────────┴──────────────┴──→ cancelled
```

| 状态 | 触发 | Inventory 联动 |
|------|------|---------------|
| draft | 创建 | - |
| confirmed | 确认合同 | publish(SalesContractConfirmed) → Inventory.Allocation |
| allocated | Inventory 回调 | Inventory 锁货完成 |
| committed | 客户确认 | publish(SalesContractCommitted) → Allocation.committed |
| partial_shipped | 部分发运 | publish(ShipmentConfirmed) → DELIVERED |
| delivered | 全部发运 | - |
| closed | 手动关结 | - |

---

## 四、EventBus 集成

```
SalesContract.confirm()
    │
    └── publish(SalesContractConfirmed)

Sales 确认后，Inventory 监听并创建 Allocation（锁货）。
发运由 M5 Shipment 模块触发。
```

---

## 五、权限

```
sales.contract.{create,read,update,confirm,cancel,close}
sales.line.{create,read,delete}
sales.price.{read,update}
```

---

## 六、模块结构

```
modules/sales/
├── __init__.py
├── models.py
├── schemas.py
├── repository.py
├── service.py
├── router.py
└── events.py
```

---

确认后进入 Coding。
