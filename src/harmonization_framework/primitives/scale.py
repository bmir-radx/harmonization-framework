from .base import PrimitiveOperation, support_iterable
from typing import Union

class Scale(PrimitiveOperation):
    """
    Operator that applies a scaling factor to a numerical value.
    """
    def __init__(self, scaling_factor: Union[int, float]):
        self.scaling_factor = scaling_factor

    def __str__(self):
        text = f"Scale by factor {self.scaling_factor}"
        return text

    def to_dict(self):
        output = {
            "operation": "scale",
            "scaling_factor": self.scaling_factor,
        }
        return output

    @support_iterable
    def transform(self, value: Union[int, float]) -> Union[int, float]:
        return value * self.scaling_factor

    @classmethod
    def from_serialization(cls, serialization):
        scaling_factor = float(serialization["scaling_factor"])
        return Scale(scaling_factor)
