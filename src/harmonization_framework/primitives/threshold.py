from .base import PrimitiveOperation, support_iterable
from typing import Union

class Threshold(PrimitiveOperation):
    """
    Operator that thresholds a numerical value.
    """
    def __init__(self, lower: Union[int, float], upper: Union[int, float]):
        if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)):
            raise TypeError("Threshold bounds must be numeric")
        if lower > upper:
            raise ValueError(f"Lower bound {lower} must be <= upper bound {upper}")
        self.lower = lower
        self.upper = upper

    def __str__(self):
        text = f"Apply Numerical Thresholds: Lower = {self.lower}, Upper = {self.upper}"
        return text

    def to_dict(self):
        """
        Serialize this operation to a JSON-friendly dict.
        """
        output = {
            "operation": "threshold",
            "lower": self.lower,
            "upper": self.upper,
        }
        return output

    @support_iterable
    def transform(self, value: Union[int, float]) -> Union[int, float]:
        """
        Clamp the input value between lower and upper bounds.

        Output type follows Python numeric promotion:
        - int bounds + int input -> int output
        - any float in bounds/input -> float output
        """
        if isinstance(self.lower, float) or isinstance(self.upper, float):
            value = float(value)
        return max(self.lower, min(self.upper, value))

    @classmethod
    def from_serialization(cls, serialization):
        """
        Reconstruct a Threshold operation from a serialized dict.
        """
        lower = float(serialization["lower"])
        upper = float(serialization["upper"])
        return Threshold(lower, upper)
