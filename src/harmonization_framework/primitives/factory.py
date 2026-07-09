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
from .case import Case
from .cast import Cast
from .coalesce import Coalesce
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


# Registry of operation name -> primitive class. This is the single source of
# truth for which operations exist: deserialization dispatches through it, and
# the CLI's --list-operations derives its listing (with help text from each
# class docstring) from it.
OPERATION_CLASSES: Dict[str, type] = {
    PrimitiveVocabulary.BIN.value: Bin,
    PrimitiveVocabulary.CASE.value: Case,
    PrimitiveVocabulary.CAST.value: Cast,
    PrimitiveVocabulary.COALESCE.value: Coalesce,
    PrimitiveVocabulary.CONVERT_DATE.value: ConvertDate,
    PrimitiveVocabulary.CONVERT_UNITS.value: ConvertUnits,
    PrimitiveVocabulary.DO_NOTHING.value: DoNothing,
    PrimitiveVocabulary.ENUM_TO_ENUM.value: EnumToEnum,
    PrimitiveVocabulary.EXTRACT_REGEX.value: ExtractRegex,
    PrimitiveVocabulary.FORMAT_NUMBER.value: FormatNumber,
    PrimitiveVocabulary.MAP_EACH.value: MapEach,
    PrimitiveVocabulary.MISSING_CODE.value: MissingCode,
    PrimitiveVocabulary.NORMALIZE_BOOLEAN.value: NormalizeBoolean,
    PrimitiveVocabulary.NORMALIZE_TEXT.value: NormalizeText,
    PrimitiveVocabulary.OFFSET.value: Offset,
    PrimitiveVocabulary.PARSE_ARRAY.value: ParseArray,
    PrimitiveVocabulary.REDUCE.value: Reduce,
    PrimitiveVocabulary.ROUND.value: Round,
    PrimitiveVocabulary.SCALE.value: Scale,
    PrimitiveVocabulary.SUBSTITUTE.value: Substitute,
    PrimitiveVocabulary.THRESHOLD.value: Threshold,
    PrimitiveVocabulary.TRUNCATE.value: Truncate,
    PrimitiveVocabulary.VALIDATE_PATTERN.value: ValidatePattern,
}


def deserialize_operation(operation: Dict[str, Any]) -> PrimitiveOperation:
    """
    Build a PrimitiveOperation from its serialized dict.

    Raises ValueError for unknown operation names.
    """
    name = operation["operation"]
    cls = OPERATION_CLASSES.get(name)
    if cls is None:
        raise ValueError(f"Unknown operation: {name}")
    return cls.from_serialization(operation)
