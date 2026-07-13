# Event Catalog —— PET 瓶片贸易 ERP

> 状态: Review V1 | 日期: 2026-07-07
> 基于: Supply Chain V3 Final Design

---

## 一、事件契约规则

1. **模块间禁止 Service 调用** —— 只能通过 DomainEvent + EventBus
2. **幂等** —— 消费者检查 `consumer + event_id`，重复事件不处理
3. **事件不可变** —— 发布后不修改，错误通过新事件补偿（如 reversed）
4. **命名** —— `{domain}.{aggregate}.{action}` 格式

---

## 二、完整事件清单

### 2.1 Purchase 域（发布方）

| # | event_type | aggregate_type | producer | consumer | 阶段 |
|---|-----------|---------------|----------|----------|------|
| E1 | `purchase.order.confirmed` | PurchaseOrder | Purchase.OrderService.confirm() | Inventory.ContractStockService | PO确认后创建货权 |
| E2 | `purchase.order.cancelled` | PurchaseOrder | Purchase.OrderService.cancel() | Inventory.ContractStockService | PO取消后释放货权 |
| E3 | `purchase.receipt.confirmed` | GoodsReceipt | Purchase.ReceiptService.confirm() | Inventory.BatchService | 收货→在途转在仓 |
| E4 | `purchase.receipt.reversed` | GoodsReceipt | Purchase.ReceiptService.reverse() | Inventory.BatchService | 收货冲销→反向记账 |

### 2.2 Inventory 域（发布方 + 消费方）

**发布**:

| # | event_type | aggregate_type | producer | consumer | 阶段 |
|---|-----------|---------------|----------|----------|------|
| E5 | `inventory.stock.received` | Batch | Inventory.BatchService.receive() | Audit, Sales.ExecutionService | 入库完成通知 |
| E6 | `inventory.allocation.created` | Allocation | Inventory.AllocationService.allocate() | Sales.ExecutionService | 锁货完成 |
| E7 | `inventory.allocation.released` | Allocation | Inventory.AllocationService.release() | Sales.ExecutionService | 锁货释放 |
| E8 | `inventory.allocation.consumed` | Allocation | Inventory.AllocationService (CommitListener) | Sales.ExecutionService | 锁货进入交付 |

**消费**:

| # | 消费事件 | handler |
|---|---------|---------|
| E1 | `purchase.order.confirmed` | ContractStockService.on_po_confirmed() |
| E3 | `purchase.receipt.confirmed` | BatchService.on_goods_received() |
| E4 | `purchase.receipt.reversed` | BatchService.on_goods_reversed() |
| E9 | `sales.contract.confirmed` | AllocationService.on_sales_confirmed() |

### 2.3 Sales 域（发布方 + 消费方）

**发布**:

| # | event_type | aggregate_type | producer | consumer | 阶段 |
|---|-----------|---------------|----------|----------|------|
| E9 | `sales.contract.confirmed` | SalesContract | Sales.ContractService.confirm() | Inventory.AllocationService | 合同确认→锁货 |
| E10 | `sales.contract.cancelled` | SalesContract | Sales.ContractService.cancel() | Inventory.AllocationService | 合同取消→释放锁货 |
| E11 | `sales.execution.updated` | SalesExecution | Sales.ExecutionService | Audit | 执行状态变更 |

**消费**:

| # | 消费事件 | handler |
|---|---------|---------|
| E6 | `inventory.allocation.created` | ExecutionService.on_allocated() |
| E7 | `inventory.allocation.released` | ExecutionService.on_released() |
| E8 | `inventory.allocation.consumed` | ExecutionService.on_consumed() |
| E5 | `inventory.stock.received` | ExecutionService (记录可用库存变化) |

---

## 三、Event Payload Schema

### E1: purchase.order.confirmed

```json
{
  "event_type": "purchase.order.confirmed",
  "aggregate_type": "PurchaseOrder",
  "aggregate_id": "uuid-po-xxx",
  "trace_id": "trace-xxx",
  "po_id": "uuid-po-xxx",
  "po_no": "PO-20260707-0001",
  "supplier_id": "uuid-bp-xxx",
  "lines": [
    {
      "material_id": "uuid-mat-xxx",
      "qty_ordered": "100.0000",
      "unit_price": "8500.0000",
      "currency_id": "uuid-cny-xxx"
    }
  ]
}
```

