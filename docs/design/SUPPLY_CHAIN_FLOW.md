# Supply Chain Flow Design —— PET 瓶片贸易

> 状态: Review V1 | 日期: 2026-07-07

---

## 一、三模块边界

```
┌──────────┐     EventBus      ┌───────────┐     EventBus      ┌──────────┐
│ Purchase │ ───────────────→  │ Inventory  │ ←─────────────── │  Sales   │
│  (M3-3)  │                   │  (M3-2)    │                  │  (M4)    │
└──────────┘                   └───────────┘                  └──────────┘
     │                              │                              │
     │ 采购合同                      │ 货权+实物                     │ 销售合同
     │ 收货单                        │ 批次+台账                     │ 锁货
     │                              │                              │
     └──────────────────────────────┴──────────────────────────────┘
                         BaseData (Company / BP / Warehouse / ...)
```

| 模块 | 职责 | 不做什么 |
|------|------|---------|
| **Purchase** | PO 合同管理、收货单、发布 Event | 不操作 Inventory 表 |
| **Inventory** | 货权库存、实物库存、批次、台账 | 不操作 PO/Receipt 表 |
| **Sales** (M4) | 销售合同、客户管理 | 不操作 Inventory 表（通过 Allocation 消费） |

---

## 二、EventBus 消息流

```
Purchase Module                    Inventory Module               Sales Module
───────────────                    ────────────────               ─────────────
PO.confirm()
    │
    ├── 更新 PO 状态
    └── publish(POConfirmed)
                                        │
                                        ▼
                                   ContractStockService
                                   .on_po_confirmed()
                                        │
                                        ├── ContractStock 创建
                                        ├── InventoryTransaction
                                        └── Ledger: IN_TRANSIT +qty

Receipt.confirm()
    │
    ├── 更新 Receipt 状态
    └── publish(GoodsReceived)
                                        │
                                        ▼
                                   BatchService
                                   .on_goods_received()
                                        │
                                        ├── ContractStock: in_transit→in_warehouse
                                        ├── Batch + BatchSource 创建
                                        ├── WarehouseStock 创建
                                        ├── InventoryTransaction
                                        └── Ledger: IN_WAREHOUSE +qty, IN_TRANSIT -qty

                                                                  SalesContract.confirm()
                                                                      │
                                                                      └── publish(SalesContractConfirmed)
                                                                              │
                                                                              ▼
                                                                         AllocationService
                                                                         .on_sales_contract()
                                                                              │
                                                                              ├── Allocation 创建
                                                                              ├── InventoryTransaction
                                                                              └── Ledger: ALLOCATED +qty

                                                                  Shipment.confirm()
                                                                      │
                                                                      └── publish(ShipmentConfirmed)
                                                                              │
                                                                              ▼
                                                                         BatchService
                                                                         .on_shipment()
                                                                              │
                                                                              ├── ContractStock: shipped+qty
                                                                              ├── WarehouseStock: on_hand-qty
                                                                              ├── InventoryTransaction
                                                                              └── Ledger: DELIVERED +qty
```

---

## 三、事件定义

| 事件 | 发布方 | 载荷 | 消费方 |
|------|--------|------|--------|
| `POConfirmed` | Purchase | po_id, supplier_id, lines[{material_id, qty}] | Inventory |
| `GoodsReceived` | Purchase | receipt_id, po_id, lines[{material_id, qty, warehouse_id, ...}] | Inventory |
| `SalesContractConfirmed` | Sales (M4) | contract_id, customer_id, lines[{material_id, qty}] | Inventory |
| `ShipmentConfirmed` | Sales (M5) | shipment_id, contract_id, lines[{batch_id, qty, warehouse_id}] | Inventory |

---

## 四、库存账户流转全链路

```
POConfirmed
    │
    ▼
IN_TRANSIT +100t          (货权增加: 已采购未入库)
    │
    │ GoodsReceived
    ▼
IN_TRANSIT -100t          (在途减少)
IN_WAREHOUSE +100t        (在仓增加: 已入库可用)
    │
    │ SalesContractConfirmed
    ▼
ALLOCATED +50t            (承诺给客户: 锁货)
    │
    │ ShipmentConfirmed
    ▼
IN_WAREHOUSE -50t         (在仓减少)
ALLOCATED -50t            (承诺释放)
DELIVERED +50t            (已交付)
```

---

## 五、模块开发顺序

```
1. Inventory V2.3 ✅ (已完成)
2. SupplyChain Flow Design ✅ (本文档)
3. Purchase V2 (EventBus 发布方)
4. Purchase → Inventory EventBus 集成
5. M4 Sales (EventBus 发布方 + Allocation 消费)
```

---

确认后进入 Purchase V2 Architecture Design。
