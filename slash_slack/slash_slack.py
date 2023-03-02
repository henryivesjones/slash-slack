import inspect
import logging
import re
from typing import Callable, Dict, List, Literal, Optional, Set, Tuple, Union
from urllib.parse import parse_qsl

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, ValidationError

from slash_slack.arg_types import BaseArgType, Float, Int, String, UnknownLengthList
from slash_slack.blocks import _make_block_message
from slash_slack.flag import Flag
from slash_slack.signature_verifier import SignatureVerifier
from slash_slack.slash_slack_command import SlashSlackCommand
from slash_slack.slash_slack_request import SlackSlashRequest


class SlashSlack:
    global_flags = {"visible"}
    url_path: str
    app: FastAPI
    commands: Dict[str, SlashSlackCommand]
    dev: bool
    signature_verifier: SignatureVerifier

    def __init__(
        self,
        dev: bool = False,
        signing_secret: Optional[str] = None,
        url_path="/slash_slack",
    ):
        self.url_path = url_path
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
                        status_code=403, detail="Unable to verify request signature."
                    )
            request_form_data = dict(parse_qsl(request_body.decode()))
            if request_form_data.get("ssl_check") == 1:
                return Response(status_code=200)
            try:
                slack_slash_request = SlackSlashRequest(**request_form_data)
            except ValidationError:
                raise HTTPException(
                    status_code=422, detail="Validation of request body failed."
                )

            command, args, flags = _parse_command_text(slack_slash_request.text.strip())

            if command not in self.commands:
                return _make_block_message(
                    _command_not_found(slack_slash_request), visible_in_channel=False
                )
            parsed_args = self.commands[command].parse_args(args)
            if parsed_args is None:
                return _make_block_message("invalid args")

            global_flags = flags.intersection(self.global_flags)
            background_tasks.add_task(
                self.commands[command].execute,
                parsed_args,
                flags.difference(self.global_flags),
                global_flags,
                slack_slash_request,
            )

            return Response(status_code=200)

    def get_fastapi(self):
        return self.app

    def command(
        self,
        command: str,
    ):
        """
        Decorator for defining a command.
        """

        def decorator_command(func: Callable):
            if command in self.commands:
                raise Exception(f"The command {command} has already been registered.")
            params, flags = _parse_func_params(func)
            self.commands[command] = SlashSlackCommand(
                command=command, func=func, flags=flags, args_type=params
            )
            return func

        return decorator_command


_FLAG_REGEXP = re.compile(r"""(?:^|(?<= ))--(?P<flag>\S+?)(?:$| )""")


def _parse_command_text(text: str) -> Tuple[str, str, Set[str]]:
    flags = set(_FLAG_REGEXP.findall(text))
    text = _FLAG_REGEXP.sub("", text).strip()
    split_text = text.split(" ")
    command = split_text[0]
    args = " ".join(split_text[1:])
    return command, args, flags


def _parse_func_params(func: Callable):
    sig = inspect.signature(func)
    params: List[Tuple[str, BaseArgType, int]] = []
    flags: List[Tuple[str, Flag, int]] = []
    for index, param in enumerate(sig.parameters.values()):
        name = param.name
        annotation = None if param.annotation is param.empty else param.annotation
        default = None if param.default is param.empty else param.default
        if isinstance(default, Flag):
            flags.append((name, default, index))
            continue

        if default is not None:
            if isinstance(default, BaseArgType):
                params.append((name, default, index))
                continue
            if isinstance(default, str):
                params.append((name, String(), index))
                continue
            if isinstance(default, float):
                params.append((name, Float(), index))
                continue
            if isinstance(default, int):
                params.append((name, Int(), index))
                continue
            raise Exception(
                f"Function {func.__name__} has an invalid default value of ({default})"
            )

        if annotation is not None:
            if annotation is str:
                params.append((name, String(), index))
                continue
            if annotation is float:
                params.append((name, Float(), index))
                continue
            if annotation is int:
                params.append((name, Int(), index))
                continue
            raise Exception(
                f"Function {func.__name__} has an invalid annotation of ({annotation}) for {name}"
            )
        params.append((name, String(), index))
    return params, flags


def _command_not_found(slack_slash_request: SlackSlashRequest) -> str:
    return f"""
The command `{slack_slash_request.command} {slack_slash_request.text}` did not match any commands I know. Please try again.
To view help run the command `{slack_slash_request.command} --help`
    """.strip()
