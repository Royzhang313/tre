"""UI Schema 数据模型 —— Metadata Driven UI"""

from dataclasses import dataclass, field


@dataclass
class ColumnDef:
    field: str
    header: str
    width: int | None = None
    sortable: bool = True
    filterable: bool = False
    format: str | None = None  # "date" | "currency" | "status_badge"


@dataclass
class FilterDef:
    field: str
    label: str
    filter_type: str = "text"  # "select" | "text" | "date_range"
    options: list[dict] | None = None


@dataclass
class ActionSchema:
    name: str
    label: str
    action_type: str = "api_call"  # "api_call" | "state_transition" | "navigate"
    http_method: str | None = None
    http_path: str | None = None
    capability: str = ""
    pre_state: str | None = None
    post_state: str | None = None
    confirm_dialog: str | None = None


@dataclass
class FormField:
    field: str
    label: str
    field_type: str = "text"  # "text" | "select" | "date" | "number" | "textarea"
    required: bool = False
    placeholder: str | None = None
    source: str | None = None  # "api://basedata/bp?bp_type=supplier"
    default: str | None = None
    validation: dict | None = None


@dataclass
class ListConfig:
    columns: list[ColumnDef] = field(default_factory=list)
    filters: list[FilterDef] = field(default_factory=list)
    default_sort: str = "created_at,desc"
    page_size: int = 20
    row_actions: list[ActionSchema] = field(default_factory=list)


@dataclass
class FormConfig:
    fields: list[FormField] = field(default_factory=list)
    submit_action: str = ""
    layout: str = "vertical"


@dataclass
class RelatedListConfig:
    """关联列表配置 —— 详情页展示的子表（如订单明细、收货记录）"""
    title: str                    # "订单明细"
    entity: str                   # "PurchaseLine"
    api_path: str                 # 数据来源 API 路径，{id} 替换为父实体 ID
    columns: list[ColumnDef] = field(default_factory=list)
    foreign_key: str = ""         # 关联字段名


@dataclass
class DetailSection:
    title: str
    fields: list[str] = field(default_factory=list)
    layout: str = "grid"


@dataclass
class DetailConfig:
    sections: list[DetailSection] = field(default_factory=list)
    related_lists: list[RelatedListConfig] = field(default_factory=list)


@dataclass
class KPICard:
    """仪表盘 KPI 指标卡"""
    label: str
    field: str
    icon: str = "Activity"
    color: str = "blue"        # blue / green / orange / purple
    source: str = ""           # 数据来源 API 路径
    format: str = "number"     # number / currency / percentage


@dataclass
class QuickAction:
    """仪表盘快捷操作"""
    label: str
    route: str
    icon: str = "Plus"
    permission: str = ""


@dataclass
class RecentTask:
    """仪表盘最近任务"""
    label: str
    field: str
    source: str = ""


@dataclass
class DashboardConfig:
    """仪表盘配置"""
    kpi_cards: list[KPICard] = field(default_factory=list)
    quick_actions: list[QuickAction] = field(default_factory=list)
    recent_tasks: list[RecentTask] = field(default_factory=list)


@dataclass
class PageSchema:
    route: str
    title: str
    page_type: str = "list"  # "list" | "form" | "detail" | "dashboard"
    entity: str = ""
    list_config: ListConfig | None = None
    form_config: FormConfig | None = None
    detail_config: DetailConfig | None = None
    dashboard_config: DashboardConfig | None = None
    actions: list[ActionSchema] = field(default_factory=list)
    permission: str = ""
    events_api: str = ""  # 事件历史 API 路径模板，如 "/api/v1/events/PurchaseOrder/{id}"

@dataclass
class MenuNode:
    label: str
    icon: str = "Folder"
    route: str | None = None
    permission: str | None = None
    children: list["MenuNode"] = field(default_factory=list)


@dataclass
class UISchema:
    module_name: str
    module_display: str
    version: str = "1.0"
    menu: MenuNode | None = None
    pages: list[PageSchema] = field(default_factory=list)
