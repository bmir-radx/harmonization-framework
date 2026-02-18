import json
from typing import Any, List

from .base import PrimitiveOperation
from .normalize_boolean import NormalizeBoolean


class ParseArray(PrimitiveOperation):
    """
    Parse array-like values into Python lists.

    Supported formats:
    - json: parse JSON arrays from strings (default)
    - delimiter: split strings by a configured delimiter
    """

    SUPPORTED_FORMATS = {"json", "delimiter"}
    SUPPORTED_ITEM_TYPES = {"auto", "string", "integer", "float", "boolean"}

    def __init__(self, format: str = "json", delimiter: str = "|", item_type: str = "auto", strict: bool = True,
                 default: Any = None, allow_singleton: bool = False):
        super().__init__()
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported parse_array format: {format}")
        if item_type not in self.SUPPORTED_ITEM_TYPES:
            raise ValueError(f"Unsupported parse_array item_type: {item_type}")
        if not isinstance(delimiter, str):
            raise TypeError("Delimiter must be a string")
        if format == "delimiter" and delimiter == "":
            raise ValueError("Delimiter must be non-empty for delimiter format")

        self.format = format
        self.delimiter = delimiter
        self.item_type = item_type
        self.strict = strict
        self.default = default
        self.allow_singleton = allow_singleton
        # Keep boolean coercion semantics aligned with NormalizeBoolean defaults.
        self._boolean_normalizer = NormalizeBoolean(strict=True)

    def __str__(self):
        return f"Parse array using {self.format} format"

    def to_dict(self):
        output = {
            "operation": "parse_array",
            "format": self.format,
            "item_type": self.item_type,
            "strict": self.strict,
            "allow_singleton": self.allow_singleton,
        }
        if self.format == "delimiter":
            output["delimiter"] = self.delimiter
        if self.default is not None:
            output["default"] = self.default
        return output

    def transform(self, value: Any) -> Any:
        try:
            items = self._parse_items(value)
            return [self._coerce_item(item) for item in items]
        except Exception as exc:
            if self.strict:
                raise ValueError(
                    f"Failed to parse array from value={value!r} "
                    f"with format={self.format!r}"
                ) from exc
            return self.default

    @classmethod
    def from_serialization(cls, serialization):
        return ParseArray(
            format=serialization.get("format", "json"),
            delimiter=serialization.get("delimiter", "|"),
            item_type=serialization.get("item_type", "auto"),
            strict=bool(serialization.get("strict", True)),
            default=serialization.get("default"),
            allow_singleton=bool(serialization.get("allow_singleton", False)),
        )

    def _parse_items(self, value: Any) -> List[Any]:
        if isinstance(value, (list, tuple)):
            return list(value)

        if isinstance(value, str):
            if self.format == "json":
                return self._parse_json(value)
            return self._parse_delimiter(value)

        if self.allow_singleton:
            return [value]

        raise TypeError(f"parse_array expects list/tuple/string input, got {type(value).__name__}")

    def _parse_json(self, value: str) -> List[Any]:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        if self.allow_singleton and not isinstance(parsed, dict):
            return [parsed]
        raise ValueError("JSON payload is not an array")

    def _parse_delimiter(self, value: str) -> List[str]:
        delimiter = self._resolve_delimiter(self.delimiter)
        if value == "":
            return []
        if delimiter == "\n":
            # Normalize Windows-style newlines for predictable splitting.
            value = value.replace("\r\n", "\n")
        return [item.strip() for item in value.split(delimiter)]

    def _coerce_item(self, item: Any) -> Any:
        if self.item_type == "auto":
            return item
        if self.item_type == "string":
            return str(item)
        if self.item_type == "integer":
            return int(item)
        if self.item_type == "float":
            return float(item)
        if self.item_type == "boolean":
            return self._boolean_normalizer.transform(item)
        return item

    @staticmethod
    def _resolve_delimiter(delimiter: str) -> str:
        if delimiter == "\\n":
            return "\n"
        return delimiter
