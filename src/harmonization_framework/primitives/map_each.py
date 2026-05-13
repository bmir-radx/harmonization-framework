from typing import Any, List

from .base import PrimitiveOperation


class MapEach(PrimitiveOperation):
    """
    Apply a nested chain of operations to each element of a list.

    Useful for multi-source rules where each source value needs the same
    per-element transform (e.g. cast each one-hot flag to int) before a
    list-consuming step like Reduce.

    The wrapped operations run in order on each element. Input must be a
    list or tuple; output is a list of the same length.
    """

    def __init__(self, operations: List[PrimitiveOperation]):
        self.operations = list(operations)

    def __str__(self):
        nested = "\n".join(f"  {op}" for op in self.operations)
        return f"For each element apply:\n{nested}"

    def to_dict(self):
        return {
            "operation": "map_each",
            "operations": [op.to_dict() for op in self.operations],
        }

    def transform(self, values: Any) -> List[Any]:
        if not isinstance(values, (list, tuple)):
            raise TypeError(f"MapEach expects a list or tuple, got {type(values).__name__}")
        results = []
        for value in values:
            current = value
            for op in self.operations:
                current = op(current)
            results.append(current)
        return results

    @classmethod
    def from_serialization(cls, serialization):
        # Imported here to avoid a circular import: factory imports MapEach,
        # MapEach.from_serialization needs the factory.
        from .factory import deserialize_operation

        operations = [deserialize_operation(op) for op in serialization["operations"]]
        return MapEach(operations)
