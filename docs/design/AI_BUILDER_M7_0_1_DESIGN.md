# M7.0.1 Domain Spec Hardening Design

> 状态: Review V1 | 日期: 2026-07-08
> 限制: 不接入 LLM、不生成代码、不修改 DB、不执行 migration

---

## 一、AIDomainSpec 生命周期增强

### 1.1 状态机

```
draft → validating → reviewing → approved → building → deployed
  │         │            │           │           │
  └─────────┴────────────┴───────────┴───────────┘
                    deprecated
```

| 状态 | 含义 | 可进入的状态 |
|------|------|-------------|
| `draft` | 编辑中 | validating |
| `validating` | 规则校验中 | reviewing, draft |
| `reviewing` | 人工 Review | approved, draft |
| `approved` | 审批通过 | building |
| `building` | Builder Agent 执行中 | deployed, draft |
| `deployed` | 已部署 | deprecated |
| `deprecated` | 已废弃 | - |

### 1.2 状态转换校验

```python
VALID_TRANSITIONS = {
    "draft":      {"validating"},
    "validating": {"reviewing", "draft"},
    "reviewing":  {"approved", "draft"},
    "approved":   {"building"},
    "building":   {"deployed", "draft"},
    "deployed":   {"deprecated"},
    "deprecated": set(),
}

class SpecLifecycle:
    @staticmethod
    def can_transition(current: str, target: str) -> bool:
        return target in VALID_TRANSITIONS.get(current, set())

    @staticmethod
    def transition(spec: AIDomainSpec, target: str, operator_id: UUID) -> None:
        if not SpecLifecycle.can_transition(spec.status, target):
            raise ConflictError(f"非法状态转换: {spec.status} → {target}")
        spec.status = target
```

---

## 二、Domain Spec Version

### 2.1 版本模型扩展

在 AIDomainSpec 上增加：

| 字段 | 类型 | 说明 |
|------|------|------|
| version | str(10) → int | 🆕 改为整数递增: 1, 2, 3... |
| parent_spec_id | UUID | 🆕 FK→AIDomainSpec, nullable。V2 的 parent = V1 |
| revision_reason | str(500) | 🆕 修订原因 |

### 2.2 版本创建

```
POST /api/v1/ai/spec/{id}/version
Request: { "revision_reason": "增加品质检验模块" }

流程:
1. 读取当前 Spec (status=deployed)
2. 创建新 Spec:
   - parent_spec_id = 当前 Spec.id
   - version = 当前 Spec.version + 1
   - status = draft
   - spec_json = 当前 Spec.spec_json (复制)
3. 返回新 Spec

规则:
- 只有 status=deployed 的 Spec 可以创建新版本
- 同一时间只有一个 active draft 版本
```

### 2.3 版本历史

```
GET /api/v1/ai/spec/{id}/history
Response:
{
  "current_version": 3,
  "versions": [
    {"id": "v1-id", "version": 1, "status": "deployed", "created_at": "..."},
    {"id": "v2-id", "version": 2, "status": "deprecated", "parent_spec_id": "v1-id"},
    {"id": "v3-id", "version": 3, "status": "draft", "parent_spec_id": "v2-id"}
  ]
}
```

---

## 三、Validator 重构为规则框架

### 3.1 规则接口

```python
# app/ai/validator/base.py

from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class ValidationResult:
    rule_name: str
    level: str              # "error" | "warning"
    message: str
    path: str = ""          # JSON path, 例如 "new_modules[0].name"

class SpecValidationRule(ABC):
    """Domain Spec 校验规则接口"""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]: ...
```

### 3.2 六条规则

| 规则文件 | 规则名 | 检查内容 |
|---------|--------|---------|
| `module_rule.py` | `module_unique` | new_modules 名称不与现有模块冲突 |
| `module_rule.py` | `module_dependency` | dependencies 中引用的模块存在 |
| `entity_rule.py` | `entity_unique` | new_entities 名称不重复 |
| `entity_rule.py` | `entity_fk_valid` | FK 引用的 target_entity 在 spec 或现有 registry 中 |
| `entity_rule.py` | `entity_field_type` | field type 格式合法 (str(N)/Decimal(N,M)/UUID/FK→) |
| `capability_rule.py` | `cap_unique` | capability name 不与现有冲突 |
| `capability_rule.py` | `cap_permission` | required_permissions 在 spec 或现有系统中定义 |
| `workflow_rule.py` | `wf_state_integrity` | transitions 引用的 from/to 都在 states 中 |
| `workflow_rule.py` | `wf_terminal_valid` | 终态 (terminal=true) 无出边 transition |
| `permission_rule.py` | `perm_format` | code 格式符合 `{module}.{resource}.{action}` |

### 3.3 执行引擎

```python
class SpecValidator:
    _rules: list[SpecValidationRule] = [
        ModuleUniqueRule(),
        ModuleDependencyRule(),
        EntityUniqueRule(),
        EntityFKValidRule(),
        EntityFieldTypeRule(),
        CapabilityUniqueRule(),
        CapabilityPermissionRule(),
        WorkflowStateIntegrityRule(),
        WorkflowTerminalValidRule(),
        PermissionFormatRule(),
    ]

    @classmethod
    def validate(cls, spec_json: dict) -> dict:
        context = cls._build_context()
        results = []
        for rule in cls._rules:
            results.extend(rule.validate(spec_json, context))

        errors = [r for r in results if r.level == "error"]
        warnings = [r for r in results if r.level == "warning"]
        return {
            "valid": len(errors) == 0,
            "errors": [{"rule": r.rule_name, "message": r.message, "path": r.path} for r in errors],
            "warnings": [{"rule": r.rule_name, "message": r.message, "path": r.path} for r in warnings],
            "rules_executed": len(cls._rules),
        }

    @classmethod
    def _build_context(cls) -> dict:
        return {
            "existing_modules": {m.name for m in ModuleRegistry.list_all()},
            "existing_capabilities": {c.name for c in CapabilityRegistry.list_all()},
            "existing_permissions": set(),  # 从 Seed 读取
        }
```

