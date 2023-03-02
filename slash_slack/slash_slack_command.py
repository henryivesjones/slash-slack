import logging
from typing import Any, Callable, List, Literal, Set, Union

import aiohttp

from slash_slack.arg_types import BaseArgType, UnknownLengthList
from slash_slack.blocks import _make_block_message
from slash_slack.flag import Flag
from slash_slack.slash_slack_request import SlackSlashRequest


class SlashSlackCommand:
    command: str
    func: Callable
    flags: List[Flag]
    args_type: Union[BaseArgType, List[BaseArgType], UnknownLengthList]

    def __init__(
        self,
        command: str,
        func: Callable,
        flags: List[Flag],
        args_type: Union[BaseArgType, List[BaseArgType], UnknownLengthList],
    ):
        self.command = command
        self.func = func
        self.flags = flags
        self.args_type = args_type

    def parse_args(self, args: str):
        if isinstance(self.args_type, list):
            split_args = [arg for arg in args.split(" ") if arg != ""]
            if len(self.args_type) != len(split_args):
                return None
            l = [
                arg_type.parse(arg) for arg, arg_type in zip(split_args, self.args_type)
            ]
            if None in l:
                return None
            return l
        if isinstance(self.args_type, UnknownLengthList):
            split_args = [arg for arg in args.split(" ") if arg != ""]
            return self.args_type.parse(split_args)

        if isinstance(self.args_type, BaseArgType):
            return self.args_type.parse(args)

        return None

    async def execute(
        self,
        args: Union[str, List[str]],
        flags: Set[str],
        global_flags: Set[str],
        slack_slash_request: SlackSlashRequest,
    ):
        response = self.func(*[args, flags][: self.func.__code__.co_argcount])
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
