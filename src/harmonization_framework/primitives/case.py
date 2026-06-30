from typing import Any, Dict, List

from .base import PrimitiveOperation, isnull


def _normalize_operands(branch):
    """A branch produces one value from one or more 'operands'. Each operand computes
    a value from one source via its own op-chain; a branch with multiple operands
    combines them with `combine` (a Reduction name string, e.g. 'sum').

    Accepts two authoring forms, normalized to the canonical operand list:
      - {"source": "x", "operations": [...]}                  -> one operand
      - {"operands": [{"source": "a", "operations": [...]}, ...], "combine": "sum"}
    """
    if "operands" in branch:
        operands = [{"source": o["source"], "operations": list(o.get("operations", []))}
                    for o in branch["operands"]]
        combine = branch.get("combine")
    else:
        operands = [{"source": branch["source"], "operations": list(branch.get("operations", []))}]
        combine = None
    return operands, combine


def _apply_operands(operands, combine, by_name):
    """Compute each operand's value, then combine. Returns the branch value."""
    from .reduce import Reduce, Reduction

    vals = []
    for o in operands:
        current = by_name[o["source"]]
        for op in o["operations"]:
            current = op(current)
        vals.append(current)
    if combine is None:
        return vals[0] if len(vals) == 1 else vals
    return Reduce(Reduction(combine)).transform(vals)


class Case(PrimitiveOperation):
    """
    Choose one of several branches by switching on a selector source, then compute
    that branch's value from one or more source operands.

    A multi-source combinator. The rule's `sources` list names every column this
    primitive may read; `transform` receives the values in that same order and
    `Case` zips them back to names internally, so branches address sources by NAME,
    never by fragile positional index.

    A branch is either a single source with an op-chain, or several `operands` (each
    a source + op-chain) combined with a reduction. The first branch whose `when`
    contains the selector value wins; null/unmatched selector -> `default`.

    Single-source branch (RADx-UP weight: unit flag selects pounds-as-is or kg->lbs):

        Case(
            sources=["weight_units", "weight_lbs", "weight_kgs"],
            selector="weight_units",
            branches=[
                {"when": ["2"], "source": "weight_lbs", "operations": [DoNothing()]},
                {"when": ["1"], "source": "weight_kgs",
                 "operations": [ConvertUnits(Unit.KILOGRAM, Unit.POUNDS), Round(0)]},
            ],
        )

    Multi-operand branch (RADx-UP height: feet+inches OR meters+cm, summed in inches):

        Case(
            sources=["height_units", "ft", "in", "m", "cm"],
            selector="height_units",
            branches=[
                {"when": ["1"], "combine": "sum", "operands": [
                    {"source": "ft", "operations": [ConvertUnits(Unit.FEET, Unit.INCH)]},
                    {"source": "in", "operations": [DoNothing()]},
                ]},
                {"when": ["2"], "combine": "sum", "operands": [
                    {"source": "m",  "operations": [ConvertUnits(Unit.METER, Unit.INCH)]},
                    {"source": "cm", "operations": [ConvertUnits(Unit.CENTIMETER, Unit.INCH)]},
                ]},
            ],
        )
    """

    def __init__(self, sources, selector, branches, default=None):
        self.sources = list(sources)
        self.selector = selector
        self.branches = []
        for b in branches:
            operands, combine = _normalize_operands(b)
            self.branches.append({"when": [str(w) for w in b["when"]],
                                  "operands": operands, "combine": combine})
        self.default = default
        if self.selector not in self.sources:
            raise ValueError(f"Case selector {self.selector!r} not in sources {self.sources}")
        for b in self.branches:
            for o in b["operands"]:
                if o["source"] not in self.sources:
                    raise ValueError(f"Case branch source {o['source']!r} not in sources {self.sources}")

    def __str__(self):
        lines = [f"Switch on {self.selector}:"]
        for b in self.branches:
            srcs = "+".join(o["source"] for o in b["operands"])
            comb = f" ({b['combine']})" if b["combine"] else ""
            lines.append(f"  when {b['when']} -> {srcs}{comb}")
        lines.append(f"  else -> {self.default!r}")
        return "\n".join(lines)

    def _by_name(self, values):
        if not isinstance(values, (list, tuple)):
            raise TypeError(f"Case expects a list of source values, got {type(values).__name__}")
        if len(values) != len(self.sources):
            raise ValueError(f"Case received {len(values)} values but has {len(self.sources)} sources")
        return dict(zip(self.sources, values))

    def transform(self, values: Any) -> Any:
        by_name = self._by_name(values)
        sel = by_name[self.selector]
        if isnull(sel):
            return self.default
        sel_key = str(sel)
        for b in self.branches:
            if sel_key in b["when"]:
                return _apply_operands(b["operands"], b["combine"], by_name)
        return self.default

    def to_dict(self):
        return {
            "operation": "case",
            "sources": list(self.sources),
            "selector": self.selector,
            "branches": [
                {
                    "when": list(b["when"]),
                    "combine": b["combine"],
                    "operands": [
                        {"source": o["source"], "operations": [op.to_dict() for op in o["operations"]]}
                        for o in b["operands"]
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
            operands = [
                {"source": o["source"],
                 "operations": [deserialize_operation(op) for op in o.get("operations", [])]}
                for o in b["operands"]
            ]
            branches.append({"when": b["when"], "combine": b.get("combine"), "operands": operands})
        return cls(
            sources=serialization["sources"],
            selector=serialization["selector"],
            branches=branches,
            default=serialization.get("default"),
        )
