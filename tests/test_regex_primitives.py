"""Tests for ExtractRegex (#100) and ValidatePattern (#101)."""

import pytest

from harmonization_framework.harmonization_rule import HarmonizationRule
from harmonization_framework.primitives import ExtractRegex, ValidatePattern


# -----------------------------------------------------------------------------
# ExtractRegex
# -----------------------------------------------------------------------------


def test_extract_regex_basic_numeric_group():
    primitive = ExtractRegex(r"MRN[:\s]+([A-Z0-9-]+)")
    assert primitive.transform("Patient MRN: A12-99") == "A12-99"


def test_extract_regex_explicit_group_index():
    primitive = ExtractRegex(r"visit_(\d+)", group=1)
    assert primitive.transform("visit_0042") == "0042"


def test_extract_regex_named_group():
    primitive = ExtractRegex(r"(?P<id>[A-Z]+\d+)", group="id")
    assert primitive.transform("see record AB123 today") == "AB123"


def test_extract_regex_group_zero_returns_full_match():
    primitive = ExtractRegex(r"\d+", group=0)
    assert primitive.transform("answer is 42 today") == "42"


def test_extract_regex_no_match_strict_raises():
    primitive = ExtractRegex(r"\d+", strict=True)
    with pytest.raises(ValueError, match="did not match"):
        primitive.transform("no digits here")


def test_extract_regex_no_match_non_strict_returns_default():
    primitive = ExtractRegex(r"\d+", strict=False, default="UNKNOWN")
    assert primitive.transform("no digits here") == "UNKNOWN"


def test_extract_regex_invalid_group_strict_raises():
    primitive = ExtractRegex(r"(\d+)", group=5, strict=True)
    with pytest.raises(ValueError, match="Group .* not found"):
        primitive.transform("matches 42 here")


def test_extract_regex_invalid_group_non_strict_returns_default():
    primitive = ExtractRegex(r"(\d+)", group=5, strict=False, default=None)
    assert primitive.transform("matches 42 here") is None


def test_extract_regex_iterable_input():
    primitive = ExtractRegex(r"(\d+)")
    assert primitive.transform(["a1", "b22", "c333"]) == ["1", "22", "333"]


def test_extract_regex_flags():
    primitive = ExtractRegex(r"([A-Z]+)", flags=["IGNORECASE"])
    assert primitive.transform("hello") == "hello"


def test_extract_regex_rejects_invalid_pattern():
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        ExtractRegex(r"[")


def test_extract_regex_rejects_unknown_flag():
    with pytest.raises(ValueError, match="Unsupported regex flag"):
        ExtractRegex(r"\d+", flags=["VERBOSE"])


def test_extract_regex_rejects_negative_group_index():
    with pytest.raises(ValueError, match="non-negative"):
        ExtractRegex(r"(\d+)", group=-1)


def test_extract_regex_serialization_roundtrip():
    primitive = ExtractRegex(
        r"MRN[:\s]+([A-Z0-9-]+)",
        group=1,
        strict=False,
        default="UNK",
    )
    payload = primitive.to_dict()
    assert payload == {
        "operation": "extract_regex",
        "expression": r"MRN[:\s]+([A-Z0-9-]+)",
        "group": 1,
        "strict": False,
        "default": "UNK",
    }
    roundtrip = ExtractRegex.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert roundtrip.transform("MRN: A12-99") == "A12-99"


def test_extract_regex_serialization_includes_flags_when_set():
    primitive = ExtractRegex(r"([a-z]+)", flags=["IGNORECASE", "MULTILINE"])
    payload = primitive.to_dict()
    assert payload["flags"] == ["IGNORECASE", "MULTILINE"]
    roundtrip = ExtractRegex.from_serialization(payload)
    assert roundtrip.transform("HELLO") == "HELLO"


def test_extract_regex_passes_null_through():
    primitive = ExtractRegex(r"\d+")
    assert primitive.transform(None) is None


