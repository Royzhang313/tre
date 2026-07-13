# M6 Core Hardening Design

> 状态: Review V1 | 日期: 2026-07-08
> 原则: 不破坏现有 Purchase/Sales/Inventory/EventBus 架构

---

## 一、Outbox Pattern —— DomainEvent 可靠发布

### 1.1 当前问题

```python
# Purchase/OrderService.confirm()
po.status = CONFIRMED
await self.po_repo.update(po)           # DB 写入成功
await event_bus.publish(POConfirmed())  # EventBus 发送成功

# 问题: 如果 EventBus 发送失败，DB 已提交，事件丢失。
# 反之: 如果外部消费者处理失败，事件已发出，无法重试。
```

### 1.2 Outbox 方案

```
Service.confirm()
    │
    ├── 1. 写入业务数据 (PO.status=confirmed)
    ├── 2. 写入 Outbox 表 (同一事务)
    └── 3. 提交事务
            │
            ▼ (事务提交后)
    OutboxDispatcher (后台轮询)
            │
            ├── 4. 读取 status=pending 的 Outbox 记录
            ├── 5. 发布到 EventBus
            ├── 6. 更新 Outbox.status=published
            └── 失败 → retry_count++, next_retry_at
```

### 1.3 Outbox 表

```python
class OutboxMessage(BaseModel):
    __tablename__ = "core_outbox"

    event_type: str          # "purchase.order.confirmed"
    aggregate_type: str      # "PurchaseOrder"
    aggregate_id: UUID
    payload: JSON            # 事件 payload (序列化的 DomainEvent)
    status: str              # pending / published / failed / dead
    retry_count: int = 0
    max_retries: int = 3
    last_error: str | None
    next_retry_at: datetime | None
    published_at: datetime | None
    created_at: datetime
```

### 1.4 集成方式

```python
# 现有 Service 代码不变，只需替换 publish 调用:
# 旧: await event_bus.publish(event)
# 新: await outbox.enqueue(event)  # 写入 Outbox 表，同一事务

class Outbox:
    @staticmethod
    async def enqueue(event: DomainEvent) -> OutboxMessage:
        """写入 Outbox（与业务数据同一 session）"""
        ...

    @staticmethod
    async def dispatch_pending() -> list[OutboxMessage]:
        """后台任务: 读取 pending → publish → 标记 published"""
        ...

# FastAPI lifespan:
# 启动后台 asyncio task: OutboxDispatcher (每 5 秒轮询)
```

### 1.5 与现有 EventBus 关系

- 保留 `EventBus.publish()` 用于**同步事件**（如测试、内部通知）
- 新增 `Outbox.enqueue()` 用于**异步可靠事件**（跨模块通信）
- EventLog 表继续记录**所有**事件（published 和 outbox 都写入 EventLog）

---

## 二、Module Registry —— AI Builder 元数据

### 2.1 设计目标

AI Builder 需要知道系统有哪些模块、每个模块有哪些实体、事件、权限，才能根据用户自然语言描述生成代码。

### 2.2 ModuleManifest

```python
@dataclass
class ModuleManifest:
    """模块元数据 —— AI Builder 的"系统地图" """
    name: str                    # "purchase"
    display_name: str            # "采购管理"
    version: str                 # "V2"
    entities: list[EntityMeta]   # 模块拥有的实体
    events_published: list[str]  # ["purchase.order.confirmed", ...]
    events_consumed: list[str]   # ["inventory.stock.received", ...]
    permissions: list[str]       # ["purchase.order.create", ...]
    dependencies: list[str]      # ["basedata", "auth"]
```

### 2.3 注册方式

每个模块的 `__init__.py` 声明自己的 Manifest：

```python
# modules/purchase/__init__.py
from app.shared.module_registry import ModuleManifest, register_module

MANIFEST = ModuleManifest(
    name="purchase",
    display_name="采购管理",
    version="V2",
    entities=[
        EntityMeta.from_orm(PurchaseOrder),
        EntityMeta.from_orm(PurchaseLine),
        EntityMeta.from_orm(GoodsReceipt),
        EntityMeta.from_orm(GoodsReceiptLine),
    ],
    events_published=[
        "purchase.order.confirmed",
        "purchase.order.cancelled",
        "purchase.receipt.confirmed",
        "purchase.receipt.reversed",
    ],
    events_consumed=[],
    permissions=[...],
    dependencies=["basedata", "auth", "inventory"],
)

register_module(MANIFEST)
```

