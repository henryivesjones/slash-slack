import inspect
import logging
import re
from typing import Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qsl

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from pydantic import ValidationError

from slash_slack.arg_types import (
    BaseArgType,
    FlagType,
    FloatType,
    IntType,
    StringType,
    UnknownLengthListType,
)
from slash_slack.blocks import _make_block_message
from slash_slack.signature_verifier import SignatureVerifier
from slash_slack.slash_slack_command import SlashSlackCommand
from slash_slack.slash_slack_request import SlashSlackRequest


class SlashSlack:
    """
    A framework for building python response servers for Slack slash bot.
    """

    global_flags = {"visible", "help"}
    url_path: str
    description: str
    app: FastAPI
    commands: Dict[str, SlashSlackCommand]
    dev: bool
    signature_verifier: SignatureVerifier

    def __init__(
        self,
        dev: bool = False,
        signing_secret: Optional[str] = None,
        url_path="/slash_slack",
        description="",
    ):
        """
        Create a Slash Slack app.
        To disable signature verification set dev=True
        """
        self.url_path = url_path
        self.description = description
        self.app = FastAPI(title="SlashSlack", openapi_url=None)
        self.commands = {}
        self.dev = dev

        if self.dev:
            logging.info("Running in DEV MODE. Signature verification is disabled.")
        else:
            if signing_secret is None:
                raise Exception(
                    "No signing secret provided. Either disable signature verification by running in dev mode, or provide the signing secret."
                )
            self.signature_verifier = SignatureVerifier(signing_secret)

        @self.app.post(self.url_path)
        async def slash_slack(request: Request, background_tasks: BackgroundTasks):
            request_body = await request.body()
            if not self.dev:
                if self.signature_verifier is None:
                    raise HTTPException(
                        status_code=500, detail="Internal Service Error"
                    )
                if not self.signature_verifier.is_valid_request(
                    request_body,
                    {key: value for key, value in request.headers.items()},
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Unable to verify request signature.",
                    )
            try:
                request_form_data = dict(parse_qsl(request_body.decode()))
                if request_form_data.get("ssl_check") == 1:
                    return Response(status_code=200)
                try:
                    slash_slack_request = SlashSlackRequest(**request_form_data)
                except ValidationError as e:
                    logging.error(e)
                    raise HTTPException(
                        status_code=422, detail="Validation of request body failed."
                    )

                command, args, flags = _parse_command_text(
                    slash_slack_request.text.strip()
                )
                if command.lower() == "help" or (command == "" and "help" in flags):
                    return self._global_help(
                        slash_slack_request, visible_in_channel="visible" in flags
                    )

                if command not in self.commands:
                    return _make_block_message(
                        _command_not_found(slash_slack_request),
                        visible_in_channel=False,
                    )
                global_flags = flags.intersection(self.global_flags)
                if "help" in global_flags:
                    return self.commands[command]._help(
                        slash_slack_request=slash_slack_request,
                        visible_in_channel="visible" in global_flags,
                    )
                parsed_args = self.commands[command].parse_args(args)
                if parsed_args is None:
                    return _make_block_message(
                        _invalid_args(
                            slash_slack_request=slash_slack_request, command=command
                        ),
                        visible_in_channel=False,
                    )

                background_tasks.add_task(
                    self.commands[command].execute,
                    parsed_args,
                    flags.difference(self.global_flags),
                    global_flags,
                    slash_slack_request,
                )

                return Response(status_code=200)
            except Exception as e:
                logging.error(e)
                return _make_block_message(
                    _unable_to_respond(), visible_in_channel=False
                )

    def get_fast_api(self):
        """
        Get the underlying fast_api app which should be exported to be run by wsgi worker (uvicorn).
        """
        return self.app

    def command(
        self, command: str, help: Optional[str] = None, summary: Optional[str] = None
    ):
        """
        Decorator for defining a command within a SlashSlack app.

        command (str): The first word used for routing between commands within a SlashSlack app.
        help    (str): The help content for this command.
        summary (str): The summary/title for this command.

        /slash-slack command
        """

        def decorator_command(func: Callable):
            if command in self.commands:
                raise Exception(f"The command {command} has already been registered.")
            params, flags, request_arg = _parse_func_params(func)
            self.commands[command] = SlashSlackCommand(
                command=command,
                func=func,
                flags=flags,
                args_type=params,
                request_arg=request_arg,
                help=help,
                summary=summary,
            )
            return func

        return decorator_command

    def _global_help(
        self, slash_slack_request: SlashSlackRequest, visible_in_channel: bool = False
    ) -> dict:
        """
        Generates the global help for this SlashSlack bot.
        """
        lines = []
        lines.append(
            f"`{slash_slack_request.command}` help.\nTo view this message run `{slash_slack_request.command} help`"
        )
        lines.append(
            f"> By default bot replies are only visible to the requestor. "
            "To make the reply visible to everyone in the channel use the `--visible` flag anywhere in your command."
        )
        lines.append(
            f"> To view help for a specific command use the `--help` flag\n> EX: `{slash_slack_request.command} <command> --help`"
        )
        if self.description != "":
            lines.append(self.description)
        lines.append("*Available Commands:*")
        for command_text, command in self.commands.items():
            command_descriptors = []
            if command.summary is not None:
                command_descriptors.append(f" {command.summary}\n>")
            command_descriptors.append(
                f" `{slash_slack_request.command}` `{command_text}`"
            )
            for arg_name, arg_type, _ in command.args_type:
                command_descriptors.append(f" `{arg_type.global_help_repr(arg_name)}`")
            for flag_name, flag_type, _ in command.flags:
                command_descriptors.append(f"`{flag_type.global_help_repr(flag_name)}`")

            lines.append(f"> {' '.join(command_descriptors)}\n")
        return _make_block_message(lines, visible_in_channel=visible_in_channel)


