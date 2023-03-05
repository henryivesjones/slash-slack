from typing import List
from unittest import TestCase, main

from slash_slack import Flag, Float, Int, SlashSlackRequest, String, UnknownLengthList
from slash_slack.arg_types import (
    FlagType,
    FloatType,
    IntType,
    StringType,
    UnknownLengthListType,
)
from slash_slack.exceptions import (
    InvalidAnnotationException,
    InvalidDefaultValueException,
    MultipleSlashSlackRequestParametersException,
    ParamAfterUnknownLengthListException,
)
from slash_slack.slash_slack import _parse_func_params


class TestParseFuncParams(TestCase):
    def test_no_params(self):
        def t():
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertListEqual([], params)
        self.assertListEqual([], flags)
        self.assertIsNone(request_arg)

    def test_single_string(self):
        def t(s: str):
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertEqual(1, len(params))
        self.assertEqual("s", params[0][0])
        self.assertTrue(isinstance(params[0][1], StringType))

        self.assertListEqual([], flags)
        self.assertIsNone(request_arg)

    def test_single_unannotated(self):
        def t(s):
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertEqual(1, len(params))
        self.assertEqual("s", params[0][0])
        self.assertTrue(isinstance(params[0][1], StringType))

        self.assertListEqual([], flags)
        self.assertIsNone(request_arg)

    def test_single_unknown_list(self):
        def t(l=UnknownLengthList(arg_type=String())):
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertEqual(1, len(params))
        self.assertEqual("l", params[0][0])
        self.assertTrue(isinstance(params[0][1], UnknownLengthListType))
        if isinstance(params[0][1], UnknownLengthListType):
            self.assertTrue(isinstance(params[0][1].arg_type, StringType))

        self.assertListEqual([], flags)
        self.assertIsNone(request_arg)

    def test_just_annotations(self):
        def t(s: str, i: int, f: float):
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertEqual(3, len(params))

        self.assertEqual("s", params[0][0])
        self.assertTrue(isinstance(params[0][1], StringType))
        self.assertEqual(0, params[0][2])

        self.assertEqual("i", params[1][0])
        self.assertTrue(isinstance(params[1][1], IntType))
        self.assertEqual(1, params[1][2])

        self.assertEqual("f", params[2][0])
        self.assertTrue(isinstance(params[2][1], FloatType))
        self.assertEqual(2, params[2][2])

        self.assertListEqual([], flags)
        self.assertIsNone(request_arg)

    def test_default_builtins(self):
        def t(s="", i=1, f=1.0):
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertEqual(3, len(params))

        self.assertEqual("s", params[0][0])
        self.assertTrue(isinstance(params[0][1], StringType))
        self.assertEqual(0, params[0][2])

        self.assertEqual("i", params[1][0])
        self.assertTrue(isinstance(params[1][1], IntType))
        self.assertEqual(1, params[1][2])

        self.assertEqual("f", params[2][0])
        self.assertTrue(isinstance(params[2][1], FloatType))
        self.assertEqual(2, params[2][2])

        self.assertListEqual([], flags)
        self.assertIsNone(request_arg)

    def test_default_funcs(self):
        def t(s=String(), i=Int(), f=Float()):
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertEqual(3, len(params))

        self.assertEqual("s", params[0][0])
        self.assertTrue(isinstance(params[0][1], StringType))
        self.assertEqual(0, params[0][2])

        self.assertEqual("i", params[1][0])
        self.assertTrue(isinstance(params[1][1], IntType))
        self.assertEqual(1, params[1][2])

        self.assertEqual("f", params[2][0])
        self.assertTrue(isinstance(params[2][1], FloatType))
        self.assertEqual(2, params[2][2])

        self.assertListEqual([], flags)
        self.assertIsNone(request_arg)

    def test_slash_slack_request(self):
        def t(slash_slack_request: SlashSlackRequest):
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertEqual(0, len(params))
        self.assertEqual(0, len(flags))
        self.assertIsNotNone(request_arg)
        if request_arg is not None:
            self.assertEqual(2, len(request_arg))
            self.assertEqual("slash_slack_request", request_arg[0])
            self.assertEqual(0, request_arg[1])

    def test_two_slash_slack_request(self):
        def t(
            slash_slack_request: SlashSlackRequest,
            slash_slack_request2: SlashSlackRequest,
        ):
            pass

        self.assertRaises(
            MultipleSlashSlackRequestParametersException, lambda: _parse_func_params(t)
        )

    def test_bad_unknown_length_list(self):
        def t(
            l=UnknownLengthList(arg_type=String()),
            s: str = String(),
        ):
            pass

        self.assertRaises(
            ParamAfterUnknownLengthListException, lambda: _parse_func_params(t)
        )

    def test_bad_default_value(self):
        def t(l=List[str]):
            pass

        self.assertRaises(InvalidDefaultValueException, lambda: _parse_func_params(t))

    def test_bad_annotation_value(self):
        def t(l: List[str]):
            pass

        self.assertRaises(InvalidAnnotationException, lambda: _parse_func_params(t))

    def test_flag(self):
        def t(s=String(), f=Flag(), s2=String(), f2=Flag()):
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertEqual(2, len(params))

        self.assertEqual(0, params[0][2])
        self.assertEqual("s", params[0][0])

        self.assertEqual(2, params[1][2])
        self.assertEqual("s2", params[1][0])

        self.assertEqual(1, flags[0][2])
        self.assertEqual("f", flags[0][0])
        self.assertTrue(isinstance(flags[0][1], FlagType))

        self.assertEqual(3, flags[1][2])
        self.assertEqual("f2", flags[1][0])
        self.assertTrue(isinstance(flags[1][1], FlagType))
        self.assertEqual(2, len(flags))
        self.assertIsNone(request_arg)

    def test_only_flag(self):
        def t(f=Flag()):
            pass

        params, flags, request_arg = _parse_func_params(t)
        self.assertEqual(0, len(params))

        self.assertEqual(1, len(flags))
        self.assertEqual("f", flags[0][0])
        self.assertTrue(isinstance(flags[0][1], FlagType))
        self.assertIsNone(request_arg)


if __name__ == "__main__":
    main()
