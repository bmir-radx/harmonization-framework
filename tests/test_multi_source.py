import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from harmonization_framework import cli
from harmonization_framework.harmonization_rule import HarmonizationRule
from harmonization_framework.harmonize import harmonize_dataset
from harmonization_framework.primitives import Cast, EnumToEnum, MapEach, Reduce
from harmonization_framework.primitives.reduce import Reduction
from harmonization_framework.rule_registry import RuleSet


def test_multi_source_rule_serialization_roundtrip():
    rule = HarmonizationRule(
        ["flag_baseline", "flag_followup", "flag_screening"],
        "visit_type",
        [
            MapEach([Cast("text", "integer")]),
            Reduce(Reduction.ONEHOT),
            EnumToEnum({0: "baseline", 1: "follow_up", 2: "screening"}),
        ],
    )
    payload = rule.serialize()

    assert payload["sources"] == ["flag_baseline", "flag_followup", "flag_screening"]
    assert payload["target"] == "visit_type"
    assert [op["operation"] for op in payload["operations"]] == [
        "map_each",
        "reduce",
        "enum_to_enum",
    ]

    roundtrip = HarmonizationRule.from_serialization(payload)
    assert roundtrip.serialize() == payload
    # Three flags, follow_up = index 1
    assert roundtrip.transform(["0", "1", "0"]) == "follow_up"


def test_harmonize_dataset_with_multi_source_one_hot_rule():
    rules = RuleSet()
    rules.add_rule(
        HarmonizationRule(
            ["flag_baseline", "flag_followup", "flag_screening"],
            "visit_type",
            [
                Reduce(Reduction.ONEHOT),
                EnumToEnum({0: "baseline", 1: "follow_up", 2: "screening"}),
            ],
        )
    )
    df = pd.DataFrame(
        [
            {"flag_baseline": 1, "flag_followup": 0, "flag_screening": 0},
            {"flag_baseline": 0, "flag_followup": 1, "flag_screening": 0},
            {"flag_baseline": 0, "flag_followup": 0, "flag_screening": 1},
        ]
    )

    out = harmonize_dataset(df, rules, dataset_name="test")
    assert out["visit_type"].tolist() == ["baseline", "follow_up", "screening"]


def test_harmonize_dataset_multi_source_sum_with_map_each():
    rules = RuleSet()
    rules.add_rule(
        HarmonizationRule(
            ["mon", "tue", "wed", "thu", "fri"],
            "total_hours",
            [
                MapEach([Cast("text", "integer")]),
                Reduce(Reduction.SUM),
            ],
        )
    )
    df = pd.DataFrame(
        [
            {"mon": "8", "tue": "8", "wed": "8", "thu": "8", "fri": "6"},
            {"mon": "4", "tue": "0", "wed": "8", "thu": "8", "fri": "8"},
        ]
    )

    out = harmonize_dataset(df, rules, dataset_name="test")
    assert out["total_hours"].tolist() == [38, 28]


def _write_csv(path: Path, rows, fieldnames):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_cli_runs_multi_source_rule(tmp_path):
    rules = [
        {
            "sources": ["flag_baseline", "flag_followup", "flag_screening"],
            "target": "visit_type",
            "operations": [
                {"operation": "map_each", "operations": [{"operation": "cast", "source": "text", "target": "integer"}]},
                {"operation": "reduce", "reduction": "one-hot"},
                {
                    "operation": "cast",
                    "source": "integer",
                    "target": "text",
                },
                {
                    "operation": "enum_to_enum",
                    "mapping": {"0": "baseline", "1": "follow_up", "2": "screening"},
                    "strict": True,
                },
            ],
        }
    ]
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules) + "\n")

    input_path = tmp_path / "input.csv"
    _write_csv(
        input_path,
        [
            {"flag_baseline": "1", "flag_followup": "0", "flag_screening": "0"},
            {"flag_baseline": "0", "flag_followup": "0", "flag_screening": "1"},
        ],
        fieldnames=["flag_baseline", "flag_followup", "flag_screening"],
    )

    output_path = tmp_path / "output.csv"
    cli.main([
        "--rules", str(rules_path),
        "--input", str(input_path),
        "--output", str(output_path),
    ])

    with output_path.open() as f:
        out_rows = list(csv.DictReader(f))
    assert out_rows == [{"visit_type": "baseline"}, {"visit_type": "screening"}]


def test_cli_multi_source_on_missing_skips_when_any_source_absent(tmp_path):
    # Multi-source rule needs all three flags; only two are present in the input.
    # A single-source rule on a present column should still run.
    rules = [
        {
            "sources": ["flag_baseline", "flag_followup", "flag_screening"],
            "target": "visit_type",
            "operations": [{"operation": "reduce", "reduction": "one-hot"}],
        },
        {"sources": ["age"], "target": "age_years", "operations": []},
    ]
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules) + "\n")

    input_path = tmp_path / "input.csv"
    _write_csv(
        input_path,
        [{"flag_baseline": "1", "flag_followup": "0", "age": "10"}],
        fieldnames=["flag_baseline", "flag_followup", "age"],
    )

    output_path = tmp_path / "output.csv"
    cli.main([
        "--rules", str(rules_path),
        "--input", str(input_path),
        "--output", str(output_path),
        "--on-missing", "skip",
    ])

    with output_path.open() as f:
        reader = csv.DictReader(f)
        out_rows = list(reader)
    assert set(reader.fieldnames) == {"age_years"}
    assert out_rows == [{"age_years": "10"}]


def test_cli_multi_source_on_missing_error_raises(tmp_path):
    rules = [
        {
            "sources": ["a", "b"],
            "target": "combined",
            "operations": [{"operation": "reduce", "reduction": "sum"}],
        }
    ]
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules) + "\n")

    input_path = tmp_path / "input.csv"
    _write_csv(input_path, [{"a": "1"}], fieldnames=["a"])
    output_path = tmp_path / "output.csv"

    with pytest.raises(SystemExit) as exc:
        cli.main([
            "--rules", str(rules_path),
            "--input", str(input_path),
            "--output", str(output_path),
            "--on-missing", "error",
        ])
    assert exc.value.code == 2
