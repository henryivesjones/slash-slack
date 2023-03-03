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

    def __init__(
        self,
        command: str,
        func: Callable,
        flags: List[Tuple[str, FlagType, int]],
        args_type: List[Tuple[str, BaseArgType, int]],
        request_arg: Optional[Tuple[str, int]],
        help: Optional[str] = None,
        summary: Optional[str] = None,
    ):
        self.command = command
        self.func = func
        self.flags = flags
        self.args_type = args_type
        self.request_arg = request_arg
        self.help = help
        self.summary = summary

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
                l += self.args_type[i][1].parse(split_args[i:])
                break
            l.append(self.args_type[i][1].parse(value))

        if None in l:
            return None
        return l

    async def execute(
        self,
        args: List[str],
        flags: Set[str],
        global_flags: Set[str],
        slash_slack_request: SlashSlackRequest,
    ):
        """
        Executes this command given already parsed args, flags, and global_flags.
        """
        f_args: List[Any] = [None for _ in range(self.func.__code__.co_argcount)]
        if self.request_arg is not None:
            _, i = self.request_arg
            f_args[i] = slash_slack_request

        for i, value in enumerate(args):
            if isinstance(self.args_type[i][1], UnknownLengthListType):
                f_args[self.args_type[i][2]] = args[i:]
                break
            f_args[self.args_type[i][2]] = value
        for name, _, i in self.flags:
            f_args[i] = name in flags

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
        lines = []
        lines.append(
            f"`{slash_slack_request.command}` `{self.command}` help.\n"
            f" To view this message run `{slash_slack_request.command} {self.command} --help`"
        )
        lines.append("")
        if self.summary is not None:
            lines[-1] += f"\n*{self.summary}*"
        if self.help is not None:
            lines[-1] += f"\n> {self.help}"

        command_descriptors = []
        command_descriptors.append(f"`{slash_slack_request.command}` `{self.command}`")
        for arg_name, arg_type, _ in self.args_type:
            command_descriptors.append(f" `{arg_type.global_help_repr(arg_name)}`")
        for flag_name, flag_type, _ in self.flags:
            command_descriptors.append(f"`{flag_type.global_help_repr(flag_name)}`")
        lines[-1] += "\n" + " ".join(command_descriptors)
        lines.append("Parameters:")

        arg_descriptors = []
        for name, arg, index in self.args_type:
            arg_descriptors.append(
                f"{f'> {arg.help}{_NL}' if arg.help else ''}> `{name}`   `{arg.help_repr()}`"
            )
        lines += arg_descriptors

        if len(self.flags) > 0:
            flag_descriptors = []
            for name, flag, index in self.flags:
                flag_descriptors.append(
                    f"> `--{name}` {f'{flag.help}' if flag.help else ''}"
                )
            lines.append(f"Flags:{_NL}{_NL.join(flag_descriptors)}")

        return _make_block_message(lines, visible_in_channel=visible_in_channel)
