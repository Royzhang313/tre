"""SpecLifecycle —— AIDomainSpec 状态机"""


from app.core.exceptions import ConflictError

VALID_TRANSITIONS = {
    "draft":      {"validating"},
    "validating": {"reviewing", "draft"},
    "reviewing":  {"approved", "draft"},
    "approved":   {"building"},
    "building":   {"deployed", "failed"},
    "deployed":   {"deprecated"},
    "failed":     {"draft"},
    "deprecated": set(),
}


class SpecLifecycle:
    TRANSITIONS = VALID_TRANSITIONS

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        return target in cls.TRANSITIONS.get(current, set())

    @classmethod
    def transition(cls, spec, target: str) -> None:
        if not cls.can_transition(spec.status, target):
            raise ConflictError(f"非法状态转换: {spec.status} → {target}")
        spec.status = target
