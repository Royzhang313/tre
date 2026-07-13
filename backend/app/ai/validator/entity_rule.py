# ruff: noqa: E501
import re

from app.ai.validator.base import SpecValidationRule, ValidationResult


class EntityUniqueRule(SpecValidationRule):
    name = "entity_unique"

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        names = [e.get("name") for e in spec_json.get("new_entities", [])]
        results = []
        for i, name in enumerate(names):
            if names.count(name) > 1:
                results.append(ValidationResult(self.name, "error", f"实体 '{name}' 重复定义", f"new_entities[{i}]"))
        return results


class EntityFKValidRule(SpecValidationRule):
    name = "entity_fk_valid"

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        local_names = {e.get("name") for e in spec_json.get("new_entities", [])}
        results = []
        for i, entity in enumerate(spec_json.get("new_entities", [])):
            for j, rel in enumerate(entity.get("relationships", [])):
                target = rel.get("target_entity", "")
                if target and target not in local_names:
                    results.append(ValidationResult(self.name, "warning", f"Entity '{entity['name']}' 引用未定义 '{target}'", f"new_entities[{i}].relationships[{j}]"))
        return results


class EntityFieldTypeRule(SpecValidationRule):
    name = "entity_field_type"
    _valid = re.compile(r"^(str\(\d+\)|Decimal\(\d+,\d+\)|int|bool|UUID|FK→.+|JSON|datetime|date)$")

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        results = []
        for i, entity in enumerate(spec_json.get("new_entities", [])):
            for j, field in enumerate(entity.get("fields", [])):
                ftype = field.get("type", "")
                if ftype and not self._valid.match(ftype):
                    results.append(ValidationResult(self.name, "warning", f"字段 '{field['name']}' 类型 '{ftype}' 不规范", f"new_entities[{i}].fields[{j}]"))
        return results
