from .base import PrimitiveOperation, support_iterable
from typing import Union

class Scale(PrimitiveOperation):
    """
    Operator that applies a scaling factor to a numerical value.
    """
    def __init__(self, scaling_factor: Union[int, float]):
        if not isinstance(scaling_factor, (int, float)):
            raise TypeError(f"Scaling factor must be numeric, got {type(scaling_factor).__name__}")
        self.scaling_factor = scaling_factor

    def __str__(self):
        text = f"Scale by factor {self.scaling_factor}"
        return text

    def to_dict(self):
        """
        Serialize this operation to a JSON-friendly dict.
        """
        output = {
            "operation": "scale",
            "scaling_factor": self.scaling_factor,
        }
        return output

    @support_iterable
    def transform(self, value: Union[int, float]) -> Union[int, float]:
        """
        Multiply the input value by the scaling factor.
        """
        return value * self.scaling_factor

    @classmethod
    def from_serialization(cls, serialization):
        """
        Reconstruct a Scale operation from a serialized dict.
        """
        scaling_factor = float(serialization["scaling_factor"])
        return Scale(scaling_factor)
