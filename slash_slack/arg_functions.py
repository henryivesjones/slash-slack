from typing import Any, Optional, Set

import slash_slack.arg_types as arg_types


def Float(
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    help: Optional[str] = None,
) -> Any:
    """
    Input arg schema float type.
    """
    return arg_types.FloatType(minimum=minimum, maximum=maximum, help=help)


def Int(
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
    help: Optional[str] = None,
) -> Any:
    """
    Input arg schema integer type.
    """
    return arg_types.IntType(minimum=minimum, maximum=maximum, help=help)


def String(
    minimum_length: Optional[int] = None,
    maximum_length: Optional[int] = None,
    help: Optional[str] = None,
) -> Any:
    """
    Input arg schema string type.

    If the only arg is of String type, then the string will contain the full body of the command.
    """
    return arg_types.StringType(
        minimum_length=minimum_length, maximum_length=maximum_length, help=help
    )


def Enum(values: Set[str], help: Optional[str] = None) -> Any:
    """
    Input arg enum type. Will validate that the input value is one of the given values.
    """
    return arg_types.EnumType(values=values, help=help)


def UnknownLengthList(
    arg_type: arg_types.BaseArgType, help: Optional[str] = None
) -> Any:
    """
    Input arg type. Will grow to encompass N # of space delimited args.

    Must be the last argument in the arg list.

    EX (l = UnknownLengthList(arg_type=String())):

    command a b c d

    l = ['a', 'b', 'c', 'd']
    """
    return arg_types.UnknownLengthListType(arg_type=arg_type, help=help)


def Flag(help: Optional[str] = None) -> Any:
    """
    Input flag arg. The value of which will be true or false depending on if `--<arg_name>` is found in the command body.
    """
    return arg_types.FlagType(help=help)
