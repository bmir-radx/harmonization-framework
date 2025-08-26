from typing import Any, List
from .element import DataElement
from .primitives.base import PrimitiveOperation
from .primitives import PrimitiveVocabulary, Bin, Cast, DoNothing, EnumToEnum, Reduce, Round, Threshold, Truncate, ConvertUnits

import json

class HarmonizationRule:
    def __init__(self, source: DataElement, target: DataElement, transformation: List[PrimitiveOperation] = None):
        self.source = source
        self.target = target
        self._transform = transformation
        self.serialization = json.dumps(self.serialize())

    def serialize(self):
        output = {
            "Source": f"{self.source}",
            "Target": f"{self.target}",
            "Operations": [
                primitive._serialize() for primitive in self._transform
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
        source = serialization["Source"]
        target = serialization["Target"]
        operations = serialization["Operations"]
        transformation = []
        for operation in operations:
            match operation["Operation"]:
                case PrimitiveVocabulary.BIN.value:
                    primitive = Bin.from_serialization(operation)
                case PrimitiveVocabulary.CAST.value:
                    primitive = Cast.from_serialization(operation)
                case PrimitiveVocabulary.ENUM.value:
                    primitive = EnumToEnum.from_serialization(operation)
                case PrimitiveVocabulary.ROUND.value:
                    primitive = Round.from_serialization(operation)
                case PrimitiveVocabulary.THRESHOLD.value:
                    primitive = Threshold.from_serialization(operation)
                case PrimitiveVocabulary.TRUNCATE.value:
                    primitive = Truncate.from_serialization(operation)
                case PrimitiveVocabulary.UNITS.value:
                    primitive = ConvertUnits.from_serialization(operation)
                case PrimitiveVocabulary.NOTHING.value:
                    primitive = DoNothing.from_serialization(operation)
            transformation.append(primitive)
        return HarmonizationRule(source, target, transformation)
