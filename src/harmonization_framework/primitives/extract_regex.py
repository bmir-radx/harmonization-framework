import re
from typing import Any, Iterable, List, Optional, Union

from .base import PrimitiveOperation, handle_null, support_iterable


# Whitelist the regex flags we accept in serialization. Limited on purpose so
# the serialized form stays portable and reviewable.
_FLAG_NAMES = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
}


def _resolve_flags(flag_names: Optional[Iterable[str]]) -> int:
    """Combine a list of flag names into an `re` flags bitmask."""
    if not flag_names:
        return 0
    bitmask = 0
    for name in flag_names:
        if name not in _FLAG_NAMES:
            raise ValueError(
                f"Unsupported regex flag: {name!r}. "
                f"Supported: {sorted(_FLAG_NAMES)}"
            )
        bitmask |= _FLAG_NAMES[name]
    return bitmask


class ExtractRegex(PrimitiveOperation):
    """
    Extract a value from a string using a regex capture group.

    Common harmonization use cases include pulling identifiers out of free
    text (e.g., MRN: A12-99) or numeric suffixes out of structured codes.
    """

    def __init__(
        self,
        expression: str,
        group: Union[int, str] = 1,
        flags: Optional[List[str]] = None,
        strict: bool = True,
        default: Any = None,
    ):
        if not isinstance(group, (int, str)):
            raise TypeError(
                f"group must be an int or str, got {type(group).__name__}"
            )
        if isinstance(group, int) and group < 0:
            raise ValueError(f"group index must be non-negative, got {group}")

        self.flags = list(flags) if flags else []
        try:
            self._pattern = re.compile(expression, _resolve_flags(self.flags))
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {expression!r}") from exc

        self.expression = expression
        self.group = group
        self.strict = strict
        self.default = default

    def __str__(self):
        return f"Extract group {self.group!r} from regex {self.expression!r}"

    def to_dict(self):
        output = {
            "operation": "extract_regex",
            "expression": self.expression,
            "group": self.group,
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
        match = self._pattern.search(value)
        if match is None:
            if self.strict:
                raise ValueError(
                    f"Pattern {self.expression!r} did not match value {value!r}"
                )
            return self.default
        try:
            return match.group(self.group)
        except (IndexError, re.error) as exc:
            if self.strict:
                raise ValueError(
                    f"Group {self.group!r} not found in match of {self.expression!r} "
                    f"against value {value!r}"
                ) from exc
            return self.default

    @classmethod
    def from_serialization(cls, serialization):
        return ExtractRegex(
            expression=serialization["expression"],
            group=serialization.get("group", 1),
            flags=serialization.get("flags"),
            strict=bool(serialization.get("strict", True)),
            default=serialization.get("default"),
        )
