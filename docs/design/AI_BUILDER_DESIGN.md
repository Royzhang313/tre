# AI Builder Design —— ERP Builder 核心能力

> 状态: Review V1 | 日期: 2026-07-08
> 目标: 自然语言 → Domain Specification → 人工 Review → 代码生成

---

## 一、Agent 分工

```
┌─────────────────────────────────────────────────────────────────┐
│                      ERP Builder AI Pipeline                     │
│                                                                  │
│  用户自然语言                                                     │
│      │                                                           │
│      ▼                                                           │
│  ┌──────────────┐    读取 AI Context                              │
│  │  Architect   │─── Module/Entity/Capability Metadata            │
│  │  Agent       │                                                │
│  │  (M7)        │──→ Domain Specification JSON                    │
│  └──────────────┘                                                │
│      │                                                           │
│      ▼ (人工 Review)                                              │
│  ┌──────────────┐                                                │
│  │  Human       │  审批 / 修改 Domain Spec                         │
│  │  Review      │                                                │
│  └──────────────┘                                                │
│      │                                                           │
│      ▼ (未来 M7.1)                                                │
│  ┌──────────────┐    执行 Domain Spec                              │
│  │  Builder     │──→ 生成: models.py / schemas.py / service.py    │
│  │  Agent       │    repository.py / router.py / events.py       │
│  │  (M7.1)      │    migration / seed / test                     │
│  └──────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
```

| Agent | 阶段 | 输入 | 输出 | 状态 |
|-------|------|------|------|------|
| **Architect** | M7 | 自然语言 + AI Context | Domain Specification JSON | 🔄 设计 |
| **Builder** | M7.1 | Domain Specification | Python 代码 + Migration | 🔮 未来 |

---

## 二、Architect Agent 设计

### 2.1 Role

```
你是 ERP Builder 的架构师 Agent。

你的职责:
1. 理解用户的业务需求（自然语言）
2. 基于系统当前能力 (AI Context) 分析差距
3. 输出 Domain Specification —— 结构化业务模型描述
4. 不生成代码，只生成设计文档

你基于的系统是 PET 瓶片贸易 ERP。
当前已有模块: Purchase, Inventory, Sales, Shipment, BaseData, Auth。
```

### 2.2 Prompt Strategy

```
Step 1: 加载 AI Context
  - 读取 GET /api/v1/system/ai-context
  - 获取: 现有模块、实体、能力、事件、权限

Step 2: 需求分析
  - 用户输入: "增加品质检验模块"
  - 提取: 模块名、实体、字段、流程、权限

Step 3: 差距分析
  - 检查 AI Context: 哪些是现有模块可以复用的?
  - 标记: Reuse / Extend / New

Step 4: 生成 Domain Spec
  - 输出结构化 JSON
  - 每个实体/字段/关系可追溯
```

### 2.3 调用方式

```python
# Architect Agent API
POST /api/v1/ai/architect/analyze
Request:
{
  "requirement": "增加品质检验模块，采购收货后需要检验 PET 瓶片的 IV 值、水分、杂质，检验合格后才能正式入库"
}

Response:
{
  "domain_spec": {
    "new_modules": [...],
    "new_entities": [...],
    "relationships": [...],
    "gaps": [...]
  },
  "suggestions": ["可复用 Batch.quality_json 字段", "可与现有 Purchase Receipt 流程集成"]
}
```

---

## 三、Domain Specification Schema

### 3.1 顶层结构

```json
{
  "spec_version": "1.0",
  "created_at": "2026-07-08T...",
  "business_domain": "PET 瓶片贸易 ERP",

  "new_modules": [],
  "extended_modules": [],
  "new_entities": [],
  "extended_entities": [],
  "new_capabilities": [],
  "new_workflows": [],
  "new_permissions": [],
  "ui_pages": [],
  "relationships": [],
  "events": [],

  "reuse": [],
  "gaps": [],
  "risks": []
}
```

### 3.2 Module 定义

