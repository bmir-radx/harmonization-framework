from .base import PrimitiveOperation, support_iterable
from datetime import datetime

class ConvertDate(PrimitiveOperation):
    """
    Convert between date/time string formats using strptime/strftime.

    Examples:
    - source_format="%Y-%m-%d", target_format="%m/%d/%Y"
    - source_format="%Y-%m-%d %H:%M:%S", target_format="%d-%b-%Y %H:%M"
    """
    def __init__(self, source_format: str, target_format: str):
        self.source_format = source_format
        self.target_format = target_format

    def __str__(self):
        text = f"Convert date time format from {self.source_format} to {self.target_format}"
        return text

    def to_dict(self):
        output = {
            "operation": "convert_date",
            "source_format": self.source_format,
            "target_format": self.target_format,
        }
        return output

    @support_iterable
    def transform(self, value: str) -> str:
        try:
            dt = datetime.strptime(value, self.source_format)
        except ValueError as exc:
            message = (
                "Failed to parse date/time value "
                f"{value!r} with source_format={self.source_format!r}"
            )
            raise ValueError(message) from exc
        return dt.strftime(self.target_format)

    @classmethod
    def from_serialization(cls, serialization):
        source_format = serialization["source_format"]
        target_format = serialization["target_format"]
        return ConvertDate(source_format, target_format)
