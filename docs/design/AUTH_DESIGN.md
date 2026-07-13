# M2 Auth 模块 —— 领域设计

> 状态: Coding Phase 2A ✅ | 版本: V3 | 日期: 2026-07-07

---

## 一、模块定位

Auth 模块负责 **身份认证（Authentication）** 和 **访问控制（Authorization）**。

是所有其他模块的**前置依赖** —— BaseData、Brand、Purchase 等模块的 `created_by` / `updated_by` 均引用 `User.id`。

---

## 二、领域模型

### 2.1 实体关系图

```
┌──────────┐          ┌──────────────┐          ┌──────────┐
│   User   │────────→│   UserRole   │←────────│   Role   │
│  (聚合根) │ 1     N  │              │  N     1  │  (聚合根) │
└──────────┘          └──────────────┘          └──────────┘
                                                       │
                                                       │ 1
                                                       │
                                                       ↓ N
                                                ┌──────────────┐
                                                │RolePermission│
                                                └──────────────┘
                                                       │
                                                       │ N
                                                       │
                                                       ↓ 1
                                                ┌──────────────┐
                                                │  Permission  │
                                                │   (聚合根)    │
                                                └──────────────┘
```

5 张表，3 个聚合根：

| 表 | 类型 | 说明 |
|----|------|------|
| User | 聚合根 | 独立管理，有自己的 Repository |
| Role | 聚合根 | 独立管理，有自己的 Repository |
| Permission | 聚合根 | 独立 Aggregate，不依附于 Role；可单独创建、修改、删除 |
| UserRole | 关联 | 用户-角色 N:N |
| RolePermission | 关联 | 角色-权限 N:N |

**Permission 独立 Aggregate 的意图**：

- 权限可提前定义，不依赖角色存在
- 权限可单独查询（例如列出系统所有可用权限）
- 删除权限时，级联清除 RolePermission 关联
- 后续 Data Permission（行级权限）通过继承 Permission 实现

---

### 2.2 User（聚合根）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, default=uuid4 | |
| username | str(50) | UNIQUE, NOT NULL | 登录名 |
| email | str(255) | UNIQUE, NOT NULL | |
| password_hash | str(255) | NOT NULL | bcrypt 哈希 |
| display_name | str(100) | NOT NULL | 显示名 |
| status | UserStatus(Enum) | NOT NULL, default=ACTIVE | ACTIVE / INACTIVE / LOCKED |
| last_login_at | datetime | nullable | 最后登录时间 |
| created_at | datetime | NOT NULL | 继承 TimestampMixin |
| updated_at | datetime | NOT NULL | 继承 TimestampMixin |

**Status 枚举 (UserStatus)**：

```python
class UserStatus(enum.StrEnum):
    ACTIVE = "active"       # 正常
    INACTIVE = "inactive"   # 已停用
    LOCKED = "locked"       # 已锁定（M2 暂不使用）
```

**状态机**：
```
ACTIVE ──→ INACTIVE   (管理员停用)
ACTIVE ──→ LOCKED     (密码错误 5 次，M2 暂不实现)
INACTIVE ──→ ACTIVE   (管理员启用)
```

---

### 2.3 Role（聚合根）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(50) | UNIQUE, NOT NULL | admin / manager / operator |
| name | str(100) | NOT NULL | 管理员 / 经理 / 操作员 |
| description | str(255) | nullable | |
| is_system | bool | NOT NULL, default=False | 系统内置角色不可删除 |
| created_at | datetime | NOT NULL | |
| updated_at | datetime | NOT NULL | |

---

### 2.4 Permission（聚合根）

Permission 是独立 Aggregate Root，有自己的 Repository，不依附于 Role。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(150) | UNIQUE, NOT NULL | 格式: `module.resource.action` |
| name | str(100) | NOT NULL | 中文描述 |
| module | str(50) | NOT NULL | 模块: auth / purchase / inventory / sales / finance |
| resource | str(50) | NOT NULL | 资源: user / role / order / product |
| action | str(50) | NOT NULL | 操作: create / read / update / delete / approve / export |
| created_at | datetime | NOT NULL | |

**命名规范**: `code` 必须匹配 `{module}.{resource}.{action}` 格式。

示例：
```
auth.user.create        → 创建用户
auth.user.read          → 查看用户
auth.role.manage        → 管理角色（含分配权限）
purchase.order.create   → 创建采购订单
purchase.order.approve  → 审批采购订单
inventory.stock.read    → 查看库存
inventory.stock.adjust  → 库存调整
```

