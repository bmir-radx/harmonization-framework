from .base import PrimitiveOperation, support_iterable
from typing import Union

class Round(PrimitiveOperation):
    """
    Round numeric values to a specified decimal precision.

    Precision follows Python's built-in `round` behavior.
    Precision must be a non-negative integer.
    """
    def __init__(self, precision: int):
        if not isinstance(precision, int):
            raise TypeError(f"Precision must be an integer, got {type(precision).__name__}")
        if precision < 0:
            raise ValueError("Precision must be non-negative")
        self.precision = precision

    def __str__(self):
        text = f"Round number to {self.precision} decimal precision"
        return text

    def to_dict(self):
        """
        Serialize this operation to a JSON-friendly dict.
        """
        output = {
            "operation": "round",
            "precision": self.precision,
        }
        return output

    @support_iterable
    def transform(self, value: Union[float]) -> Union[float]:
        """
        Round the value to the configured precision.
        """
        return round(value, self.precision)

    @classmethod
    def from_serialization(cls, serialization):
        """
        Reconstruct a Round operation from a serialized dict.
        """
        precision = int(serialization["precision"])
        return Round(precision)
