"""Builder Agent —— 统一生成器接口"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass
class GeneratedArtifact:
    artifact_type: str        # "model" | "schema" | "repository" | "service" | "router" | "permission" | "workflow" | "migration"
    path: str                 # "models.py"
    content: str              # 文件内容
    checksum: str = ""        # SHA256
    source_snapshot_id: UUID | None = None
    status: str = "pending_review"


class BaseGenerator(ABC):
    """统一生成器接口"""

    @property
    @abstractmethod
    def generator_name(self) -> str: ...

    @abstractmethod
    def generate(self, action: dict, context: dict) -> GeneratedArtifact: ...


# ============================================================
# 模板引擎
# ============================================================


class TemplateEngine:
    """简单模板引擎 —— 70% 模板生成 + 30% 数据填充"""

    @staticmethod
    def render(template: str, variables: dict) -> str:
        """替换 {{ variable }} 占位符"""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{ {key}}}}}", str(value))
        return result

    @staticmethod
    def entity_template() -> str:
        return '''class {{ class_name }}(BaseModel):
    """{{ display_name }}"""

    __tablename__ = "{{ table_name }}"

{{ fields }}
'''

    @staticmethod
    def repository_template() -> str:
        return '''class {{ class_name }}Repository(BaseRepository[{{ class_name }}]):
    def __init__(self, session: AsyncSession):
        super().__init__({{ class_name }}, session, entity_name="{{ display_name }}")
'''

    @staticmethod
    def router_template() -> str:
        return '''@router.{{ method }}("{{ path }}")
async def {{ func_name }}({{ params }}):
    async with async_session_factory() as session:
        svc = {{ service_class }}({{ repo_class }}(session))
        {{ body }}
    return APIResponse.ok({{ response }})
'''
