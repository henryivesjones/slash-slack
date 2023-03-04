from unittest import TestCase, main

from slash_slack.slash_slack import _parse_command_text


class TestParseCommandText(TestCase):
    def test_empty(self):
        command, args, flags = _parse_command_text("")
        self.assertEqual("", command)
        self.assertEqual("", args)
        self.assertSetEqual(set(), flags)

    def test_just_command(self):
        command, args, flags = _parse_command_text("a_command")
        self.assertEqual("a_command", command)
        self.assertEqual("", args)
        self.assertSetEqual(set(), flags)

        command, args, flags = _parse_command_text("a-com45mand")
        self.assertEqual("a-com45mand", command)
        self.assertEqual("", args)
        self.assertSetEqual(set(), flags)

        command, args, flags = _parse_command_text("a-com45mand")
        self.assertEqual("a-com45mand", command)
        self.assertEqual("", args)
        self.assertSetEqual(set(), flags)

    def test_single_arg(self):
        command, args, flags = _parse_command_text("command test")
        self.assertEqual("command", command)
        self.assertEqual("test", args)
        self.assertSetEqual(set(), flags)

        command, args, flags = _parse_command_text("command test-test")
        self.assertEqual("command", command)
        self.assertEqual("test-test", args)
        self.assertSetEqual(set(), flags)

        command, args, flags = _parse_command_text("command 1dsf52gfds'[]zc98")
        self.assertEqual("command", command)
        self.assertEqual("1dsf52gfds'[]zc98", args)
        self.assertSetEqual(set(), flags)
        pass

    def test_no_arg_single_flag(self):
        command, args, flags = _parse_command_text("command --help")
        self.assertEqual("command", command)
        self.assertEqual("", args)
        self.assertSetEqual({"help"}, flags)

        command, args, flags = _parse_command_text("--help")
        self.assertEqual("", command)
        self.assertEqual("", args)
        self.assertSetEqual({"help"}, flags)
        pass

    def test_multiple_args(self):
        command, args, flags = _parse_command_text("command these are args")
        self.assertEqual("command", command)
        self.assertEqual("these are args", args)
        self.assertSetEqual(set(), flags)

        command, args, flags = _parse_command_text("command these are 4 args")
        self.assertEqual("command", command)
        self.assertEqual("these are 4 args", args)
        self.assertSetEqual(set(), flags)

        command, args, flags = _parse_command_text(
            "command th\asd43dse ar5\[e 421% argsdsf--test"
        )
        self.assertEqual("command", command)
        self.assertEqual("th\asd43dse ar5\[e 421% argsdsf--test", args)
        self.assertSetEqual(set(), flags)
        pass

    def test_multiple_args_and_flags(self):
        command, args, flags = _parse_command_text(
            "command dsgfka 798dsf --help --another-flag --another-FLAG"
        )
        self.assertEqual("command", command)
        self.assertEqual("dsgfka 798dsf", args)
        self.assertSetEqual({"help", "another-flag", "another-FLAG"}, flags)
        pass

    def test_multiple_args_and_spacing(self):
        command, args, flags = _parse_command_text("command     this   is a    test")
        self.assertEqual("command", command)
        self.assertEqual("this is a test", args)
        self.assertSetEqual(set(), flags)
        pass

    def test_flag_ordering(self):
        command, args, flags = _parse_command_text(
            "command this --help   is a --another-flag test"
        )
        self.assertEqual("command", command)
        self.assertEqual("this is a test", args)
        self.assertSetEqual({"help", "another-flag"}, flags)
        pass

    def test_flag_ordering_2(self):
        command, args, flags = _parse_command_text(
            "command --help this is a test--test --test"
        )
        self.assertEqual("command", command)
        self.assertEqual("this is a test--test", args)
        self.assertSetEqual({"help", "test"}, flags)
        pass


if __name__ == "__main__":
    main()
