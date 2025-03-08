from .base import PrimitiveOperation, support_iterable
from enum import Enum
from typing import Any

class CastType(Enum):
    TEXT = "text"
    INTEGER = "integer"
    BOOLEAN = "boolean"

class Cast(PrimitiveOperation):
    """
    Cast type.
    """
    def __init__(self, source: str, target: str):
        self.source = source
        self.target = target

    def __str__(self):
        text = f"Convert type from {self.source} to {self.target}"
        return text

    def _serialize_string(self):
        return f"Cast|source={self.source},target={self.target}"

    def _serialize(self):
        output = {
            "Operation": f"{self.__class__.__name__}",
            "Source": f"{self.source}",
            "Target": f"{self.target}",
        }
        return output

    @support_iterable
    def transform(self, value: Any) -> Any:
        match self.target:
            case "text":
                return str(value)
            case "integer":
                return int(value)
            case _:
                return value

    @classmethod
    def from_serialization(cls, serialization):
        return Cast(serialization["Source"], serialization["Target"])
