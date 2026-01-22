import json
import pytest

from harmonization_framework.rule import HarmonizationRule
from harmonization_framework.primitives import Cast, DoNothing, Round


def test_rule_serializes_with_empty_operations():
    rule = HarmonizationRule("source_col", "target_col", None)
    payload = rule.serialize()

    assert payload == {
        "source": "source_col",
        "target": "target_col",
        "operations": [],
    }

    # serialization string should be valid JSON with the same payload
    assert json.loads(rule.serialization) == payload


def test_rule_serialization_roundtrip_and_transform():
    rule = HarmonizationRule(
        "age_text",
        "age_years",
        [Cast("text", "integer"), Round(0)],
    )

    payload = rule.serialize()
    assert payload["source"] == "age_text"
    assert payload["target"] == "age_years"
    assert [op["operation"] for op in payload["operations"]] == ["cast", "round"]

    roundtrip = HarmonizationRule.from_serialization(payload)
    assert roundtrip.serialize() == payload
    assert roundtrip.transform("42") == 42


def test_rule_from_serialization_unknown_operation_raises():
    payload = {
        "source": "a",
        "target": "b",
        "operations": [{"operation": "not_a_real_op"}],
    }

    with pytest.raises(ValueError, match="Unknown operation"):
        HarmonizationRule.from_serialization(payload)


def test_rule_transform_with_do_nothing():
    rule = HarmonizationRule("x", "y", [DoNothing()])
    assert rule.transform("abc") == "abc"