### E3: purchase.receipt.confirmed

```json
{
  "event_type": "purchase.receipt.confirmed",
  "aggregate_type": "GoodsReceipt",
  "aggregate_id": "uuid-gr-xxx",
  "receipt_id": "uuid-gr-xxx",
  "receipt_no": "GR-20260707-0001",
  "po_id": "uuid-po-xxx",
  "supplier_id": "uuid-bp-xxx",
  "warehouse_id": "uuid-wh-xxx",
  "received_date": "2026-07-07",
  "received_by": "uuid-user-xxx",
  "lines": [
    {
      "material_id": "uuid-mat-xxx",
      "qty": "100.0000",
      "unit_price": "8500.0000",
      "warehouse_id": "uuid-wh-xxx",
      "location_id": null
    }
  ]
}
```

### E6: inventory.allocation.created

```json
{
  "event_type": "inventory.allocation.created",
  "aggregate_type": "Allocation",
  "aggregate_id": "uuid-alloc-xxx",
  "allocation_id": "uuid-alloc-xxx",
  "contract_stock_id": "uuid-cs-xxx",
  "batch_id": null,
  "customer_id": "uuid-bp-xxx",
  "allocation_type": "sales",
  "source_type": "SalesContract",
  "source_id": "uuid-sc-xxx",
  "source_line_id": "uuid-line-xxx",
  "qty": "100.0000"
}
```

### E9: sales.contract.confirmed

```json
{
  "event_type": "sales.contract.confirmed",
  "aggregate_type": "SalesContract",
  "aggregate_id": "uuid-sc-xxx",
  "contract_id": "uuid-sc-xxx",
  "contract_no": "SC-20260707-0001",
  "customer_id": "uuid-bp-xxx",
  "lines": [
    {
      "material_id": "uuid-mat-xxx",
      "qty": "100.0000",
      "unit_price": "9000.0000"
    }
  ]
}
```

---

## 四、幂等保证

### 消费者幂等

```python
# EventConsumerLog 记录每个 (event_id, consumer) 的处理状态
class EventConsumerLog:
    event_id: UUID
    consumer: str       # "Inventory.AllocationService"
    status: str         # "processed"

# EventBus 检查
if event_bus.is_consumer_processed(event_id, "Inventory.AllocationService"):
    return  # 已处理，跳过
```

### Producer 幂等

```python
# InventoryTransaction.idempotency_key 保证同一业务操作不重复
idempotency_key = f"{reference_type}:{reference_id}:{tx_type}"
# 例如: "purchase_order:uuid-po-xxx:receive"
```

---

## 五、事件流向总图

```
                    ┌──────────┐
                    │ Purchase │
                    └────┬─────┘
                         │ E1,E2,E3,E4
                         ▼
                    ┌──────────┐
            ┌──────│Inventory │──────┐
            │       └──────────┘      │
            │ E5,E6,E7,E8            │ E5,E6,E7,E8
            ▼                        ▼
       ┌──────────┐            ┌──────────┐
       │  Sales   │            │  Audit   │
       │          │            │  (未来)   │
       │ E9,E10   │            └──────────┘
       │ E11      │
       └────┬─────┘
            │ E9,E10
            ▼
       ┌──────────┐
       │Inventory │ (AllocationService)
       └──────────┘
```

---

## 六、P2 Coding 范围

| 文件 | 内容 |
|------|------|
| `modules/inventory/listeners.py` | 🆕 监听 Purchase/Sales 事件，创建 ContractStock/Allocation |
| `modules/sales/listeners.py` | 🆕 监听 Inventory 事件，更新 SalesExecution |
| `modules/sales/service.py` | ✏️ confirm() 创建 SalesExecution (pending) |
| `modules/inventory/events.py` | 🆕 发布 inventory.* 事件 |

---

确认后进入 P2 Coding。
