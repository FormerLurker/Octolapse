# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2017  Brad Hochgesang
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

from octoprint_octolapse.gcode_parser import Commands


class TestParsing(unittest.TestCase):

    def setUp(self):
        self.Commands = Commands()
        self.Comments = ""

    def tearDown(self):
        del self.Commands

    def test_unknown_word(self):
        gcode = "K100"
        cmd, parameters = Commands.parse(gcode)
        self.assertIsNone(cmd)
        self.assertIsNone(parameters)

    def test_unknown_command(self):
        gcode = "G9999fdafdsafdafsd"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G9999")
        self.assertIsNone(parameters)

        gcode = "G9999"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G9999")
        self.assertIsNone(parameters)

    def test_comments(self):
        """Try to parse the G0 Command, parameters and comment"""

        gcode = ";"
        cmd, parameters = Commands.parse(gcode)
        self.assertIsNone(cmd)
        self.assertIsNone(parameters)

        gcode = " ;"
        cmd, parameters = Commands.parse(gcode)
        self.assertIsNone(cmd)
        self.assertIsNone(parameters)

        gcode = "; "
        cmd, parameters = Commands.parse(gcode)
        self.assertIsNone(cmd)
        self.assertIsNone(parameters)

        gcode = ";  "
        cmd, parameters = Commands.parse(gcode)
        self.assertIsNone(cmd)
        self.assertIsNone(parameters)

        gcode = "%"
        cmd, parameters = Commands.parse(gcode)
        self.assertIsNone(cmd)
        self.assertIsNone(parameters)

        gcode = "% "
        cmd, parameters = Commands.parse(gcode)
        self.assertIsNone(cmd)
        self.assertIsNone(parameters)

        gcode = "%   "
        cmd, parameters = Commands.parse(gcode)
        self.assertIsNone(cmd)
        self.assertIsNone(parameters)

        gcode = " % this is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertIsNone(cmd)
        self.assertIsNone(parameters)

        gcode = "g0 x100 y200.0 z3.0001 e1.1 f7200.000; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G0")
        self.assertEqual(parameters["X"], 100)
        self.assertEqual(parameters["Y"], 200.0)
        self.assertEqual(parameters["Z"], 3.0001)
        self.assertEqual(parameters["E"], 1.1)
        self.assertEqual(parameters["F"], 7200.000)

        gcode = "g0x100y200.0z3.0001e1.1f7200.000; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G0")
        self.assertEqual(parameters["X"], 100)
        self.assertEqual(parameters["Y"], 200.0)
        self.assertEqual(parameters["Z"], 3.0001)
        self.assertEqual(parameters["E"], 1.1)
        self.assertEqual(parameters["F"], 7200.000)

        # test signs 1
        gcode = "g0x+100y-200.0z - 3.0001e +1.1f 7200.000; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G0")
        self.assertEqual(parameters["X"], 100)
        self.assertEqual(parameters["Y"], -200.0)
        self.assertEqual(parameters["Z"], -3.0001)
        self.assertEqual(parameters["E"], 1.1)
        self.assertEqual(parameters["F"], 7200.000)
        # test signs 2
        gcode = "g0x-100y + 200.0z+  3.0001e -1.1f  +  7200.000; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G0")
        self.assertEqual(parameters["X"], -100)
        self.assertEqual(parameters["Y"], 200.0)
        self.assertEqual(parameters["Z"], 3.0001)
        self.assertEqual(parameters["E"], -1.1)
        self.assertEqual(parameters["F"], 7200.000)

        gcode = "g28xyz; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertIsNone(parameters["X"])
        self.assertIsNone(parameters["Y"])
        self.assertIsNone(parameters["Z"])

    def test_inline_comments(self):
        gcode = "g28(this is an inline commentx)yz; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertFalse("X" in parameters)
        self.assertIsNone(parameters["Y"])
        self.assertIsNone(parameters["Z"])

        gcode = "g28(this is an inline commentx); Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertFalse("X" in parameters)
        self.assertFalse("Y" in parameters)
        self.assertFalse("Z" in parameters)

        gcode = "(comment in the front)g28; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertFalse("X" in parameters)
        self.assertFalse("Y" in parameters)
        self.assertFalse("Z" in parameters)

        gcode = "(comment in the front)g28(comment in back); Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertFalse("X" in parameters)
        self.assertFalse("Y" in parameters)
        self.assertFalse("Z" in parameters)

        gcode = "(comment in the front)g(comment in middle)28(comment in back); Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertFalse("X" in parameters)
        self.assertFalse("Y" in parameters)
        self.assertFalse("Z" in parameters)

        gcode = "(comment in the front)g(comment in middle)2()8(another comment in middle)x(comment between" \
                "address and value)100()1 . 1(another); Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertEqual(parameters["X"], 1001.1)
        self.assertFalse("Y" in parameters)
        self.assertFalse("Z" in parameters)

    def test_parameter_repetition(self):
        # test parameter repetition
        gcode = "g28 xxz"
        with self.assertRaises(Exception) as context:
            Commands.parse(gcode)
        self.assertTrue('A parameter value was repeated, cannot parse gcode.' in context.exception)

        # test parameter repetition wrapped in comments
        gcode = "(comment in the front)g(comment in middle)2()8x(another comment in middle)x(comment between" \
                " address and value)100()1 . 1(another); Here is a comment"
        with self.assertRaises(Exception) as context:
            Commands.parse(gcode)
        self.assertTrue('A parameter value was repeated, cannot parse gcode.' in context.exception)

    def test_multiple_signs_parameter(self):
        # test multiple signs in parameter 1
        gcode = "(comment in the front)g(comment in middle)2()8(another comment in middle)x(comment between" \
                " address and value)+100()1 . 1+(another); Here is a comment"
        with self.assertRaises(Exception) as context:
            Commands.parse(gcode)
        self.assertTrue("Could not parse float from parameter string, saw multiple signs." in context.exception)

        # test multiple signs in parameter 2
        gcode = "(comment in the front)g(comment in middle)2()8x(another comment in middle)x(comment between" \
                " address and value)++100()1 . 1(another); Here is a comment"
        with self.assertRaises(Exception) as context:
            Commands.parse(gcode)
        self.assertTrue("Could not parse float from parameter string, saw multiple signs." in context.exception)

    def test_multiple_decimals_parameter(self):
        # test multiple decimal points in parameter 1
        gcode = "(comment in the front)g(comment in middle)2()8x(another comment in middle)x(comment between" \
                "address and value)+100()1 . 1(another).; Here is a comment"
        with self.assertRaises(Exception) as context:
            Commands.parse(gcode)
        self.assertTrue(
            "Could not parse float from parameter string, saw multiple decimal points." in context.exception
        )

        # test multiple decimal points in parameter 2
        gcode = "(comment in the front)g(comment in middle)2()8x(another comment in middle)x(comment between" \
                " address and value)1.00()1 . 1(another); Here is a comment"
        with self.assertRaises(Exception) as context:
            Commands.parse(gcode)
        self.assertTrue(
            "Could not parse float from parameter string, saw multiple decimal points." in context.exception
        )

    def test_multiple_decimals_command(self):
        # test multiple decimal points in parameter 2
        gcode = "G28.0."
        with self.assertRaises(Exception) as context:
            Commands.parse(gcode)
        self.assertTrue("Cannot parse the gcode address, multiple periods seen." in context.exception)

    def test_parse_int_negative(self):
        # test negative F error
        gcode = "G00 F- 1 09 "
        with self.assertRaises(Exception) as context:
            Commands.parse(gcode)
        self.assertTrue("The parameter value is negative, which is not allowed." in context.exception)

    def test_g0(self):

        # no parameters
        gcode = "g0"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G0")
        self.assertDictEqual({}, parameters)

        # no parameters, double 0
        gcode = "g00"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G0")
        self.assertDictEqual({}, parameters)

        # all parameters with comment
        gcode = "g0 x100 y200.0 z3.0001 e1.1 f7200.000; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G0")
        self.assertEqual(parameters["X"], 100)
        self.assertEqual(parameters["Y"], 200.0)
        self.assertEqual(parameters["Z"], 3.0001)
        self.assertEqual(parameters["E"], 1.1)
        self.assertEqual(parameters["F"], 7200.000)

        # all parameters, no spaces
        gcode = "g0x100y200.0z3.0001e1.1f7200.000"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G0")
        self.assertEqual(parameters["X"], 100)
        self.assertEqual(parameters["Y"], 200.0)
        self.assertEqual(parameters["Z"], 3.0001)
        self.assertEqual(parameters["E"], 1.1)
        self.assertEqual(parameters["F"], 7200.000)

        # all parameters, funky spaces
        gcode = "g  0 x  10 0  y2 00 .0z  3.0 001 e1. 1 f72 00 .000 "
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G0")
        self.assertEqual(parameters["X"], 100)
        self.assertEqual(parameters["Y"], 200.0)
        self.assertEqual(parameters["Z"], 3.0001)
        self.assertEqual(parameters["E"], 1.1)
        self.assertEqual(parameters["F"], 7200.000)

    def test_g1(self):
        # no parameters
        gcode = "g1"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G1")
        self.assertDictEqual({}, parameters)

        # no parameters, double 0
        gcode = "g01"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G1")
        self.assertDictEqual({}, parameters)

        # all parameters with comment
        gcode = "g1 x100 y200.0 z3.0001 e1.1 f7200.000; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G1")
        self.assertEqual(parameters["X"], 100)
        self.assertEqual(parameters["Y"], 200.0)
        self.assertEqual(parameters["Z"], 3.0001)
        self.assertEqual(parameters["E"], 1.1)
        self.assertEqual(parameters["F"], 7200.000)

        # all parameters, no spaces
        gcode = "g1x100y200.0z3.0001e1.1f7200.000"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G1")
        self.assertEqual(parameters["X"], 100)
        self.assertEqual(parameters["Y"], 200.0)
        self.assertEqual(parameters["Z"], 3.0001)
        self.assertEqual(parameters["E"], 1.1)
        self.assertEqual(parameters["F"], 7200.000)

        # all parameters, funky spaces
        gcode = "g  01 x  10 0  y2 00 .0z  3.0 001 e1. 1 f72 00 .000 "
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G1")
        self.assertEqual(parameters["X"], 100)
        self.assertEqual(parameters["Y"], 200.0)
        self.assertEqual(parameters["Z"], 3.0001)
        self.assertEqual(parameters["E"], 1.1)
        self.assertEqual(parameters["F"], 7200.000)

        # from issue 86
        gcode = "G1 X -18 Y95 F1000"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G1")
        self.assertEqual(parameters["X"], -18)
        self.assertEqual(parameters["Y"], 95)
        self.assertNotIn("Z", parameters)
        self.assertNotIn("E", parameters)
        self.assertEqual(parameters["F"], 1000)

    def test_g20(self):
        # no parameters
        gcode = "G20"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G20")
        self.assertDictEqual({}, parameters)

        # with parameters (bogus)
        gcode = "G20X100fdafdsa; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G20")
        self.assertDictEqual({}, parameters)

    def test_g21(self):
        # no parameters
        gcode = "G21"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G21")
        self.assertDictEqual({}, parameters)

        # with parameters (bogus)
        gcode = "G21X100fdafdsa; Here is a comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G21")
        self.assertDictEqual({}, parameters)

    def test_g28(self):
        # no parameters
        gcode = "G28"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertDictEqual({}, parameters)

        # all parameters, funky spaces
        gcode = "g  2  8 xy zw; some kind of comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertIsNone(parameters["X"])
        self.assertIsNone(parameters["Y"])
        self.assertIsNone(parameters["Z"])
        self.assertIsNone(parameters["W"])

        # all parameters, no spaces
        gcode = "g28wzxy; some kind of comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertIsNone(parameters["X"])
        self.assertIsNone(parameters["Y"])
        self.assertIsNone(parameters["Z"])
        self.assertIsNone(parameters["W"])

        # some parameters
        gcode = "g28 xy; some kind of comment"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "G28")
        self.assertIsNone(parameters["X"])
        self.assertIsNone(parameters["Y"])
        self.assertNotIn("Z", parameters)
        self.assertNotIn("W", parameters)


    def test_m105(self):
        gcode = "m105;"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "M105")
        self.assertDictEqual(parameters, {})

        gcode = "m105X1;"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "M105")
        self.assertDictEqual(parameters, {})

        gcode = "m105fdsafdsafdsfsdfsd;"
        cmd, parameters = Commands.parse(gcode)
        self.assertEqual(cmd, "M105")
        self.assertDictEqual(parameters, {})

#    def test_performance(self):
#        num_tests = 1000
#
#        # easy test
#        gcode = "g0"
#        print("Testing parsing performance, parsing: " + gcode)
#        start_time = time.time()
#        for i in range(0, num_tests):
#           cmd, parameters = Commands.parse(gcode)
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
#           cmd, parameters = Commands.parse(gcode)
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
#           cmd, parameters = Commands.parse(gcode)
#
#        total_time = time.time() - start_time
#        ms_per_op = total_time / num_tests * 1000
#        print("{0} parses in {1} seconds, {2}MS per parse".format(num_tests, total_time, ms_per_op))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParsing)
    unittest.TextTestRunner(verbosity=3).run(suite)
