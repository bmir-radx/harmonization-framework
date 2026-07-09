import json
from pathlib import Path

import pytest

from harmonization_framework import cli
from harmonization_framework.rule_registry import validate_rules_file


VALID_RULE = {
    "sources": ["height_in"],
    "target": "height_cm",
    "operations": [
        {"operation": "convert_units", "source_unit": "inch", "target_unit": "cm"},
        {"operation": "round", "precision": 1},
    ],
}


def _write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def test_validate_valid_json_file(tmp_path):
    rules_path = tmp_path / "rules.json"
    _write_json(rules_path, [VALID_RULE])
    assert validate_rules_file(str(rules_path)) == []


def test_validate_valid_yaml_file(tmp_path):
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text(
        "- sources: [height_in]\n"
        "  target: height_cm\n"
        "  operations:\n"
        "  - {operation: convert_units, source_unit: inch, target_unit: cm}\n"
        "  - {operation: round, precision: 1}\n"
    )
    assert validate_rules_file(str(rules_path)) == []


def test_validate_legacy_source_key(tmp_path):
    rules_path = tmp_path / "rules.json"
    _write_json(
        rules_path,
        [{"source": "a", "target": "b", "operations": [{"operation": "do_nothing"}]}],
    )
    assert validate_rules_file(str(rules_path)) == []


def test_validate_missing_file(tmp_path):
    problems = validate_rules_file(str(tmp_path / "nope.json"))
    assert problems == ["file not found"]


def test_validate_json_syntax_error(tmp_path):
    rules_path = tmp_path / "rules.json"
    rules_path.write_text("[{,]")
    problems = validate_rules_file(str(rules_path))
    assert len(problems) == 1
    assert problems[0].startswith("invalid JSON")


def test_validate_yaml_syntax_error(tmp_path):
    rules_path = tmp_path / "rules.yaml"
    rules_path.write_text("- sources: [a\n  target: b\n")
    problems = validate_rules_file(str(rules_path))
    assert len(problems) == 1
    assert problems[0].startswith("invalid YAML")


def test_validate_empty_file(tmp_path):
    rules_path = tmp_path / "rules.json"
    _write_json(rules_path, [])
    assert validate_rules_file(str(rules_path)) == ["file contains no rules"]


def test_validate_unknown_operation(tmp_path):
    rules_path = tmp_path / "rules.json"
    _write_json(
        rules_path,
        [
            {
                "sources": ["a"],
                "target": "b",
                "operations": [{"operation": "frobnicate"}],
            }
        ],
    )
    problems = validate_rules_file(str(rules_path))
    assert len(problems) == 1
    assert "'frobnicate'" in problems[0]
    assert "unknown operation" in problems[0]


def test_validate_unknown_operation_suggests_close_match(tmp_path):
    rules_path = tmp_path / "rules.json"
    _write_json(
        rules_path,
        [
            {
                "sources": ["a"],
                "target": "b",
                "operations": [{"operation": "normalize_bool"}],
            }
        ],
    )
    problems = validate_rules_file(str(rules_path))
    assert len(problems) == 1
    assert "did you mean 'normalize_boolean'?" in problems[0]


def test_validate_bad_operation_settings(tmp_path):
    # A known operation with an invalid setting (bad regex) is reported.
    rules_path = tmp_path / "rules.json"
    _write_json(
        rules_path,
        [
            {
                "sources": ["a"],
                "target": "b",
                "operations": [{"operation": "extract_regex", "expression": "("}],
            }
        ],
    )
    problems = validate_rules_file(str(rules_path))
    assert len(problems) == 1
    assert "operation 1 ('extract_regex')" in problems[0]


def test_validate_missing_target_and_sources(tmp_path):
    rules_path = tmp_path / "rules.json"
    _write_json(rules_path, [{"operations": []}])
    problems = validate_rules_file(str(rules_path))
    assert any("'target'" in p for p in problems)
    assert any("'sources'" in p for p in problems)


def test_validate_duplicate_target(tmp_path):
    rules_path = tmp_path / "rules.json"
    _write_json(rules_path, [VALID_RULE, VALID_RULE])
    problems = validate_rules_file(str(rules_path))
    assert len(problems) == 1
    assert "duplicate target 'height_cm'" in problems[0]
    assert "rule 1" in problems[0]


def test_validate_reports_all_problems(tmp_path):
    # Validation keeps going after the first bad rule.
    rules_path = tmp_path / "rules.json"
    _write_json(
        rules_path,
        [
            {"sources": ["a"], "target": "b", "operations": [{"operation": "nope1"}]},
            {"sources": ["c"], "target": "d", "operations": [{"operation": "nope2"}]},
        ],
    )
    problems = validate_rules_file(str(rules_path))
    assert len(problems) == 2


def test_cli_validate_ok(tmp_path, capsys):
    rules_path = tmp_path / "rules.json"
    _write_json(rules_path, [VALID_RULE])
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--validate", "--rules", str(rules_path)])
    assert excinfo.value.code == 0
    assert f"{rules_path}: OK" in capsys.readouterr().out


def test_cli_validate_invalid_exits_nonzero(tmp_path, capsys):
    rules_path = tmp_path / "rules.json"
    _write_json(
        rules_path,
        [{"sources": ["a"], "target": "b", "operations": [{"operation": "frobnicate"}]}],
    )
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--validate", "--rules", str(rules_path)])
    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert f"{rules_path}: INVALID" in out
    assert "frobnicate" in out
    assert "hint: run 'harmonize --list-operations'" in out


def test_cli_validate_no_hint_without_unknown_operation(tmp_path, capsys):
    rules_path = tmp_path / "rules.json"
    _write_json(rules_path, [{"target": "b"}])
    with pytest.raises(SystemExit):
        cli.main(["--validate", "--rules", str(rules_path)])
    assert "--list-operations" not in capsys.readouterr().out


def test_cli_validate_multiple_files(tmp_path, capsys):
    good = tmp_path / "good.json"
    bad = tmp_path / "bad.json"
    _write_json(good, [VALID_RULE])
    _write_json(bad, [{"target": "b"}])
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--validate", "--rules", str(good), "--rules", str(bad)])
    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert f"{good}: OK" in out
    assert f"{bad}: INVALID" in out


def test_cli_harmonize_still_requires_input_and_output(tmp_path, capsys):
    rules_path = tmp_path / "rules.json"
    _write_json(rules_path, [VALID_RULE])
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--rules", str(rules_path)])
    assert excinfo.value.code == 2
    assert "--input and --output are required" in capsys.readouterr().err
