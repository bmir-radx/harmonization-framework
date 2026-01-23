import os
import pandas as pd

from typing import List, Optional, Tuple

from .rule_store import RuleStore
from .replay_log import replay_logger as rlog


def harmonize_dataset(
    dataset: pd.DataFrame,
    harmonization_pairs: List[Tuple[str]],
    rules: RuleStore,
    dataset_name: str,
    logger=None,
) -> pd.DataFrame:
    """
    Apply harmonization rules to the provided dataset and return a new dataframe.
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
    rules: RuleStore,
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
        harmonization_pairs=harmonization_pairs,
        rules=rules,
        dataset_name=dataset_name,
        logger=logger,
    )
    harmonized.to_csv(output_path, index=False)
    return harmonized
