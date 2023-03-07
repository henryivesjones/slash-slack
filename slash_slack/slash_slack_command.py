import logging
from typing import Any, Callable, List, Optional, Set, Tuple

import aiohttp

from slash_slack.arg_types import (
    BaseArgType,
    FlagType,
    StringType,
    UnknownLengthListType,
)
from slash_slack.blocks import _make_block_message
from slash_slack.slash_slack_request import SlashSlackRequest

_NL = "\n"


class SlashSlackCommand:
    """
    Abstraction for running command functions. Input parsing, command execution, and command help live here.
    """

    command: str
    help: Optional[str] = None
    summary: Optional[str] = None
    func: Callable
    flags: List[Tuple[str, FlagType, int]]
    args_type: List[Tuple[str, BaseArgType, int]]
    request_arg: Optional[Tuple[str, int]] = None
    is_async: bool

    def __init__(
        self,
        command: str,
        func: Callable,
        flags: List[Tuple[str, FlagType, int]],
        args_type: List[Tuple[str, BaseArgType, int]],
        request_arg: Optional[Tuple[str, int]],
        help: Optional[str] = None,
        summary: Optional[str] = None,
        is_async: bool = False,
    ):
        self.command = command
        self.func = func
        self.flags = flags
        self.args_type = args_type
        self.request_arg = request_arg
        self.help = help
        self.summary = summary
        self.is_async = is_async

    def parse_args(self, args: str):
        """
        Parse input text for this command utilizing this commands flag and arg schema.
        """
        if len(self.args_type) == 1 and isinstance(self.args_type[0][1], StringType):
            p = self.args_type[0][1].parse(args)
            if p is None:
                return None
            return [p]

        split_args = [arg for arg in args.split(" ") if arg != ""]

        l = []
        for i, value in enumerate(split_args):
            if i >= len(self.args_type):
                return None
            if isinstance(self.args_type[i][1], UnknownLengthListType):
                l.append(self.args_type[i][1].parse(split_args[i:]))
                break
            l.append(self.args_type[i][1].parse(value))

        if len(self.args_type) != len(l):
            return None
        if None in l:
            return None
        return l

    def _hydrate_func_args(
        self,
        args: List[Any],
        flags: Set[str],
        slash_slack_request: SlashSlackRequest,
    ):
        f_args: List[Any] = [None for _ in range(self.func.__code__.co_argcount)]
        if self.request_arg is not None:
            _, i = self.request_arg
            f_args[i] = slash_slack_request

        for i, value in enumerate(args):
            f_args[self.args_type[i][2]] = value
        for name, _, i in self.flags:
            f_args[i] = name in flags
        return f_args

    async def execute(
        self,
        args: List[Any],
        flags: Set[str],
        global_flags: Set[str],
        slash_slack_request: SlashSlackRequest,
    ):
        """
        Executes this command given already parsed args, flags, and global_flags.
        """
        f_args = self._hydrate_func_args(args, flags, slash_slack_request)
        if self.is_async:
            response = await self.func(*f_args)
        else:
            response = self.func(*f_args)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                slash_slack_request.response_url,
                json=_make_block_message(
                    response, visible_in_channel="visible" in global_flags
                ),
            ) as resp:
                if resp.status != 200:
                    logging.error(
                        f"Received an error when sending request to callback ({resp.status}): {await resp.text()}"
                    )

    def _help(
        self, slash_slack_request: SlashSlackRequest, visible_in_channel: bool = False
    ):
        """
        Generates the help text response for this command. Returns Slack Block Kit.
        """
        _HELP = f"""
`{slash_slack_request.command}` `{self.command}` help.
To view this message run `{slash_slack_request.command} {self.command} --help`
{f"*{self.summary}*" if self.summary else ""}
{f"> {self.help}" if self.help else ""}
`{slash_slack_request.command}` {self._generate_command_signature()}
Parameters:
{self._generate_parameter_help()}
{"Flags:" if len(self.flags) > 0 else ""}
{self._generate_flag_help()}
        """.strip()

        return _make_block_message(
            _HELP,
            visible_in_channel=visible_in_channel,
        )

    def _generate_command_signature(self) -> str:
        return f"""
`{self.command}` {" ".join(f"`{t.global_help_repr(name)}`" for name, t, _ in self.args_type + self.flags)}
        """.strip()

    def _generate_parameter_help(self) -> str:
        parameter_help_contents = []
        for name, arg, index in self.args_type:
            parameter_help_contents.append(
                f"""
{f"> {arg.help}" if arg.help else ""}
> `{name}`   `{arg.help_repr()}`
            """.strip()
            )
        return (_NL * 2).join(parameter_help_contents)

    def _generate_flag_help(self) -> str:
        flag_help_contents = []
        for name, flag, index in self.flags:
            flag_help_contents.append(
                f"""
> `--{name}` {flag.help if flag.help else ''}
            """.strip()
            )

        return _NL.join(flag_help_contents)
