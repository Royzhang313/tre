# M7.3 Module Sandbox Design

> 状态: Review V1 | 日期: 2026-07-08

---

## 一、目标

AI 生成的模块不直接进入生产环境。Sandbox 提供隔离的测试空间，验证通过后才能 Promote。

```
Generated Artifact
    │
    ▼
SandboxInstance
    │
    ├── Install (写入隔离目录)
    ├── Migrate (执行 DDL)
    ├── Seed (初始化数据)
    ├── Test (pytest)
    └── Report (收集结果)
    │
    ▼
Promote (通过 → Merge Pipeline)
```

---

## 二、SandboxInstance 模型

```python
class SandboxInstance(BaseModel):
    """沙箱实例 —— 一个生成的模块的隔离测试环境"""

    __tablename__ = "ai_sandbox_instances"

    execution_id: UUID             # 哪个 BuildExecution 产生的
    module_name: str               # 模块名
    status: str                    # created/building/installed/testing/passed/failed/promoted/destroyed
    sandbox_path: str              # 隔离目录 /sandbox/{module_name}_{instance_id}/
    migration_applied: bool        # migration 是否执行成功
    test_results: JSON | None      # pytest 结果
    test_summary: str | None       # passed/failed 统计
    error_log: str | None
    promoted_to_merge_id: UUID | None  # Promote 后的 MergeRequest ID
    created_at / updated_at
```

### 状态机

```
created → building → installed → testing → passed → promoted → destroyed
  │         │           │           │
  └─────────┴───────────┴───────────┘
                failed → destroyed
```

| 状态 | 操作 | 说明 |
|------|------|------|
| `created` | 初始化 | SandboxInstance 已创建 |
| `building` | install() | 写入 /sandbox/ 目录 |
| `installed` | migrate() | 执行 migration |
| `testing` | test() | 运行 pytest |
| `passed` | - | 所有测试通过 |
| `failed` | - | 任一阶段失败 |
| `promoted` | promote() | 进入 Merge Pipeline |
| `destroyed` | destroy() | 清理沙箱 |

---

## 三、Sandbox 目录结构

```
/sandbox/{module_name}_{instance_id}/
├── app/
│   └── modules/
│       └── {module_name}/
│           ├── __init__.py
│           ├── models.py
│           ├── schemas.py
│           ├── repository.py
│           ├── service.py
│           ├── router.py
│           └── events.py
├── tests/
│   └── test_{module_name}/
│       └── test_models.py
├── migrations/
│   └── migration.sql
├── seed/
│   └── permissions.py
├── .env.sandbox
├── test_db.sqlite3         # 隔离的测试数据库
└── sandbox_report.json     # 测试报告
```

---

## 四、Sandbox Service

### 4.1 创建和构建

```python
class SandboxService:
    @staticmethod
    async def create(execution_id: UUID, module_name: str) -> SandboxInstance:
        """创建 SandboxInstance"""
        ...

    @staticmethod
    async def install(instance_id: UUID) -> SandboxInstance:
        """安装生成的文件到 /sandbox/ 目录"""
        # 1. 从 Artifact 读取文件
        # 2. 写入 /sandbox/{module}_{id}/ 目录
        # 3. 创建 __init__.py + register()
        # 4. 复制 tests/
        # 5. 创建 .env.sandbox (DATABASE_URL=sqlite:///test_db.sqlite3)
        ...

    @staticmethod
    async def migrate(instance_id: UUID) -> SandboxInstance:
        """在隔离数据库中执行 migration"""
        # 1. 启动 SQLite 连接
        # 2. 执行 migration.sql
        # 3. 标记 migration_applied = True
        ...

    @staticmethod
    async def test(instance_id: UUID) -> SandboxInstance:
        """运行 pytest 收集结果"""
        # 1. 设置 PYTHONPATH=/sandbox/{module}_{id}/
        # 2. 运行 pytest --json-report
        # 3. 收集 test_results
        # 4. 判断 passed/failed
        ...
```

### 4.2 Promote

