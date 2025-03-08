from .base import PrimitiveOperation, support_iterable
from typing import Any

class DoNothing(PrimitiveOperation):
    """
    Operator that does nothing.
    """
    def __str__(self):
        return "Do Nothing"

    @classmethod
    def from_options(cls):
        return DoNothing()

    def _serialize_string(self):
        return "DoNothing|"

    def _serialize(self):
        output = {
            "Operation": f"{self.__class__.__name__}",
        }
        return output

    @support_iterable
    def transform(self, value: Any) -> Any:
        return value

    @classmethod
    def from_serialization(cls, serialization):
        return DoNothing()
