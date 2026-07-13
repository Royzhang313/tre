# ruff: noqa: E501
from app.ai.validator.base import SpecValidationRule, ValidationResult
from app.shared.capability_registry import CapabilityRegistry


class CapabilityUniqueRule(SpecValidationRule):
    name = "capability_unique"

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        results = []
        for i, cap in enumerate(spec_json.get("new_capabilities", [])):
            if CapabilityRegistry.get(cap.get("name", "")):
                results.append(ValidationResult(self.name, "error", f"Capability '{cap['name']}' 已存在", f"new_capabilities[{i}]"))
        return results


class CapabilityPermissionRule(SpecValidationRule):
    name = "capability_permission"

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        defined = {p.get("code") if isinstance(p, dict) else p for p in spec_json.get("new_permissions", [])}
        results = []
        for i, cap in enumerate(spec_json.get("new_capabilities", [])):
            for j, perm in enumerate(cap.get("required_permissions", [])):
                if perm not in defined:
                    results.append(ValidationResult(self.name, "warning", f"Capability '{cap['name']}' 引用未定义权限 '{perm}'", f"new_capabilities[{i}].required_permissions[{j}]"))
        return results
