import pytest

from harmonization_framework import cli
from harmonization_framework.primitives.factory import OPERATION_CLASSES
from harmonization_framework.primitives.vocabulary import PrimitiveVocabulary


def test_registry_covers_full_vocabulary():
    assert set(OPERATION_CLASSES) == {member.value for member in PrimitiveVocabulary}


def test_every_operation_has_help_text():
    for name, cls in OPERATION_CLASSES.items():
        assert cls.__doc__ and cls.__doc__.strip(), f"{name} has no docstring"


def test_cli_list_operations(capsys):
    cli.main(["--list-operations"])
    out = capsys.readouterr().out
    for name in OPERATION_CLASSES:
        assert f"\n{name}\n" in f"\n{out}"
    # Spot-check that help text accompanies the names.
    assert "Convert numeric values from `source_unit` to `target_unit`" in out


def test_cli_list_operations_json(capsys):
    import json

    cli.main(["--list-operations", "--format", "json"])
    entries = json.loads(capsys.readouterr().out)
    assert {entry["operation"] for entry in entries} == set(OPERATION_CLASSES)
    for entry in entries:
        assert entry["summary"]
        assert entry["help"]
    # The full help for the combinators includes their authoring examples.
    case_entry = next(e for e in entries if e["operation"] == "case")
    assert "selector" in case_entry["help"]
    assert "branches" in case_entry["help"]


def test_cli_list_operations_ignores_other_args(capsys):
    # The list is printed even if other flags are supplied.
    cli.main(["--list-operations", "--on-missing", "warn"])
    assert "do_nothing" in capsys.readouterr().out


def test_cli_requires_rules_without_list_operations(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main([])
    assert excinfo.value.code == 2
    assert "--rules is required" in capsys.readouterr().err


def test_cli_validate_requires_rules(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--validate"])
    assert excinfo.value.code == 2
    assert "--rules is required" in capsys.readouterr().err
