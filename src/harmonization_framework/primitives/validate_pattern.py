import re
from typing import Any, List, Optional

from .base import PrimitiveOperation, handle_null, support_iterable
from .extract_regex import _resolve_flags


_VALID_MODES = {"match", "fullmatch", "search"}


class ValidatePattern(PrimitiveOperation):
    """
    Assert that a string matches a regex pattern.

    Returns the original value on success. On failure: raises `ValueError`
    if `strict=True`, else returns `default`. Use as a data-quality gate in
    a rule chain.
    """

    def __init__(
        self,
        expression: str,
        flags: Optional[List[str]] = None,
        mode: str = "match",
        strict: bool = True,
        default: Any = None,
    ):
        if mode not in _VALID_MODES:
            raise ValueError(
                f"Unsupported mode {mode!r}. Supported: {sorted(_VALID_MODES)}"
            )

        self.flags = list(flags) if flags else []
        try:
            self._pattern = re.compile(expression, _resolve_flags(self.flags))
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {expression!r}") from exc

        self.expression = expression
        self.mode = mode
        self.strict = strict
        self.default = default

    def __str__(self):
        return f"Validate value against regex {self.expression!r} ({self.mode})"

    def to_dict(self):
        output = {
            "operation": "validate_pattern",
            "expression": self.expression,
            "mode": self.mode,
            "strict": self.strict,
        }
        if self.flags:
            output["flags"] = list(self.flags)
        if self.default is not None:
            output["default"] = self.default
        return output

    @support_iterable
    @handle_null
    def transform(self, value: str) -> Any:
        if self._is_valid(value):
            return value
        if self.strict:
            raise ValueError(
                f"Value {value!r} does not match pattern {self.expression!r} "
                f"(mode={self.mode})"
            )
        return self.default

    def _is_valid(self, value: str) -> bool:
        if self.mode == "match":
            return self._pattern.match(value) is not None
        if self.mode == "fullmatch":
            return self._pattern.fullmatch(value) is not None
        return self._pattern.search(value) is not None

    @classmethod
    def from_serialization(cls, serialization):
        return ValidatePattern(
            expression=serialization["expression"],
            flags=serialization.get("flags"),
            mode=serialization.get("mode", "match"),
            strict=bool(serialization.get("strict", True)),
            default=serialization.get("default"),
        )
