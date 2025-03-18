from .base import PrimitiveOperation, support_iterable
from datetime import datetime

class ConvertDate(PrimitiveOperation):
    """
    Primitive for converting between date time formats.
    """
    def __init__(self, source_format: str, target_format: str):
        self.source_format = source_format
        self.target_format = target_format

    def __str__(self):
        text = f"Convert date time format from {self.source_format} to {self.target_format}"
        return text

    def _serialize(self):
        output = {
            "Operation": f"{self.__class__.__name__}",
            "Source Format": f"{self.source_format}",
            "Target Format": f"{self.target_format}",
        }
        return output

    @support_iterable
    def transform(self, value: str) -> str:
        dt = datetime.strptime(value, self.input_format)
        return dt.strftime(self.target_format)

    @classmethod
    def from_serialization(cls, serialization):
        source_format = serialization["Source Format"]
        target_format = serialization["Target Format"]
        return ConvertDate(source_format, target_format)
