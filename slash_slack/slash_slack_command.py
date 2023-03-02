import logging
from typing import Any, Callable, List, Literal, Set, Tuple, Union

import aiohttp

from slash_slack.arg_types import BaseArgType, String, UnknownLengthList
from slash_slack.blocks import _make_block_message
from slash_slack.flag import Flag
from slash_slack.slash_slack_request import SlackSlashRequest


class SlashSlackCommand:
    command: str
    func: Callable
    flags: List[Tuple[str, Flag, int]]
    args_type: List[Tuple[str, BaseArgType, int]]

    def __init__(
        self,
        command: str,
        func: Callable,
        flags: List[Tuple[str, Flag, int]],
        args_type: List[Tuple[str, BaseArgType, int]],
    ):
        self.command = command
        self.func = func
        self.flags = flags
        self.args_type = args_type

    def parse_args(self, args: str):
        if len(self.args_type) == 1 and isinstance(self.args_type[0][1], String):
            print("should be here")
            p = self.args_type[0][1].parse(args)
            if p is None:
                return None
            return [p]

        split_args = [arg for arg in args.split(" ") if arg != ""]
        if len(self.args_type) == 1 and isinstance(
            self.args_type[0][1], UnknownLengthList
        ):
            return self.args_type[0][1].parse(split_args)

        if len(split_args) != len(self.args_type):
            return None
        l = [
            self.args_type[index][1].parse(arg) for index, arg in enumerate(split_args)
        ]
        if None in l:
            return None
        return l

    async def execute(
        self,
        args: List[str],
        flags: Set[str],
        global_flags: Set[str],
        slack_slash_request: SlackSlashRequest,
    ):
        f_args: List[Any] = [None for _ in range(self.func.__code__.co_argcount)]
        for i, value in enumerate(args):
            f_args[self.args_type[i][2]] = value
        for name, f, i in self.flags:
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