_FLAG_REGEXP = re.compile(r"""(?:^|(?<= ))--(?P<flag>\S+?)(?:$| )""")


def _parse_command_text(text: str) -> Tuple[str, str, Set[str]]:
    flags = set(_FLAG_REGEXP.findall(text))
    text = _FLAG_REGEXP.sub("", text).strip()
    split_text = text.split(" ")
    command = split_text[0]
    args = " ".join(split_text[1:])
    return command, args, flags


def _parse_func_params(func: Callable):
    has_encountered_unknown_length_list = False
    sig = inspect.signature(func)
    params: List[Tuple[str, BaseArgType, int]] = []
    flags: List[Tuple[str, FlagType, int]] = []
    request_arg: Optional[Tuple[str, int]] = None
    for index, param in enumerate(sig.parameters.values()):
        name = param.name
        annotation = None if param.annotation is param.empty else param.annotation
        default = None if param.default is param.empty else param.default

        if annotation is SlashSlackRequest:
            if request_arg is not None:
                raise Exception(
                    f"Function {func.__name__} has a two SlashSlackRequest parameters. This is not allowed."
                )
            request_arg = (name, index)
            continue

        if isinstance(default, FlagType):
            flags.append((name, default, index))
            continue

        if has_encountered_unknown_length_list:
            raise Exception(
                f"Function {func.__name__} has a ({type(default)}) param after an UnknownListType param. This is not allowed."
            )
        if default is not None:
            if isinstance(default, BaseArgType):
                params.append((name, default, index))
                if isinstance(default, UnknownLengthListType):
                    has_encountered_unknown_length_list = True
                continue
            if isinstance(default, str):
                params.append((name, StringType(), index))
                continue
            if isinstance(default, float):
                params.append((name, FloatType(), index))
                continue
            if isinstance(default, int):
                params.append((name, IntType(), index))
                continue
            raise Exception(
                f"Function {func.__name__} has an invalid default value of ({type(default)})"
            )

        if annotation is not None:
            if annotation is str:
                params.append((name, StringType(), index))
                continue
            if annotation is float:
                params.append((name, FloatType(), index))
                continue
            if annotation is int:
                params.append((name, IntType(), index))
                continue

            raise Exception(
                f"Function {func.__name__} has an invalid annotation of ({annotation}) for {name}"
            )
        params.append((name, StringType(), index))
    return params, flags, request_arg


def _command_not_found(slack_slash_request: SlashSlackRequest) -> str:
    return f"""
The command `{slack_slash_request.command} {slack_slash_request.text}` did not match any commands I know. Please try again.
To view help run the command `{slack_slash_request.command} help`
    """.strip()


def _unable_to_respond():
    return f"""
I was unable to respond to your request due to an internal error. Please contact the bot administrator.
    """.strip()


def _invalid_args(slash_slack_request: SlashSlackRequest, command: str) -> str:
    return f"""
The command run was unable to be parsed by the `{command}` input schema:
```
{slash_slack_request.command} {slash_slack_request.text}
```
To view help for this command enter the command:
```
{slash_slack_request.command} {command} --help
```
    """.strip()
