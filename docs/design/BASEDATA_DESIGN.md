# M3-1 BaseData 模块 —— 架构设计

> 状态: Review V1.1 | 日期: 2026-07-07

---

## 一、模块定位

BaseData 是 ERP 系统的**公共基础资料中心**，只提供 Master Data CRUD。

**原则**：
- 纯数据管理，无业务逻辑
- 无 Workflow（全部直接 CRUD）
- 其他模块（Purchase、Inventory、Sales）**引用** BaseData，不反向依赖
- 全部端点需 JWT 认证 + RBAC 权限
- 权限统一格式: `basedata.{resource}.{action}`

---

## 二、实体关系图（ERD）

```
┌──────────┐       ┌──────────────┐       ┌──────────┐
│ Company  │       │  Department  │       │ Employee │
│          │←──────│              │←──────│          │
│          │ 1   N │ parent_id◇   │ 1   N │ user_id──┼──→ Auth.User
└──────────┘       └──────────────┘       └──────────┘

┌─────────────────┐
│ BusinessPartner  │──────┬────→ BPContact     (1:N)
│   (bp)           │      ├────→ BPAddress     (1:N)
│ bp_type          │      └────→ BPBankAccount (1:N)
└─────────────────┘

┌──────────┐       ┌──────────────┐       ┌──────────┐
│Warehouse │──→────│WarehouseLoc  │       │ Category │
│          │ 1   N │              │       │          │
│ code     │       │ bin_code     │       │ parent_id◇
│ name     │       │ loc_type     │       │ cat_type │
└──────────┘       └──────────────┘       └──────────┘

┌──────────┐       ┌──────────┐
│   Unit   │       │ Currency │
└──────────┘       └──────────┘
```

9 个实体（含 BP 4 表）。

---

## 三、表定义

### 3.1 Company（公司）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(20) | UNIQUE, NOT NULL | |
| name | str(100) | NOT NULL | |
| short_name | str(50) | nullable | |
| tax_id | str(50) | nullable | |
| phone | str(30) | nullable | |
| address | str(255) | nullable | |
| is_active | bool | default=True | |
| created_at/updated_at | datetime | | 继承 BaseModel |

---

### 3.2 Department（部门）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(30) | UNIQUE, NOT NULL | |
| name | str(100) | NOT NULL | |
| parent_id | UUID | FK→Department, nullable | 树形自引用 |
| company_id | UUID | FK→Company, NOT NULL | |
| manager_id | UUID | FK→Employee, nullable | |
| level | int | default=0 | 冗余深度 |
| sort_order | int | default=0 | |
| is_active | bool | default=True | |
| created_at/updated_at | datetime | | 继承 BaseModel |

---

### 3.3 Employee（员工）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(30) | UNIQUE, NOT NULL | 工号 |
| name | str(100) | NOT NULL | |
| user_id | UUID | FK→User, UNIQUE, nullable | 一个 User 只能关联一个 Employee |
| department_id | UUID | FK→Department, NOT NULL | |
| position | str(50) | nullable | |
| phone | str(30) | nullable | |
| email | str(255) | nullable | |
| entry_date | date | nullable | |
| is_active | bool | default=True | |
| created_at/updated_at | datetime | | 继承 BaseModel |

---

### 3.4 Warehouse（仓库）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(20) | UNIQUE, NOT NULL | |
| name | str(100) | NOT NULL | |
| warehouse_type | str(20) | NOT NULL | raw / finished / spare / return |
| address | str(255) | nullable | |
| company_id | UUID | FK→Company, NOT NULL | |
| is_active | bool | default=True | |
| created_at/updated_at | datetime | | 继承 BaseModel |

---

### 3.5 WarehouseLocation（库位）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| warehouse_id | UUID | FK→Warehouse, NOT NULL | |
| code | str(30) | NOT NULL | 库位编码 |
| loc_type | str(20) | NOT NULL | aisle / shelf / bin / floor |
| parent_id | UUID | FK→WarehouseLocation, nullable | 上级库位（树形） |
| capacity | Decimal | nullable | 容量 |
| uom_id | UUID | FK→Unit, nullable | 容量单位 |
| is_active | bool | default=True | |
| created_at/updated_at | datetime | | 继承 BaseModel |

**唯一约束**: `(warehouse_id, code)` 同仓库下库位编码唯一。

---

### 3.6 Unit（计量单位）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(10) | UNIQUE, NOT NULL | pcs / kg / m / box |
| name | str(50) | NOT NULL | |
| unit_type | str(20) | NOT NULL | quantity / weight / length / volume |
| decimal_places | int | default=0 | |
| is_active | bool | default=True | |
| created_at/updated_at | datetime | | 继承 BaseModel |

