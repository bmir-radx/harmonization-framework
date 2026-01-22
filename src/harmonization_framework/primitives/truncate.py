from .base import PrimitiveOperation, support_iterable

class Truncate(PrimitiveOperation):
    """
    Operator that truncates a string by cutting off the tail.
    """
    def __init__(self, length: int):
        if not isinstance(length, int):
            raise TypeError(f"Length must be an integer, got {type(length).__name__}")
        if length < 0:
            raise ValueError("Length must be non-negative")
        self.length = length

    def __str__(self):
        text = f"Truncate text to length {self.length}"
        return text

    def to_dict(self):
        """
        Serialize this operation to a JSON-friendly dict.
        """
        output = {
            "operation": "truncate",
            "length": self.length,
        }
        return output

    @support_iterable
    def transform(self, value: str) -> str:
        """
        Truncate the input string to the configured length.
        """
        return value[:self.length]

    @classmethod
    def from_serialization(cls, serialization):
        """
        Reconstruct a Truncate operation from a serialized dict.
        """
        return Truncate(int(serialization["length"]))
