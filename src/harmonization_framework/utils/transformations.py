import json
import pandas as pd
from ..harmonization_rule import HarmonizationRule
from ..rule_registry import RuleRegistry
from ..replay_log import replay_logger as rlog
from ..harmonize import harmonize_dataset
from typing import Dict, List, Tuple

def combine_datasets(datasets: List[pd.DataFrame]):
    combined_dataset = pd.concat(datasets, axis=0, ignore_index=True)
    combined_dataset.index.name = "id"
    return combined_dataset

def replay(log_file: str, datasets: Dict[str, pd.DataFrame]):
    # assume replay events on separate datasets can be interleaved arbitrarily.
    # require ordered replay only for operations on the same dataset
    events = {}
    replay_rules = RuleRegistry()
    with open(log_file, "r") as f:
        for line in f:
            event = json.loads(line.strip())
            dataset_name = event["dataset"]
            if dataset_name not in events:
                events[dataset_name] = []
            events[dataset_name].append(event)
            rule = event["action"]
            replay_rules.add_rule(HarmonizationRule.from_serialization(rule))

    # logger for the replay
    logger = rlog.configure_logger(3, "replay_" + log_file)

    results = {}
    for dataset_name in events:
        pairs = [(event["action"]["source"], event["action"]["target"]) for event in events[dataset_name]]
        result = harmonize_dataset(
            datasets[dataset_name],
            pairs,
            replay_rules,
            dataset_name,
            logger,
        )
        results[dataset_name] = result
    return results
