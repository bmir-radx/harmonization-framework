from .base import PrimitiveOperation, support_iterable
from typing import Union

class Scale(PrimitiveOperation):
    """
    Operator that applies a scaling factor to a numerical value.
    """
    def __init__(self, scaling_factor: int):
        self.scaling_factor = scaling_factor

    def __str__(self):
        text = f"Scale by factor {self.scaling_factor}"
        return text

    def _serialize(self):
        output = {
            "Operation": f"{self.__class__.__name__}",
            "Scaling Factor": f"{self.scaling_factor}",
        }
        return output

    @support_iterable
    def transform(self, value: Union[int, float]) -> Union[int, float]:
        return value * self.scaling_factor