**设计意图**：
- 三级命名空间，模块 → 资源 → 操作，级别清晰
- `module` 与权限所属的业务模块一一对应
- `action` 不限于 CRUD，可扩展 `approve`、`export`、`adjust` 等业务操作
- 后续扩展 Fine-Grained Permission 时不破坏现有结构

---

### 2.5 UserRole（关联）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| user_id | UUID | FK → User, CASCADE, PK | |
| role_id | UUID | FK → Role, CASCADE, PK | |
| assigned_by | UUID | FK → User, SET NULL, nullable | 分配人 |
| assigned_at | datetime | NOT NULL | 分配时间 |

---

### 2.6 RolePermission（关联）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| role_id | UUID | FK → Role, CASCADE, PK | |
| permission_id | UUID | FK → Permission, CASCADE, PK | |

---

## 三、业务规则

| # | 规则 | 类型 | 实现位置 |
|---|------|------|---------|
| R1 | username 唯一 | 不变量 | DB UNIQUE + Service 校验 |
| R2 | email 唯一 | 不变量 | DB UNIQUE + Service 校验 |
| R3 | 明文密码长度 ≥ 8 位 | 业务规则 | Service 校验 |
| R4 | 不能删除/停用自己 | 业务规则 | Service 校验 |
| R5 | is_system=True 的角色不可删除 | 不变量 | Service 校验 |
| R6 | Permission.code 格式: `module.resource.action` | 约定 | Schema 校验 |
| R7 | 停用用户(status=inactive) → 禁止登录 | 业务规则 | Service 校验 |
| R8 | 删除角色 → 级联删除 UserRole + RolePermission | 业务规则 | FK CASCADE |
| R9 | 删除权限 → 级联删除 RolePermission | 业务规则 | FK CASCADE |
| R10 | 用户名/密码错误 → 不区分提示"用户名或密码错误" | 安全规则 | Service |

---

## 四、领域事件

| 事件 | 触发时机 | 消费者 |
|------|----------|--------|
| UserCreated | 管理员创建用户成功 | AuditLog |
| UserLoggedIn | 登录成功 | AuditLog, 更新 last_login_at |
| UserStatusChanged | 状态变更 (active↔inactive) | 会话清理 |
| RoleAssigned | 角色分配给用户 | AuditLog |
| RoleRevoked | 角色从用户移除 | AuditLog |
| PermissionCreated | 新权限注册 | 权限缓存刷新 |

---

## 五、Token 设计

### 5.1 M2 实现（Access Token Only）

```
POST /api/v1/auth/login
  → 返回 { access_token: "eyJ...", expires_in: 7200 }
```

- 类型: JWT (HS256)
- 过期: 2 小时
- 载荷: { sub: user_id, username: username, roles: [...] }
- 存储: 客户端内存 / localStorage

### 5.2 演进规划（Refresh Token）

M2 不实现 Refresh Token，但设计上预留：

```
🔮 M3+ 上线前增加:

POST /api/v1/auth/refresh
  → 返回 { access_token: "eyJ...", refresh_token: "eyJ..." }

Token 对:
  access_token   → 15 分钟（短有效期，降低泄露风险）
  refresh_token  → 7 天（长有效期，存储于 httpOnly cookie 或安全存储）

Refresh Token 存储:
  数据库表 refresh_tokens
    id, user_id, token_hash, expires_at, revoked, created_at

撤销策略:
  - 用户修改密码 → 吊销所有 refresh_token
  - 管理员停用用户 → 吊销所有 refresh_token
```

**当前不实现的原因**: M2 仅需 Access Token 即可完成模块开发和调试。Refresh Token 涉及的 cookie 安全策略、httpOnly、CSRF 保护等需要配合前端部署架构统一设计。

---

## 六、多租户扩展说明

M2 为单租户模式，但模型设计预留多租户扩展点：

```
🔮 多租户上线时变更:

1. User 表增加字段:
   tenant_id: UUID FK → Tenant

2. 新增 Tenant 聚合根:
   Tenant
     id, code, name, status, plan, expires_at

3. 权限模型不变 —— RBAC 本身是租户无关的:
   - Role / Permission 为全局定义
   - UserRole 隐式绑定租户（通过 User.tenant_id）
   - 后续如需租户级角色 → 增加 TenantRole

4. 查询隔离:
   - Repository 层增加 tenant_id 过滤
   - 通过请求上下文注入当前租户
```

**当前不实现的原因**: M2 为单租户 ERP Builder 自身使用。多租户需求尚未确定（SaaS 模式 vs 私有部署），提前实现会引入不必要的抽象。

---

## 七、API 设计

