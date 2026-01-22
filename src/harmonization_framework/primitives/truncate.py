from .base import PrimitiveOperation, support_iterable

class Truncate(PrimitiveOperation):
    """
    Operator that truncates a string by cutting off the tail.
    """
    def __init__(self, length: int):
        self.length = length

    def __str__(self):
        text = f"Truncate text to length {self.length}"
        return text

    def to_dict(self):
        output = {
            "operation": "truncate",
            "length": self.length,
        }
        return output

    @support_iterable
    def transform(self, value: str) -> str:
        return value[:self.length]

    @classmethod
    def from_serialization(cls, serialization):
        return Truncate(int(serialization["length"]))