```python
    @staticmethod
    async def promote(instance_id: UUID) -> MergeRequest:
        """Sandbox 通过 → 进入 Merge Pipeline"""
        # 前提: status == "passed"
        # 1. 创建 MergeRequest
        # 2. 将 /sandbox/ 中的文件作为 Artifact 源
        # 3. 进入正常的 Merge Pipeline 流程
        # 4. sandbox.status = "promoted"
        # 5. sandbox.promoted_to_merge_id = mr.id
        ...
```

### 4.3 Destroy

```python
    @staticmethod
    async def destroy(instance_id: UUID) -> SandboxInstance:
        """清理沙箱"""
        # 1. 删除 /sandbox/{module}_{instance_id}/
        # 2. 删除 SQLite 数据库
        # 3. status = "destroyed"
        ...
```

---

## 五、Report 格式

```json
{
  "sandbox_id": "uuid",
  "module_name": "quality_inspection",
  "status": "passed",
  "stages": {
    "install": {"status": "completed", "files": 8},
    "migrate": {"status": "completed", "tables_created": 3},
    "test": {"status": "passed", "total": 15, "passed": 15, "failed": 0}
  },
  "test_details": [
    {"name": "test_models.py::TestInspectionOrder::test_tablename", "status": "passed"},
    {"name": "test_models.py::TestInspectionOrder::test_fields", "status": "passed"}
  ],
  "duration_seconds": 12.5
}
```

---

## 六、API

```
POST /api/v1/ai/sandbox/create
     { execution_id, module_name }
     → SandboxInstance(created)

POST /api/v1/ai/sandbox/{id}/install    → building → installed
POST /api/v1/ai/sandbox/{id}/migrate    → installed (migration_applied=true)
POST /api/v1/ai/sandbox/{id}/test       → testing → passed/failed
POST /api/v1/ai/sandbox/{id}/promote    → promoted (→ Merge Pipeline)
POST /api/v1/ai/sandbox/{id}/destroy    → destroyed

GET  /api/v1/ai/sandbox/{id}            → 查看状态 + report
GET  /api/v1/ai/sandbox/{id}/report     → 详细测试报告
```

---

## 七、完整 AI Pipeline (含 Sandbox)

```
用户需求
    ↓
Architect Agent       ✅ M7
    ↓
DomainSpec            ✅ M7
    ↓
Validator + Version   ✅ M7.0.1
    ↓
BuildPlan             ✅ M7.0.1
    ↓
BuildExecution        ✅ M7.1
    ↓
Generator Runtime     ✅ M7.1.1
    ↓
Generated Artifact    ✅ M7.1.1
    ↓
┌─────────────────────────────────────┐
│ Sandbox (M7.3)                      │
│                                     │
│  Install → Migrate → Test → Report  │
│                                     │
│  passed → Promote                   │
│  failed → Destroy                   │
└─────────────────────────────────────┘
    ↓ (promoted)
Merge Pipeline        ✅ M7.2
    ↓
Human Review
    ↓
Production
```

---

## 八、安全隔离

| 规则 | 实施 |
|------|------|
| **隔离数据库** | SQLite test_db.sqlite3，不连接生产 PostgreSQL |
| **隔离文件系统** | /sandbox/ 目录，不写入 app/modules/ |
| **隔离进程** | pytest 在子进程中运行，超时保护 |
| **可销毁** | destroy() 清理所有沙箱文件 |
| **不可自动 Promote** | Human Approve MergeRequest 后才 Promote |

---

## 九、M7.3 文件规划

```
app/ai/
├── sandbox/
│   ├── __init__.py
│   ├── models.py          # SandboxInstance
│   ├── service.py         # SandboxService
│   └── runner.py          # TestRunner (pytest subprocess)
├── service.py             # ✏️ 集成 SandboxService
└── router.py              # ✏️ /sandbox/* 端点
```

---

## 十、M7 最终全景

```
M7     Architect Agent          ✅
M7.0.1 Lifecycle + Validator    ✅
M7.1   Builder Runtime          ✅
M7.1.1 Generator Runtime        ✅
M7.2   Merge Pipeline           ✅
M7.3   Module Sandbox           ⏳ 设计中
M8     Dynamic UI Runtime       ⏳
```

---

确认后进入 M7.3 Coding。
