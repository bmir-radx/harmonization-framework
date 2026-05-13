from typing import Any, Dict

import json
import math

import pandas as pd

"""
Base interfaces and utilities for primitive operations.
"""


def isnull(value: Any) -> bool:
    """
    Return True if `value` represents a missing/null value.

    Recognised forms:
    - Python `None`
    - `float('nan')` (the legacy missing-value sentinel pandas inserts into
      numeric columns when a CSV cell is blank)
    - `pd.NA` (pandas nullable-dtype scalar)

    Lists, tuples, and strings are never considered null — only scalar values are.
    """
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    # pd.NA does not compare equal to anything, and `isinstance(pd.NA, ...)`
    # is not robust across pandas versions, so use `is` against the singleton.
    if value is pd.NA:
        return True
    return False

class PrimitiveOperation:
    def __init__(self):
        """Constructor for primitive-specific parameters."""

    def __str__(self):
        return "Generic Primitive Operation"

    def transform(self, value: Any) -> Any:
        """Primitive-specific transformation function."""
        raise NotImplementedError("transform() must be implemented by subclasses.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a JSON-serializable dict describing this operation.

        Contract:
        - Must include an "operation" key with a snake_case identifier.
        - Other keys must be snake_case.
        - Numeric values should be numbers (not strings).
        """
        raise NotImplementedError("to_dict() must be implemented by subclasses.")

    def serialize(self):
        """
        Return a JSON string representation of this operation.

        Notes:
        - Delegates to `to_dict()` for the schema definition.
        - Output is a compact JSON string suitable for storage or APIs.
        """
        return json.dumps(self.to_dict())

    def __call__(self, value: Any) -> Any:
        return self.transform(value)

    @classmethod
    def from_serialization(cls, serialization: Dict[str, Any]) -> "PrimitiveOperation":
        """Primitive-specific parsing of serialization."""
        raise NotImplementedError("from_serialization() must be implemented by subclasses.")

def support_iterable(transform):
    """
    Decorator that enables primitives to accept either a scalar or a list/tuple.

    Behavior:
    - If the input is a list or tuple, apply the wrapped transform to each element
      and return a list of results.
    - Otherwise, treat the input as a scalar and return a single transformed value.

    Rationale:
    This keeps primitive implementations simple while allowing callers to pass
    small batches without relying on pandas/numpy vectorization.
    """
    def wrapper(self, value):
        if isinstance(value, (list, tuple)):
            return [transform(self, v) for v in value]
        return transform(self, value)
    return wrapper


def handle_null(transform):
    """
    Decorator that makes a scalar transform pass `None`/NaN/pd.NA through unchanged.

    Apply to primitives whose transform expects a non-null scalar (Cast, Scale,
    Bin, Round, etc.). The decorated method is never called for a null input;
    the null value is returned as-is.

    Decorator order with `@support_iterable`:

        @support_iterable
        @handle_null
        def transform(self, value):
            ...

    `@support_iterable` is the outermost decorator so that it can fan a list
    out to per-element calls; each per-element call then goes through
    `@handle_null` before reaching the real transform.
    """
    def wrapper(self, value):
        if isnull(value):
            return value
        return transform(self, value)
    return wrapper
