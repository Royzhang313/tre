# Supply Chain E2E Test —— PET 瓶片贸易完整链路验证

> 状态: Review V1 | 日期: 2026-07-08
> 目标: 不新增模型，验证现有模块全链路 Event + 数据一致性

---

## 一、测试场景

```
供应商 A → 采购 1000吨 PET Clear Flake → 入库 → 
客户 B 购买 600吨 → 锁货 → 分两次发运 (300t + 300t)
```

---

## 二、完整链路步骤

### Step 1: 采购合同 (Purchase)

```
1.1 创建 PO
    POST /api/v1/purchase/orders
    {
      supplier_id: <SupplierA>,
      order_date: "2026-07-08",
      currency_id: <CNY>,
      incoterm: "CIF",
      payment_term: "LC at sight"
    }
    → PO.status = draft, po_no = PO-20260708-0001

1.2 添加 PO 行
    POST /api/v1/purchase/orders/{po_id}/lines
    {
      material_id: <PET_Clear_Flake>,
      qty_ordered: 1000,
      unit_price: 8500,
      currency_id: <CNY>
    }

1.3 确认 PO
    POST /api/v1/purchase/orders/{po_id}/confirm
    → PO.status = confirmed
    → EventBus.publish(PurchaseOrderConfirmed)

    预期:
    Inventory 监听 → ContractStock 创建
      material_id = <PET_Clear_Flake>
      supplier_id = <SupplierA>
      qty_contracted = 1000
      qty_in_transit = 1000
      qty_in_warehouse = 0

    验证点:
    ✅ PO.status == "confirmed"
    ✅ ContractStock.qty_in_transit == 1000
    ✅ InventoryLedger 存在 IN_TRANSIT +1000
```

### Step 2: 收货入库 (Purchase → Inventory)

```
2.1 创建收货单
    POST /api/v1/purchase/receipts
    {
      po_id: <po_id>,
      warehouse_id: <WH-A>,
      receipt_date: "2026-07-08"
    }

2.2 添加收货行
    POST /api/v1/purchase/receipts/{receipt_id}/lines
    {
      po_line_id: <line_id>,
      actual_qty: 1000,
      actual_unit_price: 8520,
      warehouse_id: <WH-A>
    }

2.3 确认收货
    POST /api/v1/purchase/receipts/{receipt_id}/confirm
    → EventBus.publish(GoodsReceiptConfirmed)

    预期:
    Inventory 监听 → BatchService.receive()
      ContractStock.qty_in_transit = 0
      ContractStock.qty_in_warehouse = 1000
      Batch: batch_no = 20260708-xxx, qty_received = 1000
      WarehouseStock: qty_on_hand = 1000

    验证点:
    ✅ ContractStock.qty_in_transit == 0
    ✅ ContractStock.qty_in_warehouse == 1000
    ✅ Batch 创建且 qty_received == 1000
    ✅ WarehouseStock.qty_on_hand == 1000
    ✅ InventoryLedger: IN_TRANSIT 1000→0 (change -1000), IN_WAREHOUSE 0→1000 (change +1000)
```

### Step 3: 销售合同 (Sales)

```
3.1 创建 SC
    POST /api/v1/sales/contracts
    {
      customer_id: <CustomerB>,
      contract_date: "2026-07-08",
      currency_id: <CNY>
    }

3.2 添加行
    POST /api/v1/sales/contracts/{sc_id}/lines
    {
      material_id: <PET_Clear_Flake>,
      qty_ordered: 600,
      unit_price: 9000,
      currency_id: <CNY>
    }

3.3 确认 SC
    POST /api/v1/sales/contracts/{sc_id}/confirm
    → SC.status = confirmed
    → EventBus.publish(SalesContractConfirmed)

    预期:
    Inventory 监听 → AllocationService.allocate()
      Allocation: allocation_type="sales", source_type="SalesContract"
      Allocation.status = active, qty = 600
    Inventory 发布 → InventoryAllocationCreated
    Sales 监听 → SalesExecution 创建
      SalesExecution: allocated_qty=600, status=allocated

    验证点:
    ✅ SC.status == "confirmed"
    ✅ Allocation 存在且 allocation_type="sales", qty=600, status=active
    ✅ Allocation.source_type == "SalesContract"
    ✅ SalesExecution.allocated_qty == 600
    ✅ SalesExecution.status == "allocated"
    ✅ InventoryLedger: ALLOCATED +600
```

### Step 4: 第一次发运 300吨 (Shipment)

