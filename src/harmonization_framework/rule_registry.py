from .harmonization_rule import HarmonizationRule
from .primitives import DoNothing

import json

class RuleRegistry:
    """
    In-memory storage for harmonization rules keyed by source and target.

    Rules are stored as a nested dict: {source: {target: HarmonizationRule}}.
    """
    def __init__(self):
        """
        Initialize an empty rule store with a built-in no-op rule.
        """
        self._rules = {}
        self._nothing = HarmonizationRule(None, None, [DoNothing()])

    def query(self, source: str, target: str = None) -> HarmonizationRule:
        """
        Retrieve a rule by source and optional target.

        If target is None, returns all rules for a given source.
        If source == target, returns a no-op rule.
        """
        # support queries using just the source
        if target is None:
            return self._rules[source]
        if source == target:
            return self._nothing
        return self._rules[source][target]

    def add_rule(self, rule: HarmonizationRule):
        """
        Add or replace a harmonization rule in the store.
        """
        source = rule.source
        target = rule.target
        if source not in self._rules:
            self._rules[source] = {}
        if target in self._rules[source]:
            print(f"Warning: rule already exists for source {rule.source} and target {rule.target}.")
        self._rules[source][target] = rule

    def list_pairs(self):
        """
        Return a list of (source, target) pairs for all stored rules.
        """
        pairs = []
        for source, targets in self._rules.items():
            for target in targets:
                pairs.append((source, target))
        return pairs

    def clean(self):
        """
        Remove all rules from the store.
        """
        self._rules = {}

    def save(self, output: str = "rules.json"):
        """
        Serialize rules to a JSON file.
        """
        rules = {}
        for source in self._rules:
            rules[source] = {target: rule.serialize() for target, rule in self._rules[source].items()}
        with open(output, "w") as out:
            json.dump(rules, out, indent=2)

    def load(self, rule_file: str, clean: bool = False):
        """
        Load rules from a JSON file, optionally clearing existing rules first.
        """
        if clean:
            self.clean()

        with open(rule_file, "r") as rf:
            rules = json.load(rf)
        for source, rules_from_source in rules.items():
            for target, rule in rules_from_source.items():
                self.add_rule(HarmonizationRule.from_serialization(rule))


# Backwards-compatible alias
RuleStore = RuleRegistry
