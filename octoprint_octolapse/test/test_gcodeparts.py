import unittest
from octoprint_octolapse.command import GcodeParts


class Test_GcodeParts(unittest.TestCase):

    def test_NullCommand(self):
        """Using None for your gcode will result in both the comand and the comment being None, with no parameters"""

        gcodeParts = GcodeParts(None)
        self.assertTrue(gcodeParts.Command is None)
        self.assertTrue(gcodeParts.Comment is None)
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_SemicolonOnly(self):
        """If only a semicolon is given, the command should be None and the comment should be the empty string, with no parameters"""
        gcodeParts = GcodeParts(";")
        self.assertTrue(gcodeParts.Command is None)
        self.assertTrue(gcodeParts.Comment == "")
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_CommentOnly(self):
        """Ensure that gcode consisting of only a semicolon and a comment contain a null command, the comment, and no parameters"""
        gcodeParts = GcodeParts(";Here is a comment")
        self.assertTrue(gcodeParts.Command is None)
        self.assertTrue(gcodeParts.Comment == "Here is a comment")
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_WhitespaceAndComment(self):
        """Ensure that gcode consisting of whitespace,a semicolon and a comment contain a null command, the comment, and no parameters"""
        gcodeParts = GcodeParts(
            "			;Here is a comment preceeded by spaces and tabs.")
        self.assertTrue(gcodeParts.Command is None)
        self.assertTrue(gcodeParts.Comment ==
                        "Here is a comment preceeded by spaces and tabs.")
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_CommandOnly(self):
        """Ensure that gcode with a command only (no parameters or coments) returns the command, a null comment, and no parameters"""
        gcodeParts = GcodeParts("THECOMMAND")
        self.assertTrue(gcodeParts.Command == "THECOMMAND")
        self.assertTrue(gcodeParts.Comment is None)
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_CommandOnlyWhitespaceBefore(self):
        """Ensure that gcode with a command only (no parameters or coments) preceeded by whitespace returns the command, a null comment, and no parameters"""
        gcodeParts = GcodeParts("		THECOMMANDWITHTABSANDSPACES")
        self.assertTrue(gcodeParts.Command == "THECOMMANDWITHTABSANDSPACES")
        self.assertTrue(gcodeParts.Comment is None)
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_CommandOnlyWhitespaceAfter(self):
        """Ensure that gcode with a command only (no parameters or coments) followed by whitespace returns the command, a null comment, and no parameters"""
        gcodeParts = GcodeParts("THECOMMANDWITHTABSANDSPACESAFTER		     ")
        self.assertTrue(gcodeParts.Command ==
                        "THECOMMANDWITHTABSANDSPACESAFTER")
        self.assertTrue(gcodeParts.Comment is None)
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_CommandOnlyWhitespaceBeforeAndAfter(self):
        """Ensure that gcode with a command only (no parameters or coments) preceeded and followed by whitespace returns the command, a null comment, and no parameters"""
        gcodeParts = GcodeParts(
            "		  THECOMMANDWITHTABSANDSPACESBEFOREANDAFTER		     ")
        self.assertTrue(gcodeParts.Command ==
                        "THECOMMANDWITHTABSANDSPACESBEFOREANDAFTER")
        self.assertTrue(gcodeParts.Comment is None)
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_CommandAndComment(self):
        """Ensure that gcode with a command and a comment return both the command, the comment, and no parameters."""
        gcodeParts = GcodeParts("THECOMMAND;The Comment")
        self.assertTrue(gcodeParts.Command == "THECOMMAND")
        self.assertTrue(gcodeParts.Comment == "The Comment")
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_CommandAndCommentWhitespace(self):
        """Ensure that gcode with a command, a comment, and whitespace around both the command and comment returns the trimmed command and the untrimmed comment with no parameters."""
        gcodeParts = GcodeParts("	THECOMMAND	;	The Comment		")
        self.assertTrue(gcodeParts.Command == "THECOMMAND")
        self.assertTrue(gcodeParts.Comment == "	The Comment		")
        self.assertTrue(len(gcodeParts.Parameters) == 0)

    def test_CommandAndParameters(self):
        """Test a command and a single parameter without comments, make sure they are returned and that the comment is None."""
        gcodeParts = GcodeParts("THECOMMAND param1")
        self.assertTrue(gcodeParts.Command == "THECOMMAND")
        self.assertTrue(gcodeParts.Comment is None)
        self.assertTrue(len(gcodeParts.Parameters) == 1)
        self.assertTrue(gcodeParts.Parameters[0] == "param1")

    def test_CommandAndParameters(self):
        """Test a command and 4 parameters without comments, make sure they are returned and that the comment is None."""
        gcodeParts = GcodeParts("THECOMMAND param1 param2 param3 param4")
        self.assertTrue(gcodeParts.Command == "THECOMMAND")
        self.assertTrue(gcodeParts.Comment is None)
        self.assertTrue(len(gcodeParts.Parameters) == 4)
        self.assertTrue(gcodeParts.Parameters[0] == "param1")
        self.assertTrue(gcodeParts.Parameters[1] == "param2")
        self.assertTrue(gcodeParts.Parameters[2] == "param3")
        self.assertTrue(gcodeParts.Parameters[3] == "param4")

    def test_CommandAndParametersWhitespace(self):
        """Test a command and 4 parameters without comments including extra whitespace.  Make sure they are returned and trimmed, and that the comment is None."""
        gcodeParts = GcodeParts(
            "	 THECOMMAND		param1  param2 param3	param4   ")
        self.assertTrue(gcodeParts.Command == "THECOMMAND")
        self.assertTrue(gcodeParts.Comment is None)
        self.assertTrue(len(gcodeParts.Parameters) == 4)
        self.assertTrue(gcodeParts.Parameters[0] == "param1")
        self.assertTrue(gcodeParts.Parameters[1] == "param2")
        self.assertTrue(gcodeParts.Parameters[2] == "param3")
        self.assertTrue(gcodeParts.Parameters[3] == "param4")

    def test_CommandParametersAndComment(self):
        """Test a command, 4 parameters and a comment, make sure they are all returned."""
        gcodeParts = GcodeParts(
            "THECOMMAND param1 param2 param3 param4;The Comment")
        self.assertTrue(gcodeParts.Command == "THECOMMAND")
        self.assertTrue(gcodeParts.Comment == "The Comment")
        self.assertTrue(len(gcodeParts.Parameters) == 4)
        self.assertTrue(gcodeParts.Parameters[0] == "param1")
        self.assertTrue(gcodeParts.Parameters[1] == "param2")
        self.assertTrue(gcodeParts.Parameters[2] == "param3")
        self.assertTrue(gcodeParts.Parameters[3] == "param4")

    def test_CommandParametersAndCommentWhitespace(self):
        """Test a command, 4 parameters and a comment, make sure they are all returned and that the command and parameters are trimmed, and that the comment is untrimmed."""
        gcodeParts = GcodeParts(
            "	THECOMMAND		param1   param2  param3 param4		;   The Comment")
        self.assertTrue(gcodeParts.Command == "THECOMMAND")
        self.assertTrue(gcodeParts.Comment == "   The Comment")
        self.assertTrue(len(gcodeParts.Parameters) == 4)
        self.assertTrue(gcodeParts.Parameters[0] == "param1")
        self.assertTrue(gcodeParts.Parameters[1] == "param2")
        self.assertTrue(gcodeParts.Parameters[2] == "param3")
        self.assertTrue(gcodeParts.Parameters[3] == "param4")

    def test_gcode(self):
        """Test a command, make sure the original gcode is stored properly."""
        gcodeParts = GcodeParts(
            "	THECOMMAND		param1   param2  param3 param4		;   The Comment")
        self.assertTrue(
            gcodeParts.Gcode == "	THECOMMAND		param1   param2  param3 param4		;   The Comment")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test_GcodeParts)
    unittest.TextTestRunner(verbosity=3).run(suite)
