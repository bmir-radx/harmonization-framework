from .base import PrimitiveOperation, support_iterable
from typing import List, Tuple

class _IntervalNode:
    def __init__(self, label: int, lower: int, upper: int, left=None, right=None):
        self.label = label
        self.lower = lower
        self.upper = upper
        self.left = left
        self.right = right


class Bin(PrimitiveOperation):
    """
    Assign values into histogram bins. 
    Performs a range query using an interval tree. Bins must not overlap.
    """
    def __init__(self, bins: List[Tuple[int, Tuple[int]]]):
        self.bins = bins
        self._tree = self._build_tree(bins, 0, len(bins)-1)

    def __str__(self):
        text = "Group data into the following bins:\n"
        bins = [f"Label: {key}, Start: {b[0]}, End: {b[1]}" for key, b in self.bins]
        return text + "\n".join(bins)

    def to_dict(self):
        output = {
            "operation": "bin",
            "bins": [
                {"label": label, "start": start, "end": end}
                for label, (start, end) in self.bins
            ],
        }
        return output

    @support_iterable
    def transform(self, value: int) -> int:
        transformed = self._query(value, self._tree)
        if transformed is None:
            print(f"Warning: value={value} does not belong to a bin.")
        return transformed

    def _query(self, value: int, node: _IntervalNode) -> int:
        if node is None:
            return None
        if value < node.lower:
            return self._query(value, node.left)
        if value > node.upper:
            return self._query(value, node.right)
        if node.lower <= value <= node.upper:
            return node.label
        return None

    def _build_tree(self, bins: List[Tuple[int, Tuple[int]]], left: int, right: int):
        if left > right:
            return None
        
        mid = (left + right) // 2
        label, (lower, upper) = bins[mid]
        
        node = _IntervalNode(
            label=label,
            lower=lower,
            upper=upper,
            left=self._build_tree(bins, left, mid-1),
            right=self._build_tree(bins, mid+1, right),
        )
        return node

    @classmethod
    def from_serialization(cls, serialization):
        bins = [
            (int(interval["label"]), (int(interval["start"]), int(interval["end"])))
            for interval in serialization["bins"]
        ]
        return Bin(bins)
