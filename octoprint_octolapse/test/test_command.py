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
		gcode = "g0 x100 y200.0 z3.0001 e1.1 f7200; Here is a comment" # test a lowercase g0 command with all parameters and a comment

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

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_Command)
	unittest.TextTestRunner(verbosity=3).run(suite)
