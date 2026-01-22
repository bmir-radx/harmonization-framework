import re
from .base import PrimitiveOperation, support_iterable

class Substitute(PrimitiveOperation):
    """
    Apply a text substitution based on a regex pattern.
    """
    def __init__(self, expression: str, substitution: str):
        """
        Create a regex substitution operation.

        Args:
            expression: Regex pattern to match.
            substitution: Replacement string for matches.
        """
        self.expression = expression
        self.substitution = substitution

    def __str__(self):
        text = f"Replace '{self.expression}' with '{self.substitution}'."
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