### 2.4 API

```
GET /api/v1/system/modules         → 所有模块列表
GET /api/v1/system/modules/{name}  → 模块详情 (含实体)
GET /api/v1/system/entities        → 所有实体
GET /api/v1/system/events          → 所有事件
```

---

## 三、Entity Metadata 模型

### 3.1 EntityMeta

```python
@dataclass
class EntityMeta:
    """实体元数据"""
    name: str                    # "PurchaseOrder"
    display_name: str            # "采购订单"
    table_name: str              # "purchase_orders"
    module: str                  # "purchase"
    is_aggregate_root: bool      # True
    fields: list[FieldMeta]
    relationships: list[RelationMeta]

@dataclass
class FieldMeta:
    name: str                    # "po_no"
    type: str                    # "str(30)"
    required: bool
    unique: bool
    description: str             # "采购单号"

@dataclass
class RelationMeta:
    name: str                    # "lines"
    target_entity: str           # "PurchaseLine"
    relation_type: str           # "one_to_many"
    foreign_key: str             # "po_id"
```

### 3.2 自动生成

```python
class EntityMeta:
    @classmethod
    def from_orm(cls, model: type[BaseModel]) -> "EntityMeta":
        """从 SQLAlchemy 模型自动生成元数据"""
        fields = []
        for col in model.__table__.columns:
            fields.append(FieldMeta(
                name=col.name,
                type=str(col.type),
                required=not col.nullable,
                unique=col.unique or False,
                description=col.comment or "",
            ))
        return cls(
            name=model.__name__,
            display_name=model.__doc__ or model.__name__,
            table_name=model.__tablename__,
            module=model.__module__.split(".")[2],
            fields=fields,
            ...
        )
```

---

## 四、Allocation 泛化 Review

### 4.1 现状 (V3)

```python
class Allocation(BaseModel):
    allocation_type: str     # "sales" | "customer_hold" | "internal_reserve" | "consignment"
    source_type: str         # "SalesContract" | "Manual" | "Transfer"
    source_id: UUID
    source_line_id: UUID | None
```

### 4.2 场景覆盖检查

| 场景 | allocation_type | source_type | source_id | 当前支持 |
|------|----------------|-------------|-----------|---------|
| 销售锁货 | `sales` | `SalesContract` | SC.id | ✅ |
| 客户暂存 | `customer_hold` | `Manual` | User.id | ✅ |
| 内部预留 | `internal_reserve` | `Manual` | User.id | ✅ |
| 寄售 | `consignment` | `ConsignmentContract`(未来) | CC.id | 🔮 |
| 质检冻结 | `quality_hold` | `InspectionOrder`(未来) | IO.id | 🔮 |
| 采购退货暂存 | `return_hold` | `PurchaseReturn`(未来) | PR.id | 🔮 |

**结论**: 当前 Allocation 模型已足够泛化，不需要修改。新场景只需新增 allocation_type 枚举值 + source_type 字符串。

### 4.3 建议补充

在 `AllocationStatus` 中增加 `suspended` 状态（暂挂），用于质检冻结等场景：

```python
class AllocationStatus(enum.StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"   # 🆕 暂挂（质检冻结等）
    RELEASED = "released"
    CONSUMED = "consumed"
```

---

## 五、实现优先级

| 优先级 | 项目 | 影响范围 | 风险 |
|--------|------|---------|------|
| **P0** | Outbox Pattern | OutboxMessage 表 + Outbox 类 + main.py 后台任务 | 低（新增表，不修改现有 Service 签名） |
| **P1** | Module Registry | ModuleManifest + register_module() + API | 低（纯新增，不影响现有代码） |
| **P2** | Entity Metadata | EntityMeta.from_orm() 自动生成 | 低 |
| **P2** | Allocation +suspended | AllocationStatus 枚举 | 低（新增枚举值） |

---

## 六、不做什么

- ❌ 不修改 Purchase/Sales/Inventory Service 签名
- ❌ 不改变 EventBus 现有 publish/subscribe 接口
- ❌ 不引入消息队列（Outbox 使用 DB 轮询，M7 可升级为 MQ）
- ❌ 不修改 Allocation 核心模型（仅增加一个枚举值）

---

确认后按 P0→P1→P2 进入 M6 Coding。
