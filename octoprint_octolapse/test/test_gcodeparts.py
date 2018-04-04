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
# following email address: FormerLurker@protonmail.com
##################################################################################

import unittest

from octoprint_octolapse.gcode_parser import GcodeParts


class TestGcodeParts(unittest.TestCase):

    def test_NullCommand(self):
        """Using None for your gcode will result in both the comand and the comment being None, with no parameters"""

        gcode_parts = GcodeParts(None)
        self.assertTrue(gcode_parts.Command is None)
        self.assertTrue(gcode_parts.Comment is None)
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_SemicolonOnly(self):
        """If only a semicolon is given, the command should be None and the comment should be the empty string,
        with no parameters """
        gcode_parts = GcodeParts(";")
        self.assertTrue(gcode_parts.Command is None)
        self.assertTrue(gcode_parts.Comment == "")
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_CommentOnly(self):
        """Ensure that gcode consisting of only a semicolon and a comment contain a null command, the comment,
        and no parameters """
        gcode_parts = GcodeParts(";Here is a comment")
        self.assertTrue(gcode_parts.Command is None)
        self.assertTrue(gcode_parts.Comment == "Here is a comment")
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_WhitespaceAndComment(self):
        """Ensure that gcode consisting of whitespace,a semicolon and a comment contain a null command, the comment,
        and no parameters """
        gcode_parts = GcodeParts(
            "			;Here is a comment preceeded by spaces and tabs.")
        self.assertTrue(gcode_parts.Command is None)
        self.assertTrue(gcode_parts.Comment ==
                        "Here is a comment preceeded by spaces and tabs.")
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_CommandOnly(self):
        """Ensure that gcode with a command only (no parameters or coments) returns the command, a null comment,
        and no parameters """
        gcode_parts = GcodeParts("THECOMMAND")
        self.assertTrue(gcode_parts.Command == "THECOMMAND")
        self.assertTrue(gcode_parts.Comment is None)
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_CommandOnlyWhitespaceBefore(self):
        """Ensure that gcode with a command only (no parameters or coments) preceeded by whitespace returns the
        command, a null comment, and no parameters """
        gcode_parts = GcodeParts("		THECOMMANDWITHTABSANDSPACES")
        self.assertTrue(gcode_parts.Command == "THECOMMANDWITHTABSANDSPACES")
        self.assertTrue(gcode_parts.Comment is None)
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_CommandOnlyWhitespaceAfter(self):
        """Ensure that gcode with a command only (no parameters or coments) followed by whitespace returns the
        command, a null comment, and no parameters """
        gcode_parts = GcodeParts("THECOMMANDWITHTABSANDSPACESAFTER		     ")
        self.assertTrue(gcode_parts.Command ==
                        "THECOMMANDWITHTABSANDSPACESAFTER")
        self.assertTrue(gcode_parts.Comment is None)
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_CommandOnlyWhitespaceBeforeAndAfter(self):
        """Ensure that gcode with a command only (no parameters or coments) preceeded and followed by whitespace
        returns the command, a null comment, and no parameters """
        gcode_parts = GcodeParts(
            "		  THECOMMANDWITHTABSANDSPACESBEFOREANDAFTER		     ")
        self.assertTrue(gcode_parts.Command ==
                        "THECOMMANDWITHTABSANDSPACESBEFOREANDAFTER")
        self.assertTrue(gcode_parts.Comment is None)
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_CommandAndComment(self):
        """Ensure that gcode with a command and a comment return both the command, the comment, and no parameters."""
        gcode_parts = GcodeParts("THECOMMAND;The Comment")
        self.assertTrue(gcode_parts.Command == "THECOMMAND")
        self.assertTrue(gcode_parts.Comment == "The Comment")
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_CommandAndCommentWhitespace(self):
        """Ensure that gcode with a command, a comment, and whitespace around both the command and comment returns
        the trimmed command and the untrimmed comment with no parameters. """
        gcode_parts = GcodeParts("	THECOMMAND	;	The Comment		")
        self.assertTrue(gcode_parts.Command == "THECOMMAND")
        self.assertTrue(gcode_parts.Comment == "	The Comment		")
        self.assertTrue(len(gcode_parts.Parameters) == 0)

    def test_CommandAndParameters_single(self):
        """Test a command and a single parameter without comments, make sure they are returned and that the comment
        is None. """
        gcode_parts = GcodeParts("THECOMMAND param1")
        self.assertTrue(gcode_parts.Command == "THECOMMAND")
        self.assertTrue(gcode_parts.Comment is None)
        self.assertTrue(len(gcode_parts.Parameters) == 1)
        self.assertTrue(gcode_parts.Parameters[0] == "param1")

    def test_CommandAndParameters_multiple(self):
        """Test a command and 4 parameters without comments, make sure they are returned and that the comment is
        None. """
        gcode_parts = GcodeParts("THECOMMAND param1 param2 param3 param4")
        self.assertTrue(gcode_parts.Command == "THECOMMAND")
        self.assertTrue(gcode_parts.Comment is None)
        self.assertTrue(len(gcode_parts.Parameters) == 4)
        self.assertTrue(gcode_parts.Parameters[0] == "param1")
        self.assertTrue(gcode_parts.Parameters[1] == "param2")
        self.assertTrue(gcode_parts.Parameters[2] == "param3")
        self.assertTrue(gcode_parts.Parameters[3] == "param4")

    def test_CommandAndParametersWhitespace(self):
        """Test a command and 4 parameters without comments including extra whitespace.  Make sure they are returned
        and trimmed, and that the comment is None. """
        gcode_parts = GcodeParts(
            "	 THECOMMAND		param1  param2 param3	param4   ")
        self.assertTrue(gcode_parts.Command == "THECOMMAND")
        self.assertTrue(gcode_parts.Comment is None)
        self.assertTrue(len(gcode_parts.Parameters) == 4)
        self.assertTrue(gcode_parts.Parameters[0] == "param1")
        self.assertTrue(gcode_parts.Parameters[1] == "param2")
        self.assertTrue(gcode_parts.Parameters[2] == "param3")
        self.assertTrue(gcode_parts.Parameters[3] == "param4")

    def test_CommandParametersAndComment(self):
        """Test a command, 4 parameters and a comment, make sure they are all returned."""
        gcode_parts = GcodeParts(
            "THECOMMAND param1 param2 param3 param4;The Comment")
        self.assertTrue(gcode_parts.Command == "THECOMMAND")
        self.assertTrue(gcode_parts.Comment == "The Comment")
        self.assertTrue(len(gcode_parts.Parameters) == 4)
        self.assertTrue(gcode_parts.Parameters[0] == "param1")
        self.assertTrue(gcode_parts.Parameters[1] == "param2")
        self.assertTrue(gcode_parts.Parameters[2] == "param3")
        self.assertTrue(gcode_parts.Parameters[3] == "param4")

    def test_CommandParametersAndCommentWhitespace(self):
        """Test a command, 4 parameters and a comment, make sure they are all returned and that the command and
        parameters are trimmed, and that the comment is untrimmed. """
        gcode_parts = GcodeParts(
            "	THECOMMAND		param1   param2  param3 param4		;   The Comment")
        self.assertTrue(gcode_parts.Command == "THECOMMAND")
        self.assertTrue(gcode_parts.Comment == "   The Comment")
        self.assertTrue(len(gcode_parts.Parameters) == 4)
        self.assertTrue(gcode_parts.Parameters[0] == "param1")
        self.assertTrue(gcode_parts.Parameters[1] == "param2")
        self.assertTrue(gcode_parts.Parameters[2] == "param3")
        self.assertTrue(gcode_parts.Parameters[3] == "param4")

    def test_gcode(self):
        """Test a command, make sure the original gcode is stored properly."""
        gcode_parts = GcodeParts(
            "	THECOMMAND		param1   param2  param3 param4		;   The Comment")
        self.assertTrue(
            gcode_parts.Gcode == "	THECOMMAND		param1   param2  param3 param4		;   The Comment")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGcodeParts)
    unittest.TextTestRunner(verbosity=3).run(suite)
