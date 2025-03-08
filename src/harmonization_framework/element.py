from enum import Enum
from typing import Dict, Optional


class DEType(Enum):
    TEXT = ("text", str)
    INTEGER = ("integer", int)
    DECIMAL = ("decimal", float)
    ONEHOT = ("one-hot", int)
    ENUMERATION = ("enumeration", int)

    def __init__(self, name, primitive):
        self._name = name
        self._type = primitive


class DataElement:
    """
    This should fully specify a data element.
    Placeholder for now. Should probably be something from
    the CEDAR artifact library.
    """
    label: str
    element_type: DEType
    enumerations: Optional[Dict[int, str]] = None

    def __hash__(self):
        return hash(self.label)
