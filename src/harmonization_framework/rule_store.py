from .rule import HarmonizationRule
from .primitives import DoNothing

import json

class RuleStore:
    def __init__(self):
        self._rules = {}
        self._nothing = HarmonizationRule(None, None, [DoNothing()])

    def query(self, source: str, target: str = None) -> HarmonizationRule:
        # support queries using just the source
        if target is None:
            return self._rules[source]
        if source == target:
            return self._nothing
        return self._rules[source][target]

    def add_rule(self, rule: HarmonizationRule):
        source = rule.source
        target = rule.target
        if source not in self._rules:
            self._rules[source] = {}
        if target in self._rules[source]:
            print(f"Warning: rule already exists for source {rule.source} and target {rule.target}.")
        self._rules[source][target] = rule

    def clean(self):
        self._rules = {}

    def save(self, output: str = "rules.json"):
        rules = {}
        for source in self._rules:
            rules[source] = {target: rule.serialize() for target, rule in self._rules[source].items()}
        with open(output, "w") as out:
            json.dump(rules, out, indent=2)

    def load(self, rule_file: str, clean: bool = False):
        if clean:
            self.clean()

        with open(rule_file, "r") as rf:
            rules = json.load(rf)
        for source, rules_from_source in rules.items():
            for target, rule in rules_from_source.items():
                self.add_rule(HarmonizationRule.from_serialization(rule))
