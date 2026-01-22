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

    This primitive expects a single list/tuple of values as input and returns
    one reduced value (e.g., sum, any, all). It does not accept scalar input.
    """
    def __init__(self, reduction: Reduction):
        self.reduction = reduction

    def __str__(self):
        text = f"Apply {self.reduction} reduction"
        return text

    def to_dict(self):
        """
        Serialize this reduction to a JSON-friendly dict.
        """
        output = {
            "operation": "reduce",
            "reduction": self.reduction.value,
        }
        return output

    def transform(self, values: List[Any]) -> Any:
        """
        Reduce a list of values according to the configured reduction.

        Supported reductions:
        - any/none/all: boolean reductions (return 0/1)
        - one-hot: return the index of the single active bit (or None on error)
        - sum: numeric sum
        """
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
        """
        Return the index of the single truthy value in a one-hot vector.
        """
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
        """
        Reconstruct a Reduce operation from a serialized dict.
        """
        reduction = Reduction(serialization["reduction"])
        return Reduce(reduction)
