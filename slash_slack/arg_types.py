from abc import ABC, abstractmethod
from typing import Any, Optional, Set

from pydantic import BaseModel


class BaseArgType(ABC):
    @abstractmethod
    def parse(self, value) -> Any:
        pass


class Float(BaseArgType, BaseModel):
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    def parse(self, value):
        try:
            parsed_value = float(value)
        except ValueError:
            return None
        if (self.maximum is not None and parsed_value > self.maximum) or (
            self.minimum is not None and parsed_value < self.minimum
        ):
            return None
        return parsed_value


class Int(BaseArgType, BaseModel):
    minimum: Optional[int] = None
    maximum: Optional[int] = None

    def parse(self, value):
        try:
            parsed_value = int(value)
        except ValueError:
            return None
        if (self.maximum is not None and parsed_value > self.maximum) or (
            self.minimum is not None and parsed_value < self.minimum
        ):
            return None
        return parsed_value


class String(BaseArgType, BaseModel):
    minimum_length: Optional[int] = None
    maximum_length: Optional[int] = None
    # regex: Optional[str] = None

    def parse(self, value):
        try:
            parsed_value = str(value)
        except ValueError:
            return None
        if (
            self.maximum_length is not None and len(parsed_value) > self.maximum_length
        ) or (
            self.minimum_length is not None and len(parsed_value) < self.minimum_length
        ):
            return None
        return parsed_value


class Enum(BaseArgType, BaseModel):
    values: Set[str]

    def parse(self, value):
        value = str(value)
        if value not in self.values:
            return None
        return value


class UnknownLengthList:
    def __init__(self, type: BaseArgType):
        self.type = type

    def parse(self, value):
        l = []
        for arg in value:
            l.append(self.type.parse(arg))
        if None in l:
            return None
        return l
