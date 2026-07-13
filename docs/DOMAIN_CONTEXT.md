# Domain Context —— PET 瓶片贸易 ERP

> 每个 Phase 开始前必须重新阅读本文，确保设计不偏离业务场景。

---

## 一、业务定位

**PET 瓶片贸易 ERP 系统**。

不是制造 ERP。不是 SAP 通用 ERP。不做无边界抽象。

### 核心流程

```
采购 → 入库 → 库存 → 销售 → 出库 → 物流 → 结算
```

### 业务特点

- 大宗商品贸易（Bulk Commodity Trading）
- 计量单位：**吨（t）**
- 同一个品种可以有多个批次，分别来自不同供应商、不同价格、不同入库时间
- 库存管理核心维度：**(品种 + 批次 + 仓库)**
- 销售前可以**锁货**（为客户锁定特定批次的库存）

---

## 二、需要做的

| 概念 | 说明 |
|------|------|
| Material（品种） | PET Clear Flake / Blue Flake / Green Flake 等，用名称+等级+产地描述 |
| Batch/Lot（批次） | 不同供应商、不同采购价、不同入库时间的同一品种 = 不同批次 |
| Grade（等级） | A / B / C / 特级 / 一级 / 二级 |
| Origin（产地） | 日本 / 泰国 / 中国回收 等 |
| Trade Type | virgin（原生）/ recycled（回收）/ flake（瓶片） |
| Stock（库存） | 以 (batch_id, warehouse_id, location_id) 为粒度 |
| Reservation（锁货） | 销售订单确认前/后为客户锁定特定批次的库存 |
| Weight（重量） | 统一用吨（t），Decimal(18,4) |
| Quality JSON | PET 指标：IV 值、水分、PVC 含量、熔点、颜色等 |
| Transfer（调拨） | 批次从一个仓库转移到另一个仓库 |
| Supplier | 引用 BaseData.BusinessPartner（bp_type=supplier） |
| Customer | 引用 BaseData.BusinessPartner（bp_type=customer） |

---

## 三、不需要做的

以下概念**不属于本系统**，禁止超前设计：

- ❌ SKU / 条码管理体系
- ❌ 生产工单（Production Order）
- ❌ BOM（物料清单）
- ❌ 生产领料 / 投料
- ❌ 制造属性（工艺路线、工作中心）
- ❌ 多单位换算（吨是唯一单位）
- ❌ 序列号管理
- ❌ 复杂 WMS（仓储管理系统）

**如果某个设计看起来像是在做"通用 ERP"或"制造 ERP"，停下来重新读第一条。**

---

## 四、关键业务规则

1. **品种不设唯一约束** —— name/grade/origin 是业务属性，由用户在 UI 层管理
2. **批次是库存核心维度** —— 查询库存、锁货、出库都要指定批次
3. **一个批次可以分布在多个仓库** —— 通过 Stock 表 (batch_id, warehouse_id) 关联
4. **库存变更只追加** —— StockTransaction 只增不删不改，idempotency_key 幂等
5. **锁货是销售行为** —— Reservation 关联 customer + sales_order，不是制造预留
6. **Supplier/Customer 统一** —— 都引用 BaseData.BusinessPartner，用 bp_type 区分

---

## 五、模块开发状态

| Phase | 模块 | 状态 |
|-------|------|------|
| M0 | Project Skeleton | ✅ |
| M1 | Shared Kernel | ✅ |
| M2 | Auth (RBAC) | ✅ |
| M3-1 | BaseData (Company/Dept/Employee/Warehouse/Unit/Currency/Category/BP) | ✅ |
| M3-2 | Inventory Core (Material/Batch/Stock/Transaction/Reservation) | 🔄 V1.3 待 Coding |
| M3-3 | Purchase (Supplier/PO/Receipt) | ⬜ |
| M4 | Sales / Document / Template | ⬜ |
| M5 | Shipment / Workflow | ⬜ |
| M6 | Finance | ⬜ |
| M7 | Settlement / Logistics | ⬜ |

---

## 六、术语表

| 中文 | 英文 | 说明 |
|------|------|------|
| 品种 | Material | PET 瓶片贸易品种 |
| 批次 | Batch / Lot | 同一品种的不同入库批次 |
| 等级 | Grade | A/B/C |
| 产地 | Origin | 国家/地区 |
| 吨 | Ton (t) | 统一计量单位 |
| 锁货 | Reservation | 销售库存占用 |
| 调拨 | Transfer | 仓库间转移 |
| 业务伙伴 | BusinessPartner | 供应商或客户 |
| 在手量 | qty_on_hand | 当前仓库实际库存 |
| 已锁量 | qty_reserved | 已承诺给客户的数量 |
| 可用量 | qty_available | on_hand - reserved |
| 入库 | Receive | 采购到货入库 |
| 出库 | Ship | 销售发货出库 |