```json
{
  "new_modules": [
    {
      "name": "quality_inspection",
      "display_name": "品质检验",
      "version": "V1",
      "description": "采购收货后对 PET 瓶片进行品质检验",
      "dependencies": ["purchase", "inventory", "basedata"]
    }
  ]
}
```

### 3.3 Entity 定义

```json
{
  "new_entities": [
    {
      "name": "InspectionOrder",
      "display_name": "检验单",
      "table_name": "quality_inspection_orders",
      "module": "quality_inspection",
      "is_aggregate_root": true,
      "fields": [
        {"name": "inspection_no", "type": "str(30)", "required": true, "unique": true, "description": "检验单号"},
        {"name": "receipt_id", "type": "FK→GoodsReceipt", "required": true, "description": "关联收货单"},
        {"name": "batch_id", "type": "FK→Batch", "required": false, "description": "关联批次"},
        {"name": "inspector_id", "type": "FK→User", "required": true, "description": "检验人"},
        {"name": "iv_result", "type": "str(10)", "required": false, "description": "IV 实测值"},
        {"name": "moisture_result", "type": "str(10)", "required": false, "description": "水分实测值"},
        {"name": "result", "type": "str(20)", "required": true, "description": "pass / fail / pending"},
        {"name": "status", "type": "str(20)", "required": true, "description": "draft / in_progress / completed"}
      ],
      "relationships": [
        {"name": "lines", "target_entity": "InspectionLine", "relation_type": "one_to_many"}
      ]
    }
  ]
}
```

### 3.4 Capability 定义

```json
{
  "new_capabilities": [
    {
      "name": "quality.inspection.create",
      "display_name": "创建检验单",
      "module": "quality_inspection",
      "http_method": "POST",
      "http_path": "/api/v1/quality/inspections",
      "required_permissions": ["quality.inspection.create"],
      "events_published": ["quality.inspection.completed"],
      "ai_tags": ["品质", "检验", "质检"]
    }
  ]
}
```

### 3.5 Workflow 定义

```json
{
  "new_workflows": [
    {
      "name": "inspection_workflow",
      "entity": "InspectionOrder",
      "initial_state": "draft",
      "states": [
        {"code": "draft", "name": "草稿"},
        {"code": "in_progress", "name": "检验中"},
        {"code": "completed", "name": "已完成", "terminal": true}
      ],
      "transitions": [
        {"name": "开始检验", "from_state": "draft", "to_state": "in_progress"},
        {"name": "完成检验", "from_state": "in_progress", "to_state": "completed"}
      ]
    }
  ]
}
```

### 3.6 UI Page 定义

```json
{
  "ui_pages": [
    {
      "route": "/quality/inspections",
      "title": "品质检验",
      "page_type": "list",
      "entity": "InspectionOrder",
      "columns": ["inspection_no", "receipt_id", "result", "status", "created_at"],
      "actions": ["create", "view", "start", "complete"]
    }
  ]
}
```

---

## 四、与现有系统集成

### 4.1 AI Context 消费

Architect Agent 在分析前调用 `GET /api/v1/system/ai-context` 获取：

```json
{
  "system": {"name": "ERP Builder", "domain": "PET 瓶片贸易 ERP"},
  "modules": [
    {"name": "purchase", "entities": [...], "capabilities": [...]},
    {"name": "inventory", ...}
  ],
  "capabilities": {
    "total": 45,
    "by_module": {"purchase": [...], "sales": [...]}
  }
}
```

**用途**:
- 复用现有实体 → `extended_entities` (增加字段)
- 复用现有模块 → `extended_modules` (增加能力)
- 检测命名冲突
- 建议复用关系（如 FK 到已有的 BusinessPartner）

### 4.2 Domain Spec → 现有 Registry

Architect Agent 输出的 Domain Spec 可直接映射到现有 Registry：

| Domain Spec | Registry |
|-------------|----------|
| `new_modules[]` | `ModuleRegistry.register(ModuleManifest)` |
| `new_entities[]` | `EntityMeta` |
| `new_capabilities[]` | `CapabilityRegistry.register(Capability)` |
| `new_workflows[]` | `WorkflowDefinition` |
| `new_permissions[]` | Seed 扩展 |