```
4.1 创建 Shipment SH-001
    POST /api/v1/shipment/orders
    {
      warehouse_id: <WH-A>,
      customer_id: <CustomerB>,
      carrier: "ABC Logistics",
      vehicle_no: "沪A12345",
      container_no: "TEXU1234567"
    }

4.2 添加行
    POST /api/v1/shipment/orders/{sh1_id}/lines
    {
      allocation_id: <alloc_id>,
      batch_id: <batch_id>,
      warehouse_id: <WH-A>,
      material_id: <PET_Clear_Flake>,
      qty_shipped: 300
    }

4.3 物流确认（不改变库存）
    POST /api/v1/shipment/orders/{sh1_id}/confirm
    → SH-001.status = confirmed

    验证点:
    ✅ Shipment.status == "confirmed"
    ✅ WarehouseStock.qty_on_hand == 1000 (未变)

4.4 发运（ALLOCATED → COMMITTED）
    POST /api/v1/shipment/orders/{sh1_id}/ship
    → SH-001.status = shipped
    → EventBus.publish(ShipmentShipped)

    预期:
    Inventory 监听 → Allocation 部分 consumed (300t 进入 COMMITTED)
    Sales 监听 → SalesExecution.committed_qty=300

    验证点:
    ✅ Shipment.status == "shipped"
    ✅ Allocation 剩余 active qty = 300 (600-300 已 committed)
    ✅ SalesExecution.committed_qty == 300
    ✅ WarehouseStock.qty_on_hand == 1000 (仍未变)

4.5 送达（COMMITTED → DELIVERED，库存减少）
    POST /api/v1/shipment/orders/{sh1_id}/deliver
    → SH-001.status = delivered
    → EventBus.publish(ShipmentDelivered)

    预期:
    Inventory 监听 → WarehouseStock -300t, ContractStock.qty_shipped +300
    Sales 监听 → SalesExecution.shipped_qty=300

    验证点:
    ✅ WarehouseStock.qty_on_hand == 700
    ✅ ContractStock.qty_shipped == 300
    ✅ SalesExecution.shipped_qty == 300
    ✅ InventoryLedger: DELIVERED +300
```

### Step 5: 第二次发运 300吨 (Shipment)

```
5.1 创建 Shipment SH-002
    (同上 SH-001 流程，qty=300)

5.2 确认 → ship → deliver

    验证点:
    ✅ WarehouseStock.qty_on_hand == 400
    ✅ ContractStock.qty_shipped == 600
    ✅ SalesExecution.committed_qty == 600
    ✅ SalesExecution.shipped_qty == 600
    ✅ SalesExecution.status == "delivered"
    ✅ Allocation 全部 consumed
    ✅ PO.status: complete (qty_received == qty_shipped)
```

---

## 三、最终验证矩阵

### 3.1 数量一致性

| 账户 | 期望值 | 计算 |
|------|--------|------|
| ContractStock.qty_contracted | 1000 | PO 合同量 |
| ContractStock.qty_in_transit | 0 | 全部入库 |
| ContractStock.qty_in_warehouse | 1000 | 入库量 |
| ContractStock.qty_allocated | 0 | 全部 consumed |
| ContractStock.qty_shipped | 600 | 两次发运 |
| WarehouseStock.qty_on_hand | 400 | 1000 - 600 |
| Allocation.active qty | 0 | 全部 consumed |
| SalesExecution.allocated_qty | 600 | |
| SalesExecution.committed_qty | 600 | |
| SalesExecution.shipped_qty | 600 | |

### 3.2 InventoryLedger 完整性

| 步骤 | account_code | change_qty |
|------|-------------|------------|
| PO 确认 | IN_TRANSIT | +1000 |
| 收货入库 | IN_TRANSIT | -1000 |
| 收货入库 | IN_WAREHOUSE | +1000 |
| 锁货 | ALLOCATED | +600 |
| 发运 SH-001 | DELIVERED | +300 |
| 发运 SH-002 | DELIVERED | +300 |

### 3.3 Event 链路完整性

```
purchase.order.confirmed    → Inventory: ContractStock 创建 ✅
purchase.receipt.confirmed  → Inventory: IN_TRANSIT→IN_WAREHOUSE ✅
sales.contract.confirmed    → Inventory: Allocation 创建 ✅
inventory.allocation.created → Sales: SalesExecution 创建 ✅
shipment.shipped (×2)       → Inventory: ALLOCATED→COMMITTED ✅
shipment.delivered (×2)     → Inventory: WarehouseStock 扣减 ✅
```

### 3.4 模块隔离验证

| 模块 | 不应 import | 验证方式 |
|------|-----------|---------|
| Purchase | Inventory Service | grep `from app.modules.inventory.service` |
| Sales | Inventory Service | grep `from app.modules.inventory.service` |
| Shipment | Inventory Service | grep `from app.modules.inventory.service` |
| Inventory | Purchase/Sales Service | grep `from app.modules.(purchase|sales).service` |

---

## 四、测试实现方式

### 选项 A: Python 集成测试 (pytest + async)

```python
@pytest.mark.asyncio
async def test_e2e_purchase_to_delivery():
    # Step 1-5 全部通过 HTTP client 调用
    # 每个 Step 后 assert 状态
    pass
```

### 选项 B: 手动 API 测试 (通过 Swagger / curl)

### 选项 C: 仅验证模块隔离 + 数据模型正确性 (当前 198 条 pytest)

---

## 五、决策

选项 A 需要完整数据库环境 (PostgreSQL + Alembic migration)，当前不可用。

**建议**: 先完成 Code Review 级别验证：
1. ✅ ruff + mypy 通过
2. ✅ 198 条 pytest 模型测试通过
3. 补充 import 隔离检查脚本

PostgreSQL 就绪后补 E2E 集成测试。

---

确认后执行 Code Review 验证。
