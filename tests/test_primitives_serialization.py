import pytest

from harmonization_framework.primitives import (
    Bin,
    Cast,
    ConvertDate,
    ConvertUnits,
    DoNothing,
    EnumToEnum,
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
from harmonization_framework.primitives.normalize import Normalization
from harmonization_framework.primitives.reduce import Reduction


def test_bin_serialization_and_transform():
    low_label = 100
    high_label = 200
    primitive = Bin([(low_label, (0, 9)), (high_label, (10, 19))])
    payload = primitive.to_dict()

    assert payload["operation"] == "bin"
    assert payload["bins"] == [
        {"label": low_label, "start": 0, "end": 9},
        {"label": high_label, "start": 10, "end": 19},
    ]

    roundtrip = Bin.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform(3) == low_label
    assert primitive.transform([3, 12]) == [low_label, high_label]


def test_bin_rejects_overlapping_bins():
    with pytest.raises(ValueError, match="Overlapping bins detected"):
        Bin([(1, (0, 10)), (2, (10, 20))])


def test_bin_rejects_inverted_ranges():
    with pytest.raises(ValueError, match="Invalid bin range"):
        Bin([(1, (5, 2))])


def test_cast_serialization_and_transform():
    primitive = Cast("text", "integer")
    payload = primitive.to_dict()

    assert payload == {"operation": "cast", "source": "text", "target": "integer"}

    roundtrip = Cast.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform("42") == 42
    assert primitive.transform(["1", "2"]) == [1, 2]


def test_cast_boolean():
    primitive = Cast("text", "boolean")
    assert primitive.transform("true") is True
    assert primitive.transform("0") is False
    assert primitive.transform(1) is True
    assert primitive.transform(0) is False
    assert primitive.transform([True, False]) == [True, False]


def test_cast_decimal_and_float():
    decimal_cast = Cast("text", "decimal")
    float_cast = Cast("text", "float")

    assert decimal_cast.transform("3.5") == pytest.approx(3.5)
    assert float_cast.transform("4.25") == pytest.approx(4.25)
    assert float_cast.transform([1, 2.5]) == [1.0, 2.5]


def test_cast_validation_rejects_unknown_target():
    with pytest.raises(ValueError, match="Unsupported cast target"):
        Cast("text", "unknown")


def test_enum_to_enum_serialization_and_transform():
    primitive = EnumToEnum({1: 10, 2: 20})
    payload = primitive.to_dict()

    assert payload["operation"] == "enum_to_enum"
    assert payload["mapping"] == {1: 10, 2: 20}
    assert payload["strict"] is False

    roundtrip = EnumToEnum.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform(1) == 10
    assert primitive.transform([1, 2]) == [10, 20]


def test_enum_to_enum_string_mapping_roundtrip():
    payload = {
        "operation": "enum_to_enum",
        "mapping": {"BL": "baseline", "FU": "follow_up"},
        "default": "unknown",
        "strict": False,
    }

    roundtrip = EnumToEnum.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert roundtrip.transform("BL") == "baseline"
    assert roundtrip.transform(["BL", "FU", "ZZ"]) == ["baseline", "follow_up", "unknown"]


def test_enum_to_enum_string_keys_preserved():
    payload = {
        "operation": "enum_to_enum",
        "mapping": {"1": "one", "2": "two"},
        "strict": False,
    }

    roundtrip = EnumToEnum.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert roundtrip.transform("1") == "one"


def test_enum_to_enum_default_for_missing_value():
    primitive = EnumToEnum({1: 10}, default=-1)
    assert primitive.transform(2) == -1
    assert primitive.transform([1, 2]) == [10, -1]


def test_enum_to_enum_strict_raises_for_missing_value():
    primitive = EnumToEnum({1: 10}, strict=True)
    with pytest.raises(KeyError, match="Missing mapping"):
        primitive.transform(2)


def test_round_serialization_and_transform():
    primitive = Round(2)
    payload = primitive.to_dict()

    assert payload == {"operation": "round", "precision": 2}

    roundtrip = Round.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform(1.234) == 1.23
    assert primitive.transform([1.234, 2.345]) == [1.23, 2.35]


def test_round_rejects_invalid_precision():
    with pytest.raises(TypeError, match="Precision must be an integer"):
        Round(2.5)
    with pytest.raises(ValueError, match="non-negative"):
        Round(-1)


def test_threshold_serialization_and_transform():
    primitive = Threshold(0, 10)
    payload = primitive.to_dict()

    assert payload == {"operation": "threshold", "lower": 0, "upper": 10}

    roundtrip = Threshold.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform(-5) == 0
    assert primitive.transform(15) == 10
    assert primitive.transform([-5, 5, 15]) == [0, 5, 10]


def test_threshold_validation_and_type_promotion():
    with pytest.raises(TypeError, match="bounds must be numeric"):
        Threshold("low", 1)
    with pytest.raises(ValueError, match="Lower bound"):
        Threshold(5, 1)

    int_bounds = Threshold(0, 10)
    float_bounds = Threshold(0.0, 10.0)
    assert isinstance(int_bounds.transform(5), int)
    assert isinstance(float_bounds.transform(5), float)


def test_truncate_serialization_and_transform():
    primitive = Truncate(3)
    payload = primitive.to_dict()

    assert payload == {"operation": "truncate", "length": 3}

    roundtrip = Truncate.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform("abcdef") == "abc"
    assert primitive.transform(["abcdef", "xyz"]) == ["abc", "xyz"]


def test_truncate_rejects_invalid_length():
    with pytest.raises(TypeError, match="Length must be an integer"):
        Truncate(3.5)
    with pytest.raises(ValueError, match="non-negative"):
        Truncate(-1)


def test_convert_units_serialization_and_transform():
    primitive = ConvertUnits(Unit.INCH, Unit.CENTIMETER)
    payload = primitive.to_dict()

    assert payload == {
        "operation": "convert_units",
        "source_unit": "inch",
        "target_unit": "cm",
    }

    roundtrip = ConvertUnits.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform(2) == pytest.approx(5.08, rel=1e-6)
    assert primitive.transform([1, 2]) == pytest.approx([2.54, 5.08], rel=1e-6)


def test_convert_units_rejects_invalid_units():
    with pytest.raises(ValueError, match="Invalid units"):
        ConvertUnits("nope", "cm")


def test_normalize_text_serialization_and_transform():
    primitive = NormalizeText(Normalization.LOWER)
    payload = primitive.to_dict()

    assert payload == {"operation": "normalize_text", "normalization": "lower"}

    roundtrip = NormalizeText.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform("AbC") == "abc"
    assert primitive.transform(["AbC", "DeF"]) == ["abc", "def"]


def test_convert_date_serialization_and_transform():
    primitive = ConvertDate("%Y-%m-%d", "%m/%d/%Y")
    payload = primitive.to_dict()

    assert payload == {
        "operation": "convert_date",
        "source_format": "%Y-%m-%d",
        "target_format": "%m/%d/%Y",
    }

    roundtrip = ConvertDate.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform("2026-01-22") == "01/22/2026"
    assert primitive.transform(["2026-01-22", "2026-12-31"]) == ["01/22/2026", "12/31/2026"]


def test_convert_date_invalid_input_raises_with_context():
    primitive = ConvertDate("%Y-%m-%d", "%m/%d/%Y")
    with pytest.raises(ValueError, match="source_format"):
        primitive.transform("01/22/2026")


def test_scale_serialization_and_transform():
    primitive = Scale(2.5)
    payload = primitive.to_dict()

    assert payload == {"operation": "scale", "scaling_factor": 2.5}

    roundtrip = Scale.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform(2) == 5.0
    assert primitive.transform([2, 4]) == [5.0, 10.0]


def test_scale_rejects_non_numeric():
    with pytest.raises(TypeError, match="Scaling factor must be numeric"):
        Scale("nope")


def test_offset_serialization_and_transform():
    primitive = Offset(3)
    payload = primitive.to_dict()

    assert payload == {"operation": "offset", "offset": 3}

    roundtrip = Offset.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform(5) == 8
    assert primitive.transform([1, 2]) == [4, 5]


def test_offset_rejects_non_numeric():
    with pytest.raises(TypeError, match="Offset must be numeric"):
        Offset("nope")


def test_reduce_serialization_and_transform():
    primitive = Reduce(Reduction.SUM)
    payload = primitive.to_dict()

    assert payload == {"operation": "reduce", "reduction": "sum"}

    roundtrip = Reduce.from_serialization(payload)
    assert roundtrip.to_dict() == payload

    assert primitive.transform([1, 2, 3]) == 6


def test_reduce_rejects_non_list():
    primitive = Reduce(Reduction.SUM)
    with pytest.raises(TypeError, match="list or tuple"):
        primitive.transform(5)


def test_reduce_rejects_empty_list():
    primitive = Reduce(Reduction.ANY)
    with pytest.raises(ValueError, match="non-empty"):
        primitive.transform([])


def test_reduce_onehot_validates_values():
    primitive = Reduce(Reduction.ONEHOT)
    with pytest.raises(ValueError, match="0/1"):
        primitive.transform([0, 2, 0])


def test_substitute_serialization_and_transform():
    primitive = Substitute(r"foo", "bar")
    payload = primitive.to_dict()

    assert payload == {"operation": "substitute", "expression": "foo", "substitution": "bar"}

    roundtrip = Substitute.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform("foo baz") == "bar baz"
    assert primitive.transform(["foo", "food"]) == ["bar", "bard"]


def test_substitute_rejects_invalid_regex():
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        Substitute(r"[", "x")


def test_do_nothing_serialization_and_transform():
    primitive = DoNothing()
    payload = primitive.to_dict()

    assert payload == {"operation": "do_nothing"}

    roundtrip = DoNothing.from_serialization(payload)
    assert roundtrip.to_dict() == payload
    assert primitive.transform("abc") == "abc"
    assert primitive.transform([1, 2]) == [1, 2]
