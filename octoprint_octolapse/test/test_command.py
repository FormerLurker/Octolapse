import unittest
from octoprint_octolapse.command import Command,Commands

class Test_Command(unittest.TestCase):
	def setUp(self):
		self.Commands = Commands()
	def tearDown(self):
		del self.Commands

	def test_G0_ParseAll(self):
		"""Try to parse the G0 Command, parameters and comment"""

		# gcode to test
		gcode = "g0 x100 y200.0 z3.0001 e1.1 f7200.000; Here is a comment" # test a lowercase g0 command with all parameters and a comment

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G0")
		self.assertTrue(cmd.Parameters["X"].Value == "100")
		self.assertTrue(cmd.Parameters["Y"].Value == "200.0")
		self.assertTrue(cmd.Parameters["Z"].Value == "3.0001")
		self.assertTrue(cmd.Parameters["E"].Value == "1.1")
		self.assertTrue(cmd.Parameters["F"].Value == "7200")
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

	def test_G0_ParsePartialParameters(self):
		"""Try to parse the G0 Command with only partial parameters and no comment"""

		# gcode to test
		gcode = "g0 y200.0 f7200" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G0")
		self.assertTrue(cmd.Parameters["X"].Value == None)
		self.assertTrue(cmd.Parameters["Y"].Value == "200.0")
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.Parameters["F"].Value == "7200")
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G0_ParsePartialParametersOutOfOrder(self):
		"""Try to parse the G0 Command with out of order parameters and no comment"""

		# gcode to test
		gcode = "g0 f7200 y200.0 X100.0 "

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G0")
		self.assertTrue(cmd.Parameters["X"].Value == "100.0")
		self.assertTrue(cmd.Parameters["Y"].Value == "200.0")
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.Parameters["F"].Value == "7200")
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G0_ParseRepeatParameters(self):
		"""Try to parse the G0 Command with repeating parameters, and what the hell throw in a comment.  The X parameter value should be equal to the first occurance value."""

		# gcode to test
		gcode = "g0   z100     X200.0 X100.0 ; This is a comment  "

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G0")
		self.assertTrue(cmd.Parameters["X"].Value == "200.0")
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value == "100")
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.Parameters["F"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " This is a comment  ")

	def test_G0_ParseNonmatchingParams(self):
		"""Try to parse the G0 Command, parameters and comment.  """

		# gcode to test
		gcode = "g0 x. yA z 1 e. f-; Here is a comment" # test a lowercase g0 command with all parameters and a comment

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G0")
		self.assertTrue(cmd.Parameters["X"].Value is None)
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.Parameters["F"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

	def test_G1_ParseAll(self):
		"""Try to parse the G1 Command, parameters and comment.  """

		# gcode to test
		gcode = "g1 x+0 y-0.0 z-.0001 e. f; Here is a comment" # test a lowercase g1 command with all parameters and a comment

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G1")
		self.assertTrue(cmd.Parameters["X"].Value == "+0")
		self.assertTrue(cmd.Parameters["Y"].Value == "-0.0")
		self.assertTrue(cmd.Parameters["Z"].Value == "-.0001")
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.Parameters["F"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

	def test_G1_ParsePartialParameters(self):
		"""Try to parse the G1 Command with only partial parameters and no comment"""

		# gcode to test
		gcode = "g1 x200.0 e7200" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G1")
		self.assertTrue(cmd.Parameters["X"].Value == "200.0")
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["E"].Value == "7200")
		self.assertTrue(cmd.Parameters["F"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G1_ParsePartialParametersOutOfOrder(self):
		"""Try to parse the G1 Command with out of order parameters and no comment"""

		# gcode to test
		gcode = "g1 e0 z.0 X1 "

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G1")
		self.assertTrue(cmd.Parameters["X"].Value == "1")
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value == ".0")
		self.assertTrue(cmd.Parameters["E"].Value == "0")
		self.assertTrue(cmd.Parameters["F"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G1_ParseRepeatParameters(self):
		"""Try to parse the G1 Command with repeating parameters, and what the hell throw in a comment.  The X parameter value should be equal to the first occurance value."""
		# gcode to test
		gcode = "g1   y1 z2 y3 z4 z5 x6 y7 x8 x9 z10        ; This is a comment  "

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G1")
		self.assertTrue(cmd.Parameters["X"].Value == "6")
		self.assertTrue(cmd.Parameters["Y"].Value == "1")
		self.assertTrue(cmd.Parameters["Z"].Value == "2")
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.Parameters["F"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " This is a comment  ")

	def test_G1_ParseNonmatchingParams(self):
		"""Try to parse the G1 Command, parameters and comment.  """

		# gcode to test
		gcode = "g1 x. yA z 1 e. f-; Here is a comment" # test a lowercase g1 command with all parameters and a comment

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G1")
		self.assertTrue(cmd.Parameters["X"].Value is None)
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.Parameters["F"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

	def test_G92(self):
		"""Try to parse the G92 Command by itself"""

		# gcode to test
		gcode = "g92" # test a lowercase g92 command with all parameters and a comment

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G92")
		self.assertTrue(cmd.Parameters["X"].Value is None)
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G92_ParseAll(self):
		"""Try to parse the G92 Command, parameters and comment.  """

		# gcode to test
		gcode = "g92 x+0 y-0.0 z-.0001 e. ; Here is a comment" # test a lowercase g92 command with all parameters and a comment

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G92")
		self.assertTrue(cmd.Parameters["X"].Value == "+0")
		self.assertTrue(cmd.Parameters["Y"].Value == "-0.0")
		self.assertTrue(cmd.Parameters["Z"].Value == "-.0001")
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

	def test_G92_ParsePartialParameters(self):
		"""Try to parse the G92 Command with only partial parameters and no comment"""

		# gcode to test
		gcode = "g92 x200.0 e7200" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G92")
		self.assertTrue(cmd.Parameters["X"].Value == "200.0")
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["E"].Value == "7200")
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G92_ParsePartialParametersOutOfOrder(self):
		"""Try to parse the G92 Command with out of order parameters and no comment"""

		# gcode to test
		gcode = "g92 e0 z.0 X1 "

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G92")
		self.assertTrue(cmd.Parameters["X"].Value == "1")
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value == ".0")
		self.assertTrue(cmd.Parameters["E"].Value == "0")
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G92_ParseRepeatParameters(self):
		"""Try to parse the G92 Command with repeating parameters, and what the hell throw in a comment.  The X parameter value should be equal to the first occurance value."""
		# gcode to test
		gcode = "g92   y1 z2 y3 z4 z5 x6 y7 x8 x9 z10        ; This is a comment  "

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G92")
		self.assertTrue(cmd.Parameters["X"].Value == "6")
		self.assertTrue(cmd.Parameters["Y"].Value == "1")
		self.assertTrue(cmd.Parameters["Z"].Value == "2")
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " This is a comment  ")

	def test_G92_ParseNonmatchingParams(self):
		"""Try to parse the G92 Command, parameters and comment.  """

		# gcode to test
		gcode = "g92 x. yA z 1 e. f-; Here is a comment"

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G92")
		self.assertTrue(cmd.Parameters["X"].Value is None)
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["E"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

	def test_M82(self):
		"""Try to parse the M82 Command, parameters and comment.  """

		# gcode to test
		gcode = "M82" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M82")

	def test_M82_Comment(self):
		"""Try to parse the M82 Command with a comment and whitespace.  """

		# gcode to test
		gcode = " m82  ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M82")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")

	def test_M82_BadParametersComment(self):
		"""Try to parse the M82 Command with some bogus parameters and a comment with whitespace.  """

		# gcode to test
		gcode = " m82 bogusParam1	bogusParam2    BogusParam3:ff ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M82")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")


	def test_M83(self):
		"""Try to parse the M83 Command, parameters and comment.  """

		# gcode to test
		gcode = "M83" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M83")

	def test_M83_Comment(self):
		"""Try to parse the M83 Command with a comment and whitespace.  """

		# gcode to test
		gcode = " m83  ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M83")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")

	def test_M83_BadParametersComment(self):
		"""Try to parse the M83 Command with some bogus parameters and a comment with whitespace.  """

		# gcode to test
		gcode = " m83 bogusParam1	bogusParam2    BogusParam3:ff ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M83")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")

	def test_G90(self):
		"""Try to parse the G90 Command, parameters and comment.  """

		# gcode to test
		gcode = "G90" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G90")

	def test_G90_Comment(self):
		"""Try to parse the G90 Command with a comment and whitespace.  """

		# gcode to test
		gcode = " g90  ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G90")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")

	def test_G90_BadParametersComment(self):
		"""Try to parse the G90 Command with some bogus parameters and a comment with whitespace.  """

		# gcode to test
		gcode = " g90 bogusParam1	bogusParam2    BogusParam3:ff ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G90")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")

	def test_G91(self):
		"""Try to parse the G91 Command, parameters and comment.  """

		# gcode to test
		gcode = "G91" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G91")

	def test_G91_Comment(self):
		"""Try to parse the G91 Command with a comment and whitespace.  """

		# gcode to test
		gcode = " g91  ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G91")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")

	def test_G91_BadParametersComment(self):
		"""Try to parse the G91 Command with some bogus parameters and a comment with whitespace.  """

		# gcode to test
		gcode = " g91 bogusParam1	bogusParam2    BogusParam3:ff ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G91")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")

	def test_M104(self):
		"""Try to parse the M104 Command"""

		# Test all parameters and comment
		gcode = "m104 s11.223; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M104")
		self.assertTrue(cmd.Parameters["S"].Value == "11.223")
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		# Test all parameters and no comment
		gcode = "M104 s11"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M104")
		self.assertTrue(cmd.Parameters["S"].Value == "11")
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test no parameters and a comment
		gcode = "M104; Here is another comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M104")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is another comment")

		# Test with no comment and no parameters
		gcode = "   M104  "
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M104")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with only bad parameters
		gcode = "   M104  unknownparam"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M104")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with bad parameter and good parameter and comment
		gcode = "   M104  unknownparam s100; comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M104")
		self.assertTrue(cmd.Parameters["S"].Value == "100")
		self.assertTrue(cmd.CommandParts.Comment == " comment")

	def test_M140(self):
		"""Try to parse the M140 Command"""
		# Test all parameters and comment
		gcode = "m140 s11.223 h100; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M140")
		self.assertTrue(cmd.Parameters["S"].Value == "11.223")
		self.assertTrue(cmd.Parameters["H"].Value == "100")
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		# Test all parameters with invalid (no decimal allowed in H param)
		gcode = "m140 s11.223 h100.00; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M140")
		self.assertTrue(cmd.Parameters["S"].Value == "11.223")
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		# Test all parameters and no comment
		gcode = "M140 s11 h200"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M140")
		self.assertTrue(cmd.Parameters["S"].Value == "11")
		self.assertTrue(cmd.Parameters["H"].Value == "200")
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test no parameters and a comment
		gcode = "M140; Here is another comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M140")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is another comment")

		# Test with no comment and no parameters
		gcode = "   M140  "
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M140")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with only bad parameters
		gcode = "   M140  unknownparam"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M140")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with bad parameter and good parameter and comment
		gcode = "   M140 h332 unknownparam s100; comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M140")
		self.assertTrue(cmd.Parameters["S"].Value == "100")
		self.assertTrue(cmd.Parameters["H"].Value == "332")
		self.assertTrue(cmd.CommandParts.Comment == " comment")

	def test_M141(self):
		"""Try to parse the M141 Command"""
		# Test all parameters and comment
		gcode = "m141 s11.223 h100; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M141")
		self.assertTrue(cmd.Parameters["S"].Value == "11.223")
		self.assertTrue(cmd.Parameters["H"].Value == "100")
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		# Test all parameters with invalid (no decimal allowed in H param)
		gcode = "m141 s11.223 h100.00; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M141")
		self.assertTrue(cmd.Parameters["S"].Value == "11.223")
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		# Test all parameters and no comment
		gcode = "M141 s11 h200"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M141")
		self.assertTrue(cmd.Parameters["S"].Value == "11")
		self.assertTrue(cmd.Parameters["H"].Value == "200")
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test no parameters and a comment
		gcode = "M141; Here is another comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M141")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is another comment")

		# Test with no comment and no parameters
		gcode = "   M141  "
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M141")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with only bad parameters
		gcode = "   M141  unknownparam"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M141")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with bad parameter and good parameter and comment
		gcode = "   M141 h332 unknownparam s100; comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M141")
		self.assertTrue(cmd.Parameters["S"].Value == "100")
		self.assertTrue(cmd.Parameters["H"].Value == "332")
		self.assertTrue(cmd.CommandParts.Comment == " comment")

	def test_M109(self):
		"""Try to parse the M109 Command"""
		# Test all parameters and comment
		gcode = "m109 s11.223 r100; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M109")
		self.assertTrue(cmd.Parameters["S"].Value == "11.223")
		self.assertTrue(cmd.Parameters["R"].Value == "100")
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		# Test all parameters and no comment
		gcode = "M109 s11 r200"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M109")
		self.assertTrue(cmd.Parameters["S"].Value == "11")
		self.assertTrue(cmd.Parameters["R"].Value == "200")
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test no parameters and a comment
		gcode = "M109; Here is another comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M109")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["R"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is another comment")

		# Test with no comment and no parameters
		gcode = "   M109  "
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M109")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["R"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with only bad parameters
		gcode = "   M109  unknownparam"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M109")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["R"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with bad parameter and good parameter and comment
		gcode = "   M109 r332 unknownparam s100; comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M109")
		self.assertTrue(cmd.Parameters["S"].Value == "100")
		self.assertTrue(cmd.Parameters["R"].Value == "332")
		self.assertTrue(cmd.CommandParts.Comment == " comment")

	def test_M190(self):
		"""Try to parse the M190 Command"""
		# Test all parameters and comment
		gcode = "m190 s11.223 r100; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M190")
		self.assertTrue(cmd.Parameters["S"].Value == "11.223")
		self.assertTrue(cmd.Parameters["R"].Value == "100")
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		# Test all parameters and no comment
		gcode = "M190 s11 r200"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M190")
		self.assertTrue(cmd.Parameters["S"].Value == "11")
		self.assertTrue(cmd.Parameters["R"].Value == "200")
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test no parameters and a comment
		gcode = "M190; Here is another comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M190")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["R"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is another comment")

		# Test with no comment and no parameters
		gcode = "   M190  "
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M190")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["R"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with only bad parameters
		gcode = "   M190  unknownparam"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M190")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["R"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with bad parameter and good parameter and comment
		gcode = "   M190 r332 unknownparam s100; comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M190")
		self.assertTrue(cmd.Parameters["S"].Value == "100")
		self.assertTrue(cmd.Parameters["R"].Value == "332")
		self.assertTrue(cmd.CommandParts.Comment == " comment")

	def test_M191(self):
		"""Try to parse the M191 Command"""
		# Test all parameters and comment
		gcode = "m191 s11.223 r100; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M191")
		self.assertTrue(cmd.Parameters["S"].Value == "11.223")
		self.assertTrue(cmd.Parameters["R"].Value == "100")
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		
		# Test all parameters and no comment
		gcode = "M191 s11 r200"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M191")
		self.assertTrue(cmd.Parameters["S"].Value == "11")
		self.assertTrue(cmd.Parameters["R"].Value == "200")
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test no parameters and a comment
		gcode = "M191; Here is another comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M191")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["R"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is another comment")

		# Test with no comment and no parameters
		gcode = "   m191  "
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M191")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["R"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with only bad parameters
		gcode = "   M191  unknownparam"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M191")
		self.assertTrue(cmd.Parameters["S"].Value is None)
		self.assertTrue(cmd.Parameters["R"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with bad parameter and good parameter and comment
		gcode = "   M191 r332 unknownparam s100; comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M191")
		self.assertTrue(cmd.Parameters["S"].Value == "100")
		self.assertTrue(cmd.Parameters["R"].Value == "332")
		self.assertTrue(cmd.CommandParts.Comment == " comment")

	def test_M116(self):
		"""Try to parse the M116 Command"""
		# Test all parameters and comment
		gcode = "m116 P11 H22 C33; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M116")
		self.assertTrue(cmd.Parameters["P"].Value == "11")
		self.assertTrue(cmd.Parameters["H"].Value == "22")
		self.assertTrue(cmd.Parameters["C"].Value == "33")
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		# Test all parameters with invalid (no decimal allowed in H param)
		gcode = "m116 p11.1 h22.2 c33.33; Here is a comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M116")
		self.assertTrue(cmd.Parameters["P"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.Parameters["C"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

		# Test all parameters and no comment
		gcode = "m116 P11 H22 C33"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M116")
		self.assertTrue(cmd.Parameters["P"].Value == "11")
		self.assertTrue(cmd.Parameters["H"].Value == "22")
		self.assertTrue(cmd.Parameters["C"].Value == "33")
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test no parameters and a comment
		gcode = "M116; Here is another comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M116")
		self.assertTrue(cmd.Parameters["P"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.Parameters["C"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is another comment")

		# Test with no comment and no parameters
		gcode = "   M116  "
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M116")
		self.assertTrue(cmd.Parameters["P"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.Parameters["C"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with only bad parameters
		gcode = "   M116  unknownparam"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M116")
		self.assertTrue(cmd.Parameters["P"].Value is None)
		self.assertTrue(cmd.Parameters["H"].Value is None)
		self.assertTrue(cmd.Parameters["C"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

		# Test with bad parameter and good parameter and comment
		gcode = "   M116 p11 unknownparam h22 c33; comment"
		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)
		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M116")
		self.assertTrue(cmd.Parameters["P"].Value == "11")
		self.assertTrue(cmd.Parameters["H"].Value == "22")
		self.assertTrue(cmd.Parameters["C"].Value == "33")
		self.assertTrue(cmd.CommandParts.Comment == " comment")


	def test_G28(self):
		"""Try to parse the G28 Command by itself"""

		# gcode to test
		gcode = "g28" # test a lowercase g28 command with all parameters and a comment

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G28")
		self.assertTrue(cmd.Parameters["X"].Value is None)
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["W"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G28_ParseAll(self):
		"""Try to parse the G28 Command, parameters and comment.  """

		# gcode to test
		gcode = "g28 x y z w; Here is a comment" # test a lowercase g28 command with all parameters and a comment

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G28")
		self.assertTrue(cmd.Parameters["X"].Value is not None)
		self.assertTrue(cmd.Parameters["Y"].Value is not None)
		self.assertTrue(cmd.Parameters["Z"].Value is not None)
		self.assertTrue(cmd.Parameters["W"].Value is not None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

	def test_G28_ParsePartialParameters(self):
		"""Try to parse the G28 Command with only partial parameters and no comment"""

		# gcode to test
		gcode = "g28 x z" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G28")
		self.assertTrue(cmd.Parameters["X"].Value is not None)
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is not None)
		self.assertTrue(cmd.Parameters["W"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G28_ParsePartialParametersOutOfOrder(self):
		"""Try to parse the G28 Command with out of order parameters and no comment"""

		# gcode to test
		gcode = "g28 z x y"

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G28")
		self.assertTrue(cmd.Parameters["X"].Value is not None)
		self.assertTrue(cmd.Parameters["Y"].Value is not None)
		self.assertTrue(cmd.Parameters["Z"].Value is not None)
		self.assertTrue(cmd.Parameters["W"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment is None)

	def test_G28_ParseRepeatParameters(self):
		"""Try to parse the G28 Command with repeating parameters, and what the hell throw in a comment.  The X parameter value should be equal to the first occurance value."""
		# gcode to test
		gcode = "g28  x y z x y z z y x    ; This is a comment  "

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G28")
		self.assertTrue(cmd.Parameters["X"].Value is not None)
		self.assertTrue(cmd.Parameters["Y"].Value is not None)
		self.assertTrue(cmd.Parameters["Z"].Value is not None)
		self.assertTrue(cmd.Parameters["W"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " This is a comment  ")

	def test_G28_ParseNonmatchingParams(self):
		"""Try to parse the G28 Command, parameters and comment.  """

		# gcode to test
		gcode = "g28 x a b c d ; Here is a comment"

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G28")
		self.assertTrue(cmd.Parameters["X"].Value is not None)
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["W"].Value is None)
		self.assertTrue(cmd.CommandParts.Comment == " Here is a comment")

	def test_G28_ParseWithWParameter(self):
		"""Try to parse the G28 Command: G28 w"""

		# gcode to test
		gcode = "g28 w"

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "G28")
		self.assertTrue(cmd.Parameters["X"].Value is None)
		self.assertTrue(cmd.Parameters["Y"].Value is None)
		self.assertTrue(cmd.Parameters["Z"].Value is None)
		self.assertTrue(cmd.Parameters["W"].Value is not None)

	def test_M114(self):
		"""Try to parse the M114 Command, parameters and comment.  """

		# gcode to test
		gcode = "M114" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M114")

	def test_M114_Comment(self):
		"""Try to parse the M114 Command with a comment and whitespace.  """

		# gcode to test
		gcode = " m114  ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M114")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")

	def test_M114_BadParametersComment(self):
		"""Try to parse the M114 Command with some bogus parameters and a comment with whitespace.  """

		# gcode to test
		gcode = " m114 bogusParam1	bogusParam2    BogusParam3:ff ; With a comment" 

		# get the command from the gcode
		cmd = self.Commands.GetCommand(gcode)

		# make sure we get the correct command and parameters
		self.assertTrue(cmd.Command == "M114")
		self.assertTrue(cmd.CommandParts.Comment == " With a comment")

	def test_(self):
		# test extrusion removal
		# Send a G0 command without parameters
		self.assertTrue(self.Commands.AlterCommandForTestMode("g0   ; test") == ("G0",))
		# Send a G0 command without extrusion
		self.assertTrue(self.Commands.AlterCommandForTestMode("g0 x100.0 y100.0 z100.0 f7200;no extrusion") == ("G0 X100.0 Y100.0 Z100.0 F7200",))
		# send the same command, but with out of order parameters
		self.assertTrue(self.Commands.AlterCommandForTestMode("g0 f7200   x100.0  y100.0 z100.0;no extrusion") == ("G0 X100.0 Y100.0 Z100.0 F7200",))
		# test without comments
		self.assertTrue(self.Commands.AlterCommandForTestMode("g0 f7200   x100.0  y100.0 z100.0") == ("G0 X100.0 Y100.0 Z100.0 F7200",))
		# Send a G0 command without parameters
		self.assertTrue(self.Commands.AlterCommandForTestMode("g1   ; test") == ("G1",))
		# Send a G1 command with extrusion
		self.assertTrue(self.Commands.AlterCommandForTestMode("g1 x100.0 y100.0 z100.0 e-1.0 f7200;extrusion") == ("G1 X100.0 Y100.0 Z100.0 F7200",))
		# send the same command, but with out of order parameters
		self.assertTrue(self.Commands.AlterCommandForTestMode("g1 e-1.0 f7200    x100.0 y100.0 z100.0 ;extrusion") == ("G1 X100.0 Y100.0 Z100.0 F7200",))
		# test without comments
		self.assertTrue(self.Commands.AlterCommandForTestMode("g1 e-1.0 f7200    x100.0 y100.0 z100.0") == ("G1 X100.0 Y100.0 Z100.0 F7200",))

		# test temp suppression
		#Test M104 with no parameters
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M104"))
		#Test M104 with no parameters and a comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M104 ; Whatsis"))
		#Test M104 with all parameters and comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M104  s100.2 ;no extrusion"))
		#Test M104 with all parameters and no comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M104 S100"))

		#Test M140 with no parameters
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M140"))
		#Test M140 with no parameters and a comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M140 ; Whatsis"))
		#Test M140 with all parameters and comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M140  s100.2 h111;no extrusion"))
		#Test M140 with all parameters and no comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("m140 s100.2 h111 S100"))

		#Test M141 with no parameters
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode(" M141		"))
		#Test M141 with no parameters and a comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M141 ; Whatsis"))
		#Test M141 with all parameters and comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M141  s100.2 H331;no extrusion"))
		#Test M141 with all parameters and no comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M141  H331 S100"))

		#Test M109 with no parameters
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M109"))
		#Test M109 with no parameters and a comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M109 ; Whatsis"))
		#Test M109 with all parameters and comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M109  r2221.333 s100.2 ;no extrusion"))
		#Test M109 with all parameters and no comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M109 S100 r2221.333 "))

		#Test M190 with no parameters
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M190"))
		#Test M190 with no parameters and a comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M190 ; Whatsis"))
		#Test M190 with all parameters and comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M190  r2221.333  s100.2 ;no extrusion"))
		#Test M190 with all parameters and no comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M190 S100 R2221.333 "))

		#Test M191 with no parameters
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M191"))
		#Test M191 with no parameters and a comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M191 ; Whatsis"))
		#Test M191 with all parameters and comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M191  s100.2   r2221.333  ;no extrusion"))
		#Test M191 with all parameters and no comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M191 r2221.333 S100"))

		#Test M116 with no parameters
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M116"))
		#Test M116 with no parameters and a comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M116 ; Whatsis"))
		#Test M116 with all parameters and comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M116 p1 h3232 c122 ;no extrusion"))
		#Test M116 with all parameters and no comment
		self.assertTrue((None,) == self.Commands.AlterCommandForTestMode("M116 c233 h112 p3332"))

		# test all gcodes that are in our CommandsDictionary, but not G0,G1 or temp commands
		self.assertTrue(self.Commands.AlterCommandForTestMode("G2") is None)
		self.assertTrue(self.Commands.AlterCommandForTestMode("G92") is None)
		self.assertTrue(self.Commands.AlterCommandForTestMode("G82") is None)
		self.assertTrue(self.Commands.AlterCommandForTestMode("G28") is None)
		self.assertTrue(self.Commands.AlterCommandForTestMode("G90") is None)
		self.assertTrue(self.Commands.AlterCommandForTestMode("G91") is None)
		self.assertTrue(self.Commands.AlterCommandForTestMode("M114") is None)

		# test some gcodes that are NOT in our CommandsDictionary
		self.assertTrue(self.Commands.AlterCommandForTestMode("NotInOurCommandsCommand1") is None)
		self.assertTrue(self.Commands.AlterCommandForTestMode("NotInOurCommandsCommands ; with a comment") is None)
		self.assertTrue(self.Commands.AlterCommandForTestMode("A random series of letters") is None)
if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_Command)
	unittest.TextTestRunner(verbosity=3).run(suite)