---

## 四、BuildPlan 领域模型

### 4.1 模型

```python
class BuildPlan(BaseModel):
    """Builder Agent 执行计划 —— 暂不执行，仅记录"""

    __tablename__ = "ai_build_plans"

    spec_id: UUID              # FK→AIDomainSpec
    status: str                # draft / approved / executing / completed / failed
    actions: dict              # JSON 执行步骤
    estimated_changes: str     # 预估变更摘要
    risks: str | None          # 风险提示
    started_at: str | None
    completed_at: str | None
    error_log: str | None
```

### 4.2 Actions Schema

```json
{
  "actions": [
    {
      "action": "create_module",
      "target": "quality_inspection",
      "params": {
        "name": "quality_inspection",
        "display_name": "品质检验",
        "dependencies": ["purchase", "inventory"]
      }
    },
    {
      "action": "create_entity",
      "target": "InspectionOrder",
      "params": {
        "module": "quality_inspection",
        "table_name": "quality_inspection_orders",
        "fields": [...]
      }
    },
    {
      "action": "create_capability",
      "target": "quality.inspection.create",
      "params": {
        "http_method": "POST",
        "http_path": "/api/v1/quality/inspections"
      }
    },
    {
      "action": "create_permission",
      "target": "quality.inspection.create"
    },
    {
      "action": "extend_entity",
      "target": "Batch",
      "params": {
        "add_fields": [{"name": "inspection_result", "type": "str(20)"}]
      }
    }
  ],
  "order": [
    "create_module",
    "create_entity",
    "create_permission",
    "extend_entity",
    "create_capability",
    "create_workflow",
    "create_ui_page"
  ]
}
```

### 4.3 BuildPlan 状态机

```
draft → approved → executing → completed
                 → failed
```

### 4.4 生成 BuildPlan

```
POST /api/v1/ai/spec/{id}/generate-plan

流程:
1. 读取 Spec (status=approved)
2. 解析 spec_json
3. 生成 Actions:
   - new_modules[] → create_module
   - new_entities[] → create_entity
   - new_capabilities[] → create_capability
   - new_workflows[] → create_workflow
   - new_permissions[] → create_permission
   - ui_pages[] → create_ui_page
   - extended_entities[] → extend_entity
4. 写入 BuildPlan (status=draft)
5. 返回 BuildPlan
```

---

## 五、DomainSpecSnapshot —— 冻结输入

### 5.1 模型

```python
class DomainSpecSnapshot(BaseModel):
    """Builder 执行时的冻结快照 —— 不受 Spec 后续修改影响"""

    __tablename__ = "ai_domain_spec_snapshots"

    spec_id: UUID              # FK→AIDomainSpec
    spec_version: int          # 快照时的 version
    plan_id: UUID | None       # FK→BuildPlan
    spec_json: dict            # 冻结的完整 spec
    registry_version: str      # 快照时的 registry 版本
    created_at: datetime
```

### 5.2 使用方式

```
Builder Agent 执行前:
1. 读取 Spec (status=approved)
2. 生成 BuildPlan
3. 创建 DomainSpecSnapshot (冻结 spec_json)
4. Builder 读取 Snapshot（不读取实时 Spec）
5. 执行 Actions
```

---

## 六、API 汇总

### 新增端点

```
POST   /api/v1/ai/spec/{id}/version         → 创建新版本
GET    /api/v1/ai/spec/{id}/history          → 版本历史
POST   /api/v1/ai/spec/{id}/generate-plan    → 生成 BuildPlan
GET    /api/v1/ai/plan/{id}                  → 查看 BuildPlan
POST   /api/v1/ai/plan/{id}/approve          → 审批 BuildPlan
```

### 修改端点

```
POST /api/v1/ai/spec/{id}/validate
  → 规则框架重构，返回 rule_name/path 结构化错误
```

---

## 七、M7.0.1 文件规划

```
app/ai/
├── __init__.py
├── models.py              # AIDomainSpec + BuildPlan + DomainSpecSnapshot
├── schemas.py             # ✏️ 增加 VersionCreate / BuildPlan 相关
├── service.py             # ✏️ 增加 SpecLifecycle / PlanService / SnapshotService
├── router.py              # ✏️ 增加新端点
├── validator/
│   ├── __init__.py
│   ├── base.py            # SpecValidationRule + ValidationResult
│   ├── module_rule.py     # module_unique / module_dependency
│   ├── entity_rule.py     # entity_unique / entity_fk_valid / entity_field_type
│   ├── capability_rule.py # cap_unique / cap_permission
│   ├── workflow_rule.py   # wf_state_integrity / wf_terminal_valid
│   └── permission_rule.py # perm_format
└── lifecycle.py           # SpecLifecycle 状态机
```

---

## 八、边界

| ✅ M7.0.1 | ❌ 不做 |
|-----------|--------|
| Spec 生命周期 (7 状态) | LLM 调用 |
| Version 管理 (parent/修订原因) | 代码生成 |
| Validator 规则框架 (10 条规则) | 数据库 migration |
| BuildPlan 模型 (只生成不执行) | Builder Agent 执行 |
| DomainSpecSnapshot 冻结 | 外部 API 集成 |

---

确认后进入 M7.0.1 Coding。
