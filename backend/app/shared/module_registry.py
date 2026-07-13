"""Module Registry —— 模块元数据注册中心（AI Builder 的系统地图）"""

from dataclasses import dataclass, field

# ============================================================
# Command / UI / Workflow Meta
# ============================================================


@dataclass
class ModuleCommand:
    name: str
    display_name: str
    description: str = ""
    http_method: str = "POST"
    http_path: str = ""
    request_schema: str = ""
    response_schema: str = ""
    required_permission: str = ""
    side_effects: list[str] = field(default_factory=list)


@dataclass
class UIPageMeta:
    route: str
    title: str
    page_type: str = "list"  # list / form / detail / dashboard
    entity: str = ""
    columns: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    dashboard_config: dict | None = None  # 仪表盘配置（page_type="dashboard" 时使用）
    related_lists: list[dict] | None = None  # 关联列表配置（page_type="detail" 时使用）


@dataclass
class WorkflowRef:
    workflow_name: str
    entity: str
    trigger_command: str = ""


# ============================================================
# Field / Relation Meta
# ============================================================


@dataclass
class FieldMeta:
    name: str
    type: str
    required: bool = False
    unique: bool = False
    description: str = ""


@dataclass
class RelationMeta:
    name: str
    target_entity: str
    relation_type: str = "one_to_many"
    foreign_key: str = ""


# ============================================================
# Entity Meta
# ============================================================


@dataclass
class EntityMeta:
    name: str
    display_name: str
    table_name: str
    module: str
    is_aggregate_root: bool = False
    fields: list[FieldMeta] = field(default_factory=list)
    relationships: list[RelationMeta] = field(default_factory=list)

    @classmethod
    def from_orm(cls, model: type) -> "EntityMeta":
        """从 SQLAlchemy 模型自动生成元数据"""
        table = getattr(model, "__tablename__", model.__name__.lower())
        fields = []
        tbl = getattr(model, "__table__", None)
        tbl_columns = tbl.columns if tbl is not None else []
        for col in tbl_columns:
            fields.append(FieldMeta(
                name=col.name,
                type=str(getattr(col, "type", "unknown")),
                required=not getattr(col, "nullable", True),
                unique=getattr(col, "unique", False) or False,
                description=getattr(col, "comment", "") or "",
            ))
        return cls(
            name=model.__name__,
            display_name=model.__doc__ or model.__name__,
            table_name=table,
            module=model.__module__.split(".")[2] if len(model.__module__.split(".")) > 2 else "",
            fields=fields,
        )


# ============================================================
# Module Manifest
# ============================================================


@dataclass
class ModuleManifest:
    name: str
    display_name: str
    version: str = "V1"
    entities: list[EntityMeta] = field(default_factory=list)
    commands: list[ModuleCommand] = field(default_factory=list)
    ui_pages: list[UIPageMeta] = field(default_factory=list)
    workflows: list[WorkflowRef] = field(default_factory=list)
    events_published: list[str] = field(default_factory=list)
    events_consumed: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "version": self.version,
            "entities": [
                {"name": e.name, "display_name": e.display_name, "table_name": e.table_name}
                for e in self.entities
            ],
            "commands": [
                {"name": c.name, "display_name": c.display_name, "http_method": c.http_method, "http_path": c.http_path}
                for c in self.commands
            ],
            "ui_pages": [{"route": p.route, "title": p.title, "page_type": p.page_type} for p in self.ui_pages],
            "events_published": self.events_published,
            "events_consumed": self.events_consumed,
            "permissions": self.permissions,
            "dependencies": self.dependencies,
        }


# ============================================================
# Module Registry
# ============================================================


class ModuleRegistry:
    _modules: dict[str, ModuleManifest] = {}

    @classmethod
    def register(cls, manifest: ModuleManifest) -> None:
        cls._modules[manifest.name] = manifest

    @classmethod
    def get(cls, name: str) -> ModuleManifest | None:
        return cls._modules.get(name)

    @classmethod
    def list_all(cls) -> list[ModuleManifest]:
        return list(cls._modules.values())

    @classmethod
    def clear(cls) -> None:
        cls._modules.clear()
