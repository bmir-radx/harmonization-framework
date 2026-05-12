import json
from typing import Dict, List

import pandas as pd

from ..harmonization_rule import HarmonizationRule
from ..harmonize import harmonize_dataset
from ..replay_log import replay_logger as rlog
from ..rule_registry import RuleSet


def combine_datasets(datasets: List[pd.DataFrame]):
    combined_dataset = pd.concat(datasets, axis=0, ignore_index=True)
    combined_dataset.index.name = "id"
    return combined_dataset


def replay(log_file: str, datasets: Dict[str, pd.DataFrame]):
    """
    Replay a log file against the provided datasets.

    Each line of the log is a JSON event with {"dataset", "action"}, where
    action is a serialized HarmonizationRule. Rules are grouped by dataset and
    applied in log order via a per-dataset RuleSet.
    """
    events: Dict[str, List[dict]] = {}
    with open(log_file, "r") as f:
        for line in f:
            event = json.loads(line.strip())
            events.setdefault(event["dataset"], []).append(event)

    logger = rlog.configure_logger(3, "replay_" + log_file)

    results = {}
    for dataset_name, dataset_events in events.items():
        rules = RuleSet()
        for event in dataset_events:
            rules.add_rule(HarmonizationRule.from_serialization(event["action"]))
        results[dataset_name] = harmonize_dataset(
            datasets[dataset_name],
            rules,
            dataset_name,
            logger,
        )
    return results
