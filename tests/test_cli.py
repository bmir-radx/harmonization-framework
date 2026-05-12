import csv
import json
from pathlib import Path

import pytest

from harmonization_framework import cli


def _write_csv(path: Path, rows, fieldnames):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_rules(path: Path, rules: list) -> None:
    path.write_text(json.dumps(rules, indent=2) + "\n")


def test_cli_harmonize_csv_multiple_rules(tmp_path):
    rules_a = [
        {
            "sources": ["a"],
            "target": "b",
            "operations": [
                {"operation": "enum_to_enum", "mapping": {"1": 10, "2": 20}, "strict": True}
            ],
        }
    ]
    rules_c = [
        {
            "sources": ["c"],
            "target": "d",
            "operations": [
                {"operation": "cast", "source": "text", "target": "integer"}
            ],
        }
    ]

    rules_a_path = tmp_path / "rules_a.json"
    rules_c_path = tmp_path / "rules_c.json"
    _write_rules(rules_a_path, rules_a)
    _write_rules(rules_c_path, rules_c)

    input_path = tmp_path / "input.csv"
    rows = [
        {"a": "1", "c": "3"},
        {"a": "2", "c": "4"},
    ]
    _write_csv(input_path, rows, fieldnames=["a", "c"])

    output_path = tmp_path / "output.csv"

    cli.main([
        "--rules", str(rules_a_path),
        "--rules", str(rules_c_path),
        "--input", str(input_path),
        "--output", str(output_path),
    ])

    with output_path.open() as f:
        reader = csv.DictReader(f)
        out_rows = list(reader)

    assert set(reader.fieldnames) == {"b", "d"}
    assert out_rows == [
        {"b": "10", "d": "3"},
        {"b": "20", "d": "4"},
    ]


def test_cli_targets_filter_and_metadata(tmp_path):
    rules = [
        {"sources": ["a"], "target": "b", "operations": []},
        {"sources": ["c"], "target": "d", "operations": []},
    ]
    rules_path = tmp_path / "rules.json"
    _write_rules(rules_path, rules)

    input_path = tmp_path / "input.csv"
    rows = [
        {"a": "x", "c": "y"},
    ]
    _write_csv(input_path, rows, fieldnames=["a", "c"])

    output_path = tmp_path / "output.csv"
    cli.main([
        "--rules", str(rules_path),
        "--input", str(input_path),
        "--output", str(output_path),
        "--targets", "b",
        "--include-metadata",
    ])

    with output_path.open() as f:
        reader = csv.DictReader(f)
        out_rows = list(reader)

    assert set(reader.fieldnames) == {"b", "source dataset", "original_id"}
    assert out_rows[0]["b"] == "x"
    assert out_rows[0]["original_id"] == "0"
    assert out_rows[0]["source dataset"] == "input.csv"


def test_cli_missing_behavior(tmp_path, capsys):
    rules = [
        {"sources": ["missing_col"], "target": "b", "operations": []},
        {"sources": ["a"], "target": "c", "operations": []},
    ]
    rules_path = tmp_path / "rules.json"
    _write_rules(rules_path, rules)

    input_path = tmp_path / "input.csv"
    rows = [{"a": "1"}]
    _write_csv(input_path, rows, fieldnames=["a"])

    output_path = tmp_path / "output.csv"

    # warn should skip missing and still produce output for a->c
    cli.main([
        "--rules", str(rules_path),
        "--input", str(input_path),
        "--output", str(output_path),
        "--on-missing", "warn",
    ])
    captured = capsys.readouterr()
    assert "skipping missing source columns" in captured.out

    with output_path.open() as f:
        reader = csv.DictReader(f)
        out_rows = list(reader)
    assert set(reader.fieldnames) == {"c"}
    assert out_rows == [{"c": "1"}]

    # error should surface as argparse failure (SystemExit code 2)
    with pytest.raises(SystemExit) as exc:
        cli.main([
            "--rules", str(rules_path),
            "--input", str(input_path),
            "--output", str(output_path),
            "--on-missing", "error",
        ])
    assert exc.value.code == 2


def test_cli_tsv_autodetect(tmp_path):
    rules = [
        {"sources": ["a"], "target": "b", "operations": []},
    ]
    rules_path = tmp_path / "rules.json"
    _write_rules(rules_path, rules)

    input_path = tmp_path / "input.tsv"
    with input_path.open("w", newline="") as f:
        f.write("a\tc\n")
        f.write("x\tz\n")

    output_path = tmp_path / "output.tsv"
    cli.main([
        "--rules", str(rules_path),
        "--input", str(input_path),
        "--output", str(output_path),
        "--on-missing", "warn",
    ])

    with output_path.open() as f:
        content = f.read()

    lines = content.strip().splitlines()
    assert lines[0] == "b"
    assert "x" in lines[1]


def test_cli_missing_rules_file(tmp_path):
    input_path = tmp_path / "input.csv"
    _write_csv(input_path, [{"a": "1"}], fieldnames=["a"])
    output_path = tmp_path / "output.csv"

    with pytest.raises(SystemExit) as exc:
        cli.main([
            "--rules", str(tmp_path / "missing_rules.json"),
            "--input", str(input_path),
            "--output", str(output_path),
        ])
    assert exc.value.code == 2


def test_cli_missing_input_file(tmp_path):
    rules = [
        {"sources": ["a"], "target": "b", "operations": []},
    ]
    rules_path = tmp_path / "rules.json"
    _write_rules(rules_path, rules)

    with pytest.raises(SystemExit) as exc:
        cli.main([
            "--rules", str(rules_path),
            "--input", str(tmp_path / "missing.csv"),
            "--output", str(tmp_path / "output.csv"),
        ])
    assert exc.value.code == 2


def test_cli_accepts_legacy_nested_rules_schema(tmp_path):
    # Legacy nested {source: {target: rule}} schema should still load.
    legacy_rules = {
        "a": {"b": {"source": "a", "target": "b", "operations": []}},
    }
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(legacy_rules))

    input_path = tmp_path / "input.csv"
    _write_csv(input_path, [{"a": "1"}], fieldnames=["a"])
    output_path = tmp_path / "output.csv"

    cli.main([
        "--rules", str(rules_path),
        "--input", str(input_path),
        "--output", str(output_path),
    ])

    with output_path.open() as f:
        reader = csv.DictReader(f)
        out_rows = list(reader)
    assert set(reader.fieldnames) == {"b"}
    assert out_rows == [{"b": "1"}]
