from .base import PrimitiveOperation, support_iterable
from typing import Union
from enum import Enum

import pint

UREG = pint.UnitRegistry()

class Unit(Enum):
    # temperature
    FAHRENHEIT = "degF"
    CELCIUS = "degC"
    # weight/mass
    KILOGRAM = "kg"
    POUNDS = "lb"
    # length/height
    FEET = "feet"
    INCH = "inch"
    METER = "m"
    CENTIMETER = "cm"
    KILOMETER = "km"
    MILE = "mile"
    # time
    HOUR = "hour"
    DAY = "day"
    MONTH = "month"
    YEAR = "year"

class CustomUnit:
    def __init__(self, value):
        self.value = value

class ConvertUnits(PrimitiveOperation):
    def __init__(self, source: Union[Unit, str], target: Union[Unit, str]):
        if isinstance(source, str):
            source = CustomUnit(source)
        if isinstance(target, str):
            target = CustomUnit(target)
        self.source = source
        self.target = target

    def __str__(self):
        text = f"Perform conversion from {self.source.value} to {self.target.value}"
        return text

    def to_dict(self):
        output = {
            "operation": "convert_units",
            "source_unit": self.source.value,
            "target_unit": self.target.value,
        }
        return output

    @support_iterable
    def transform(self, value: Union[int, float]) -> Union[int, float]:
        quantity = UREG.Quantity(value, self.source.value)
        return quantity.to(self.target.value).magnitude

    @classmethod
    def from_serialization(cls, serialization):
        source = CustomUnit(serialization["source_unit"])
        target = CustomUnit(serialization["target_unit"])
        return ConvertUnits(source, target)
