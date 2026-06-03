"""
Null-handling contract for the primitive layer.

Scalar primitives decorated with @handle_null must pass `None`, `float NaN`,
and `pd.NA` through unchanged. List-consuming primitives (Reduce, MapEach)
must reject null elements rather than silently dropping or propagating them.
"""

import math

import numpy as np
import pandas as pd
import pytest

from harmonization_framework.harmonization_rule import HarmonizationRule
from harmonization_framework.harmonize import harmonize_dataset
from harmonization_framework.primitives import (
    Bin,
    Cast,
    ConvertDate,
    ConvertUnits,
    FormatNumber,
    MapEach,
    MissingCode,
    NormalizeText,
    Offset,
    Reduce,
    Round,
    Scale,
    Substitute,
    Threshold,
    Truncate,
    Unit,
)
from harmonization_framework.primitives.base import handle_null, isnull
from harmonization_framework.primitives.normalize import Normalization
from harmonization_framework.primitives.reduce import Reduction
from harmonization_framework.rule_registry import RuleSet


NULLS = [None, float("nan"), pd.NA]


def _is_same_null(actual, expected):
    """Helper: NaN != NaN, pd.NA != anything, so compare by category."""
    if expected is None:
        return actual is None
    if isinstance(expected, float) and math.isnan(expected):
        return isinstance(actual, float) and math.isnan(actual)
    if expected is pd.NA:
        return actual is pd.NA
    return actual == expected


# --- isnull() ----------------------------------------------------------------


def test_isnull_recognises_none_nan_pdna():
    assert isnull(None)
    assert isnull(float("nan"))
    assert isnull(np.nan)
    assert isnull(pd.NA)


def test_isnull_rejects_non_nulls():
    assert not isnull(0)
    assert not isnull("")
    assert not isnull([])
    assert not isnull(False)
    assert not isnull("hello")
    assert not isnull(3.14)


# --- @handle_null decorator --------------------------------------------------


def test_handle_null_passes_through_and_calls_underlying_only_for_non_null():
    calls = []

    class _Probe:
        @handle_null
        def transform(self, value):
            calls.append(value)
            return value * 2

    probe = _Probe()
    assert probe.transform(None) is None
    assert math.isnan(probe.transform(float("nan")))
    assert probe.transform(pd.NA) is pd.NA
    assert probe.transform(3) == 6
    # Underlying transform was only invoked for the non-null call.
    assert calls == [3]


# --- Scalar primitives pass nulls through ------------------------------------


@pytest.mark.parametrize("null", NULLS)
def test_scale_passes_null_through(null):
    assert _is_same_null(Scale(2.0).transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_missing_code_passes_genuine_null_through(null):
    # MissingCode is not @handle_null (its null check is explicit), but a real
    # null must never be treated as a code: it passes through unchanged.
    primitive = MissingCode({-999: "not_measured"})
    assert _is_same_null(primitive.transform(null), null)


def test_missing_code_nulls_only_declared_codes():
    primitive = MissingCode({-999: "not_measured"})
    assert primitive.transform(-999) is None      # the code -> real null
    assert primitive.transform(-998) == -998      # neighbour value untouched
    assert primitive.transform(0) == 0            # zero is not a code


@pytest.mark.parametrize("null", NULLS)
def test_offset_passes_null_through(null):
    assert _is_same_null(Offset(3).transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_round_passes_null_through(null):
    assert _is_same_null(Round(2).transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_threshold_passes_null_through(null):
    assert _is_same_null(Threshold(0, 10).transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_truncate_passes_null_through(null):
    assert _is_same_null(Truncate(5).transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_cast_passes_null_through(null):
    # All cast targets must short-circuit on null.
    for target in ("text", "integer", "boolean", "decimal", "float"):
        assert _is_same_null(Cast("text", target).transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_bin_passes_null_through(null):
    primitive = Bin([("low", (0, 9)), ("high", (10, 19))])
    assert _is_same_null(primitive.transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_format_number_passes_null_through(null):
    assert _is_same_null(FormatNumber(2).transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_normalize_text_passes_null_through(null):
    assert _is_same_null(NormalizeText(Normalization.LOWER).transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_substitute_passes_null_through(null):
    assert _is_same_null(Substitute(r"foo", "bar").transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_convert_units_passes_null_through(null):
    assert _is_same_null(ConvertUnits(Unit.KILOGRAM, Unit.POUNDS).transform(null), null)


@pytest.mark.parametrize("null", NULLS)
def test_convert_date_passes_null_through(null):
    assert _is_same_null(ConvertDate("%Y-%m-%d", "%m/%d/%Y").transform(null), null)


# --- support_iterable still passes nulls through inside a list ---------------


def test_scale_list_with_nulls_returns_list_with_nulls_preserved():
    out = Scale(2.0).transform([1, None, 3, float("nan"), 5])
    assert out[0] == 2.0
    assert out[1] is None
    assert out[2] == 6.0
    assert math.isnan(out[3])
    assert out[4] == 10.0


# --- Reduce rejects nulls ----------------------------------------------------


def test_reduce_rejects_null_element():
    with pytest.raises(ValueError, match="null value at position 1"):
        Reduce(Reduction.SUM).transform([1, None, 3])


def test_reduce_rejects_nan_element():
    with pytest.raises(ValueError, match="null value at position 0"):
        Reduce(Reduction.SUM).transform([float("nan"), 1, 2])


def test_reduce_rejects_pdna_element():
    with pytest.raises(ValueError, match="null value at position 2"):
        Reduce(Reduction.ANY).transform([1, 0, pd.NA])


# --- MapEach rejects nulls ---------------------------------------------------


def test_map_each_rejects_null_element():
    with pytest.raises(ValueError, match="null value at position 1"):
        MapEach([Cast("text", "integer")]).transform(["1", None, "3"])


def test_map_each_rejects_pdna_element():
    with pytest.raises(ValueError, match="null value at position 0"):
        MapEach([Offset(1)]).transform([pd.NA, 1, 2])


# --- End-to-end: pandas DataFrame with NaN ----------------------------------


def test_harmonize_dataset_does_not_crash_on_nan_inputs():
    """The motivating real-world case: a CSV with blank cells lands as NaN
    in pandas, and applying a rule chain should leave those rows as null
    rather than raising."""
    rules = RuleSet()
    rules.add_rule(
        HarmonizationRule(
            ["weight_lbs"],
            "weight_kg",
            [Scale(0.453592), Round(2)],
        )
    )
    df = pd.DataFrame({"weight_lbs": [100.0, float("nan"), 200.0, None]})

    out = harmonize_dataset(df, rules, dataset_name="test")
    values = out["weight_kg"].tolist()
    assert values[0] == pytest.approx(45.36)
    # Both NaN and None coming in survive as NaN/None on the way out.
    assert isnull(values[1])
    assert values[2] == pytest.approx(90.72)
    assert isnull(values[3])
