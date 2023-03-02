from abc import ABC, abstractmethod
from typing import Any, Optional, Set


class BaseArgType(ABC):
    help: Optional[str] = None

    @abstractmethod
    def parse(self, value) -> Any:
        pass


class FloatType(BaseArgType):
    help: Optional[str] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    def __init__(
        self,
        help: Optional[str] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
    ):
        self.help = help
        self.minimum = minimum
        self.maximum = maximum

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


class IntType(BaseArgType):
    help: Optional[str] = None
    minimum: Optional[int] = None
    maximum: Optional[int] = None

    def __init__(
        self,
        help: Optional[str] = None,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
    ):
        self.help = help
        self.minimum = minimum
        self.maximum = maximum

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


class StringType(BaseArgType):
    help: Optional[str] = None
    minimum_length: Optional[int] = None
    maximum_length: Optional[int] = None

    # regex: Optional[str] = None

    def __init__(
        self,
        help: Optional[str] = None,
        minimum_length: Optional[int] = None,
        maximum_length: Optional[int] = None,
    ):
        self.help = help
        self.minimum_length = minimum_length
        self.maximum_length = maximum_length

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


class EnumType(BaseArgType):
    help: Optional[str] = None
    values: Set[str]

    def __init__(
        self,
        values: Set[str],
        help: Optional[str] = None,
    ):
        self.help = help
        self.values = values

    def parse(self, value):
        value = str(value)
        if value not in self.values:
            return None
        return value


class UnknownLengthListType(BaseArgType):
    help: Optional[str] = None
    arg_type: BaseArgType

    def __init__(self, arg_type: BaseArgType, help: Optional[str] = None):
        self.arg_type = arg_type
        self.help = help

    def parse(self, value):
        l = []
        for arg in value:
            l.append(self.arg_type.parse(arg))
        if None in l:
            return None
        return l


class FlagType:
    help: Optional[str] = None

    def __init__(self, help: Optional[str] = None):
        self.help = help
