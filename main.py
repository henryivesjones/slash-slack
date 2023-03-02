from typing import Set

from slash_slack import SlashSlack
from slash_slack.arg_types import Enum, Float, String
from slash_slack.flag import Flag

slash = SlashSlack(dev=True)
app = slash.get_fastapi()


@slash.command("test")
def test_fn(text=String(minimum_length=10), upper=Flag(), lower=Flag()):
    if upper:
        return text.upper()
    if lower:
        return text.lower()

    return text


# @slash.command(
#     "test", flags=[Flag(value="upper"), Flag(value="lower")], args_type=String()
# )
# def test_fn(args: str, flags: Set[str]):
#     if "upper" in flags:
#         return args.upper()
#     if "lower" in flags:
#         return args.lower()

#     return args


@slash.command("math")
def math_fn(x=Float(), m=Enum(values={"*", "+", "-", "/"}), y=Float()):
    if m == "*":
        return x * y
    if m == "+":
        return x + y
    if m == "-":
        return x - y
    if m == "/":
        return x / y
