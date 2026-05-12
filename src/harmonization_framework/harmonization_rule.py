from typing import Any, Dict, List, Optional
from .primitives.base import PrimitiveOperation
from .primitives import PrimitiveVocabulary, Bin, Cast, ConvertDate, ConvertUnits, DoNothing, EnumToEnum, FormatNumber, NormalizeBoolean, NormalizeText, Offset, ParseArray, Reduce, Round, Scale, Substitute, Threshold, Truncate

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
        transformation = []
        for operation in operations:
            match operation["operation"]:
                case PrimitiveVocabulary.BIN.value:
                    primitive = Bin.from_serialization(operation)
                case PrimitiveVocabulary.CAST.value:
                    primitive = Cast.from_serialization(operation)
                case PrimitiveVocabulary.CONVERT_DATE.value:
                    primitive = ConvertDate.from_serialization(operation)
                case PrimitiveVocabulary.CONVERT_UNITS.value:
                    primitive = ConvertUnits.from_serialization(operation)
                case PrimitiveVocabulary.DO_NOTHING.value:
                    primitive = DoNothing.from_serialization(operation)
                case PrimitiveVocabulary.ENUM_TO_ENUM.value:
                    primitive = EnumToEnum.from_serialization(operation)
                case PrimitiveVocabulary.FORMAT_NUMBER.value:
                    primitive = FormatNumber.from_serialization(operation)
                case PrimitiveVocabulary.NORMALIZE_BOOLEAN.value:
                    primitive = NormalizeBoolean.from_serialization(operation)
                case PrimitiveVocabulary.NORMALIZE_TEXT.value:
                    primitive = NormalizeText.from_serialization(operation)
                case PrimitiveVocabulary.OFFSET.value:
                    primitive = Offset.from_serialization(operation)
                case PrimitiveVocabulary.PARSE_ARRAY.value:
                    primitive = ParseArray.from_serialization(operation)
                case PrimitiveVocabulary.REDUCE.value:
                    primitive = Reduce.from_serialization(operation)
                case PrimitiveVocabulary.ROUND.value:
                    primitive = Round.from_serialization(operation)
                case PrimitiveVocabulary.SCALE.value:
                    primitive = Scale.from_serialization(operation)
                case PrimitiveVocabulary.SUBSTITUTE.value:
                    primitive = Substitute.from_serialization(operation)
                case PrimitiveVocabulary.THRESHOLD.value:
                    primitive = Threshold.from_serialization(operation)
                case PrimitiveVocabulary.TRUNCATE.value:
                    primitive = Truncate.from_serialization(operation)
                case _:
                    raise ValueError(f"Unknown operation: {operation['operation']}")
            transformation.append(primitive)
        return HarmonizationRule(sources, target, transformation, metadata=metadata)
