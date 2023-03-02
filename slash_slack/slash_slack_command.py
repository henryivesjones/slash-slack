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


class SlashSlackCommand:
    command: str
    help: Optional[str] = None
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
    ):
        self.command = command
        self.func = func
        self.flags = flags
        self.args_type = args_type
        self.request_arg = request_arg
        self.help = help

    def parse_args(self, args: str):
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
        slack_slash_request: SlashSlackRequest,
    ):
        f_args: List[Any] = [None for _ in range(self.func.__code__.co_argcount)]
        if self.request_arg is not None:
            _, i = self.request_arg
            f_args[i] = slack_slash_request

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
                slack_slash_request.response_url,
                json=_make_block_message(
                    response, visible_in_channel="visible" in global_flags
                ),
            ) as resp:
                if resp.status != 200:
                    logging.error(
                        f"Received an error when sending request to callback ({resp.status}): {await resp.text()}"
                    )
