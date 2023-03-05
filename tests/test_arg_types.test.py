from unittest import TestCase, main

from slash_slack.arg_types import (
    EnumType,
    FloatType,
    IntType,
    StringType,
    UnknownLengthListType,
)


class TestFloatType(TestCase):
    def test_parse_empty(self):
        v = FloatType()
        parsed = v.parse(None)
        self.assertEqual(None, parsed)

    def test_parse_valid(self):
        v = FloatType()
        parsed = v.parse("1.0")
        self.assertEqual(1.0, parsed)
        parsed = v.parse("10")
        self.assertEqual(10.0, parsed)

    def test_negative(self):
        v = FloatType()
        parsed = v.parse("-100")
        self.assertEqual(-100.0, parsed)

    def test_minimum(self):
        v = FloatType(minimum=10.0)
        parsed = v.parse("100.0")
        self.assertEqual(100.0, parsed)

    def test_minimum_should_fail(self):
        v = FloatType(minimum=10.0)
        parsed = v.parse("-10.0")
        self.assertEqual(None, parsed)

    def test_maximum(self):
        v = FloatType(maximum=10)
        parsed = v.parse("1")
        self.assertEqual(1.0, parsed)

    def test_maximum_should_fail(self):
        v = FloatType(maximum=10)
        parsed = v.parse("100.0")
        self.assertEqual(None, parsed)

    def test_list(self):
        v = FloatType()
        parsed = v.parse(["1", "0", "0"])
        self.assertEqual(None, parsed)


class TestIntType(TestCase):
    def test_parse_empty(self):
        v = IntType()
        parsed = v.parse(None)
        self.assertEqual(None, parsed)

    def test_parse_valid(self):
        v = IntType()
        parsed = v.parse("1.0")
        self.assertEqual(None, parsed)
        parsed = v.parse("10")
        self.assertEqual(10, parsed)

    def test_negative(self):
        v = IntType()
        parsed = v.parse("-100")
        self.assertEqual(-100, parsed)

    def test_minimum(self):
        v = IntType(minimum=10)
        parsed = v.parse("100")
        self.assertEqual(100, parsed)

    def test_minimum_should_fail(self):
        v = IntType(minimum=10)
        parsed = v.parse("-10")
        self.assertEqual(None, parsed)

    def test_maximum(self):
        v = IntType(maximum=10)
        parsed = v.parse("1")
        self.assertEqual(1, parsed)

    def test_maximum_should_fail(self):
        v = IntType(maximum=10)
        parsed = v.parse("100")
        self.assertEqual(None, parsed)

    def test_list(self):
        v = IntType()
        parsed = v.parse(["1", "0", "0"])
        self.assertEqual(None, parsed)


class TestStringType(TestCase):
    def test_empty(self):
        v = StringType()
        parsed = v.parse("")
        self.assertEqual("", parsed)

    def test_none(self):
        v = StringType()
        parsed = v.parse(None)
        self.assertEqual(None, parsed)
        pass

    def test_good(self):
        v = StringType()
        parsed = v.parse("thisisastring")
        self.assertEqual("thisisastring", parsed)
        pass

    def test_with_spaces(self):
        v = StringType()
        parsed = v.parse("this is a string")
        self.assertEqual("this is a string", parsed)
        pass

    def test_minimum_length(self):
        v = StringType(minimum_length=10)
        parsed = v.parse("1234567890")
        self.assertEqual("1234567890", parsed)

        parsed = v.parse("123456789")
        self.assertEqual(None, parsed)

    def test_maximum(self):
        v = StringType(maximum_length=10)
        parsed = v.parse("12345678901")
        self.assertEqual(None, parsed)

        parsed = v.parse("1234567")
        self.assertEqual("1234567", parsed)


class TestEnumType(TestCase):
    def test_empty(self):
        v = EnumType(values={"test"})
        parsed = v.parse("")
        self.assertEqual(None, parsed)

    def test_no_match(self):
        v = EnumType(values={"test"})
        parsed = v.parse("another-value")
        self.assertEqual(None, parsed)

    def test_match(self):
        v = EnumType(values={"test"})
        parsed = v.parse("test")
        self.assertEqual("test", parsed)


class TestUnknownLengthListType(TestCase):
    def test_empty(self):
        v = UnknownLengthListType(arg_type=StringType())
        parsed = v.parse("")
        self.assertEqual([], parsed)

        v = UnknownLengthListType(arg_type=StringType())
        parsed = v.parse([])
        self.assertEqual([], parsed)

    def test_one(self):
        v = UnknownLengthListType(arg_type=StringType())
        parsed = v.parse("one")
        self.assertEqual(["one"], parsed)

    def test_one_arg(self):
        v = UnknownLengthListType(arg_type=StringType())
        parsed = v.parse(["one"])
        self.assertEqual(["one"], parsed)

    def test_multiple_args(self):
        v = UnknownLengthListType(arg_type=StringType())
        parsed = v.parse(["one", "two"])
        self.assertEqual(["one", "two"], parsed)

    def test_good_type_conversion(self):
        v = UnknownLengthListType(arg_type=FloatType())
        parsed = v.parse(["1.0", "200"])
        self.assertEqual([1.0, 200.0], parsed)

    def test_bad_type_conversion(self):
        v = UnknownLengthListType(arg_type=FloatType())
        parsed = v.parse(["asf", "200"])
        self.assertEqual(None, parsed)


if __name__ == "__main__":
    main()
