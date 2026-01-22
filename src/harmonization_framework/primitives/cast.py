from .base import PrimitiveOperation, support_iterable
from enum import Enum
from typing import Any

class CastType(Enum):
    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DECIMAL = "decimal"
    FLOAT = "float"

class Cast(PrimitiveOperation):
    """
    Cast values between supported primitive types.

    Supported targets: "text", "integer", "boolean", "decimal", "float".
    Boolean casting accepts common string/number representations.
    """
    def __init__(self, source: str, target: str):
        if target not in {member.value for member in CastType}:
            raise ValueError(f"Unsupported cast target: {target}")
        self.source = source
        self.target = target

    def __str__(self):
        text = f"Convert type from {self.source} to {self.target}"
        return text

    def to_dict(self):
        output = {
            "operation": "cast",
            "source": self.source,
            "target": self.target,
        }
        return output

    @support_iterable
    def transform(self, value: Any) -> Any:
        match self.target:
            case "text":
                return str(value)
            case "integer":
                return int(value)
            case "boolean":
                return self._to_boolean(value)
            case "decimal":
                return float(value)
            case "float":
                return float(value)
            case _:
                return value

    def _to_boolean(self, value: Any) -> bool:
        """
        Convert common string/number representations into a boolean.

        Accepted truthy strings: true, t, yes, y, 1
        Accepted falsy strings: false, f, no, n, 0, "" (empty)
        Numbers: 0 -> False, non-zero -> True
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "t", "yes", "y", "1"}:
                return True
            if normalized in {"false", "f", "no", "n", "0", ""}:
                return False
        raise ValueError(f"Cannot cast value to boolean: {value!r}")

    @classmethod
    def from_serialization(cls, serialization):
        return Cast(serialization["source"], serialization["target"])
