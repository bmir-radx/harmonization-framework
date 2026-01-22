import re
from .base import PrimitiveOperation, support_iterable

class Substitute(PrimitiveOperation):
    """
    Apply a text substitution based on a regex pattern.
    """
    def __init__(self, expression: str, substitution: str):
        self.expression = expression
        self.substitution = substitution

    def __str__(self):
        text = f"Replace 'f{self.expression}' with 'f{self.substitution}'."
        return text

    def to_dict(self):
        output = {
            "operation": "substitute",
            "expression": self.expression,
            "substitution": self.substitution,
        }
        return output

    @support_iterable
    def transform(self, value: str) -> str:
        return re.sub(self.expression, self.substitution, value)

    @classmethod
    def from_serialization(cls, serialization):
        expression = serialization["expression"]
        substitution = serialization["substitution"]
        return Substitute(expression, substitution)
