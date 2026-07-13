# Capability Registry Design

> 状态: Review V1 | 日期: 2026-07-08
> 目标: AI Agent 发现和调用系统能力的统一接口

---

## 一、Capability 概念

Capability = 系统对外暴露的**可调用业务能力**。AI Agent 通过 Capability Registry 知道系统能做什么，然后调用对应的 API 或触发工作流。

```
AI Agent (自然语言)
    │
    ├── 1. 查询 Capability Registry (系统能做什么?)
    │     → GET /api/v1/capabilities
    │
    ├── 2. 匹配用户意图 → 找到对应 Capability
    │     "创建一个采购订单" → capability: "purchase.order.create"
    │
    └── 3. 调用 Capability (Input → Execute → Output)
          → POST /api/v1/purchase/orders { body }
```

---

## 二、Capability 模型

```python
@dataclass
class Capability:
    """系统能力 —— AI Agent 可调用的业务操作"""

    # 标识
    name: str                    # "purchase.order.create"
    display_name: str            # "创建采购订单"
    description: str             # "创建 PET 瓶片采购订单，支持多品种多币种。确认后触发货权变化。"
    module: str                  # "purchase"
    version: str                 # "V2"

    # 调用
    http_method: str             # "POST"
    http_path: str               # "/api/v1/purchase/orders"
    input_schema: dict           # JSON Schema 格式的入参定义
    output_schema: dict          # JSON Schema 格式的出参定义

    # 安全
    required_permissions: list[str]  # ["purchase.order.create"]
    auth_required: bool = True

    # 副作用
    events_published: list[str]  # ["purchase.order.confirmed"]
    events_consumed: list[str]   # []

    # 前置条件
    preconditions: list[str]     # ["supplier 已存在", "material 已定义"]
    idempotent: bool             # 是否幂等

    # AI 提示
    ai_tags: list[str]           # ["采购", "订单", "供应商"]
    ai_prompt_hint: str          # "用户说"创建采购订单"时，优先匹配此能力"

    # 关联
    related_capabilities: list[str]  # ["purchase.order.confirm", "purchase.receipt.create"]
```

---

## 三、Input/Output Schema

### 3.1 JSON Schema 模板

```json
{
  "input_schema": {
    "type": "object",
    "required": ["supplier_id", "order_date", "currency_id"],
    "properties": {
      "supplier_id": {
        "type": "string", "format": "uuid",
        "description": "供应商 ID",
        "ai_hint": "从 BusinessPartner 中筛选 bp_type=supplier 的条目"
      },
      "order_date": {
        "type": "string", "format": "date",
        "description": "下单日期",
        "default": "$today"
      },
      "expected_date": {
        "type": "string", "format": "date",
        "description": "预计到货日期"
      },
      "currency_id": {
        "type": "string", "format": "uuid",
        "description": "币种",
        "ai_hint": "默认使用本币 CNY"
      },
      "incoterm": {
        "type": "string", "enum": ["FOB", "CIF", "CFR"],
        "description": "贸易术语"
      },
      "remark": {
        "type": "string", "maxLength": 500,
        "description": "备注"
      }
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "id": {"type": "string", "format": "uuid"},
      "po_no": {"type": "string", "description": "自动生成的采购单号"}
    }
  }
}
```

### 3.2 Pydantic → JSON Schema 自动生成

```python
from pydantic import BaseModel

class POCreate(BaseModel):
    supplier_id: UUID
    order_date: str
    currency_id: UUID
    # ...

# 自动生成
schema = POCreate.model_json_schema()
# → Capability.input_schema = schema
```

---

## 四、Capability 注册

### 4.1 注册方式

每个模块在 `__init__.py` 中注册自己的 Capability：

```python
# modules/purchase/__init__.py
from app.shared.capability_registry import Capability, register_capability

register_capability(Capability(
    name="purchase.order.create",
    display_name="创建采购订单",
    description="创建 PET 瓶片采购订单，支持多品种多币种。确认后触发货权变化。",
    module="purchase",
    version="V2",
    http_method="POST",
    http_path="/api/v1/purchase/orders",
    input_schema=POCreate.model_json_schema(),
    output_schema={"type": "object", "properties": {"id": {}, "po_no": {}}},
    required_permissions=["purchase.order.create"],
    events_published=["purchase.order.confirmed"],
    preconditions=["supplier 已存在", "material 已定义"],
    ai_tags=["采购", "订单", "供应商"],
    ai_prompt_hint="用户说'创建采购订单'/'下一笔采购单'时优先匹配",
    related_capabilities=["purchase.order.confirm", "purchase.order.add_line"],
))
```

### 4.2 全局注册表

