from .base import PrimitiveOperation, support_iterable
from typing import Any, Dict

class EnumToEnum(PrimitiveOperation):
    """
    Operator that maps an input based on its prescribed mapping.

    If strict is True, missing mappings raise a KeyError.
    If strict is False, missing mappings return the configured default (or None).
    """
    def __init__(self, mapping: Dict[int, int], default: Any = None, strict: bool = False):
        self.mapping = mapping
        self.default = default
        self.strict = strict

    def __str__(self):
        map_items = [f"  {key}->{val}" for key, val in self.mapping.items()]
        text = "Mapping:\n" + "\n".join(map_items)
        return text

    def to_dict(self):
        output = {
            "operation": "enum_to_enum",
            "mapping": self.mapping,
            "strict": self.strict,
        }
        if self.default is not None:
            output["default"] = self.default
        return output

    @support_iterable
    def transform(self, value: Any) -> Any:
        if value not in self.mapping:
            if self.strict:
                raise KeyError(f"Missing mapping for value: {value}")
            # this should be a properly logged warning
            print(f"Warning: value={value} does not have a defined mapping.")
            return self.default
        return self.mapping[value]

    @classmethod
    def from_serialization(cls, serialization):
        mapping = {
            int(key): int(value)
            for key, value in serialization["mapping"].items()
        }
        default = serialization.get("default")
        strict = bool(serialization.get("strict", False))
        return EnumToEnum(mapping, default=default, strict=strict)