---

### 3.7 Currency（币种）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(5) | UNIQUE, NOT NULL | CNY / USD / EUR |
| name | str(50) | NOT NULL | |
| symbol | str(5) | NOT NULL | ¥ / $ / € |
| exchange_rate | Decimal(18,6) | default=1.0 | |
| is_base | bool | default=False | 唯一本币 |
| is_active | bool | default=True | |
| created_at/updated_at | datetime | | 继承 BaseModel |

---

### 3.8 Category（分类）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(30) | UNIQUE, NOT NULL | |
| name | str(100) | NOT NULL | |
| parent_id | UUID | FK→Category, nullable | 树形自引用 |
| cat_type | str(20) | NOT NULL | material / product / bp / document |
| level | int | default=0 | 冗余深度 |
| sort_order | int | default=0 | |
| is_active | bool | default=True | |
| created_at/updated_at | datetime | | 继承 BaseModel |

**用途**: 统一分类体系，M3-2 Material 和 M3-3 Supplier 均引用 Category。

---

### 3.9 BusinessPartner 四表

#### 3.9.1 BusinessPartner（bp 主表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| code | str(30) | UNIQUE, NOT NULL | |
| name | str(200) | NOT NULL | |
| bp_type | str(20) | NOT NULL | customer / supplier / both |
| tax_id | str(50) | nullable | 税号 |
| category_id | UUID | FK→Category, nullable | 分类 |
| company_id | UUID | FK→Company, NOT NULL | |
| payment_terms | str(100) | nullable | 付款条件 |
| credit_days | int | default=0 | 账期（天） |
| ext_json | JSON | nullable | 真正不可预测的扩展属性 |
| is_active | bool | default=True | |
| created_at/updated_at | datetime | | 继承 BaseModel |

#### 3.9.2 BPContact（联系人）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| bp_id | UUID | FK→BusinessPartner, CASCADE, NOT NULL | |
| name | str(100) | NOT NULL | |
| mobile | str(30) | NOT NULL | |
| email | str(255) | nullable | |
| position | str(50) | nullable | 职务 |
| is_primary | bool | default=False | 是否首要联系人 |
| created_at/updated_at | datetime | | 继承 BaseModel |

**唯一约束**: `(bp_id, mobile)`

#### 3.9.3 BPAddress（地址）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| bp_id | UUID | FK→BusinessPartner, CASCADE, NOT NULL | |
| address_type | str(20) | NOT NULL | billing / shipping / warehouse |
| country | str(50) | nullable | 国家 |
| province | str(50) | nullable | 省/州 |
| city | str(50) | nullable | 城市 |
| line1 | str(255) | NOT NULL | 地址行1 |
| line2 | str(255) | nullable | 地址行2 |
| postal_code | str(20) | nullable | 邮编 |
| is_default | bool | default=False | |
| created_at/updated_at | datetime | | 继承 BaseModel |

#### 3.9.4 BPBankAccount（银行账户）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | |
| bp_id | UUID | FK→BusinessPartner, CASCADE, NOT NULL | |
| bank_name | str(100) | NOT NULL | |
| account_name | str(100) | NOT NULL | |
| account_no | str(50) | NOT NULL | |
| swift_code | str(20) | nullable | |
| currency_code | str(5) | NOT NULL | 币种（CNY/USD） |
| is_default | bool | default=False | |
| created_at/updated_at | datetime | | 继承 BaseModel |

---

## 四、Repository 设计

每实体一个 Repository，继承 `BaseRepository[T]`。

| Repository | 新增方法 |
|------------|---------|
| `CompanyRepository` | `get_by_code` |
| `DepartmentRepository` | `list_by_company`, `list_children`, `get_by_code` |
| `EmployeeRepository` | `get_by_user_id`, `list_by_department`, `get_by_code` |
| `WarehouseRepository` | `list_by_company`, `get_by_code` |
| `WarehouseLocationRepository` | `list_by_warehouse`, `get_by_code(warehouse_id, code)` |
| `UnitRepository` | `get_by_code` |
| `CurrencyRepository` | `get_by_code`, `get_base` |
| `CategoryRepository` | `list_by_type`, `list_children`, `get_by_code` |
| `BusinessPartnerRepository` | `get_by_code`, `list_by_type` |
| `BPContactRepository` | `list_by_bp`, `get_primary(bp_id)` |
| `BPAddressRepository` | `list_by_bp`, `get_default(bp_id, type)` |
| `BPBankAccountRepository` | `list_by_bp`, `get_default(bp_id)` |

