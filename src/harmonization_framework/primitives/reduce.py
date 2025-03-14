from .base import PrimitiveOperation
from collections.abc import Iterable
from enum import Enum
from typing import Any, List

def support_iterable(transform):
    def wrapper(self, values):
        if isinstance(values, Iterable) and not isinstance(values, (str, bytes)):
            if all(isinstance(v, Iterable) and not isinstance(v, (str, bytes)) for v in values):
                return [transform(self, v) for v in values]
        return transform(self, values)
    return wrapper

class Reduction(Enum):
    # boolean operations, e.g., for one-hot conversions
    ANY = "any" # at least one bit is nonzero
    NONE = "none" # all bits are 0
    ALL = "all" # all bits are nonzero
    # for N binary values, take the index of the flipped bit
    # if the target bit is not 1, need a mapping before reduction
    ONEHOT = "one-hot"

class Reduce(PrimitiveOperation):
    """
    Reduction operation that transforms N inputs to 1 output.
    """
    def __init__(self, reduction: Reduction):
        self.reduction = reduction

    def __str__(self):
        text = f"Apply {self.reduction} reduction"
        return text

    def _serialize(self):
        output = {
            "Operation": f"{self.__class__.__name__}",
            "Reduction": f"{self.reduction}",
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
            case _:
                return values

    @support_iterable
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