---

## 五、Validation Flow

```
Domain Spec
    │
    ├── 1. Schema Validation (JSON Schema 格式校验)
    │
    ├── 2. Naming Conflict Check
    │      entity 名是否与现有冲突?
    │      permission code 是否重复?
    │
    ├── 3. Relationship Integrity
    │      FK 引用的 entity 是否存在?
    │      循环依赖?
    │
    ├── 4. Permission Consistency
    │      Capability 引用的 permission 是否在 spec 中定义?
    │
    └── 5. Module Boundary Check
           是否违反模块隔离规则?
           是否有跨模块 Service 调用?
```

### Validation API

```
POST /api/v1/ai/architect/validate
Request: Domain Spec JSON
Response:
{
  "valid": true/false,
  "errors": [...],
  "warnings": [...]
}
```

---

## 六、Human Review Point

Domain Spec 生成后，**必须**经过人工 Review 才能进入 Builder Agent。

```
Architect Agent → Domain Spec → Human Review ──┬── Approve → Builder Agent
                                                │
                                                ├── Modify → 返回 Architect
                                                │
                                                └── Reject → 终止
```

### Review 检查清单

| 检查项 | 说明 |
|--------|------|
| 业务合理性 | 生成的模块是否符合 PET 瓶片贸易场景? |
| 命名规范 | Entity/Capability/Permission 命名是否一致? |
| 复用检查 | 是否合理复用了现有模块? 还是重复造轮子? |
| 架构约束 | 是否违反模块隔离? 是否有跨模块 Service 调用? |
| 数据模型 | 字段类型是否合理? 是否缺必要字段? |

---

## 七、API 端点

```
POST /api/v1/ai/architect/analyze       → 分析需求 → 生成 Domain Spec
POST /api/v1/ai/architect/validate       → 验证 Domain Spec
GET  /api/v1/ai/context                  → 获取 AI Context（复用 system/ai-context）
GET  /api/v1/ai/architect/templates      → 获取 Domain Spec 模板
```

---

## 八、安全边界

| 边界 | 规则 |
|------|------|
| **不执行业务操作** | Architect Agent 只读 AI Context，不修改任何业务数据 |
| **不访问 DB** | 不直接查询业务表，只通过 Registry/API 获取元数据 |
| **不调用外部 LLM API** | M7 阶段 Domain Spec 为手动构建（M8 接入真实 LLM） |
| **人工 Review 强制** | Domain Spec 必须经过人工确认才能传递给 Builder Agent |

---

## 九、M7 交付范围

| 阶段 | 交付 | 说明 |
|------|------|------|
| **M7** | Domain Spec Schema + Architect API | 结构化蓝图，不生成代码 |
| **M7.1** (未来) | Builder Agent | Domain Spec → Python 代码 |
| **M8** (未来) | LLM 集成 | 接入真实 AI 模型进行需求分析 |

---

## 十、示例：Architect Agent 完整流程

```
输入:
"增加品质检验模块。采购收货后对 PET 瓶片检验 IV、水分、杂质。
检验合格 → 入库。检验不合格 → 退货或降级。"

↓ Architect Agent 处理

1. 加载 AI Context
   发现: purchase.receipt.confirmed 事件已存在
   发现: Batch 有 quality_json 字段可复用
   发现: Inventory 有 IN_TRANSIT 状态

2. 输出 Domain Spec:
   new_modules: [quality_inspection]
   new_entities: [InspectionOrder, InspectionLine]
   new_capabilities: [quality.inspection.create, quality.inspection.complete]
   new_workflows: [inspection_workflow]
   extended_entities: [Batch.quality_json → 读取检验结果]
   events: [
     {new: "quality.inspection.completed"},
     {consume: "purchase.receipt.confirmed" → 自动创建检验单}
   ]

↓ Human Review → Approve

↓ Builder Agent (M7.1)
   生成: modules/quality_inspection/{models,schemas,repository,service,router,events}.py
   生成: migration
   生成: seed permissions
   生成: test
```

---

确认后进入 M7 Coding。
