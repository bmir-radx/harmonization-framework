from .base import PrimitiveOperation, support_iterable
from typing import Union

class FormatNumber(PrimitiveOperation):
    """
    Format numeric values to a fixed number of decimal places.

    Output is a string, intended for stable presentation (e.g., CSV output).
    """
    def __init__(self, precision: int):
        if not isinstance(precision, int):
            raise TypeError(f"Precision must be an integer, got {type(precision).__name__}")
        if precision < 0:
            raise ValueError("Precision must be non-negative")
        self.precision = precision

    def __str__(self):
        return f"Format number to {self.precision} decimal places"

    def to_dict(self):
        """Serialize this operation to a JSON-friendly dict."""
        return {
            "operation": "format_number",
            "precision": self.precision,
        }

    @support_iterable
    def transform(self, value: Union[int, float]) -> str:
        """Format the numeric value to the configured decimal precision."""
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"FormatNumber expects a numeric value, got {type(value).__name__}")
        return f"{value:.{self.precision}f}"

    @classmethod
    def from_serialization(cls, serialization):
        """Reconstruct a FormatNumber operation from a serialized dict."""
        precision = int(serialization["precision"])
        return FormatNumber(precision)
