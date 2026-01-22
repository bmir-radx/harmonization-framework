from .base import PrimitiveOperation, support_iterable
from typing import Any, Dict

class EnumToEnum(PrimitiveOperation):
    """
    Operator that maps an input based on its prescribed mapping.
    """
    def __init__(self, mapping: Dict[int, int]):
        self.mapping = mapping

    def __str__(self):
        map_items = [f"  {key}->{val}" for key, val in self.mapping.items()]
        text = "Mapping:\n" + "\n".join(map_items)
        return text

    def _serialize(self):
        output = {
            "operation": "enum_to_enum",
            "mapping": self.mapping,
        }
        return output

    @support_iterable
    def transform(self, value: Any) -> Any:
        if value not in self.mapping:
            # this should be a properly logged warning
            print(f"Warning: value={value} does not have a defined mapping.")
            return None
        return self.mapping[value]

    @classmethod
    def from_serialization(cls, serialization):
        mapping = {
            int(key): int(value)
            for key, value in serialization["mapping"].items()
        }
        return EnumToEnum(mapping)
