from .base import PrimitiveOperation, support_iterable
from typing import Union

class Offset(PrimitiveOperation):
    """
    Operator that applies an offset to a numerical value.
    """
    def __init__(self, offset: Union[int, float]):
        if not isinstance(offset, (int, float)):
            raise TypeError(f"Offset must be numeric, got {type(offset).__name__}")
        self.offset = offset

    def __str__(self):
        text = f"Offset by a value {self.offset}"
        return text

    def to_dict(self):
        """
        Serialize this operation to a JSON-friendly dict.
        """
        output = {
            "operation": "offset",
            "offset": self.offset,
        }
        return output

    @support_iterable
    def transform(self, value: Union[int, float]) -> Union[int, float]:
        """
        Add the configured offset to the input value.
        """
        return value + self.offset

    @classmethod
    def from_serialization(cls, serialization):
        """
        Reconstruct an Offset operation from a serialized dict.
        """
        offset = float(serialization["offset"])
        return Offset(offset)
