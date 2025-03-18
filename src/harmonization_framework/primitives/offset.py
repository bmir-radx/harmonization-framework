from .base import PrimitiveOperation, support_iterable
from typing import Union

class Offset(PrimitiveOperation):
    """
    Operator that applies an offset to a numerical value.
    """
    def __init__(self, offset: Union[int, float]):
        self.offset = offset

    def __str__(self):
        text = f"Offset by a value {self.offset}"
        return text

    def _serialize(self):
        output = {
            "Operation": f"{self.__class__.__name__}",
            "Offset": f"{self.offset}",
        }
        return output

    @support_iterable
    def transform(self, value: Union[int, float]) -> Union[int, float]:
        return value + self.offset

    @classmethod
    def from_serialization(cls, serialization):
        offset = float(serialization["Offset"])
        return Offset(offset)
