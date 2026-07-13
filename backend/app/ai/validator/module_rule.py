# ruff: noqa: E501
from app.ai.validator.base import SpecValidationRule, ValidationResult


class ModuleUniqueRule(SpecValidationRule):
    name = "module_unique"

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        existing = context.get("existing_modules", set())
        results = []
        for i, mod in enumerate(spec_json.get("new_modules", [])):
            if mod.get("name") in existing:
                results.append(ValidationResult(self.name, "error", f"模块 '{mod['name']}' 已存在", f"new_modules[{i}]"))
        return results


class ModuleDependencyRule(SpecValidationRule):
    name = "module_dependency"

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        existing = context.get("existing_modules", set())
        new_names = {m.get("name") for m in spec_json.get("new_modules", [])}
        all_mods = existing | new_names
        results = []
        for i, mod in enumerate(spec_json.get("new_modules", [])):
            for j, dep in enumerate(mod.get("dependencies", [])):
                if dep not in all_mods:
                    results.append(ValidationResult(self.name, "warning", f"模块 '{mod['name']}' 依赖 '{dep}' 不存在", f"new_modules[{i}].dependencies[{j}]"))
        return results
