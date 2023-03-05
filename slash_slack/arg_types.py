from abc import ABC, abstractmethod
from typing import Any, Optional, Set


class BaseArgType(ABC):
    help: Optional[str] = None

    @abstractmethod
    def parse(self, value) -> Any:
        pass

    @abstractmethod
    def help_repr(self) -> str:
        pass

    @abstractmethod
    def global_help_repr(self, name: str) -> str:
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
        except TypeError:
            return None
        if (self.maximum is not None and parsed_value > self.maximum) or (
            self.minimum is not None and parsed_value < self.minimum
        ):
            return None
        return parsed_value

    def help_repr(self) -> str:
        qualifiers = ""
        if self.minimum is not None and self.maximum is not None:
            qualifiers = f" ({self.maximum} > cal > {self.minimum})"
        elif self.minimum is not None:
            qualifiers = f" (val > {self.minimum})"
        elif self.minimum is not None:
            qualifiers = f" ({self.maximum} > val)"
        return f"float{qualifiers}"

    def global_help_repr(self, name: str) -> str:
        return f"{name}:float"


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
        except TypeError:
            return None
        if (self.maximum is not None and parsed_value > self.maximum) or (
            self.minimum is not None and parsed_value < self.minimum
        ):
            return None
        return parsed_value

    def help_repr(self) -> str:
        qualifiers = ""
        if self.minimum is not None and self.maximum is not None:
            qualifiers = f" ({self.maximum} > val > {self.minimum})"
        elif self.minimum is not None:
            qualifiers = f" (val > {self.minimum})"
        elif self.minimum is not None:
            qualifiers = f" ({self.maximum} > val)"
        return f"int{qualifiers}"

    def global_help_repr(self, name: str) -> str:
        return f"{name}:int"


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
        if value is None:
            return None
        try:
            parsed_value = str(value)
        except ValueError:
            return None
        except TypeError:
            return None
        if (
            self.maximum_length is not None and len(parsed_value) > self.maximum_length
        ) or (
            self.minimum_length is not None and len(parsed_value) < self.minimum_length
        ):
            return None
        return parsed_value

    def help_repr(self) -> str:
        qualifiers = ""
        if self.minimum_length is not None and self.maximum_length is not None:
            qualifiers = f" ({self.maximum_length} > length > {self.minimum_length})"
        elif self.minimum_length is not None:
            qualifiers = f" (length > {self.minimum_length})"
        elif self.minimum_length is not None:
            qualifiers = f" ({self.maximum_length} > length)"
        return f"string{qualifiers}"

    def global_help_repr(self, name: str) -> str:
        return f"{name}:text"


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

    def help_repr(self) -> str:
        return f"enum ({'|'.join(self.values)})"

    def global_help_repr(self, name: str) -> str:
        return f"{name}:{'|'.join(self.values)}"


class UnknownLengthListType(BaseArgType):
    help: Optional[str] = None
    arg_type: BaseArgType

    def __init__(self, arg_type: BaseArgType, help: Optional[str] = None):
        self.arg_type = arg_type
        self.help = help

    def parse(self, value):
        l = []
        if isinstance(value, str):
            value = [a for a in value.split(" ") if a != ""]
        for arg in value:
            l.append(self.arg_type.parse(arg))
        if None in l:
            return None
        return l

    def help_repr(self) -> str:
        return f"{self.arg_type.help_repr()} [...]"

    def global_help_repr(self, name: str) -> str:
        return f"{self.arg_type.global_help_repr(name)} [...]"


class FlagType:
    help: Optional[str] = None

    def __init__(self, help: Optional[str] = None):
        self.help = help

    def global_help_repr(self, name: str) -> str:
        return f"[--{name}]"
