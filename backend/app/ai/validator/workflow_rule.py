# ruff: noqa: E501
from app.ai.validator.base import SpecValidationRule, ValidationResult


class WorkflowStateIntegrityRule(SpecValidationRule):
    name = "workflow_state_integrity"

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        results = []
        for i, wf in enumerate(spec_json.get("new_workflows", [])):
            state_codes = {s.get("code") for s in wf.get("states", [])}
            for j, t in enumerate(wf.get("transitions", [])):
                if t.get("from_state") not in state_codes:
                    results.append(ValidationResult(self.name, "error", f"from_state '{t['from_state']}' 未定义", f"new_workflows[{i}].transitions[{j}]"))
                if t.get("to_state") not in state_codes:
                    results.append(ValidationResult(self.name, "error", f"to_state '{t['to_state']}' 未定义", f"new_workflows[{i}].transitions[{j}]"))
        return results


class WorkflowTerminalValidRule(SpecValidationRule):
    name = "workflow_terminal_valid"

    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]:
        results = []
        for i, wf in enumerate(spec_json.get("new_workflows", [])):
            terminals = {s.get("code") for s in wf.get("states", []) if s.get("terminal")}
            for j, t in enumerate(wf.get("transitions", [])):
                if t.get("from_state") in terminals:
                    results.append(ValidationResult(self.name, "error", f"终态 '{t['from_state']}' 不应有出边", f"new_workflows[{i}].transitions[{j}]"))
        return results
