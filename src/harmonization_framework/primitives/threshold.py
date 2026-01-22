from .base import PrimitiveOperation, support_iterable
from typing import Union

class Threshold(PrimitiveOperation):
    """
    Operator that thresholds a numerical value.
    """
    def __init__(self, lower: Union[int, float], upper: Union[int, float]):
        self.lower = lower
        self.upper = upper

    def __str__(self):
        text = f"Apply Numerical Thresholds: Lower = {self.lower}, Upper = {self.upper}"
        return text

    def to_dict(self):
        output = {
            "operation": "threshold",
            "lower": self.lower,
            "upper": self.upper,
        }
        return output

    @support_iterable
    def transform(self, value: Union[int, float]) -> Union[int, float]:
        """
        This does not properly handle case where a float comes in 
        and has an int threshold applied.
        """
        return max(self.lower, min(self.upper, value))

    @classmethod
    def from_serialization(cls, serialization):
        lower = float(serialization["lower"])
        upper = float(serialization["upper"])
        return Threshold(lower, upper)
