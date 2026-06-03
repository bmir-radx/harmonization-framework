from typing import Any, Dict, List, Union

from .base import PrimitiveOperation, isnull, support_iterable


class MissingCode(PrimitiveOperation):
    """
    Operator that turns a column's missing-value codes into real nulls.

    Real datasets frequently encode "missing" as an in-band sentinel value — a
    numeric code like -999 or a token like "UNK" — rather than as an empty cell.
    Such a code is an ordinary value to pandas: it survives every transform and
    corrupts results. This primitive recognises a declared set of codes and maps
    each to a genuine null (None), while passing all other values — including
    real nulls — through unchanged. It is the identity-preserving null map that
    EnumToEnum cannot express (EnumToEnum sends unmapped values to its default).

    Codes carry a human label describing what the code means ("not_measured",
    "refused", …). The labels are not emitted into the output column (a null has
    no room for a reason); instead the harmonize engine reports each nulled cell,
    with its label and row index, to the replay log. The labels are also recorded
    in `rules.json` via `to_dict`, so the ruleset documents what each code means.

    Intended placement: MissingCode should be the FIRST primitive in a rule's
    transformation chain, because it operates on the raw source value and the
    engine re-scans the raw source column to report hits. Putting a value-
    altering primitive before it would desynchronise the report from the data.

    Args:
        codes: Either a list of codes (`[-999, -1]`, each labelled "missing") or
            a dict mapping code -> label (`{-999: "not_measured"}`). Normalised
            to a dict internally.
    """

    DEFAULT_LABEL = "missing"

    def __init__(self, codes: Union[List[Any], Dict[Any, str]]):
        if isinstance(codes, dict):
            normalized = dict(codes)
        elif isinstance(codes, (list, tuple, set)):
            normalized = {code: self.DEFAULT_LABEL for code in codes}
        else:
            raise TypeError("MissingCode codes must be a list or a dict")
        if not normalized:
            raise ValueError("MissingCode requires at least one code")
        self.codes = normalized

    def __str__(self):
        items = [f"  {code}->null ({label})" for code, label in self.codes.items()]
        return "Missing-value codes:\n" + "\n".join(items)

    def to_dict(self):
        """
        Serialize this operation to a JSON-friendly dict.

        Always emits the normalized {code: label} dict form, so a MissingCode
        built from a bare list round-trips identically to one built from a dict.
        """
        return {
            "operation": "missing_code",
            "codes": self.codes,
        }

    @support_iterable
    def transform(self, value: Any) -> Any:
        """
        Map a declared missing-value code to None; pass everything else through.

        A genuine null is passed through unchanged (it is already missing and is
        never treated as a code). Any value matching a declared code becomes
        None. All other values are returned unchanged — the identity branch.
        """
        if isnull(value):
            return value
        if value in self.codes:
            return None
        return value

    @classmethod
    def from_serialization(cls, serialization):
        """
        Reconstruct a MissingCode operation from a serialized dict.

        JSON object keys are always strings, so an integer code like -999 or a
        float code like -999.0 round-trips as the string "-999"/"-999.0" and
        would no longer match a numeric input. Mirror EnumToEnum's coercion:
        restore int-like keys to int and float-like keys to float so lookups
        match identically in-memory and after a rules.json round-trip. Labels
        (values) are left untouched.
        """
        codes = serialization["codes"]

        def is_int_like(value: Any) -> bool:
            if isinstance(value, bool):
                return False
            if isinstance(value, int):
                return True
            if isinstance(value, str):
                stripped = value.strip()
                return stripped.lstrip("-").isdigit() and stripped != ""
            return False

        def is_float_like(value: Any) -> bool:
            if isinstance(value, bool):
                return False
            if isinstance(value, (int, float)):
                return True
            if isinstance(value, str):
                try:
                    float(value)
                    return True
                except ValueError:
                    return False
            return False

        def coerce_key(key: Any) -> Any:
            if is_int_like(key):
                return int(key)
            if is_float_like(key):
                return float(key)
            return key

        coerced = {coerce_key(key): value for key, value in codes.items()}
        return MissingCode(coerced)
