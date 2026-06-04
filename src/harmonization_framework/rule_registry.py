import json
import logging
from typing import Iterable, List

import yaml

from .harmonization_rule import HarmonizationRule

logger = logging.getLogger(__name__)


def _is_yaml(path: str) -> bool:
    """Return True if `path` names a YAML file (.yaml / .yml)."""
    return path.lower().endswith((".yaml", ".yml"))


def _blank_line_between_rules(dumped: str) -> str:
    """
    Insert a blank line before each top-level rule in dumped YAML (except the
    first), so a multi-rule file is easy to scan. Top-level rules are the list
    items that begin at column 0 with "- "; continuation lines are indented and
    left untouched. Purely cosmetic — the parsed content is unchanged.
    """
    lines = dumped.split("\n")
    out = []
    for i, line in enumerate(lines):
        if i > 0 and line.startswith("- "):
            out.append("")
        out.append(line)
    return "\n".join(out)


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
        Serialize rules to a flat array file.

        The format is chosen by the file extension: `.yaml`/`.yml` writes YAML,
        anything else writes JSON. Both encode the same structure (a list of
        rule dicts), so the choice is purely about which on-disk form you want.

        YAML is emitted with `default_flow_style=None`: scalar-only collections
        (a `sources` list, a `{from, to}` mapping entry) render inline, while the
        surrounding structure stays in block form. A blank line is inserted
        between top-level rules so the file is easy to scan. This keeps the rule
        skeleton readable while compacting the leaf items.
        """
        payload = [rule.serialize() for rule in self._rules]
        with open(output, "w") as out:
            if _is_yaml(output):
                dumped = yaml.safe_dump(payload, sort_keys=False, default_flow_style=None)
                out.write(_blank_line_between_rules(dumped))
            else:
                json.dump(payload, out, indent=2)

    def load(self, rule_file: str, clean: bool = False) -> None:
        """
        Load rules from a JSON or YAML file, optionally clearing existing rules
        first. The format is chosen by the file extension (`.yaml`/`.yml` for
        YAML, otherwise JSON).

        Accepts both the new flat-array schema and the legacy nested
        {source: {target: rule}} schema for migration convenience.
        """
        if clean:
            self.clean()

        with open(rule_file, "r") as rf:
            if _is_yaml(rule_file):
                data = yaml.safe_load(rf)
            else:
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
