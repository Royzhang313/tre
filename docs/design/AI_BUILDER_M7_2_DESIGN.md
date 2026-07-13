# M7.2 Artifact Merge & Deployment Pipeline Design

> 状态: Review V1 | 日期: 2026-07-08

---

## 一、目标

完成 DomainSpec → BuildPlan → Generate → Review → Merge 完整闭环。

```
GeneratedArtifact (approved)
    │
    ▼
Merge Pipeline
    │
    ├── 1. Conflict Check      (目标文件是否已存在? 是否冲突?)
    ├── 2. Diff/Patch Generate  (生成变更预览)
    ├── 3. Migration Check      (检查 migration.sql)
    ├── 4. Merge Request        (创建 MergeRequest)
    ├── 5. Registry Update      (自动注册 Module/Capability/Permission)
    ├── 6. Apply                (写入目标目录)
    └── 7. Verify               (ruff + mypy + pytest)
```

---

## 二、Merge Pipeline 架构

### 2.1 流程

```
┌──────────────────────────────────────────────────────┐
│                 Merge Pipeline                        │
│                                                       │
│  Artifact(approved)                                   │
│      │                                                │
│      ▼                                                │
│  ┌──────────┐   检查目标路径是否已有文件                  │
│  │ Conflict │   → 无冲突: 继续                         │
│  │ Check    │   → 有冲突: 生成 diff, 创建 ConflictLog   │
│  └──────────┘                                         │
│      │                                                │
│      ▼                                                │
│  ┌──────────┐   生成变更预览                            │
│  │ Diff Gen │   → 新增文件列表                          │
│  │          │   → 修改文件 diff                         │
│  └──────────┘                                         │
│      │                                                │
│      ▼                                                │
│  ┌──────────┐   检查 migration.sql                     │
│  │Migration │   → 提取 DDL 语句                        │
│  │ Check    │   → 生成 MigrationReview                 │
│  └──────────┘                                         │
│      │                                                │
│      ▼                                                │
│  ┌──────────┐   创建 MergeRequest                     │
│  │ Merge    │   status: pending_review                 │
│  │ Request  │                                         │
│  └──────────┘                                         │
│      │                                                │
│      ▼ (Human Review)                                  │
│  ┌──────────┐                                         │
│  │ Apply    │   写入 app/modules/{module}/              │
│  │          │   更新 ModuleRegistry                     │
│  │          │   注册 Capability                         │
│  │          │   注册 Permission                         │
│  └──────────┘                                         │
│      │                                                │
│      ▼                                                │
│  ┌──────────┐   ruff check + mypy + pytest             │
│  │ Verify   │   → 通过: completed                      │
│  │          │   → 失败: rollback                       │
│  └──────────┘                                         │
└──────────────────────────────────────────────────────┘
```

### 2.2 模型

```python
class MergeRequest(BaseModel):
    """合并请求 —— 一组 Artifact 的合并操作"""
    __tablename__ = "ai_merge_requests"

    execution_id: UUID
    status: str          # pending_review / approved / applying / completed / failed / rolled_back
    diff_summary: JSON    # 变更概要
    conflict_log: JSON | None
    applied_at: str | None
    verified_at: str | None
    rollback_snapshot: JSON | None  # 回滚快照（原文件内容）


class ConflictLog(BaseModel):
    """冲突记录"""
    __tablename__ = "ai_conflict_logs"

    merge_request_id: UUID
    file_path: str
    conflict_type: str   # "file_exists" | "class_conflict" | "permission_conflict" | "route_conflict"
    existing_content: str | None
    new_content: str | None
    resolved: bool = False
```

---

## 三、Conflict Check 规则

| 冲突类型 | 检测 | 处理 |
|---------|------|------|
| `file_exists` | `app/modules/{name}/models.py` 已存在 | 生成 diff，人工选择覆盖/合并/跳过 |
| `class_conflict` | models.py 中已有同名 class | 警告，人工处理 |
| `permission_conflict` | seed 中已有相同 code | 跳过，不重复注册 |
| `route_conflict` | API 路径已被注册 | 警告 |
| `capability_conflict` | Capability 已存在 | 跳过 |

---

## 四、Registry Auto-Update

Merge 成功后自动执行：

```python
# 1. 注册模块
ModuleRegistry.register(ModuleManifest(
    name=module_name,
    display_name=display_name,
    version="V1",
    entities=[...],
    permissions=[...],
))

# 2. 注册 Capability
for cap in generated_capabilities:
    CapabilityRegistry.register(Capability(...))

# 3. 扩展 Seed 权限
# 在 seed.py 中追加新权限（或通过 Migration 执行）

# 4. 注册路由
# 如果模块有 __init__.py 且调用了 register()，重启后自动加载
```

---

## 五、API

```
POST /api/v1/ai/merge/request
     { execution_id: "uuid" }
     → 创建 MergeRequest, 执行 Conflict Check, 生成 diff

GET  /api/v1/ai/merge/{request_id}
     → 查看 MergeRequest 详情 (diff_summary, conflict_log)

POST /api/v1/ai/merge/{request_id}/approve
     → 审批通过

POST /api/v1/ai/merge/{request_id}/apply
     → 执行 Apply (写入文件 + 注册 + 验证)

GET  /api/v1/ai/merge/{request_id}/diff
     → 查看文件级 diff

POST /api/v1/ai/merge/{request_id}/rollback
     → 回滚 (从 rollback_snapshot 恢复)
```

---

## 六、安全边界

| 规则 | 实施 |
|------|------|
| **不直接覆盖** | Apply 前必须 MergeRequest.approved |
| **可回滚** | rollback_snapshot 保存原文件内容 |
| **验证必须通过** | ruff + mypy + pytest 全部通过才标记 completed |
| **不支持跨模块 merge** | 一次 Merge 只针对一个模块 |
| **Migration 不自动执行** | 只生成 SQL，人工执行 |

---

## 七、Artifact 增强 (追溯)

```python
class Artifact(BaseModel):  # 更新现有模型
    # ... 现有字段
    generator_name: str       # 🆕 "EntityGenerator"
    generator_version: str    # 🆕 "v1"
    created_by: UUID | None   # 🆕 谁触发的生成
    review_user: UUID | None  # 🆕 谁审批的
    review_time: str | None   # 🆕 审批时间
```

---

## 八、M7.2 文件规划

```
app/ai/
├── merge/
│   ├── __init__.py
│   ├── models.py          # MergeRequest + ConflictLog
│   ├── conflict.py        # ConflictChecker
│   ├── diff_gen.py        # DiffGenerator
│   ├── applier.py         # MergeApplier (写入 + 注册)
│   └── verifier.py        # MergeVerifier (ruff + mypy)
├── models.py              # ✏️ Artifact 增强
├── service.py             # ✏️ MergeService
└── router.py              # ✏️ /merge/* 端点
```

---

## 九、M7.3 Preview: Module Sandbox

Merge 完成后，M7.3 可以验证生成的模块：

```
Generated Module
    │
    ▼
Sandbox Environment
    │
    ├── 启动隔离的 FastAPI
    ├── 运行 pytest
    ├── 执行 E2E 测试
    └── 返回 SandboxReport
```

---

确认后进入 M7.2 Coding。
