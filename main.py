from typing import List

from slash_slack import (
    Enum,
    Flag,
    Float,
    SlashSlack,
    SlashSlackRequest,
    String,
    UnknownLengthList,
)

slash = SlashSlack(dev=True)
app = slash.get_fastapi()


@slash.command("test")
def test_fn(text: str = String(minimum_length=10), upper: bool = Flag(), lower=Flag()):
    if upper:
        return text.upper()
    if lower:
        return text.lower()

    return text


@slash.command("math")
def math_fn(
    x: float = Float(), m: str = Enum(values={"*", "+", "-", "/"}), y: float = Float()
):
    if m == "*":
        return x * y
    if m == "+":
        return x + y
    if m == "-":
        return x - y
    if m == "/":
        return x / y


@slash.command("u")
def unknown(
    slash_slack_request: SlashSlackRequest,
    t: str,
    l: List[str] = UnknownLengthList(arg_type=String()),
):
    return "_+_".join(str(s) for s in l) + " " + t + " " + slash_slack_request.user_name
