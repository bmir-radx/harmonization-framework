from typing import Any, Dict, List, Optional
from .primitives.base import PrimitiveOperation
from .primitives.factory import deserialize_operation

import json


class HarmonizationRule:
    def __init__(
        self,
        sources: List[str],
        target: str,
        transformation: Optional[List[PrimitiveOperation]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.sources = list(sources) if sources is not None else []
        self.target = target
        self._transform = transformation
        self.metadata = metadata
        self.serialization = json.dumps(self.serialize())

    def serialize(self):
        output = {
            "sources": list(self.sources),
            "target": f"{self.target}",
            "operations": [
                primitive.to_dict() for primitive in (self._transform or [])
            ],
        }
        if self.metadata:
            output["metadata"] = self.metadata
        return output

    def __str__(self):
        text = []
        for i, transform in enumerate(self._transform or []):
            text.append(f"Harmonization Operation {i+1}:")
            text.append(str(transform))
        return "\n".join(text)

    def transform(self, values: Any) -> Any:
        """
        Apply transformation primitives in serial.

        Accepts either a scalar (single-source rule called directly) or a list
        of values (one per entry in `sources`). Single-source rules unwrap the
        singleton before passing it to the operations chain so existing
        primitives continue to receive a scalar.
        """
        if isinstance(values, list):
            value = values[0] if len(self.sources) == 1 else values
        else:
            value = values
        if self._transform is None:
            return value
        for transform in self._transform:
            value = transform(value)
        return value

    @classmethod
    def from_serialization(cls, serialization):
        # Accept both new "sources": [...] schema and legacy "source": "..." key.
        if "sources" in serialization:
            sources = list(serialization["sources"])
        else:
            sources = [serialization["source"]]
        target = serialization["target"]
        operations = serialization["operations"]
        metadata = serialization.get("metadata")
        transformation = [deserialize_operation(op) for op in operations]
        return HarmonizationRule(sources, target, transformation, metadata=metadata)
