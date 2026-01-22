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
        try:
            re.compile(expression)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {expression!r}") from exc
        self.expression = expression
        self.substitution = substitution

    def __str__(self):
        text = f"Replace '{self.expression}' with '{self.substitution}'."
        return text

    def to_dict(self):
        """
        Serialize this operation to a JSON-friendly dict.
        """
        output = {
            "operation": "substitute",
            "expression": self.expression,
            "substitution": self.substitution,
        }
        return output

    @support_iterable
    def transform(self, value: str) -> str:
        """
        Replace all regex matches in the input with the substitution string.
        """
        return re.sub(self.expression, self.substitution, value)

    @classmethod
    def from_serialization(cls, serialization):
        """
        Reconstruct a Substitute operation from a serialized dict.
        """
        expression = serialization["expression"]
        substitution = serialization["substitution"]
        return Substitute(expression, substitution)
