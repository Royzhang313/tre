"""AI Builder —— M7.0.1 模型 + 验证器 + 生命周期测试"""

from app.ai.lifecycle import SpecLifecycle
from app.ai.models import AIDomainSpec, BuildPlan, DomainSpecSnapshot
from app.ai.service import SpecValidator
from app.shared.module_registry import ModuleManifest, ModuleRegistry


def _ann(cls: type) -> dict:
    result: dict = {}
    for base in reversed(cls.__mro__):
        result.update(getattr(base, "__annotations__", {}))
    return result


class TestAIDomainSpec:
    def test_tablename(self):
        assert AIDomainSpec.__tablename__ == "ai_domain_specs"

    def test_new_fields(self):
        ann = _ann(AIDomainSpec)
        assert "parent_spec_id" in ann
        assert "revision_reason" in ann


class TestBuildPlan:
    def test_tablename(self):
        assert BuildPlan.__tablename__ == "ai_build_plans"


class TestDomainSpecSnapshot:
    def test_tablename(self):
        assert DomainSpecSnapshot.__tablename__ == "ai_domain_spec_snapshots"

    def test_context_fields(self):
        ann = _ann(DomainSpecSnapshot)
        for f in ("module_registry_version", "capability_registry_version", "ai_context_version"):
            assert f in ann


class TestSpecLifecycle:
    def test_valid_transition(self):
        assert SpecLifecycle.can_transition("draft", "validating") is True

    def test_invalid_transition(self):
        assert SpecLifecycle.can_transition("draft", "approved") is False

    def test_all_states(self):
        states = {"draft", "validating", "reviewing", "approved", "building", "deployed", "failed", "deprecated"}
        assert set(SpecLifecycle.TRANSITIONS.keys()) == states


class TestSpecValidator:
    def test_module_conflict(self):
        ModuleRegistry.register(ModuleManifest(name="test_existing", display_name="Test"))
        result = SpecValidator.validate({"new_modules": [{"name": "test_existing"}]})
        assert result["valid"] is False
        ModuleRegistry.clear()

    def test_workflow_integrity(self):
        result = SpecValidator.validate({
            "new_workflows": [{
                "name": "test_wf", "initial_state": "draft",
                "states": [{"code": "draft"}, {"code": "done", "terminal": True}],
                "transitions": [
                    {"name": "go", "from_state": "draft", "to_state": "missing"}
                ]
            }]
        })
        assert result["valid"] is False

    def test_permission_format(self):
        result = SpecValidator.validate({"new_permissions": [{"code": "bad format!"}]})
        assert len(result["warnings"]) > 0

    def test_10_rules(self):
        assert SpecValidator._rules is not None
        assert len(SpecValidator._rules) == 10
