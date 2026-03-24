# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2023  Brad Hochgesang
##################################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see the following:
# https://github.com/FormerLurker/Octolapse/blob/master/LICENSE
#
# You can contact the author either through the git-hub repository, or at the
# following email address: FormerLurker@pm.me
##################################################################################
import time
import unittest

from octoprint_octolapse.gcode_commands import Commands, Response


class TestParsing(unittest.TestCase):

    def setUp(self):
        self.Commands = Commands()
        self.Comments = ""

    def tearDown(self):
        del self.Commands

    def test_unknown_word(self):
        gcode = "K100"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNone(parsed.parameters)

    def test_LocationResponse(self):
        line = 'ok X:150.0 Y:150.0 Z:0.7 E:0.0'
        parsed = Response.parse_position_line(line)
        self.assertTrue(parsed)
        if parsed:
            # we don't know T or F when printing from SD since
            # there's no way to query it from the firmware and
            # no way to track it ourselves when not streaming
            # the file - this all sucks sooo much

            x = parsed.get("x")
            y = parsed.get("y")
            z = parsed.get("z")
            e = None
            if "e" in parsed:
                e = parsed.get("e")
            return {'x': x, 'y': y, 'z': z, 'e': e, }

    def test_LocationResponse_E3D_ToolChanger(self):
        # Note that C is between Z and E, which doesn't yet work
        line = 'X:272.500 Y:140.000 Z:15.000 C:4.600 E:0.000 E0:0.0 Count 66000 21200 24000 7360 Machine 272.500 140.000 15.000 4.600 Bed comp 0.000'
        # This adjusted format DOES work currently
        #line = 'X:272.500 Y:140.000 Z:15.000 E:0.000 E0:0.0 C:4.600 Count 66000 21200 24000 7360 Machine 272.500 140.000 15.000 4.600 Bed comp 0.000'
        parsed = Response.parse_position_line(line)
        self.assertTrue(parsed)
        if parsed:
            # we don't know T or F when printing from SD since
            # there's no way to query it from the firmware and
            # no way to track it ourselves when not streaming
            # the file - this all sucks sooo much

            x = parsed.get("x")
            y = parsed.get("y")
            z = parsed.get("z")
            e = None
            if "e" in parsed:
                e = parsed.get("e")
            return {'x': x, 'y': y, 'z': z, 'e': e, }

    def test_unknown_command(self):
        gcode = "G9999fdafdsafdafsd"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G9999")
        self.assertIsNone(parsed.parameters)

        gcode = "G9999"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G9999")
        self.assertIsNone(parsed.parameters)

    def test_comments(self):
        """Try to parse the G0 Command, parsed.parameters and comment"""

        gcode = ";"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNone(parsed.parameters)

        gcode = " ;"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNone(parsed.parameters)

        gcode = "; "
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNone(parsed.parameters)

        gcode = ";  "
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNone(parsed.parameters)

        gcode = "%"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNone(parsed.parameters)

        gcode = "% "
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNone(parsed.parameters)

        gcode = "%   "
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNone(parsed.parameters)

        gcode = " % this is a comment"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNone(parsed.parameters)

        gcode = "g0 x100 y200.0 z3.0001 e1.1 f7200.000; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G0")
        self.assertEqual(parsed.parameters["X"], 100)
        self.assertEqual(parsed.parameters["Y"], 200.0)
        self.assertEqual(parsed.parameters["Z"], 3.0001)
        self.assertEqual(parsed.parameters["E"], 1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)

        gcode = "g0x100y200.0z3.0001e1.1f7200.000; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G0")
        self.assertEqual(parsed.parameters["X"], 100)
        self.assertEqual(parsed.parameters["Y"], 200.0)
        self.assertEqual(parsed.parameters["Z"], 3.0001)
        self.assertEqual(parsed.parameters["E"], 1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)

        # test signs 1
        gcode = "g0x+100y-200.0z - 3.0001e +1.1f 7200.000; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G0")
        self.assertEqual(parsed.parameters["X"], 100)
        self.assertEqual(parsed.parameters["Y"], -200.0)
        self.assertEqual(parsed.parameters["Z"], -3.0001)
        self.assertEqual(parsed.parameters["E"], 1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)
        # test signs 2
        gcode = "g0x-100y + 200.0z+  3.0001e -1.1f  +  7200.000; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G0")
        self.assertEqual(parsed.parameters["X"], -100)
        self.assertEqual(parsed.parameters["Y"], 200.0)
        self.assertEqual(parsed.parameters["Z"], 3.0001)
        self.assertEqual(parsed.parameters["E"], -1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)

        gcode = "g28xyz; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertIsNone(parsed.parameters["X"])
        self.assertIsNone(parsed.parameters["Y"])
        self.assertIsNone(parsed.parameters["Z"])

    def test_inline_comments(self):
        gcode = "g28(this is an inline commentx)yz; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertFalse("X" in parsed.parameters)
        self.assertIsNone(parsed.parameters["Y"])
        self.assertIsNone(parsed.parameters["Z"])

        gcode = "g28(this is an inline commentx); Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertFalse("X" in parsed.parameters)
        self.assertFalse("Y" in parsed.parameters)
        self.assertFalse("Z" in parsed.parameters)

        gcode = "(comment in the front)g28; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertFalse("X" in parsed.parameters)
        self.assertFalse("Y" in parsed.parameters)
        self.assertFalse("Z" in parsed.parameters)

        gcode = "(comment in the front)g28(comment in back); Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertFalse("X" in parsed.parameters)
        self.assertFalse("Y" in parsed.parameters)
        self.assertFalse("Z" in parsed.parameters)

        gcode = "(comment in the front)g(comment in middle)28(comment in back); Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertFalse("X" in parsed.parameters)
        self.assertFalse("Y" in parsed.parameters)
        self.assertFalse("Z" in parsed.parameters)

        gcode = "(comment in the front)g(comment in middle)2()8(another comment in middle)x(comment between" \
                "address and value)100()1 . 1(another); Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertEqual(parsed.parameters["X"], 1001.1)
        self.assertFalse("Y" in parsed.parameters)
        self.assertFalse("Z" in parsed.parameters)

    def test_parameter_repetition(self):
        # test parameter repetition
        gcode = "g28 xxz"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNotNone(parsed.error)
        self.assertNotEqual(len(parsed.error), 0)

        # test parameter repetition wrapped in comments
        gcode = "(comment in the front)g(comment in middle)2()8x(another comment in middle)x(comment between" \
                " address and value)100()1 . 1(another); Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNotNone(parsed.error)
        self.assertNotEqual(len(parsed.error), 0)

    def test_multiple_signs_parameter(self):
        # test multiple signs in parameter 1
        gcode = "(comment in the front)g(comment in middle)2()8(another comment in middle)x(comment between" \
                " address and value)+100()1 . 1+(another); Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNotNone(parsed.error)
        self.assertNotEqual(len(parsed.error), 0)
        # test multiple signs in parameter 2
        gcode = "(comment in the front)g(comment in middle)2()8x(another comment in middle)x(comment between" \
                " address and value)++100()1 . 1(another); Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNotNone(parsed.error)
        self.assertNotEqual(len(parsed.error), 0)

    def test_multiple_decimals_parameter(self):
        # test multiple decimal points in parameter 1
        gcode = "(comment in the front)g(comment in middle)2()8x(another comment in middle)x(comment between" \
                "address and value)+100()1 . 1(another).; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNotNone(parsed.error)
        self.assertNotEqual(len(parsed.error), 0)

        # test multiple decimal points in parameter 2
        gcode = "(comment in the front)g(comment in middle)2()8x(another comment in middle)x(comment between" \
                " address and value)1.00()1 . 1(another); Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNotNone(parsed.error)
        self.assertNotEqual(len(parsed.error), 0)

    def test_multiple_decimals_command(self):
        # test multiple decimal points in parameter 2
        gcode = "G28.0."
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNotNone(parsed.error)
        self.assertNotEqual(len(parsed.error), 0)

    def test_parse_int_negative(self):
        # test negative F error
        gcode = "G00 F- 1 09 "
        parsed = Commands.parse(gcode)
        self.assertIsNone(parsed.cmd)
        self.assertIsNotNone(parsed.error)
        self.assertNotEqual(len(parsed.error), 0)

    def test_g0(self):

        # no parameters
        gcode = "g0"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G0")
        self.assertDictEqual({}, parsed.parameters)

        # no parameters, double 0
        gcode = "g00"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G0")
        self.assertDictEqual({}, parsed.parameters)

        # all parameters with comment
        gcode = "g0 x100 y200.0 z3.0001 e1.1 f7200.000; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G0")
        self.assertEqual(parsed.parameters["X"], 100)
        self.assertEqual(parsed.parameters["Y"], 200.0)
        self.assertEqual(parsed.parameters["Z"], 3.0001)
        self.assertEqual(parsed.parameters["E"], 1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)

        # all parameters, no spaces
        gcode = "g0x100y200.0z3.0001e1.1f7200.000"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G0")
        self.assertEqual(parsed.parameters["X"], 100)
        self.assertEqual(parsed.parameters["Y"], 200.0)
        self.assertEqual(parsed.parameters["Z"], 3.0001)
        self.assertEqual(parsed.parameters["E"], 1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)

        # all parameters, funky spaces
        gcode = "g  0 x  10 0  y2 00 .0z  3.0 001 e1. 1 f72 00 .000 "
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G0")
        self.assertEqual(parsed.parameters["X"], 100)
        self.assertEqual(parsed.parameters["Y"], 200.0)
        self.assertEqual(parsed.parameters["Z"], 3.0001)
        self.assertEqual(parsed.parameters["E"], 1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)

    def test_g1(self):
        # no parameters
        gcode = "g1"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G1")
        self.assertDictEqual({}, parsed.parameters)

        # no parameters, double 0
        gcode = "g01"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G1")
        self.assertDictEqual({}, parsed.parameters)

        # all parameters with comment
        gcode = "g1 x100 y200.0 z3.0001 e1.1 f7200.000; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G1")
        self.assertEqual(parsed.parameters["X"], 100)
        self.assertEqual(parsed.parameters["Y"], 200.0)
        self.assertEqual(parsed.parameters["Z"], 3.0001)
        self.assertEqual(parsed.parameters["E"], 1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)

        # all parameters, no spaces
        gcode = "g1x100y200.0z3.0001e1.1f7200.000"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G1")
        self.assertEqual(parsed.parameters["X"], 100)
        self.assertEqual(parsed.parameters["Y"], 200.0)
        self.assertEqual(parsed.parameters["Z"], 3.0001)
        self.assertEqual(parsed.parameters["E"], 1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)

        # all parameters, funky spaces
        gcode = "g  01 x  10 0  y2 00 .0z  3.0 001 e1. 1 f72 00 .000 "
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G1")
        self.assertEqual(parsed.parameters["X"], 100)
        self.assertEqual(parsed.parameters["Y"], 200.0)
        self.assertEqual(parsed.parameters["Z"], 3.0001)
        self.assertEqual(parsed.parameters["E"], 1.1)
        self.assertEqual(parsed.parameters["F"], 7200.000)

        # from issue 86
        gcode = "G1 X -18 Y95 F1000"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G1")
        self.assertEqual(parsed.parameters["X"], -18)
        self.assertEqual(parsed.parameters["Y"], 95)
        self.assertNotIn("Z", parsed.parameters)
        self.assertNotIn("E", parsed.parameters)
        self.assertEqual(parsed.parameters["F"], 1000)

    def test_g20(self):
        # no parameters
        gcode = "G20"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G20")
        self.assertDictEqual({}, parsed.parameters)

        # with parameters (bogus)
        gcode = "G20X100fdafdsa; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G20")
        self.assertDictEqual({}, parsed.parameters)

    def test_g21(self):
        # no parameters
        gcode = "G21"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G21")
        self.assertDictEqual({}, parsed.parameters)

        # with parameters (bogus)
        gcode = "G21X100fdafdsa; Here is a comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G21")
        self.assertDictEqual({}, parsed.parameters)

    def test_g28(self):
        # no parameters
        gcode = "G28"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertDictEqual({}, parsed.parameters)

        # all parameters, funky spaces
        gcode = "g  2  8 xy zw; some kind of comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertIsNone(parsed.parameters["X"])
        self.assertIsNone(parsed.parameters["Y"])
        self.assertIsNone(parsed.parameters["Z"])
        self.assertIsNone(parsed.parameters["W"])

        # all parameters, no spaces
        gcode = "g28wzxy; some kind of comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertIsNone(parsed.parameters["X"])
        self.assertIsNone(parsed.parameters["Y"])
        self.assertIsNone(parsed.parameters["Z"])
        self.assertIsNone(parsed.parameters["W"])

        # some parameters
        gcode = "g28 xy; some kind of comment"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "G28")
        self.assertIsNone(parsed.parameters["X"])
        self.assertIsNone(parsed.parameters["Y"])
        self.assertNotIn("Z", parsed.parameters)
        self.assertNotIn("W", parsed.parameters)


    def test_m105(self):
        gcode = "m105;"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "M105")
        self.assertDictEqual(parsed.parameters, {})

        gcode = "m105X1;"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "M105")
        self.assertDictEqual(parsed.parameters, {})

        gcode = "m105fdsafdsafdsfsdfsd;"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "M105")
        self.assertDictEqual(parsed.parameters, {})

    def test_t(self):
        gcode = "T?"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "T")
        self.assertDictEqual(parsed.parameters, {"T": None})

        gcode = " T? "
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "T")
        self.assertDictEqual(parsed.parameters, {"T":None})

        gcode = " T ? "
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "T")
        self.assertDictEqual(parsed.parameters, {"T": None})

        gcode = "T1;"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "T")
        self.assertDictEqual(parsed.parameters, {"T": 1})

        gcode = "T 1 ;"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "T")
        self.assertDictEqual(parsed.parameters, {"T": 1})

        gcode = "T 1.11 ;"
        parsed = Commands.parse(gcode)
        self.assertEqual(parsed.cmd, "T")
        self.assertDictEqual(parsed.parameters, {"T": 1})
