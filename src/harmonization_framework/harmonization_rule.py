from typing import Any, List
from .element import DataElement
from .primitives.base import PrimitiveOperation
from .primitives import PrimitiveVocabulary, Bin, Cast, ConvertDate, ConvertUnits, DoNothing, EnumToEnum, NormalizeText, Offset, Reduce, Round, Scale, Substitute, Threshold, Truncate

import json

# Backwards-compatible alias

class HarmonizationRule:
    def __init__(self, source: DataElement, target: DataElement, transformation: List[PrimitiveOperation] = None):
        self.source = source
        self.target = target
        self._transform = transformation
        self.serialization = json.dumps(self.serialize())

    def serialize(self):
        output = {
            "source": f"{self.source}",
            "target": f"{self.target}",
            "operations": [
                primitive.to_dict() for primitive in (self._transform or [])
            ],
        }
        return output

    def __str__(self):
        text = []
        for i, transform in enumerate(self._transform):
            text.append(f"Harmonization Operation {i+1}:")
            text.append(str(transform))
        return "\n".join(text)
    
    def transform(self, value: Any) -> Any:
        """
        Apply transformation primitives in serial.
        """
        if self._transform is None:
            return value
        for transform in self._transform:
            value = transform(value)
        return value

    @classmethod
    def from_serialization(cls, serialization):
        source = serialization["source"]
        target = serialization["target"]
        operations = serialization["operations"]
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
                case PrimitiveVocabulary.NORMALIZE_TEXT.value:
                    primitive = NormalizeText.from_serialization(operation)
                case PrimitiveVocabulary.OFFSET.value:
                    primitive = Offset.from_serialization(operation)
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
        return HarmonizationRule(source, target, transformation)


# Backwards-compatible alias
Rule = HarmonizationRule
