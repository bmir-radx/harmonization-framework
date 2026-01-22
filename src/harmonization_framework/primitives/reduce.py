from .base import PrimitiveOperation
from enum import Enum
from typing import Any, List

class Reduction(Enum):
    # boolean operations, e.g., for one-hot conversions
    ANY = "any" # at least one bit is nonzero
    NONE = "none" # all bits are 0
    ALL = "all" # all bits are nonzero
    # for N binary values, take the index of the flipped bit
    # if the target bit is not 1, need a mapping before reduction
    ONEHOT = "one-hot"
    SUM = "sum"

class Reduce(PrimitiveOperation):
    """
    Reduction operation that transforms N inputs to 1 output.
    """
    def __init__(self, reduction: Reduction):
        self.reduction = reduction

    def __str__(self):
        text = f"Apply {self.reduction} reduction"
        return text

    def to_dict(self):
        output = {
            "operation": "reduce",
            "reduction": self.reduction.value,
        }
        return output

    def transform(self, values: List[Any]) -> Any:
        match self.reduction:
            case Reduction.ANY:
                return int(any(values))
            case Reduction.NONE:
                return int(not any(values))
            case Reduction.ALL:
                return int(all(values))
            case Reduction.ONEHOT:
                return self.onehot_reduction(values)
            case Reduction.SUM:
                return sum(values)
            case _:
                return values

    def onehot_reduction(self, values) -> int:
        total = sum(values)
        if total != 1:
            print(f"One-hot reduction error: sum = {total}")
            return None
        for i, value in enumerate(values):
            if value:
                return i
        print("One-hot reduction error: no flipped bit found")
        return None

    @classmethod
    def from_serialization(cls, serialization):
        reduction = Reduction(serialization["reduction"])
        return Reduce(reduction)
