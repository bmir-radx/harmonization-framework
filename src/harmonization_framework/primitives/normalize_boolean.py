from .base import PrimitiveOperation, support_iterable
from typing import Any, Iterable, List, Optional


class NormalizeBoolean(PrimitiveOperation):
    """
    Normalize common truthy/falsy representations to booleans.

    This primitive is intended for datasets that encode booleans as strings
    or numeric flags (e.g., "Yes", "y", "1", "no", "0").

    Defaults:
        truthy: ["true", "t", "yes", "y", "1", 1, True, "on"]
        falsy:  ["false", "f", "no", "n", "0", 0, False, "off", ""]

    If truthy/falsy are not provided, these defaults are used.
    """

    DEFAULT_TRUTHY: List[Any] = ["true", "t", "yes", "y", "1", 1, True, "on"]
    DEFAULT_FALSY: List[Any] = ["false", "f", "no", "n", "0", 0, False, "off", ""]

    def __init__(
        self,
        truthy: Optional[Iterable[Any]] = None,
        falsy: Optional[Iterable[Any]] = None,
        strict: bool = True,
        default: Optional[bool] = None,
    ):
        """
        Create a boolean normalization operation.

        Args:
            truthy: Iterable of values treated as True.
                Strings are normalized via strip().lower().
            falsy: Iterable of values treated as False.
                Strings are normalized via strip().lower().
            strict: If True, unknown values raise ValueError.
                If False, unknown values return `default`.
            default: Fallback value when strict=False. Often None.
        """
        self.truthy = list(truthy) if truthy is not None else list(self.DEFAULT_TRUTHY)
        self.falsy = list(falsy) if falsy is not None else list(self.DEFAULT_FALSY)
        self.strict = strict
        self.default = default

        self._truthy_set = {self._normalize_token(v) for v in self.truthy}
        self._falsy_set = {self._normalize_token(v) for v in self.falsy}

    def __str__(self) -> str:
        return "Normalize boolean-like values"

    def to_dict(self):
        """
        Serialize this operation to a JSON-friendly dict.

        Includes the configured truthy/falsy lists and strict/default behavior.
        """
        output = {
            "operation": "normalize_boolean",
            "truthy": self.truthy,
            "falsy": self.falsy,
            "strict": self.strict,
        }
        if self.default is not None:
            output["default"] = self.default
        return output

    @support_iterable
    def transform(self, value: Any) -> bool:
        """
        Convert a single value to True/False based on configured mappings.

        Raises:
            ValueError if strict=True and the value is not recognized.
        """
        token = self._normalize_token(value)
        if token in self._truthy_set:
            return True
        if token in self._falsy_set:
            return False
        if self.strict:
            raise ValueError(f"Unknown boolean-like value: {value!r}")
        return self.default

    @classmethod
    def from_serialization(cls, serialization):
        """
        Reconstruct a NormalizeBoolean operation from a serialized dict.
        """
        return NormalizeBoolean(
            truthy=serialization.get("truthy"),
            falsy=serialization.get("falsy"),
            strict=bool(serialization.get("strict", True)),
            default=serialization.get("default"),
        )

    @staticmethod
    def _normalize_token(value: Any) -> Any:
        """
        Normalize a token for set membership checks.

        - Strings are trimmed and lowercased.
        - Non-strings are passed through unchanged.
        """
        if isinstance(value, str):
            return value.strip().lower()
        return value
