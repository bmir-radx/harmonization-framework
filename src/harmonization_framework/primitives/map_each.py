from typing import Any, List

from .base import PrimitiveOperation, isnull


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
        """
        Apply the nested op chain to every element of `values`.

        MapEach rejects null elements rather than silently passing them
        through, so that a multi-source rule producing a partial input is
        surfaced as a data-quality issue. Scalar primitives downstream of
        MapEach handle their own nulls via @handle_null, but in a multi-source
        list a null element usually means the source column itself is missing
        for that row — better to fail loudly.
        """
        if not isinstance(values, (list, tuple)):
            raise TypeError(f"MapEach expects a list or tuple, got {type(values).__name__}")
        results = []
        for index, value in enumerate(values):
            if isnull(value):
                raise ValueError(
                    f"MapEach received a null value at position {index}; "
                    f"map_each will not silently pass nulls through."
                )
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
