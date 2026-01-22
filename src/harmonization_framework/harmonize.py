import pandas as pd

from typing import Dict, List, Tuple

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
