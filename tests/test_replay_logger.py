import json
import logging

import pandas as pd

from harmonization_framework.harmonization_rule import HarmonizationRule
from harmonization_framework.harmonize import harmonize_dataset
from harmonization_framework.primitives import MissingCode, Scale
from harmonization_framework.replay_log import replay_logger as rlog
from harmonization_framework.rule_registry import RuleSet
from harmonization_framework.utils.transformations import replay


def test_configure_logger_clears_handlers(tmp_path):
    log1 = tmp_path / "log1.jsonl"
    log2 = tmp_path / "log2.jsonl"

    logger1 = rlog.configure_logger(3, str(log1))
    assert len(logger1.handlers) == 1

    logger2 = rlog.configure_logger(3, str(log2))
    assert logger2 is logger1
    assert len(logger2.handlers) == 1

    # Ensure the active handler points to the most recent log file
    handler = logger2.handlers[0]
    assert isinstance(handler, logging.FileHandler)
    assert handler.baseFilename == str(log2)


def _read_log_events(log_path):
    with open(log_path) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_missing_code_hits_are_logged_per_row(tmp_path):
    df = pd.DataFrame({"reading_lb": [150.0, 160.0, -999.0, 175.5]})
    rules = RuleSet()
    rules.add_rule(
        HarmonizationRule(
            sources=["reading_lb"],
            target="reading_kg",
            transformation=[MissingCode({-999: "not_measured"}), Scale(0.45359237)],
        )
    )

    log_path = tmp_path / "replay.log"
    logger = rlog.configure_logger(3, str(log_path))
    out = harmonize_dataset(df, rules, "messy", logger)
    for handler in logger.handlers:
        handler.flush()

    # The code was nulled, so the scaled output is missing for that row.
    assert pd.isna(out["reading_kg"].iloc[2])

    events = _read_log_events(log_path)
    rule_events = [e for e in events if e.get("event") == "rule"]
    hit_events = [e for e in events if e.get("event") == "missing_code"]

    assert len(rule_events) == 1
    assert len(hit_events) == 1
    hit = hit_events[0]
    assert hit["dataset"] == "messy"
    assert hit["target"] == "reading_kg"
    assert hit["source"] == "reading_lb"
    assert hit["row"] == 2
    assert hit["value"] == -999.0
    assert hit["label"] == "not_measured"


def test_replay_skips_missing_code_events(tmp_path, monkeypatch):
    df = pd.DataFrame({"reading_lb": [150.0, -999.0]})
    rules = RuleSet()
    rules.add_rule(
        HarmonizationRule(
            sources=["reading_lb"],
            target="reading_kg",
            transformation=[MissingCode({-999: "not_measured"}), Scale(0.45359237)],
        )
    )

    # replay() prefixes the log filename with "replay_", so run from a scratch
    # cwd with a relative name to keep that derived path valid.
    monkeypatch.chdir(tmp_path)
    logger = rlog.configure_logger(3, "replay.log")
    expected = harmonize_dataset(df, rules, "messy", logger)
    for handler in logger.handlers:
        handler.flush()

    # The log contains a missing_code line; replay must skip it (not try to
    # rebuild a rule from it) and still reproduce the rule result.
    results = replay("replay.log", {"messy": df})
    replayed = results["messy"]

    assert replayed["reading_kg"].iloc[0] == expected["reading_kg"].iloc[0]
    assert pd.isna(replayed["reading_kg"].iloc[1])
