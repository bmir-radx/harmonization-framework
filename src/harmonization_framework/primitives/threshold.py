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

    def _serialize_string(self):
        return f"Threshold|lower={self.lower},upper={self.upper}"

    def _serialize(self):
        output = {
            "Operation": f"{self.__class__.__name__}",
            "Lower": f"{self.lower}",
            "Upper": f"{self.upper}",
        }
        return output

    @support_iterable
    def transform(self, value: Union[int, float]) -> Union[int, float]:
        """
        This does not properly handle case where a float comes in 
        and has an int threshold applied.
        """
        return max(self.lower, min(self.upper, value))