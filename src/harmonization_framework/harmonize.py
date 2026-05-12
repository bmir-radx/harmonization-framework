import os
import pandas as pd

from typing import Callable, Optional

from .rule_registry import RuleSet
from .replay_log import replay_logger as rlog


def harmonize_dataset(
    dataset: pd.DataFrame,
    rules: RuleSet,
    dataset_name: str,
    logger=None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> pd.DataFrame:
    """
    Apply every rule in the rule set to the provided dataset and return a new dataframe.

    For each rule, the columns named in `rule.sources` are read from the dataset
    and passed (as a list, one element per source) to `rule.transform`. The
    result is written to a new column named `rule.target`. Single-source rules
    transparently unwrap to a scalar inside `transform`.

    The output dataframe contains every column from the input plus the produced
    target columns, along with `source dataset` and `original_id` metadata
    columns.

    Args:
        dataset: Source dataframe.
        rules: RuleSet whose rules will all be applied.
        dataset_name: Name used for the `source dataset` metadata column.
        logger: Optional replay logger for recording applied rules.
        progress_callback: Optional callback invoked with (processed, total) counts.
    """
    dataset_harmonized = dataset.copy()

    rules_list = rules.all_rules()
    total_steps = len(dataset) * len(rules_list) if rules_list else 0
    processed = 0

    for rule in rules_list:
        print(f"Applying rule -> {rule.target} (sources: {rule.sources})")
        if logger:
            rlog.log_operation(logger, rule, dataset_name)

        def transform_with_progress(row, _rule=rule):
            nonlocal processed
            result = _rule.transform(row.tolist())
            processed += 1
            if progress_callback:
                progress_callback(processed, total_steps)
            return result

        dataset_harmonized[rule.target] = dataset[rule.sources].apply(
            transform_with_progress, axis=1
        )

    dataset_harmonized["source dataset"] = [dataset_name] * len(dataset)
    dataset_harmonized["original_id"] = dataset.index.to_list()
    return dataset_harmonized


def harmonize_file(
    input_path: str,
    output_path: str,
    rules: RuleSet,
    dataset_name: Optional[str] = None,
    logger=None,
) -> pd.DataFrame:
    """
    Load a CSV file, apply harmonization, and save the result to disk.
    """
    if dataset_name is None:
        dataset_name = os.path.basename(input_path)

    dataset = pd.read_csv(input_path)
    harmonized = harmonize_dataset(
        dataset=dataset,
        rules=rules,
        dataset_name=dataset_name,
        logger=logger,
    )
    harmonized.to_csv(output_path, index=False)
    return harmonized
