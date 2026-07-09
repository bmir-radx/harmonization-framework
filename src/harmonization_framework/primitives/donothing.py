from .base import PrimitiveOperation, support_iterable
from typing import Any

class DoNothing(PrimitiveOperation):
    """
    Pass the value through unchanged. Takes no settings.

    Useful as an explicit placeholder where an operation chain is required
    but no transformation is wanted — for example a `case`/`coalesce` branch
    that uses a column as-is.
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
