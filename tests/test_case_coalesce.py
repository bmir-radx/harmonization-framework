"""Tests for the Case and Coalesce multi-source combinator primitives."""
import pandas as pd

from harmonization_framework.harmonization_rule import HarmonizationRule
from harmonization_framework.harmonize import harmonize_dataset
from harmonization_framework.primitives import (
    Case, Coalesce, ConvertUnits, DoNothing, Round, Scale)
from harmonization_framework.primitives.units import Unit
from harmonization_framework.rule_registry import RuleSet


# --- Case ----------------------------------------------------------------

def _weight_case():
    return Case(
        sources=["weight_units", "weight_lbs", "weight_kgs"],
        selector="weight_units",
        branches=[
            {"when": ["2"], "source": "weight_lbs", "operations": [DoNothing()]},
            {"when": ["1"], "source": "weight_kgs", "operations": [Scale(2.20462), Round(0)]},
        ],
        default=None,
    )


def test_case_selects_pounds_branch_as_is():
    c = _weight_case()
    # units=2 (pounds): take weight_lbs unchanged
    assert c.transform(["2", 150, 68]) == 150


def test_case_selects_kg_branch_and_converts():
    c = _weight_case()
    # units=1 (kilograms): convert weight_kgs -> lbs, rounded
    assert c.transform(["1", 150, 68]) == round(68 * 2.20462)


def test_case_int_selector_matches_string_when():
    c = _weight_case()
    # selector arrives as an int 1 (e.g. pandas) but `when` is "1"
    assert c.transform([1, 150, 68]) == round(68 * 2.20462)


def test_case_null_selector_returns_default():
    c = _weight_case()
    assert c.transform([None, 150, 68]) is None


def test_case_unmatched_selector_returns_default():
    c = _weight_case()
    assert c.transform(["99", 150, 68]) is None


def test_case_serialization_roundtrip():
    rule = HarmonizationRule(
        ["weight_units", "weight_lbs", "weight_kgs"], "nih_weight", [_weight_case()]
    )
    payload = rule.serialize()
    assert payload["operations"][0]["operation"] == "case"
    roundtrip = HarmonizationRule.from_serialization(payload)
    assert roundtrip.serialize() == payload
    assert roundtrip.transform(["1", 150, 68]) == round(68 * 2.20462)


def test_case_in_harmonize_dataset():
    rules = RuleSet()
    rules.add_rule(
        HarmonizationRule(
            ["weight_units", "weight_lbs", "weight_kgs"], "nih_weight", [_weight_case()]
        )
    )
    df = pd.DataFrame([
        {"weight_units": "2", "weight_lbs": 150, "weight_kgs": None},  # pounds
        {"weight_units": "1", "weight_lbs": None, "weight_kgs": 68},   # kilograms
    ])
    out = harmonize_dataset(df, rules, dataset_name="t")
    assert out["nih_weight"].tolist() == [150, round(68 * 2.20462)]


# --- Case with multi-operand branches (height: feet+inches OR meters+cm) ----

def _height_case():
    return Case(
        sources=["height_units", "ft", "inch", "m", "cm"],
        selector="height_units",
        branches=[
            {"when": ["1"], "combine": "sum", "operands": [
                {"source": "ft", "operations": [ConvertUnits(Unit.FEET, Unit.INCH)]},
                {"source": "inch", "operations": [DoNothing()]},
            ]},
            {"when": ["2"], "combine": "sum", "operands": [
                {"source": "m", "operations": [ConvertUnits(Unit.METER, Unit.INCH)]},
                {"source": "cm", "operations": [ConvertUnits(Unit.CENTIMETER, Unit.INCH)]},
            ]},
        ],
        default=None,
    )


def test_case_multioperand_feet_inches_sum():
    c = _height_case()
    # 5 ft + 7 in -> 60 + 7 = 67 inches
    assert c.transform(["1", 5, 7, None, None]) == 67


def test_case_multioperand_meters_cm_sum():
    c = _height_case()
    # 1 m + 70 cm -> ~39.37 + ~27.56 inches
    result = c.transform(["2", None, None, 1, 70])
    assert abs(result - (1 / 0.0254 + 70 / 2.54)) < 0.01


def test_case_multioperand_serialization_roundtrip():
    rule = HarmonizationRule(
        ["height_units", "ft", "inch", "m", "cm"], "nih_height", [_height_case()]
    )
    payload = rule.serialize()
    roundtrip = HarmonizationRule.from_serialization(payload)
    assert roundtrip.serialize() == payload
    assert roundtrip.transform(["1", 5, 7, None, None]) == 67


# --- Coalesce ------------------------------------------------------------

def _weight_coalesce():
    return Coalesce(
        sources=["weight_lbs", "weight_kgs"],
        branches=[
            {"source": "weight_lbs", "operations": [DoNothing()]},
            {"source": "weight_kgs", "operations": [Scale(2.20462), Round(0)]},
        ],
        default=None,
    )


def test_coalesce_first_non_null_wins():
    c = _weight_coalesce()
    assert c.transform([150, None]) == 150          # lbs present
    assert c.transform([None, 68]) == round(68 * 2.20462)  # only kg present


def test_coalesce_precedence_when_both_present():
    c = _weight_coalesce()
    # both populated -> first branch (lbs) wins
    assert c.transform([150, 68]) == 150


def test_coalesce_all_null_returns_default():
    c = _weight_coalesce()
    assert c.transform([None, None]) is None


def test_coalesce_serialization_roundtrip():
    rule = HarmonizationRule(["weight_lbs", "weight_kgs"], "nih_weight", [_weight_coalesce()])
    payload = rule.serialize()
    assert payload["operations"][0]["operation"] == "coalesce"
    roundtrip = HarmonizationRule.from_serialization(payload)
    assert roundtrip.serialize() == payload
    assert roundtrip.transform([None, 68]) == round(68 * 2.20462)


# --- Coalesce with multi-operand branches + combine ----------------------
# Weight reported either as a single pounds field, OR as stone + pounds (two
# fields summed). No unit flag, so Coalesce picks whichever branch is populated;
# the stone+pounds branch uses `combine: "sum"` over two operands.

def _weight_coalesce_combine():
    return Coalesce(
        sources=["weight_lbs", "weight_stone", "weight_stone_lbs"],
        branches=[
            {"source": "weight_lbs", "operations": [DoNothing()]},
            {"combine": "sum", "operands": [
                {"source": "weight_stone", "operations": [Scale(14)]},  # stone -> lbs
                {"source": "weight_stone_lbs", "operations": [DoNothing()]},  # leftover pounds, as-is
            ]},
        ],
        default=None,
    )


def test_coalesce_combine_sums_multioperand_branch():
    c = _weight_coalesce_combine()
    # single pounds field populated -> first branch wins, value as-is
    assert c.transform([150, None, None]) == 150
    # only stone+pounds populated -> second branch: 10 st * 14 + 7 lb = 147
    assert c.transform([None, 10, 7]) == 147


def test_coalesce_combine_serialization_roundtrip():
    rule = HarmonizationRule(
        ["weight_lbs", "weight_stone", "weight_stone_lbs"], "nih_weight",
        [_weight_coalesce_combine()],
    )
    payload = rule.serialize()
    # the multi-operand branch carries combine="sum" and two operands
    branch = payload["operations"][0]["branches"][1]
    assert branch["combine"] == "sum"
    assert [o["source"] for o in branch["operands"]] == ["weight_stone", "weight_stone_lbs"]
    roundtrip = HarmonizationRule.from_serialization(payload)
    assert roundtrip.serialize() == payload
    assert roundtrip.transform([None, 10, 7]) == 147
