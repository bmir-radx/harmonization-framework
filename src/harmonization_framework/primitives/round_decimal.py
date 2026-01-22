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

    def to_dict(self):
        output = {
            "operation": "round",
            "precision": self.precision,
        }
        return output

    @support_iterable
    def transform(self, value: Union[float]) -> Union[float]:
        return round(value, self.precision)

    @classmethod
    def from_serialization(cls, serialization):
        precision = int(serialization["precision"])
        return Round(precision)
