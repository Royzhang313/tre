"""Capability Registry —— AI Agent 发现和调用系统能力"""

from dataclasses import dataclass, field


@dataclass
class Capability:
    name: str
    display_name: str
    description: str = ""
    module: str = ""
    version: str = "V1"
    http_method: str = "POST"
    http_path: str = ""
    input_schema: dict = field(default_factory=dict)
    output_schema: dict = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)
    auth_required: bool = True
    events_published: list[str] = field(default_factory=list)
    events_consumed: list[str] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    idempotent: bool = False
    ai_tags: list[str] = field(default_factory=list)
    ai_prompt_hint: str = ""
    related_capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name, "display_name": self.display_name, "description": self.description,
            "module": self.module, "version": self.version,
            "http_method": self.http_method, "http_path": self.http_path,
            "input_schema": self.input_schema, "output_schema": self.output_schema,
            "required_permissions": self.required_permissions,
            "events_published": self.events_published, "events_consumed": self.events_consumed,
            "preconditions": self.preconditions, "idempotent": self.idempotent,
            "ai_tags": self.ai_tags, "ai_prompt_hint": self.ai_prompt_hint,
            "related_capabilities": self.related_capabilities,
        }


class CapabilityRegistry:
    _capabilities: dict[str, Capability] = {}

    @classmethod
    def register(cls, cap: Capability) -> None:
        cls._capabilities[cap.name] = cap

    @classmethod
    def get(cls, name: str) -> Capability | None:
        return cls._capabilities.get(name)

    @classmethod
    def list_all(cls) -> list[Capability]:
        return list(cls._capabilities.values())

    @classmethod
    def list_by_module(cls, module: str) -> list[Capability]:
        return [c for c in cls._capabilities.values() if c.module == module]

    @classmethod
    def search(cls, query: str) -> list[Capability]:
        q = query.lower()
        results = []
        for cap in cls._capabilities.values():
            if q in cap.name.lower() or q in cap.display_name or q in cap.description:
                results.append(cap)
            elif any(q in tag for tag in cap.ai_tags):
                results.append(cap)
        return results

    @classmethod
    def build_index(cls) -> dict:
        all_caps = [c.to_dict() for c in cls._capabilities.values()]
        by_module: dict[str, list] = {}
        for c in all_caps:
            by_module.setdefault(c["module"], []).append(c["name"])
        return {"total": len(all_caps), "by_module": by_module, "all": all_caps}

    @classmethod
    def clear(cls) -> None:
        cls._capabilities.clear()