```python
class CapabilityRegistry:
    _capabilities: dict[str, Capability] = {}

    @classmethod
    def register(cls, cap: Capability) -> None:
        cls._capabilities[cap.name] = cap

    @classmethod
    def list_all(cls) -> list[Capability]:
        return list(cls._capabilities.values())

    @classmethod
    def get(cls, name: str) -> Capability:
        return cls._capabilities[name]

    @classmethod
    def search(cls, query: str) -> list[Capability]:
        """AI Agent 搜索: 按 name/tags/description 模糊匹配"""
        q = query.lower()
        return [
            cap for cap in cls._capabilities.values()
            if q in cap.name.lower()
            or q in cap.display_name
            or any(q in tag for tag in cap.ai_tags)
        ]

    @classmethod
    def build_index(cls) -> dict:
        """生成 AI 可消费的能力索引"""
        return {
            "total": len(cls._capabilities),
            "by_module": _group_by_module(cls._capabilities),
            "by_tag": _group_by_tag(cls._capabilities),
            "all": [cap.to_dict() for cap in cls._capabilities.values()],
        }
```

---

## 五、API 设计

```
GET  /api/v1/capabilities                    → 所有能力列表
GET  /api/v1/capabilities?module=purchase    → 按模块筛选
GET  /api/v1/capabilities?q=采购订单          → AI 搜索
GET  /api/v1/capabilities/{name}             → 单个能力详情（含 Input/Output Schema）
POST /api/v1/capabilities/search              → 语义搜索 { "intent": "我想采购一批 PET" }
GET  /api/v1/capabilities/index               → AI 能力索引（供 AI Agent 加载）
```

### 语义搜索端点

```json
// POST /api/v1/capabilities/search
// Request:
{ "intent": "我想采购 500 吨 PET Clear Flake" }

// Response:
{
  "matched_capabilities": [
    {
      "name": "purchase.order.create",
      "score": 0.95,
      "reason": "匹配: 采购 + PET + 吨",
      "suggested_params": {
        "material_id": "<需查询 PET Clear Flake>",
        "qty_ordered": 500
      }
    }
  ]
}
```

---

## 六、与 AI ContextBuilder 集成

```
                     ┌──────────────────┐
                     │  AI ContextBuilder│
                     │  (M6.1)          │
                     └────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ModuleManifest│    │ EntityContext │    │  Capability  │
│ (模块/命令/UI) │    │ (实体/状态/事件)│    │ (能力/输入/输出)│
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   AI Context     │
                    │   JSON Snapshot  │
                    │   (完整系统地图)   │
                    └──────────────────┘
```

ContextBuilder 调用 `CapabilityRegistry.build_index()`，将 Capability 列表合并到 AI Context 中：

```json
{
  "system": {...},
  "modules": [...],
  "capabilities": {
    "total": 45,
    "by_module": {
      "purchase": ["purchase.order.create", "purchase.order.confirm", ...],
      "sales": ["sales.contract.create", "sales.contract.confirm", ...]
    },
    "all": [...]
  },
  "events": [...]
}
```

---

## 七、现有模块 Capability 清单

| 模块 | Capability | HTTP |
|------|-----------|------|
| **Purchase** | purchase.order.create | POST /orders |
| | purchase.order.confirm | POST /orders/{id}/confirm |
| | purchase.order.cancel | POST /orders/{id}/cancel |
| | purchase.order.add_line | POST /orders/{id}/lines |
| | purchase.receipt.create | POST /receipts |
| | purchase.receipt.confirm | POST /receipts/{id}/confirm |
| | purchase.receipt.reverse | POST /receipts/{id}/reverse |
| **Inventory** | inventory.material.create | POST /materials |
| | inventory.stock.receive | POST /receive |
| | inventory.allocation.create | POST /allocations |
| | inventory.allocation.release | POST /allocations/{id}/release |
| **Sales** | sales.contract.create | POST /contracts |
| | sales.contract.confirm | POST /contracts/{id}/confirm |
| | sales.contract.cancel | POST /contracts/{id}/cancel |
| **Shipment** | shipment.order.create | POST /orders |
| | shipment.order.ship | POST /orders/{id}/ship |
| | shipment.order.deliver | POST /orders/{id}/deliver |

---

## 八、实现范围

| 优先级 | 文件 | 说明 |
|--------|------|------|
| P0 | `shared/capability_registry.py` | Capability dataclass + CapabilityRegistry |
| P1 | `api/v1/system.py` | /capabilities 端点 + /ai-context 扩展 |
| P2 | 各模块注册 | 每个模块的 `__init__.py` 注册 Capability |

---

确认后进入 M6 Coding。
