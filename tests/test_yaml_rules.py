"""
YAML rule files behave identically to JSON.

`RuleSet.save`/`load` choose the format by file extension (.yaml/.yml -> YAML,
otherwise JSON). YAML and JSON encode the same flat array of rule dicts, so a
rule set round-trips through either form and produces identical harmonized
output. YAML also preserves integer mapping keys natively (a property the
example suite relies on for one-hot index -> label mappings).
"""

import csv

import pandas as pd

from harmonization_framework import cli
from harmonization_framework.harmonization_rule import HarmonizationRule
from harmonization_framework.harmonize import harmonize_dataset
from harmonization_framework.primitives import EnumToEnum, Round
from harmonization_framework.rule_registry import RuleSet


def _sample_ruleset() -> RuleSet:
    rules = RuleSet()
    # An int-keyed enum mapping to string labels — the case that must keep its
    # key type through serialization — plus a second primitive for variety.
    rules.add_rule(
        HarmonizationRule(
            sources=["code"],
            target="label",
            transformation=[EnumToEnum({1: "one", 2: "two"}, default="other", strict=False)],
        )
    )
    rules.add_rule(
        HarmonizationRule(
            sources=["measure"],
            target="measure_rounded",
            transformation=[Round(1)],
        )
    )
    return rules


def test_yaml_roundtrip_preserves_int_keys(tmp_path):
    path = tmp_path / "rules.yaml"
    _sample_ruleset().save(str(path))

    loaded = RuleSet()
    loaded.load(str(path), clean=True)

    df = pd.DataFrame({"code": [1, 2, 3], "measure": [1.23, 4.56, 7.89]})
    out = harmonize_dataset(df, loaded, "t")

    # Integer keys survived YAML: 1 -> one, 2 -> two, 3 (unmapped) -> other.
    assert out["label"].tolist() == ["one", "two", "other"]
    assert out["measure_rounded"].tolist() == [1.2, 4.6, 7.9]


def test_json_and_yaml_produce_identical_output(tmp_path):
    json_path = tmp_path / "rules.json"
    yaml_path = tmp_path / "rules.yaml"
    _sample_ruleset().save(str(json_path))
    _sample_ruleset().save(str(yaml_path))

    df = pd.DataFrame({"code": [1, 2, 3], "measure": [1.23, 4.56, 7.89]})

    from_json = RuleSet()
    from_json.load(str(json_path), clean=True)
    from_yaml = RuleSet()
    from_yaml.load(str(yaml_path), clean=True)

    out_json = harmonize_dataset(df, from_json, "t")
    out_yaml = harmonize_dataset(df, from_yaml, "t")
    pd.testing.assert_frame_equal(out_json, out_yaml)


def test_extension_detection(tmp_path):
    # .yml is YAML too.
    yml_path = tmp_path / "rules.yml"
    _sample_ruleset().save(str(yml_path))
    text = yml_path.read_text()
    assert "operation: enum_to_enum" in text  # YAML, not JSON braces

    loaded = RuleSet()
    loaded.load(str(yml_path), clean=True)
    assert len(loaded) == 2

    # An unknown extension defaults to JSON.
    json_default = tmp_path / "rules.rules"
    _sample_ruleset().save(str(json_default))
    assert json_default.read_text().lstrip().startswith("[")  # JSON array


def test_yaml_uses_hybrid_flow_for_leaf_collections(tmp_path):
    # default_flow_style=None renders scalar-only collections inline (a sources
    # list, a {from, to} mapping entry) while keeping the surrounding structure
    # in block form. This is a readability choice; it must still round-trip.
    path = tmp_path / "rules.yaml"
    _sample_ruleset().save(str(path))
    text = path.read_text()

    assert "sources: [code]" in text          # scalar list rendered inline
    assert "- {from: 1, to: one}" in text      # mapping entry rendered inline
    assert "operations:" in text               # outer structure stays block

    # A blank line separates top-level rules (the second rule is preceded by one).
    assert "\n\n- sources: [measure]" in text  # second rule's source is `measure`

    loaded = RuleSet()
    loaded.load(str(path), clean=True)
    df = pd.DataFrame({"code": [1, 2, 3], "measure": [1.23, 4.56, 7.89]})
    assert harmonize_dataset(df, loaded, "t")["label"].tolist() == ["one", "two", "other"]


def test_cli_accepts_yaml_rules(tmp_path):
    rules = _sample_ruleset()
    yaml_path = tmp_path / "rules.yaml"
    rules.save(str(yaml_path))

    input_path = tmp_path / "input.csv"
    with input_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "measure"])
        writer.writeheader()
        writer.writerows([{"code": "1", "measure": "1.23"}, {"code": "2", "measure": "4.56"}])

    output_path = tmp_path / "output.csv"
    cli.main([
        "--rules", str(yaml_path),
        "--input", str(input_path),
        "--output", str(output_path),
    ])

    with output_path.open() as f:
        out_rows = list(csv.DictReader(f))
    assert [r["label"] for r in out_rows] == ["one", "two"]
