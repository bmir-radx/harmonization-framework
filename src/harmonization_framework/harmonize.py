import os
import pandas as pd

from typing import List, Optional, Tuple

from .rule_registry import RuleRegistry
from .replay_log import replay_logger as rlog


def harmonize_dataset(
    dataset: pd.DataFrame,
    harmonization_pairs: List[Tuple[str]],
    rules: RuleRegistry,
    dataset_name: str,
    logger=None,
) -> pd.DataFrame:
    """
    Apply harmonization rules to the provided dataset and return a new dataframe.

    This function:
    - Renames columns based on the provided source/target pairs.
    - Applies the corresponding harmonization rule to each source column.
    - Appends `source dataset` and `original_id` metadata columns.

    Args:
        dataset: Source dataframe containing the original columns.
        harmonization_pairs: List of (source, target) column name pairs.
        rules: RuleRegistry with harmonization rules keyed by source/target.
        dataset_name: Name used for the `source dataset` metadata column.
        logger: Optional replay logger for recording applied rules.
    """
    # make a new dataframe with the same number of rows and columns
    # and rename the columns
    dataset_harmonized = dataset.copy()
    dataset_harmonized.rename(
        columns={source: target for source, target in harmonization_pairs},
        inplace=True,
    )
    # apply harmonization rule to each column
    for source, target in harmonization_pairs:
        print(f"Requested rule: {source} -> {target}")
        rule = rules.query(source, target)
        # record action in replay logger
        if logger:
            rlog.log_operation(logger, rule, dataset_name)
        dataset_harmonized.rename(columns={source: target}, inplace=True)
        dataset_harmonized[target] = dataset[source].apply(rule.transform)
    # save source dataset
    dataset_harmonized["source dataset"] = [dataset_name] * len(dataset)
    # save old ids
    dataset_harmonized["original_id"] = dataset.index.to_list()
    return dataset_harmonized


def harmonize_file(
    input_path: str,
    output_path: str,
    harmonization_pairs: List[Tuple[str, str]],
    rules: RuleRegistry,
    dataset_name: Optional[str] = None,
    logger=None,
) -> pd.DataFrame:
    """
    Load a CSV file, apply harmonization, and save the result to disk.

    Args:
        input_path: Path to the input CSV.
        output_path: Path where the harmonized CSV will be written.
        harmonization_pairs: List of (source, target) column name pairs.
        rules: RuleRegistry with harmonization rules keyed by source/target.
        dataset_name: Optional label used for the `source dataset` column.
        logger: Optional replay logger for recording applied rules.
    """
    if dataset_name is None:
        dataset_name = os.path.basename(input_path)

    # Load the input dataset and apply harmonization rules.
    dataset = pd.read_csv(input_path)
    harmonized = harmonize_dataset(
        dataset=dataset,
        harmonization_pairs=harmonization_pairs,
        rules=rules,
        dataset_name=dataset_name,
        logger=logger,
    )
    # Persist the output to disk.
    harmonized.to_csv(output_path, index=False)
    return harmonized
