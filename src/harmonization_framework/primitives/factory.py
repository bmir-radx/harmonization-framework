"""
Deserialize a primitive operation from its JSON-friendly dict form.

Lives in its own module so that primitives that hold nested operations
(e.g. MapEach) can deserialize their children without importing
HarmonizationRule, and without forcing a circular import through
primitives/__init__.py.
"""

from typing import Any, Dict

from .base import PrimitiveOperation
from .bin_primitive import Bin
from .cast import Cast
from .dates import ConvertDate
from .donothing import DoNothing
from .enum2enum import EnumToEnum
from .extract_regex import ExtractRegex
from .format_number import FormatNumber
from .map_each import MapEach
from .missing_code import MissingCode
from .normalize import NormalizeText
from .normalize_boolean import NormalizeBoolean
from .offset import Offset
from .parse_array import ParseArray
from .reduce import Reduce
from .round_decimal import Round
from .scale import Scale
from .substitute import Substitute
from .threshold import Threshold
from .truncate import Truncate
from .units import ConvertUnits
from .validate_pattern import ValidatePattern
from .vocabulary import PrimitiveVocabulary


def deserialize_operation(operation: Dict[str, Any]) -> PrimitiveOperation:
    """
    Build a PrimitiveOperation from its serialized dict.

    Raises ValueError for unknown operation names.
    """
    name = operation["operation"]
    match name:
        case PrimitiveVocabulary.BIN.value:
            return Bin.from_serialization(operation)
        case PrimitiveVocabulary.CAST.value:
            return Cast.from_serialization(operation)
        case PrimitiveVocabulary.CONVERT_DATE.value:
            return ConvertDate.from_serialization(operation)
        case PrimitiveVocabulary.CONVERT_UNITS.value:
            return ConvertUnits.from_serialization(operation)
        case PrimitiveVocabulary.DO_NOTHING.value:
            return DoNothing.from_serialization(operation)
        case PrimitiveVocabulary.ENUM_TO_ENUM.value:
            return EnumToEnum.from_serialization(operation)
        case PrimitiveVocabulary.EXTRACT_REGEX.value:
            return ExtractRegex.from_serialization(operation)
        case PrimitiveVocabulary.FORMAT_NUMBER.value:
            return FormatNumber.from_serialization(operation)
        case PrimitiveVocabulary.MAP_EACH.value:
            return MapEach.from_serialization(operation)
        case PrimitiveVocabulary.MISSING_CODE.value:
            return MissingCode.from_serialization(operation)
        case PrimitiveVocabulary.NORMALIZE_BOOLEAN.value:
            return NormalizeBoolean.from_serialization(operation)
        case PrimitiveVocabulary.NORMALIZE_TEXT.value:
            return NormalizeText.from_serialization(operation)
        case PrimitiveVocabulary.OFFSET.value:
            return Offset.from_serialization(operation)
        case PrimitiveVocabulary.PARSE_ARRAY.value:
            return ParseArray.from_serialization(operation)
        case PrimitiveVocabulary.REDUCE.value:
            return Reduce.from_serialization(operation)
        case PrimitiveVocabulary.ROUND.value:
            return Round.from_serialization(operation)
        case PrimitiveVocabulary.SCALE.value:
            return Scale.from_serialization(operation)
        case PrimitiveVocabulary.SUBSTITUTE.value:
            return Substitute.from_serialization(operation)
        case PrimitiveVocabulary.THRESHOLD.value:
            return Threshold.from_serialization(operation)
        case PrimitiveVocabulary.TRUNCATE.value:
            return Truncate.from_serialization(operation)
        case PrimitiveVocabulary.VALIDATE_PATTERN.value:
            return ValidatePattern.from_serialization(operation)
        case _:
            raise ValueError(f"Unknown operation: {name}")
