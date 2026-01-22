import re
import unicodedata

from .base import PrimitiveOperation, support_iterable
from enum import Enum

class Normalization(Enum):
    STRIP = "strip" # strip white space
    LOWER = "lower" # convert to all lower case
    UPPER = "upper" # convert to all upper case
    ACCENT = "remove_accents"
    PUNCTUATION = "remove_punctuation"
    SPECIAL = "remove_special_characters"

class NormalizeText(PrimitiveOperation):
    """
    Perform a text normalization operation.
    """
    def __init__(self, normalization: Normalization):
        self.normalization = normalization

    def __str__(self):
        text = f"Apply {self.normalization} normalization"
        return text

    def to_dict(self):
        output = {
            "operation": "normalize_text",
            "normalization": self.normalization.value,
        }
        return output

    @support_iterable
    def transform(self, value: str) -> str:
        match self.normalization:
            case Normalization.STRIP:
                return value.strip()
            case Normalization.LOWER:
                return value.lower()
            case Normalization.UPPER:
                return value.upper()
            case Normalization.ACCENT:
                return self.remove_accents(value)
            case Normalization.PUNCTUATION:
                return self.remove_punctuation(value)
            case Normalization.SPECIAL:
                return self.remove_special_characters(value)
            case _:
                return value

    def remove_accents(self, value: str) -> str:
        """
        Remove accents and diacritics using NFKC normalization.
        """
        normalized = unicodedata.normalize("NFKC", value)
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def remove_punctuation(self, value: str) -> str:
        """
        Remove all characters other than letter, digit, underscore,
        space, tab, and newline
        """
        return re.sub(r"[^\w\s]", "", value)

    def remove_special_characters(self, value: str) -> str:
        """
        Remove all characters other than letters, digits, and white space.
        """
        return re.sub(r"[^\da-zA-Z\s]", "", value)

    @classmethod
    def from_serialization(cls, serialization):
        normalization = Normalization(serialization["normalization"])
        return NormalizeText(normalization)
