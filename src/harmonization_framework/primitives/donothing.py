from .base import PrimitiveOperation, support_iterable
from typing import Any

class DoNothing(PrimitiveOperation):
    """
    Operator that does nothing.
    """
    def __str__(self):
        return "Do Nothing"

    def to_dict(self):
        output = {
            "operation": "do_nothing",
        }
        return output

    @support_iterable
    def transform(self, value: Any) -> Any:
        return value

    @classmethod
    def from_serialization(cls, serialization):
        return DoNothing()
