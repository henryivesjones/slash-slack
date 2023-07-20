from typing import List

from slash_slack import Enum, Flag, Float, SlashSlack, String, UnknownLengthList
from slash_slack.blocks import _make_block_message

slash = SlashSlack(
    dev=True,
    description="A python framework for slack slash bots.",
    acknowledge_response="Working on your request...",
)
app = slash.get_fast_api()


@slash.command(
    "echo",
    summary="Echo",
    help="Returns the provided text (made upper or lower case)",
)
def test_fn(
    content: str = String(help="The content which will be echoed"),
    upper: bool = Flag(help="Converts the input text to all UPPERCASE"),
    lower: bool = Flag(help="Converts the input text to all lowercase"),
):
    if upper:
        return content.upper()
    if lower:
        return content.lower()

    return content


@slash.command(
    "math",
    summary="Performs basic arithmetic between two numbers",
    acknowledge_response="Responding to a math request...",
)
def math_fn(
    x: float = Float(help="A number."),
    symbol: str = Enum(
        values={"*", "+", "-", "/"}, help="The arithmetic operation to use."
    ),
    y: float = Float(help="A number."),
):
    if symbol == "*":
        return x * y
    if symbol == "+":
        return x + y
    if symbol == "-":
        return x - y
    if symbol == "/":
        return x / y


@slash.command(
    "avg",
    summary="Return the average of the given numbers",
    help="EX: `avg 90 100 110.9`",
)
def unknown(
    nums: List[float] = UnknownLengthList(
        arg_type=Float(), help="The numbers to average."
    ),
):
    return f"The avg of the given numbers is {sum(nums) / len(nums)}"
