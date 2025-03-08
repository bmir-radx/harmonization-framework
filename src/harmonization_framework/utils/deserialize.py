from typing import Dict, List, Callable, Tuple
from ..primitives import Bin, Cast, ConvertUnits, DoNothing, EnumToEnum, Threshold, Truncate
from ..primitives.vocabulary import PrimitiveVocabulary

def _deserialize_mapping(text: str) -> Dict[int, int]:
    pairs = [pair for pair in text.split(".")]
    mapping = {}
    for pair in pairs:
        key, value = map(int, pair.split(":"))
        mapping[int(key)] = int(value)
    return mapping

def _deserialize_bins(text: str) -> Dict[int, Tuple[int]]:
    """
    Example: bins=0:0-20.1:21-40
    """
    bin_strings = text.split(".")
    bins = []
    for string in bin_strings:
        label, interval = string.split(":")
        lower, upper = interval.split("-")
        bins.append((int(label), (int(lower), int(upper))))
    bins.sort(key = lambda x: x[1][1]) # sort by lower bound of interval
    return bins

def _deserialize_kwargs(params: List[str]) -> Dict[str, str]:
    """
    Parameters are serialized as follows:
        max=100,min=0,mapping={}
    They will be processed into the correct types elsewhere.
    """
    kwargs = {}
    for text in params:
        p = text.split("=")
        if len(p) < 2: # no params
            continue
        key, val = p # requires 2 values
        kwargs[key] = val
    return kwargs

def _deserialize_operation(text: str) -> Callable:
    """
    Process operation serialization string to callback function.
    Example 1: casting and thresholding
        castStrToInt|max=100,min=0 -> castStrToInt(upper_bound=100, lower_bound=0)
    """
    key, param_text = text.split("|")
    params = _deserialize_kwargs(param_text.split(","))
    match key:
        case PrimitiveVocabulary.CAST.value:
            return Cast(
                source=params["source"],
                target=params["target"],
            )
        case PrimitiveVocabulary.THRESHOLD.value:
            return Threshold(
                lower=int(params["lower"]),
                upper=int(params["upper"]),
            )
        case PrimitiveVocabulary.ENUM.value:
            return EnumToEnum(mapping=_deserialize_mapping(params["map"]))
        case PrimitiveVocabulary.BIN.value:
            return Bin(bins=_deserialize_bins(params["bins"]))
        case PrimitiveVocabulary.TRUNCATE.value:
            return Truncate(length=int(params["length"]))
        case PrimitiveVocabulary.UNITS.value:
            return ConvertUnits(source=params["source"], target=params["target"])
        case PrimitiveVocabulary.NOTHING.value:
            return DoNothing()
        case _:
            return DoNothing()

def deserialize(transformation: str) -> List[Callable]:
    """
    Serialization: 
        primitiveName|parameter1,parameter2,...,parameterN;primitive2Name...
    """
    operations_text = transformation.split(";")
    operations = [_deserialize_operation(text) for text in operations_text]
    return operations
