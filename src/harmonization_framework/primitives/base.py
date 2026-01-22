from typing import Any
from collections.abc import Iterable

import json

class PrimitiveOperation:
    def __init__(self):
        """Constructor for primitive-specitive parameters"""
        pass

    def __str__(self):
        return "Generic Primitive Operation"

    def transform(self, value: Any) -> Any:
        """Primitive-specific transformation function"""
        pass

    def to_dict(self):
        """
        Return a JSON-serializable dict describing this operation.

        Contract:
        - Must include an "operation" key with a snake_case identifier.
        - Other keys must be snake_case.
        - Numeric values should be numbers (not strings).
        """
        pass

    def serialize(self):
        return json.dumps(self.to_dict())

    def __call__(self, value: Any) -> Any:
        return self.transform(value)

    @classmethod
    def from_serialization(cls, serialization):
        """Primtive-specific parsing of serialization"""
        pass

def support_iterable(transform):
    def wrapper(self, value):
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return [transform(self, v) for v in value]
        else:
            return transform(self, value)
    return wrapper
