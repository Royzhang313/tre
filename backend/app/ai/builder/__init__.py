"""Builder Agent —— 代码生成器框架"""

from app.ai.builder.base import BaseGenerator, GeneratedArtifact, TemplateEngine


def register_all_generators():
    from app.ai.builder.create_capability_gen import CreateCapabilityGenerator
    from app.ai.builder.create_entity_gen import CreateEntityGenerator
    from app.ai.builder.create_module_gen import CreateModuleGenerator
    from app.ai.builder.create_permission_gen import CreatePermissionGenerator
    from app.ai.builder.create_repository_gen import CreateRepositoryGenerator
    from app.ai.builder.create_router_gen import CreateRouterGenerator
    from app.ai.builder.create_schema_gen import CreateSchemaGenerator
    from app.ai.builder.create_ui_page_gen import CreateUiPageGenerator
    from app.ai.builder.create_workflow_gen import CreateWorkflowGenerator
    from app.ai.builder.extend_entity_gen import ExtendEntityGenerator
    from app.ai.service import GeneratorRegistry
    GeneratorRegistry.register("create_module", CreateModuleGenerator)
    GeneratorRegistry.register("create_entity", CreateEntityGenerator)
    GeneratorRegistry.register("extend_entity", ExtendEntityGenerator)
    GeneratorRegistry.register("create_capability", CreateCapabilityGenerator)
    GeneratorRegistry.register("create_workflow", CreateWorkflowGenerator)
    GeneratorRegistry.register("create_permission", CreatePermissionGenerator)
    GeneratorRegistry.register("create_ui_page", CreateUiPageGenerator)
    GeneratorRegistry.register("create_schema", CreateSchemaGenerator)
    GeneratorRegistry.register("create_repository", CreateRepositoryGenerator)
    GeneratorRegistry.register("create_router", CreateRouterGenerator)


__all__ = ["BaseGenerator", "GeneratedArtifact", "TemplateEngine", "register_all_generators"]
