from .base import PrimitiveOperation, support_iterable
from typing import Union

class Round(PrimitiveOperation):
    """
    Operator that a decimal value to a specified precision.
    """
    def __init__(self, precision: int):
        self.precision = precision

    def __str__(self):
        text = f"Round number to {self.precision} decimal precision"
        return text

    def _serialize_string(self):
        return f"Round|precision={self.precision}"

    def _serialize(self):
        output = {
            "Operation": f"{self.__class__.__name__}",
            "Precision": f"{self.precision}",
        }
        return output

    @support_iterable
    def transform(self, value: Union[float]) -> Union[float]:
        return round(value, self.precision)

    @classmethod
    def from_serialization(cls, serialization):
        precision = int(serialization["Precision"])
        return Round(precision)
