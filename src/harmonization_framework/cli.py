import argparse
import os
import sys
from typing import Iterable, List, Sequence, Tuple

import pandas as pd

from .harmonize import harmonize_dataset
from .rule_registry import RuleRegistry


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
    # Autodetect delimiter based on file extension.
    _, ext = os.path.splitext(path.lower())
    sep = "\t" if ext in {".tsv", ".tab"} else ","
    return pd.read_csv(path, sep=sep)


def _write_table(df: pd.DataFrame, path: str) -> None:
    # Use the same delimiter heuristics as the reader for output.
    _, ext = os.path.splitext(path.lower())
    sep = "\t" if ext in {".tsv", ".tab"} else ","
    df.to_csv(path, index=False, sep=sep)


def _load_rules(rule_paths: Iterable[str]) -> RuleRegistry:
    # Merge multiple rules files into a single registry.
    registry = RuleRegistry()
    first = True
    for path in rule_paths:
        registry.load(path, clean=first)
        first = False
    return registry


def _select_pairs(
    all_pairs: List[Tuple[str, str]],
    targets: List[str],
) -> List[Tuple[str, str]]:
    # Filter rule pairs by requested targets when provided.
    if not targets:
        return all_pairs
    target_set = set(targets)
    return [(source, target) for source, target in all_pairs if target in target_set]


def _filter_missing(
    pairs: List[Tuple[str, str]],
    columns: Iterable[str],
    on_missing: str,
) -> List[Tuple[str, str]]:
    # Enforce missing-source behavior: error, warn+skip, or skip.
    column_set = set(columns)
    missing = [pair for pair in pairs if pair[0] not in column_set]
    if not missing:
        return pairs

    if on_missing == "error":
        missing_sources = ", ".join(sorted({source for source, _ in missing}))
        raise ValueError(f"Missing source columns: {missing_sources}")

    if on_missing == "warn":
        missing_sources = ", ".join(sorted({source for source, _ in missing}))
        print(f"Warning: skipping missing source columns: {missing_sources}")

    # skip missing when warn or skip
    return [pair for pair in pairs if pair[0] in column_set]


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
        # Load and merge all rule files into one registry.
        rules = _load_rules(args.rules)
        # Read the input dataset (CSV/TSV).
        dataset = _read_table(args.input)
    except FileNotFoundError as exc:
        parser.error(f"{exc.filename} not found.")
        return
    except ValueError as exc:
        parser.error(str(exc))
        return

    # Determine which targets to generate.
    targets = _split_list(args.targets)
    pairs = _select_pairs(rules.list_pairs(), targets)
    if not pairs:
        parser.error("No harmonization pairs selected. Check --targets or rules.")
        return

    # Drop or error on missing source columns based on CLI flag.
    try:
        pairs = _filter_missing(pairs, dataset.columns, args.on_missing)
    except ValueError as exc:
        parser.error(str(exc))
        return
    if not pairs:
        parser.error("No harmonization pairs available after filtering missing columns.")
        return

    # Default dataset name mirrors input filename if not explicitly set.
    dataset_name = args.dataset_name
    if dataset_name is None:
        dataset_name = os.path.basename(args.input)

    # Apply harmonization.
    try:
        harmonized = harmonize_dataset(
            dataset=dataset,
            harmonization_pairs=pairs,
            rules=rules,
            dataset_name=dataset_name,
            logger=None,
        )
    except Exception as exc:
        parser.error(f"Failed to harmonize: {exc}")
        return

    # Emit only target columns by default, optionally include metadata.
    target_columns = [target for _, target in pairs]
    if args.include_metadata:
        target_columns += ["source dataset", "original_id"]
    harmonized = harmonized[target_columns]

    # Persist output with delimiter matched to file extension.
    _write_table(harmonized, args.output)


if __name__ == "__main__":
    main()