### 7.1 认证

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/v1/auth/login | 登录，返回 JWT access_token | 否 |
| GET | /api/v1/auth/me | 当前用户信息 + 权限列表 | JWT |

### 7.2 用户管理

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /api/v1/auth/users | 创建用户 | auth.user.create |
| GET | /api/v1/auth/users | 用户列表（分页） | auth.user.read |
| GET | /api/v1/auth/users/{id} | 用户详情 | auth.user.read |
| PATCH | /api/v1/auth/users/{id} | 更新用户 | auth.user.update |
| DELETE | /api/v1/auth/users/{id} | 停用用户 | auth.user.delete |
| PATCH | /api/v1/auth/users/{id}/roles | 分配角色 | auth.role.manage |

### 7.3 角色管理

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /api/v1/auth/roles | 创建角色 | auth.role.manage |
| GET | /api/v1/auth/roles | 角色列表 | auth.role.manage |
| DELETE | /api/v1/auth/roles/{id} | 删除角色 | auth.role.manage |

### 7.4 权限管理

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | /api/v1/auth/permissions | 创建权限 | auth.role.manage |
| GET | /api/v1/auth/permissions | 权限列表 | auth.role.manage |

---

## 八、预设数据（Seed）

启动时自动创建，`is_system=True` 不可删除。

### 角色

```
admin    → 系统管理员 (is_system=True)
manager  → 经理
operator → 操作员
```

### 权限

```
auth.user.create    → 创建用户
auth.user.read      → 查看用户
auth.user.update    → 更新用户
auth.user.delete    → 删除/停用用户
auth.role.manage    → 管理角色和权限
```

### 管理员账户

管理员在**首次启动时**通过环境变量创建，不硬编码密码：

```
环境变量:
  ERP_ADMIN_USERNAME=admin        (默认: admin)
  ERP_ADMIN_PASSWORD=<必填>       (未设置则跳过 Seed)
  ERP_ADMIN_EMAIL=admin@erp.local (默认: admin@erp.local)
```

**约束**：
- `ERP_ADMIN_PASSWORD` 未设置 → 启动日志输出警告，跳过管理员创建
- 密码仅在首次创建时使用，后续修改通过 API
- `ERP_ADMIN_PASSWORD` 不写入数据库日志或任何明文文件

---

## 九、Schema DTO（API 边界）

### 请求

| Schema | 字段 |
|--------|------|
| `UserCreate` | username(3-50), email, password(8-128), display_name(1-100) |
| `UserUpdate` | email?, display_name?, status?(UserStatus) |
| `RoleCreate` | code(2-50), name(1-100), description? |
| `RoleUpdate` | name?, description? |
| `LoginRequest` | username, password |
| `AssignRolesRequest` | role_ids: list[UUID] (≥1) |

### 响应

| Schema | 字段 | 备注 |
|--------|------|------|
| `UserResponse` | id, username, email, display_name, status, last_login_at, created_at, updated_at | from_attributes=True |
| `RoleResponse` | id, code, name, description, is_system, created_at, updated_at | from_attributes=True |
| `PermissionResponse` | id, code, name, module, resource, action, created_at | from_attributes=True |
| `LoginResponse` | access_token, token_type:"bearer", expires_in:7200 | |
| `UserMeResponse` | +roles: list[str], +permissions: list[str] | |

### 响应格式

所有 API 统一使用 `APIResponse[T]` 包装：
```json
{"code": 0, "message": "success", "data": { ... }}
```

列表使用 `PageResponse[T]` 分页：
```json
{"items": [...], "total": 100, "page": 1, "page_size": 20, "pages": 5}
```

---

## 十、边界

| 项目 | 说明 |
|------|------|
| ✅ M2 实现 | User/Role/Permission CRUD + JWT 登录 + RBAC 角色分配 + Seed |
| ❌ M2 不做 | Data Permission（行级权限）、OAuth/SSO、密码重试锁定、多因子认证、Refresh Token、多租户 |
| 🔮 演进规划 | Refresh Token（M3+）、多租户（待定）、Data Permission（M4+）、行级权限 |

---

## 十一、依赖

```
app/shared/
├── base_model.py        → User, Role, Permission 继承 BaseModel
├── base_repository.py   → 3 个独立 Repository（UserRepo / RoleRepo / PermissionRepo）
├── base_schema.py       → APIResponse, PageRequest/Response
└── base_service.py      → 3 个独立 Service

app/core/
├── exceptions.py        → NotFoundError, ConflictError, UnauthorizedError
└── events.py            → DomainEvent, event_bus
```

**不依赖任何业务模块。**

---

确认后进入 Coding 阶段。
