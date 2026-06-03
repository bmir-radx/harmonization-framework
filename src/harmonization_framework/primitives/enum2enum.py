import logging
from typing import Any, Dict

from .base import PrimitiveOperation, support_iterable

logger = logging.getLogger(__name__)

class EnumToEnum(PrimitiveOperation):
    """
    Operator that maps an input based on its prescribed mapping.

    If strict is True, missing mappings raise a KeyError.
    If strict is False, missing mappings return the configured default (or None).
    """
    def __init__(self, mapping: Dict[Any, Any], default: Any = None, strict: bool = False):
        """
        Create a mapping from source enum values to target enum values.

        Args:
            mapping: Dict of source -> target values (string or numeric keys/values).
            default: Value to return when a mapping is missing (strict=False only).
            strict: When True, raise a KeyError for missing mappings.
        """
        self.mapping = mapping
        self.default = default
        self.strict = strict

    def __str__(self):
        map_items = [f"  {key}->{val}" for key, val in self.mapping.items()]
        text = "Mapping:\n" + "\n".join(map_items)
        return text

    def to_dict(self):
        """
        Serialize this mapping to a JSON-friendly dict.

        The mapping is serialized as a LIST of {"from", "to"} entries rather than
        a JSON object. JSON object keys are always strings, so an object form
        would silently coerce non-string keys (e.g. the integer index emitted by
        Reduce(ONEHOT)) to strings on a round-trip, breaking the lookup. The
        entry-list keeps each key in a value position, preserving its native JSON
        type (int stays int, float stays float, str stays str).
        """
        output = {
            "operation": "enum_to_enum",
            "mapping": [{"from": key, "to": value} for key, value in self.mapping.items()],
            "strict": self.strict,
        }
        if self.default is not None:
            output["default"] = self.default
        return output

    @support_iterable
    def transform(self, value: Any) -> Any:
        """
        Map a single value using the configured mapping.
        """
        if value not in self.mapping:
            if self.strict:
                raise KeyError(f"Missing mapping for value: {value}")
            logger.warning("Value %r does not have a defined mapping.", value)
            return self.default
        return self.mapping[value]

    @classmethod
    def from_serialization(cls, serialization):
        """
        Reconstruct an EnumToEnum mapping from a serialized dict.

        `mapping` is a list of {"from", "to"} entries (see `to_dict`). Each key
        and value is read back at its native JSON type, so no key-type coercion
        is needed — int keys stay int, str keys stay str.
        """
        mapping = {entry["from"]: entry["to"] for entry in serialization["mapping"]}
        default = serialization.get("default")
        strict = bool(serialization.get("strict", False))
        return EnumToEnum(mapping, default=default, strict=strict)
