import json
import logging
from typing import Iterable, List

from .harmonization_rule import HarmonizationRule

logger = logging.getLogger(__name__)


class RuleSet:
    """
    Flat, target-keyed collection of harmonization rules.

    Rules are stored as a list, but at most one rule per target is allowed.
    Adding a rule for an existing target replaces it and emits a warning.
    """

    def __init__(self):
        self._rules: List[HarmonizationRule] = []

    def add_rule(self, rule: HarmonizationRule) -> None:
        """
        Add a rule, or replace the existing rule for the same target.
        """
        for i, existing in enumerate(self._rules):
            if existing.target == rule.target:
                logger.warning("Rule already exists for target %s; replacing.", rule.target)
                self._rules[i] = rule
                return
        self._rules.append(rule)

    def find(self, target: str) -> HarmonizationRule:
        """
        Return the rule producing the given target, or raise KeyError.
        """
        for rule in self._rules:
            if rule.target == target:
                return rule
        raise KeyError(target)

    def for_targets(self, targets: Iterable[str]) -> List[HarmonizationRule]:
        """
        Return rules whose target appears in `targets`, preserving insertion order.
        """
        wanted = set(targets)
        return [rule for rule in self._rules if rule.target in wanted]

    def all_rules(self) -> List[HarmonizationRule]:
        return list(self._rules)

    def all_targets(self) -> List[str]:
        return [rule.target for rule in self._rules]

    def __len__(self) -> int:
        return len(self._rules)

    def __iter__(self):
        return iter(self._rules)

    def clean(self) -> None:
        self._rules = []

    def save(self, output: str = "rules.json") -> None:
        """
        Serialize rules to a JSON file as a flat array.
        """
        payload = [rule.serialize() for rule in self._rules]
        with open(output, "w") as out:
            json.dump(payload, out, indent=2)

    def load(self, rule_file: str, clean: bool = False) -> None:
        """
        Load rules from a JSON file, optionally clearing existing rules first.

        Accepts both the new flat-array schema and the legacy nested
        {source: {target: rule}} schema for migration convenience.
        """
        if clean:
            self.clean()

        with open(rule_file, "r") as rf:
            data = json.load(rf)

        for rule_payload in _iter_rule_payloads(data):
            self.add_rule(HarmonizationRule.from_serialization(rule_payload))


def _iter_rule_payloads(data):
    """
    Yield rule payloads from either the flat-array schema or the legacy
    nested {source: {target: rule}} schema.
    """
    if isinstance(data, list):
        yield from data
        return
    if isinstance(data, dict):
        for _source, targets in data.items():
            if not isinstance(targets, dict):
                continue
            for _target, rule_payload in targets.items():
                yield rule_payload
        return
    raise ValueError(f"Unrecognized rules file format: expected list or dict, got {type(data).__name__}")
