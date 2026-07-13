import re

from app.ai.validator.base import SpecValidationRule, ValidationResult


class PermissionFormatRule(SpecValidationRule):
    name = "permission_format"
    _valid = re.compile(r"^[a-z]+(\.[a-z-]+){1,3}$")

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        results = []
        for i, perm in enumerate(spec_json.get("new_permissions", [])):
            code = str(perm.get("code") if isinstance(perm, dict) else perm)
            if not self._valid.match(code):
                results.append(ValidationResult(self.name, "warning", f"权限 '{code}' 格式不规范", f"new_permissions[{i}]"))
        return results
