from unittest import TestCase, main

from slash_slack import Flag, Float, Int, SlashSlackRequest, String, UnknownLengthList
from slash_slack.slash_slack_command import SlashSlackCommand


def a(s: str):
    pass


def b(s: str, i: int, f: float):
    pass


def c(s: str, fl=Flag()):
    pass


def d(s: str, u=UnknownLengthList(arg_type=String())):
    pass


def e():
    pass


def f(s: str, slash_slack_request: SlashSlackRequest):
    pass


def g(s: str, fl=Flag(), i=Int()):
    pass


SLASH_SLACK_REQUEST = SlashSlackRequest(
    token="test",
    team_id="123",
    team_domain="123",
    enterprise_id="123",
    enterprise_name="1234",
    channel_id="1234",
    channel_name="test",
    user_id="1234",
    user_name="John Doe",
    command="command",
    text="a text",
    response_url="google.com",
    trigger_id="1239873",
    api_app_id="2134",
)


class TestSlashSlackCommand(TestCase):
    def test_parse_args_no_args(self):
        command = SlashSlackCommand(
            command="test",
            func=e,
            flags=[],
            args_type=[],
            request_arg=None,
        )
        parsed_args = command.parse_args("")
        self.assertEqual([], parsed_args)

    def test_parse_args_one_string(self):
        command = SlashSlackCommand(
            command="test",
            func=a,
            flags=[],
            args_type=[("s", String(), 0)],
            request_arg=None,
        )
        parsed_args = command.parse_args("test")
        self.assertEqual(["test"], parsed_args)

        parsed_args = command.parse_args("test me multiple words one arg")
        self.assertEqual(["test me multiple words one arg"], parsed_args)

    def test_parse_args_multiple_types(self):
        command = SlashSlackCommand(
            command="test",
            func=b,
            flags=[],
            args_type=[("s", String(), 0), ("i", Int(), 1), ("f", Float(), 2)],
            request_arg=None,
        )
        parsed_args = command.parse_args("test 1 1.0 0")
        self.assertEqual(None, parsed_args)
        parsed_args = command.parse_args("test")
        self.assertEqual(None, parsed_args)
        parsed_args = command.parse_args("test 1 1.0")
        self.assertEqual(["test", 1, 1.0], parsed_args)

    def test_parse_args_unknown_length_list(self):
        command = SlashSlackCommand(
            command="test",
            func=d,
            flags=[],
            args_type=[
                ("s", String(), 0),
                ("u", UnknownLengthList(arg_type=String()), 1),
            ],
            request_arg=None,
        )
        parsed_args = command.parse_args("test a b c")
        self.assertEqual(["test", ["a", "b", "c"]], parsed_args)

        parsed_args = command.parse_args("test")
        self.assertEqual(None, parsed_args)

        parsed_args = command.parse_args("a b")
        self.assertEqual(["a", ["b"]], parsed_args)

    def test_parse_args_empty(self):
        command = SlashSlackCommand(
            command="test",
            func=a,
            flags=[],
            args_type=[("s", String(), 0)],
            request_arg=None,
        )
        parsed_args = command.parse_args("")
        self.assertEqual([""], parsed_args)

    def test_parse_args_too_few(self):
        command = SlashSlackCommand(
            command="test",
            func=b,
            flags=[],
            args_type=[("s", String(), 0), ("i", Int(), 1), ("f", Float(), 2)],
            request_arg=None,
        )
        parsed_args = command.parse_args("test 1")
        self.assertEqual(None, parsed_args)

    def test_parse_args_too_many(self):
        command = SlashSlackCommand(
            command="test",
            func=b,
            flags=[],
            args_type=[("s", String(), 0), ("i", Int(), 1), ("f", Float(), 2)],
            request_arg=None,
        )
        parsed_args = command.parse_args("test 1 2.0 3.0")
        self.assertEqual(None, parsed_args)

    def test_parse_args_wrong_type(self):
        command = SlashSlackCommand(
            command="test",
            func=b,
            flags=[],
            args_type=[("s", String(), 0), ("i", Int(), 1), ("f", Float(), 2)],
            request_arg=None,
        )
        parsed_args = command.parse_args("test 1.0 abc")
        self.assertEqual(None, parsed_args)

    def test_hydrate_func_args(self):
        command = SlashSlackCommand(
            command="test",
            func=b,
            flags=[],
            args_type=[("s", String(), 0), ("i", Int(), 1), ("f", Float(), 2)],
            request_arg=None,
        )
        _func_arg = command._hydrate_func_args(
            ["test", 123, 10.0], set(), SLASH_SLACK_REQUEST
        )
        self.assertEqual(["test", 123, 10.0], _func_arg)

    def test_hydrate_func_args_flags(self):
        command = SlashSlackCommand(
            command="test",
            func=g,
            flags=[("fl", Flag(), 1)],
            args_type=[("s", String(), 0), ("i", Int(), 2)],
            request_arg=None,
        )
        _func_arg = command._hydrate_func_args(
            ["test", 123], set(), SLASH_SLACK_REQUEST
        )
        self.assertEqual(["test", False, 123], _func_arg)

        _func_arg = command._hydrate_func_args(
            ["test", 123], {"fl"}, SLASH_SLACK_REQUEST
        )
        self.assertEqual(["test", True, 123], _func_arg)

    def test_hydrate_func_args_request_arg(self):
        command = SlashSlackCommand(
            command="test",
            func=f,
            flags=[],
            args_type=[("s", String(), 0)],
            request_arg=("slash_slack_request", 1),
        )
        _func_arg = command._hydrate_func_args(["test"], set(), SLASH_SLACK_REQUEST)
        self.assertEqual(["test", SLASH_SLACK_REQUEST], _func_arg)


if __name__ == "__main__":
    main()
