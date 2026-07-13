"""Validator Base —— 规则接口"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ValidationResult:
    rule_name: str
    level: str       # "error" | "warning"
    message: str
    path: str = ""   # JSON path


class SpecValidationRule(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def validate(self, spec_json: dict, context: dict) -> list[ValidationResult]: ...
