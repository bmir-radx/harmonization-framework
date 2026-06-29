from typing import Any

from .base import PrimitiveOperation, isnull
from .case import _normalize_terms, _apply_terms


class Coalesce(PrimitiveOperation):
    """
    Pick the first branch whose (primary) source is non-null, then compute that
    branch's value from one or more source terms.

    A multi-source combinator, like Case but with the branch chosen by
    populated-ness rather than an explicit selector. Use Case when the data carries
    an authoritative unit/type flag; use Coalesce when "whichever field was filled
    in" is the right rule.

    A branch is a single source with an op-chain, or several `terms` (each a
    source + op-chain) combined with a reduction (same shape as Case branches). A
    branch is considered populated when its first term's source is non-null. Branch
    order defines precedence; all sources null -> `default`.

        Coalesce(
            sources=["weight_lbs", "weight_kgs"],
            branches=[
                {"source": "weight_lbs", "operations": []},
                {"source": "weight_kgs",
                 "operations": [ConvertUnits(Unit.KILOGRAM, Unit.POUNDS), Round(0)]},
            ],
        )
    """

    def __init__(self, sources, branches, default=None):
        self.sources = list(sources)
        self.branches = []
        for b in branches:
            terms, combine = _normalize_terms(b)
            self.branches.append({"terms": terms, "combine": combine})
        self.default = default
        for b in self.branches:
            for t in b["terms"]:
                if t["source"] not in self.sources:
                    raise ValueError(f"Coalesce branch source {t['source']!r} not in sources {self.sources}")

    def __str__(self):
        lines = ["Coalesce (first non-null):"]
        for b in self.branches:
            srcs = "+".join(t["source"] for t in b["terms"])
            comb = f" ({b['combine']})" if b["combine"] else ""
            lines.append(f"  {srcs}{comb}")
        lines.append(f"  else -> {self.default!r}")
        return "\n".join(lines)

    def _by_name(self, values):
        if not isinstance(values, (list, tuple)):
            raise TypeError(f"Coalesce expects a list of source values, got {type(values).__name__}")
        if len(values) != len(self.sources):
            raise ValueError(f"Coalesce received {len(values)} values but has {len(self.sources)} sources")
        return dict(zip(self.sources, values))

    def transform(self, values: Any) -> Any:
        by_name = self._by_name(values)
        for b in self.branches:
            primary = by_name[b["terms"][0]["source"]]
            if not isnull(primary):
                return _apply_terms(b["terms"], b["combine"], by_name)
        return self.default

    def to_dict(self):
        return {
            "operation": "coalesce",
            "sources": list(self.sources),
            "branches": [
                {
                    "combine": b["combine"],
                    "terms": [
                        {"source": t["source"], "operations": [op.to_dict() for op in t["operations"]]}
                        for t in b["terms"]
                    ],
                }
                for b in self.branches
            ],
            "default": self.default,
        }

    @classmethod
    def from_serialization(cls, serialization):
        from .factory import deserialize_operation

        branches = []
        for b in serialization["branches"]:
            terms = [
                {"source": t["source"],
                 "operations": [deserialize_operation(op) for op in t.get("operations", [])]}
                for t in b["terms"]
            ]
            branches.append({"combine": b.get("combine"), "terms": terms})
        return cls(
            sources=serialization["sources"],
            branches=branches,
            default=serialization.get("default"),
        )