def test_extract_regex_in_rule_chain():
    rule = HarmonizationRule(
        ["raw_id"],
        "extracted_id",
        [ExtractRegex(r"ID:(\w+)", group=1)],
    )
    roundtrip = HarmonizationRule.from_serialization(rule.serialize())
    assert roundtrip.transform("ID:ABC123") == "ABC123"


# -----------------------------------------------------------------------------
# ValidatePattern
# -----------------------------------------------------------------------------


def test_validate_pattern_returns_value_when_valid_default_match():
    primitive = ValidatePattern(r"[A-Z]{2}\d{6}")
    assert primitive.transform("AB123456") == "AB123456"


def test_validate_pattern_strict_failure_raises():
    primitive = ValidatePattern(r"^[A-Z]{2}\d{6}$", mode="fullmatch")
    with pytest.raises(ValueError, match="does not match"):
        primitive.transform("AB12345")


def test_validate_pattern_non_strict_failure_returns_default():
    primitive = ValidatePattern(
        r"^[A-Z]{2}\d{6}$",
        mode="fullmatch",
        strict=False,
        default=None,
    )
    assert primitive.transform("invalid") is None


def test_validate_pattern_match_mode_anchors_at_start_only():
    # 'match' only requires anchoring at the start; trailing text is OK.
    primitive = ValidatePattern(r"[A-Z]{2}", mode="match")
    assert primitive.transform("AB-extra") == "AB-extra"
    with pytest.raises(ValueError):
        primitive.transform("-AB")


def test_validate_pattern_fullmatch_mode_anchors_both_ends():
    primitive = ValidatePattern(r"[A-Z]{2}", mode="fullmatch")
    assert primitive.transform("AB") == "AB"
    with pytest.raises(ValueError):
        primitive.transform("ABC")


def test_validate_pattern_search_mode_matches_anywhere():
    primitive = ValidatePattern(r"\d+", mode="search")
    assert primitive.transform("the answer is 42") == "the answer is 42"
    with pytest.raises(ValueError):
        primitive.transform("no digits")


def test_validate_pattern_iterable_input():
    primitive = ValidatePattern(r"^[A-Z]{2}$", mode="fullmatch")
    assert primitive.transform(["AB", "CD"]) == ["AB", "CD"]


def test_validate_pattern_iterable_strict_failure_propagates():
    primitive = ValidatePattern(r"^[A-Z]{2}$", mode="fullmatch")
    with pytest.raises(ValueError, match="does not match"):
        primitive.transform(["AB", "abc"])


def test_validate_pattern_rejects_invalid_pattern():
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        ValidatePattern(r"[")


def test_validate_pattern_rejects_invalid_mode():
    with pytest.raises(ValueError, match="Unsupported mode"):
        ValidatePattern(r"\d+", mode="weird")


def test_validate_pattern_rejects_unknown_flag():
    with pytest.raises(ValueError, match="Unsupported regex flag"):
        ValidatePattern(r"\d+", flags=["WHATEVER"])


def test_validate_pattern_serialization_roundtrip():
    primitive = ValidatePattern(
        r"^[A-Z]{2}\d{6}$",
        flags=["IGNORECASE"],
        mode="fullmatch",
        strict=False,
        default="INVALID",
    )
    payload = primitive.to_dict()
    assert payload == {
        "operation": "validate_pattern",
        "expression": r"^[A-Z]{2}\d{6}$",
        "mode": "fullmatch",
        "strict": False,
        "flags": ["IGNORECASE"],
        "default": "INVALID",
    }
    roundtrip = ValidatePattern.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert roundtrip.transform("ab123456") == "ab123456"


def test_validate_pattern_passes_null_through():
    primitive = ValidatePattern(r"^[A-Z]+$", mode="fullmatch")
    assert primitive.transform(None) is None


def test_validate_pattern_in_rule_chain():
    rule = HarmonizationRule(
        ["id"],
        "validated_id",
        [ValidatePattern(r"^[A-Z]{2}\d{6}$", mode="fullmatch")],
    )
    roundtrip = HarmonizationRule.from_serialization(rule.serialize())
    assert roundtrip.transform("AB123456") == "AB123456"
    with pytest.raises(ValueError):
        roundtrip.transform("nope")