---

## 五、Service 设计

全部 CRUD，无 Workflow。

| Service | 特有逻辑 |
|---------|---------|
| `CompanyService` | 无 |
| `DepartmentService` | 禁止循环 parent_id；manager_id 必须是 Employee |
| `EmployeeService` | user_id 唯一（一人一账号）；校验 dept 存在 |
| `WarehouseService` | 删除时检查无 Location 子节点 |
| `WarehouseLocationService` | 同 warehouse 下 code 唯一；禁止循环 parent_id |
| `UnitService` | 无 |
| `CurrencyService` | 设 is_base 时取消其他本币 |
| `CategoryService` | 禁止循环 parent_id |
| `BusinessPartnerService` | 创建时 auto-generate code（如未提供）；级联软删除 contacts/addresses/banks |
| `BPContactService` | bp_id + mobile 唯一 |
| `BPAddressService` | 设 default 时取消同类型其他 default |
| `BPBankAccountService` | 设 default 时取消其他 default |

---

## 六、API 规划

### 6.1 路由前缀

```
/api/v1/basedata/{resource}
```

### 6.2 标准端点（每个 resource 6 个）

```
POST   /api/v1/basedata/{resource}          # 新增
GET    /api/v1/basedata/{resource}          # 分页列表
GET    /api/v1/basedata/{resource}/{id}     # 详情
PUT    /api/v1/basedata/{resource}/{id}     # 全量更新
PATCH  /api/v1/basedata/{resource}/{id}     # 部分更新
DELETE /api/v1/basedata/{resource}/{id}     # 软删除
```

### 6.3 Resource 列表

```
companies          → Company
departments        → Department
employees          → Employee
warehouses         → Warehouse
warehouse-locations → WarehouseLocation
units              → Unit
currencies         → Currency
categories         → Category
business-partners  → BusinessPartner
bp-contacts        → BPContact（query: ?bp_id=）
bp-addresses       → BPAddress（query: ?bp_id=）
bp-bank-accounts   → BPBankAccount（query: ?bp_id=）
```

### 6.4 特殊端点

```
GET /api/v1/basedata/departments/tree?company_id=
GET /api/v1/basedata/categories/tree?cat_type=
GET /api/v1/basedata/warehouses/{id}/locations
```

### 6.5 响应格式

统一 `APIResponse[T]`，列表用 `PageResponse[T]`。

---

## 七、权限设计

全部权限统一格式: `basedata.{resource}.{action}`

```
# Company
basedata.company.create / read / update / delete

# Department
basedata.department.create / read / update / delete

# Employee
basedata.employee.create / read / update / delete

# Warehouse + Location
basedata.warehouse.create / read / update / delete
basedata.warehouse-location.create / read / update / delete

# Unit
basedata.unit.create / read / update / delete

# Currency
basedata.currency.create / read / update / delete

# Category
basedata.category.create / read / update / delete

# BusinessPartner + 子表
basedata.bp.create / read / update / delete
basedata.bp-contact.create / read / update / delete
basedata.bp-address.create / read / update / delete
basedata.bp-bank-account.create / read / update / delete
```

共 13 × 4 = 52 条新权限，admin 角色自动获得全部。

---

## 八、模块结构

```
modules/basedata/
├── __init__.py
├── models.py            # 12 个 ORM 实体 + 枚举
├── schemas.py           # 12 组 Create/Update/Response
├── repository.py        # 12 个 Repository
├── service.py           # 12 个 Service
├── router.py            # 标准 CRUD + 特殊端点
└── events.py            # 领域事件
```

**BP 子表与其主表在同一模块内，Router 放在同一文件**（BaseData 实体虽多但逻辑简单，拆文件反而增加跳转成本）。

---

## 九、权限 Seed 扩展

M3-1 在 `modules/auth/seed.py` 增加 52 条 `basedata.*` 权限，admin 角色自动获得全部。

---

## 十、依赖

```
app/shared/       → BaseModel, BaseRepository, BaseSchema
app/core/         → exceptions, events
app/modules/auth/ → CurrentUser, get_current_user, require_permission
```

**不依赖 Purchase、Inventory、Sales。**

---

## 十一、边界

| ✅ M3-1 | ❌ 不做 |
|---------|--------|
| 12 个实体完整 CRUD | Material（M3-2） |
| BP 四表（主表 + contact/address/bank） | Stock / Inventory（M3-2） |
| Warehouse + Location | Purchase Order（M3-3） |
| Category 统一分类 | 多租户 |
| 52 条权限 + Seed | Workflow |

---

确认后进入 Coding。
