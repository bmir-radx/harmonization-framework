import json
import pandas as pd
from ..rule import HarmonizationRule
from ..rule_store import RuleStore
from ..replay_log import replay_logger as rlog
from typing import Dict, List, Tuple

def harmonize_dataset(
        dataset: pd.DataFrame,
        harmonization_pairs: List[Tuple[str]],
        rules: RuleStore,
        dataset_name: str,
        logger = None,
) -> pd.DataFrame:
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

def combine_datasets(datasets: List[pd.DataFrame]):
    combined_dataset = pd.concat(datasets, axis=0, ignore_index=True)
    combined_dataset.index.name = "id"
    return combined_dataset

def replay(log_file: str, datasets: Dict[str, pd.DataFrame]):
    # assume replay events on separate datasets can be interleaved arbitrarily.
    # require ordered replay only for operations on the same dataset
    events = {}
    replay_rules = RuleStore()
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
        pairs = [(event["action"]["Source"], event["action"]["Target"]) for event in events[dataset_name]]
        result = harmonize_dataset(
            datasets[dataset_name],
            pairs,
            replay_rules,
            dataset_name,
            logger,
        )
        results[dataset_name] = result
    return results