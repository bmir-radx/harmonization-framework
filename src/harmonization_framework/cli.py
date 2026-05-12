import argparse
import os
from typing import Iterable, List, Sequence

import pandas as pd

from .harmonize import harmonize_dataset
from .harmonization_rule import HarmonizationRule
from .rule_registry import RuleSet


def _split_list(values: Sequence[str]) -> List[str]:
    # Accept repeated flags or comma-separated lists and normalize into a flat list.
    items: List[str] = []
    for value in values:
        if value is None:
            continue
        for part in value.split(","):
            part = part.strip()
            if part:
                items.append(part)
    return items


def _read_table(path: str) -> pd.DataFrame:
    _, ext = os.path.splitext(path.lower())
    sep = "\t" if ext in {".tsv", ".tab"} else ","
    return pd.read_csv(path, sep=sep)


def _write_table(df: pd.DataFrame, path: str) -> None:
    _, ext = os.path.splitext(path.lower())
    sep = "\t" if ext in {".tsv", ".tab"} else ","
    df.to_csv(path, index=False, sep=sep)


def _load_rules(rule_paths: Iterable[str]) -> RuleSet:
    # Merge multiple rules files into a single rule set.
    rules = RuleSet()
    first = True
    for path in rule_paths:
        rules.load(path, clean=first)
        first = False
    return rules


def _filter_to_targets(rules: RuleSet, targets: List[str]) -> RuleSet:
    # Apply --targets as a load-time filter on the rule set itself.
    if not targets:
        return rules
    filtered = RuleSet()
    for rule in rules.for_targets(targets):
        filtered.add_rule(rule)
    return filtered


def _filter_missing_sources(
    rules: RuleSet,
    columns: Iterable[str],
    on_missing: str,
) -> RuleSet:
    # Enforce missing-source behavior: error, warn+skip, or skip. A rule is
    # considered missing if any of its source columns is absent.
    column_set = set(columns)
    missing_rules: List[HarmonizationRule] = []
    kept_rules: List[HarmonizationRule] = []
    for rule in rules.all_rules():
        if all(source in column_set for source in rule.sources):
            kept_rules.append(rule)
        else:
            missing_rules.append(rule)

    if missing_rules:
        missing_sources = sorted(
            {source for rule in missing_rules for source in rule.sources if source not in column_set}
        )
        if on_missing == "error":
            raise ValueError(f"Missing source columns: {', '.join(missing_sources)}")
        if on_missing == "warn":
            print(f"Warning: skipping missing source columns: {', '.join(missing_sources)}")

    filtered = RuleSet()
    for rule in kept_rules:
        filtered.add_rule(rule)
    return filtered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harmonize",
        description="Apply harmonization rules to a CSV/TSV file.",
    )
    parser.add_argument(
        "--rules",
        required=True,
        action="append",
        help="Path to a rules JSON file. Can be provided multiple times.",
    )
    parser.add_argument("--input", required=True, help="Input CSV/TSV file.")
    parser.add_argument("--output", required=True, help="Output CSV/TSV file.")
    parser.add_argument(
        "--targets",
        action="append",
        default=[],
        help="Comma-separated list of target columns to generate.",
    )
    parser.add_argument(
        "--dataset-name",
        default=None,
        help="Optional dataset name for metadata columns.",
    )
    parser.add_argument(
        "--on-missing",
        choices=["error", "warn", "skip"],
        default="error",
        help="Behavior when a source column is missing.",
    )
    parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Include source dataset and original_id columns in output.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        rules = _load_rules(args.rules)
        dataset = _read_table(args.input)
    except FileNotFoundError as exc:
        parser.error(f"{exc.filename} not found.")
        return
    except ValueError as exc:
        parser.error(str(exc))
        return

    # Filter the rule set to requested targets before harmonization.
    targets = _split_list(args.targets)
    rules = _filter_to_targets(rules, targets)
    if len(rules) == 0:
        parser.error("No harmonization rules selected. Check --targets or rules.")
        return

    try:
        rules = _filter_missing_sources(rules, dataset.columns, args.on_missing)
    except ValueError as exc:
        parser.error(str(exc))
        return
    if len(rules) == 0:
        parser.error("No harmonization rules available after filtering missing columns.")
        return

    dataset_name = args.dataset_name
    if dataset_name is None:
        dataset_name = os.path.basename(args.input)

    try:
        harmonized = harmonize_dataset(
            dataset=dataset,
            rules=rules,
            dataset_name=dataset_name,
            logger=None,
        )
    except Exception as exc:
        parser.error(f"Failed to harmonize: {exc}")
        return

    target_columns = rules.all_targets()
    if args.include_metadata:
        target_columns = target_columns + ["source dataset", "original_id"]
    harmonized = harmonized[target_columns]

    _write_table(harmonized, args.output)


if __name__ == "__main__":
    main()
