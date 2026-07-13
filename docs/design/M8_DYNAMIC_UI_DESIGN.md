# M8 Dynamic UI Runtime Design

> 状态: Review V1 | 日期: 2026-07-08
> 原则: UI = Metadata Renderer，不保存业务逻辑

---

## 一、架构

```
Backend Metadata (M6)               Frontend Runtime (M8)
─────────────────────               ─────────────────────
ModuleManifest                       MetadataLoader
EntityContext         ──→ API ──→    PageRenderer
CapabilityRegistry                   FormRenderer
WorkflowDefinition                   TableRenderer
Permission                           ActionRenderer
                                     MenuRenderer
```

---

## 二、UI Schema 模型

### 2.1 UISchema 顶层

```python
@dataclass
class UISchema:
    """模块的完整 UI 描述 —— 驱动前端渲染"""

    module_name: str              # "purchase"
    module_display: str           # "采购管理"
    menu: MenuNode                # 菜单树
    pages: list[PageSchema]       # 页面列表
```

### 2.2 Page 类型

```python
@dataclass
class PageSchema:
    """页面定义"""
    route: str                    # "/purchase/orders"
    title: str                    # "采购订单"
    page_type: str                # "list" | "form" | "detail" | "dashboard"
    entity: str                   # "PurchaseOrder"
    list_config: ListConfig | None
    form_config: FormConfig | None
    detail_config: DetailConfig | None
    actions: list[ActionSchema]   # 操作按钮
    permission: str               # 页面级权限
```

### 2.3 ListConfig（列表页）

```python
@dataclass
class ListConfig:
    """列表页配置"""
    columns: list[ColumnDef]      # 显示的列
    filters: list[FilterDef]      # 筛选条件
    default_sort: str             # "created_at,desc"
    page_size: int = 20
    row_actions: list[ActionSchema]  # 行操作

@dataclass
class ColumnDef:
    field: str                    # "po_no"
    header: str                   # "采购单号"
    width: int | None
    sortable: bool = True
    filterable: bool = False
    format: str | None            # "date" | "currency" | "status_badge"

@dataclass
class FilterDef:
    field: str                    # "status"
    label: str                    # "状态"
    filter_type: str              # "select" | "text" | "date_range"
    options: list[dict] | None    # [{"value": "draft", "label": "草稿"}, ...]
```

### 2.4 FormConfig（表单页）

```python
@dataclass
class FormConfig:
    """表单配置"""
    fields: list[FormField]       # 表单字段
    submit_action: str            # "purchase.order.create"
    layout: str = "vertical"      # "vertical" | "horizontal" | "grid"

@dataclass
class FormField:
    field: str                    # "supplier_id"
    label: str                    # "供应商"
    field_type: str               # "text" | "select" | "date" | "number" | "textarea"
    required: bool
    placeholder: str | None
    source: str | None            # 数据源: "api://basedata/bp?bp_type=supplier"
    default: str | None
    validation: dict | None       # {"min": 1, "max": 100}
```

### 2.5 DetailConfig（详情页）

```python
@dataclass
class DetailConfig:
    """详情配置"""
    sections: list[DetailSection]

@dataclass
class DetailSection:
    title: str                    # "基本信息"
    fields: list[str]             # ["po_no", "supplier_id", "order_date", "status"]
    layout: str = "grid"
```

### 2.6 ActionSchema（操作按钮）

```python
@dataclass
class ActionSchema:
    """操作按钮"""
    name: str                     # "confirm"
    label: str                    # "确认"
    action_type: str              # "api_call" | "state_transition" | "navigate"
    http_method: str | None       # "POST"
    http_path: str | None         # "/api/v1/purchase/orders/{id}/confirm"
    capability: str               # "purchase.order.confirm"
    pre_state: str | None         # 前置状态
    post_state: str | None        # 后置状态
    confirm_dialog: str | None    # "确认采购订单?"
```

---

## 三、UI Runtime —— 渲染引擎

### 3.1 核心流程

```
GET /api/v1/ui/{module}/schema
    │
    ▼ 返回 UISchema JSON
Frontend MetadataLoader
    │
    ├── MenuRenderer    → 侧边栏菜单
    ├── PageRenderer    → 根据 page_type 选择渲染器
    │   ├── ListPage    → AG Grid + Filters + RowActions
    │   ├── FormPage    → shadcn/ui Form + Validation
    │   └── DetailPage  → Card Sections + Timeline
    └── ActionRenderer  → 按钮 + 权限检查 + 状态判断
```

### 3.2 API

```
GET  /api/v1/ui/{module}/schema        → 模块完整 UISchema
GET  /api/v1/ui/{module}/pages/{name}  → 单个页面 Schema
GET  /api/v1/ui/menu                    → 全系统菜单树
```

### 3.3 菜单自动生成

```json
{
  "menu": [
    {
      "label": "采购管理",
      "icon": "ShoppingCart",
      "children": [
        {"label": "采购订单", "route": "/purchase/orders", "permission": "purchase.order.read"},
        {"label": "收货管理", "route": "/purchase/receipts", "permission": "purchase.receipt.read"}
      ]
    },
    {
      "label": "库存管理",
      "icon": "Package",
      "children": [
        {"label": "货权库存", "route": "/inventory/contract-stocks", "permission": "inventory.stock.read"},
        {"label": "实物库存", "route": "/inventory/warehouse-stocks", "permission": "inventory.stock.read"}
      ]
    }
  ]
}
```

