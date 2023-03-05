# slash-slack
A python framework for building slack slash bots. Get input parsing and validation, command routing, async responses, auto-generated help dialog, response visibility, and response message formatting all for free.

`slash-slack` is a web server with a single endpoint (by default `/slash_slack`). In order to connect the Slack Slash command with the `slash-slack` server, the `slash-slack` server must be publicly accessible and the slash command must be configured with Slack. View [Slack slash command documentation](https://api.slack.com/interactivity/slash-commands) here.

```python
# EX: /slash-slack math 10 * 10
# Response: 100.0
import os

from slash_slack import Flag, Float, SlashSlack, String

slash = SlashSlack(signing_secret=os.environ['SLACK_SIGNING_SECRET'])
app = slash.get_fast_api()


@slash.command("math")
def math_fn(
    x: float = Float(),
    symbol: str = Enum(values={"*", "+", "-", "/"}),
    y: float = Float(),
):
    if symbol == "*":
        return x * y
    if symbol == "+":
        return x + y
    if symbol == "-":
        return x - y
    if symbol == "/":
        return x / y
```

View a tutorial of creating a Slack slash command bot with `slash-slack` [here](https://github.com/henryivesjones/slash-slack/blob/main/how_to/how_to_create_slash_slack_bot_python.md).

# Why use `slash-slack`?
Building a slack slash bot can seem very straightforward at first, however there are some complexities that make it difficult. `slash-slack` handles all of the complexities for you letting you focus on the bot response handlers.

## Webhook signature verification
`slash-slack` will verify that incoming requests were made by slack by validating the request signature. To disable signature verification use the `dev=True` option when creating the `SlashSlack` object.

## Command Response Timeout/Async responses
Slack requires that the slash bot webhook be responded to within 3 seconds.

Often times the action being taken by the bot will depend on external services which might not respond within 3 seconds.

`slash-slack` sends an immediate `200` response to the webhook request, and runs the command function in the background. When the command function finishes, the response is sent back to slack using the `response_url` from the request.

## Input Arg/Flag parsing
`slash-slack` takes care of parsing command input into pre-defined args and flags which let you focus on writing the command function, and not wrangling the content into the format that you need.

## Auto-generated help
`slash-slack` provides help dialog auto-generated from your commands, args, and flags. Additional details can be embedded directly into the command decorator and arg/flag initializers.

To request global help:
```
/slash-slack help
```

To request command specific help:
```
/slash-slack command --help
```

## Response visibility
Slack slash command responses can be made visible only to the requestor, or to the entire channel. `slash-slack` adds the ability for any command to be made visible with the `--visible` flag.

## Response formatting
Slack expects responses to be in the Slack Block Kit format. `slash-slack` will automatically convert your string responses into slack `mrkdown` blocks.

# Deployment
`slash-slack` is a WSGI app based on the FastAPI framework. Deploy using `uvicorn`.
You must expose the underlying app from the `SlashSlack` bot.
```python
# main.py
from slash_slack import SlashSlack

slash = SlashSlack()
app = slash.get_fast_api()

```
```
uvicorn main:app --port 9002 --reload
```

# Development/Webhook mocking.
A mock slack webhook client `mock-slack` is bundled with `slash-slack`. This client can be used to mock webhooks sent by slack.

To enter the mock slack client simply run `mock-slack`.

> `SlashSlack` must be `dev=True` to disable signature verification.

`mock-slack` will prompt you for input. Responses from the `slash-slack` server will be served in your browser in the Slack Block Kit Builder.
```
$ mock-slack
MSG: echo test
```


# Command Inputs
The inputs and parsing for each command is determined by the parameters to the function. `SlashSlack` parses the function parameters and generates an input schema.

When a request is made to a given command, `SlashSlack` attempts to parse the input text into the command input schema.
## Flags
Flags are boolean options that can be added to commands anywhere within the request. During the input parsing, flags are parsed and removed, and then args are parsed.

There is no difference in doing `/slash-slack command arg --flag` and `/slash-slack command --flag arg`.
### Global Flags
There are 2 global flags: `--visible` and `--help`.

The `--visible` flag will make the response visible in the channel that the request was made. By default, responses are only visible to the user which made the request.

The `--help` flag will indicate that the `SlashSlack` app should return the relevant help message. Whether that is app level `/slash-slack --help`, or command level `/slash-slack command --help`.
## Args
All non-flag arguments to the command function make up the input schema for the command function. This means that the # of words in the command request must match up with the # of non-flag arguments. (With two exceptions: String, UnknownLengthList).

### String
When the only non-flag parameter for the function is a `String()` then the entire argument body (with flags removed) will be passed into that parameter.
```python
# EX: /slash-slack echo hello --upper world
# Response: HELLO WORLD
@slash.command("echo")
def echo(s: str, upper: bool = Flag()):
    return s
```
### Unknown Length List
To collect an arbitrary # of args from the user use the `UnknownLengthList` arg type. This arg type will be passed a list of all of the values passed to it parsed into the given type.

Because this consumes args till the end of the arg list, this must be the last non-flag param for the command function.
```python
# EX: /slash-slack avg 10, 20, 30
# Response: 20.0
@slash.command("avg")
def avg(numbers = UnknownLengthList(arg_type=Float())):
    return sum(numbers) / len(numbers)
```

### SlashSlackRequest
If you want to have access to the complete request as sent from the slack servers. Add a param with the type annotation of `SlashSlackRequest` to the command function.

```python
# EX: /slash-slack echo hello world
# Response: hello world This request was made by John Doe
@slash.command("echo")
def echo(content: str, slash_slack_request: SlashSlackRequest):
    return f"{content} This request was made by {slash_slack_request.user_name}"

```

# Example Application with Usage
```python
from typing import List

from slash_slack import Enum, Flag, Float, SlashSlack, String, UnknownLengthList

slash = SlashSlack(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    description="A python framework for slack slash bots.",
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

```
## Global Help
```
/slash-slack help
```
![Global Help Example](https://github.com/henryivesjones/slash-slack/blob/main/static/global_help.png?raw=true)

## Command Help
```
/slash-slack math --help
```
![Math Command Help Example](https://github.com/henryivesjones/slash-slack/blob/main/static/math_command_help.png?raw=true)

## Command invocation
```
/slash-slack math 10 * 20
```
![Math Command Usage Example](https://github.com/henryivesjones/slash-slack/blob/main/static/math_command_usage.png?raw=true)

## Command parsing error
```
/slash-slack math a * 100
```
![Math Command Parse Error Example](https://github.com/henryivesjones/slash-slack/blob/main/static/math_command_parse_error.png?raw=true)
