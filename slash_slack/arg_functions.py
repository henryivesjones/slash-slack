from typing import Any, Optional, Set

import slash_slack.arg_types as arg_types


def Float(
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    help: Optional[str] = None,
) -> Any:
    return arg_types.FloatType(minimum=minimum, maximum=maximum, help=help)


def Int(
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
    help: Optional[str] = None,
) -> Any:
    return arg_types.IntType(minimum=minimum, maximum=maximum, help=help)


def String(
    minimum_length: Optional[int] = None,
    maximum_length: Optional[int] = None,
    help: Optional[str] = None,
) -> Any:
    return arg_types.StringType(
        minimum_length=minimum_length, maximum_length=maximum_length, help=help
    )


def Enum(values: Set[str], help: Optional[str] = None) -> Any:
    return arg_types.EnumType(values=values, help=help)


def UnknownLengthList(
    arg_type: arg_types.BaseArgType, help: Optional[str] = None
) -> Any:
    return arg_types.UnknownLengthListType(arg_type=arg_type, help=help)


def Flag(help: Optional[str] = None) -> Any:
    return arg_types.FlagType(help=help)