**生成逻辑**：读取 `ModuleManifest.ui_pages` → 按模块分组 → 按 permission 过滤。

---

## 四、权限绑定

### 4.1 渲染时检查

```typescript
// Frontend pseudo-code
function renderAction(action: ActionSchema, userPermissions: Set<string>) {
    if (!userPermissions.has(action.capability)) {
        return null;  // 无权限，不渲染
    }
    return <Button ... />;
}

function renderPage(page: PageSchema, userPermissions: Set<string>) {
    if (!userPermissions.has(page.permission)) {
        return <Forbidden />;
    }
    return <PageRenderer page={page} />;
}
```

### 4.2 Capability → UI 映射

| Capability | UI 元素 |
|-----------|---------|
| `{module}.{entity}.create` | 新增按钮 + 创建表单 |
| `{module}.{entity}.read` | 列表页面 + 详情页面 |
| `{module}.{entity}.update` | 编辑按钮 + 编辑表单 |
| `{module}.{entity}.delete` | 删除按钮 |
| `{module}.{entity}.confirm` | 确认按钮（状态转换） |

---

## 五、Workflow 集成

### 5.1 状态驱动操作

```json
{
  "entity": "PurchaseOrder",
  "state_field": "status",
  "state_actions": {
    "draft": [
      {"name": "confirm", "label": "确认", "capability": "purchase.order.confirm"}
    ],
    "confirmed": [
      {"name": "create_receipt", "label": "创建收货单", "capability": "purchase.receipt.create"}
    ],
    "complete": [
      {"name": "close", "label": "关结", "capability": "purchase.order.close"}
    ]
  }
}
```

**生成逻辑**：读取 `WorkflowDefinition.transitions` → 按 `from_state` 分组 → 生成 `state_actions`。

### 5.2 渲染

```
详情页:
  Status: [draft] ▼
  
  [确认] [取消] [编辑]
   ↑ 只有当前状态允许的操作才渲染
```

---

## 六、前端技术栈

| 层 | 技术 | 用途 |
|----|------|------|
| MetadataLoader | TanStack Query | `GET /api/v1/ui/{module}/schema` |
| PageRenderer | React + shadcn/ui | 根据 page_type 渲染 |
| TableRenderer | AG Grid Community | 列表页 |
| FormRenderer | shadcn/ui Form | 创建/编辑表单 |
| ActionRenderer | Permissions + State | 按钮 + 权限 + 状态检查 |
| MenuRenderer | TanStack Router | 侧边栏菜单 |

---

## 七、后端 API

```
GET /api/v1/ui/menu                          → 全系统菜单树
GET /api/v1/ui/{module}/schema               → 模块 UISchema
GET /api/v1/ui/{module}/pages/{entity}        → 单个实体页面
GET /api/v1/ui/{module}/actions/{entity}      → 实体操作按钮
GET /api/v1/ui/state-actions/{entity}/{state} → 状态驱动操作
```

### 实现

```python
@router.get("/ui/{module}/schema")
async def get_module_ui_schema(module: str):
    """从 ModuleManifest 生成 UISchema"""
    manifest = ModuleRegistry.get(module)
    if not manifest:
        return APIResponse.fail(404, f"模块 {module} 不存在")

    pages = []
    for page_meta in manifest.ui_pages:
        pages.append(PageSchema(
            route=page_meta.route,
            title=page_meta.title,
            page_type=page_meta.page_type,
            entity=page_meta.entity,
            list_config=ListConfig(
                columns=[ColumnDef(field=c, header=c) for c in page_meta.columns],
            ) if page_meta.page_type == "list" else None,
            actions=[ActionSchema(name=a, label=a) for a in page_meta.actions],
            permission=f"{module}.{page_meta.entity}.read",
        ))

    return APIResponse.ok(UISchema(
        module_name=module,
        module_display=manifest.display_name,
        menu=MenuNode(label=manifest.display_name, children=...),
        pages=pages,
    ))
```

---

## 八、M8 文件规划

```
backend/app/ai/
├── ui/
│   ├── __init__.py
│   ├── models.py          # UISchema / PageSchema / ListConfig / FormConfig 等 dataclass
│   ├── generator.py       # UISchemaGenerator (from ModuleManifest)
│   └── router.py          # /ui/* API

frontend/src/
├── metadata/
│   ├── loader.ts          # MetadataLoader (TanStack Query)
│   └── types.ts           # TypeScript 类型
├── renderers/
│   ├── PageRenderer.tsx
│   ├── TableRenderer.tsx  # AG Grid
│   ├── FormRenderer.tsx   # shadcn/ui Form
│   └── ActionRenderer.tsx
└── hooks/
    └── useUISchema.ts     # useQuery → /ui/schema
```

---

## 九、M8 边界

| ✅ M8 | ❌ 不做 |
|-------|--------|
| UISchema dataclass + API | 完整前端应用 |
| 后端 UI Schema 生成 | React 组件库 |
| 菜单/列表/表单 Schema | 拖拽页面编辑器 |
| 权限绑定 Action | 自定义 CSS |
| Workflow 状态驱动操作 | 前端路由引擎 |

---

## 十、整体系统完成度

```
M0-M5: Core ERP               ✅
M6:    AI Context/Capability   ✅
M7:    AI Builder Pipeline     ✅
M7.1:  Builder Runtime         ✅
M7.2:  Merge Pipeline          ✅
M7.3:  Module Sandbox          ✅
M8:    Dynamic UI Runtime      ⏳ 设计中
```

---

确认后进入 M8 Coding。