#    def test_performance(self):
#        num_tests = 1000
#
#        # easy test
#        gcode = "g0"
#        print("Testing parsing performance, parsing: " + gcode)
#        start_time = time.time()
#        for i in range(0, num_tests):
#           parsed = Commands.parse(gcode)
#
#        total_time = time.time() - start_time
#        ms_per_op = total_time / num_tests * 1000
#        print("{0} parses in {1} seconds, {2}MS per parse".format(num_tests, total_time, ms_per_op))
#
#        # medium test
#        gcode = "g0 x100.000 y-200.00"
#        print("Testing parsing performance, parsing: " + gcode)
#        start_time = time.time()
#        for i in range(0, num_tests):
#           parsed = Commands.parse(gcode)
#
#        total_time = time.time() - start_time
#        ms_per_op = total_time / num_tests * 1000
#        print("{0} parses in {1} seconds, {2}MS per parse".format(num_tests, total_time, ms_per_op))
#
#        # murder test
#        gcode = "g  0 x  10 0 ( y2 00 .0 ) y2 00 .0z (inline comment) 3.0 001 e1. 1 f72 00 .000; this is a comment; "
#        print("Testing parsing performance, parsing: " + gcode)
#        start_time = time.time()
#        for i in range(0, num_tests):
#           parsed = Commands.parse(gcode)
#
#        total_time = time.time() - start_time
#        ms_per_op = total_time / num_tests * 1000
#        print("{0} parses in {1} seconds, {2}MS per parse".format(num_tests, total_time, ms_per_op))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParsing)
    unittest.TextTestRunner(verbosity=3).run(suite)
