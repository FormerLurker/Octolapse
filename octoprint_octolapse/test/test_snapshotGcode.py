import unittest
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.gcode import SnapshotGcodeGenerator, SnapshotGcode
from octoprint_octolapse.extruder import Extruder

class Test_SnapshotGcode(unittest.TestCase):
	def setUp(self):
		self.Settings = OctolapseSettings("c:\\test\\")
		self.Extruder = Extruder(self.Settings)
	def tearDown(self):
		del self.Settings
		del self.Extruder
	def CreateOctoprintPrinterProfile(self):
		return dict(
				volume = dict(
					width= 250,
					depth= 200,
					height= 200,
					formFactor="Not A Circle",
					custom_box=False,
				)
			)
	def test_GetSnapshotPosition_Absolute(self):
		"""Test getting absolute snapshot positions for x and y"""
		# adjust the settings for absolute position and create the snapshot gcode generator
		self.Settings.CurrentStabilization().x_type = "fixed_coordinate"
		self.Settings.CurrentStabilization().x_fixed_coordinate = 10
		self.Settings.CurrentStabilization().y_type = "fixed_coordinate"
		self.Settings.CurrentStabilization().y_fixed_coordinate = 20
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())

		# get the coordinates and test
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 10 and coords["Y"]==20)
		# get the coordinates and test
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,1)
		self.assertTrue(coords["X"] == 10 and coords["Y"]==20)
		# get the coordinates and test
		coords = snapshotGcodeGenerator.GetSnapshotPosition(100,100)
		self.assertTrue(coords["X"] == 10 and coords["Y"]==20)
	def test_GetSnapshotPosition_AbsolutePath(self):
		"""Test getting absolute path snapshot positions for x and y"""
		# adjust the settings for absolute position and create the snapshot gcode generator
		self.Settings.CurrentStabilization().x_type = "fixed_path"
		self.Settings.CurrentStabilization().x_fixed_path = "0,1,2,3,4,5"
		self.Settings.CurrentStabilization().y_type = "fixed_path"
		self.Settings.CurrentStabilization().y_fixed_path = "5,4,3,2,1,0"
		

		# test with no loop
		self.Settings.CurrentStabilization().x_fixed_path_loop = False
		self.Settings.CurrentStabilization().x_fixed_path_invert_loop = False
		self.Settings.CurrentStabilization().y_fixed_path_loop = False
		self.Settings.CurrentStabilization().y_fixed_path_invert_loop = False
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==5)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 1 and coords["Y"]==4)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,0)
		self.assertTrue(coords["X"] == 2 and coords["Y"]==3)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,1)
		self.assertTrue(coords["X"] == 3 and coords["Y"]==2)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,1)
		self.assertTrue(coords["X"] == 4 and coords["Y"]==1)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 5 and coords["Y"]==0)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 5 and coords["Y"]==0)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 5 and coords["Y"]==0)

		# test with loop, no invert
		self.Settings.CurrentStabilization().x_fixed_path_loop = True
		self.Settings.CurrentStabilization().x_fixed_path_invert_loop = False
		self.Settings.CurrentStabilization().y_fixed_path_loop = True
		self.Settings.CurrentStabilization().y_fixed_path_invert_loop = False
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==5)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 1 and coords["Y"]==4)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,0)
		self.assertTrue(coords["X"] == 2 and coords["Y"]==3)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,1)
		self.assertTrue(coords["X"] == 3 and coords["Y"]==2)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,1)
		self.assertTrue(coords["X"] == 4 and coords["Y"]==1)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 5 and coords["Y"]==0)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==5)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 1 and coords["Y"]==4)

		# test with loop and invert
		self.Settings.CurrentStabilization().x_fixed_path_loop = True
		self.Settings.CurrentStabilization().x_fixed_path_invert_loop = True
		self.Settings.CurrentStabilization().y_fixed_path_loop = True
		self.Settings.CurrentStabilization().y_fixed_path_invert_loop = True
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==5)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 1 and coords["Y"]==4)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,0)
		self.assertTrue(coords["X"] == 2 and coords["Y"]==3)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,1)
		self.assertTrue(coords["X"] == 3 and coords["Y"]==2)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,1)
		self.assertTrue(coords["X"] == 4 and coords["Y"]==1)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 5 and coords["Y"]==0)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 4 and coords["Y"]==1)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 3 and coords["Y"]==2)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 2 and coords["Y"]==3)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 1 and coords["Y"]==4)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==5)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 1 and coords["Y"]==4)
	def test_GetSnapshotPosition_BedRelative(self):
		"""Test getting bed relative snapshot positions for x and y"""
		# adjust the settings for absolute position and create the snapshot gcode generator
		self.Settings.CurrentStabilization().x_type = "relative"
		self.Settings.CurrentStabilization().x_relative = 0
		self.Settings.CurrentStabilization().y_type = "relative"
		self.Settings.CurrentStabilization().y_relative = 100
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())

		# get the coordinates and test
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==200)
		# get the coordinates and test
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,1)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==200)
		# get the coordinates and test
		coords = snapshotGcodeGenerator.GetSnapshotPosition(100,100)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==200)
	def test_GetSnapshotPosition_BedRelativePath(self):
		"""Test getting bed relative path snapshot positions for x and y"""
		# adjust the settings for absolute position and create the snapshot gcode generator
		self.Settings.CurrentStabilization().x_type = "relative_path"
		self.Settings.CurrentStabilization().x_relative_path = "0,25,50,75,100"
		self.Settings.CurrentStabilization().y_type = "relative_path"
		self.Settings.CurrentStabilization().y_relative_path = "100,75,50,25,0"
		


		# test with no loop
		self.Settings.CurrentStabilization().x_relative_path_loop = False
		self.Settings.CurrentStabilization().x_relative_path_invert_loop = False
		self.Settings.CurrentStabilization().y_relative_path_loop = False
		self.Settings.CurrentStabilization().y_relative_path_invert_loop = False
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==200)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 62.5 and coords["Y"]==150)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,0)
		self.assertTrue(coords["X"] == 125 and coords["Y"]==100)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,1)
		self.assertTrue(coords["X"] == 187.5 and coords["Y"]==50)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,1)
		self.assertTrue(coords["X"] == 250 and coords["Y"]==0)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 250 and coords["Y"]==0)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 250 and coords["Y"]==0)
		

		# test with loop, no invert
		self.Settings.CurrentStabilization().x_relative_path_loop = True
		self.Settings.CurrentStabilization().x_relative_path_invert_loop = False
		self.Settings.CurrentStabilization().y_relative_path_loop = True
		self.Settings.CurrentStabilization().y_relative_path_invert_loop = False
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==200)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 62.5 and coords["Y"]==150)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,0)
		self.assertTrue(coords["X"] == 125 and coords["Y"]==100)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,1)
		self.assertTrue(coords["X"] == 187.5 and coords["Y"]==50)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,1)
		self.assertTrue(coords["X"] == 250 and coords["Y"]==0)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==200)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 62.5 and coords["Y"]==150)

		# test with loop and invert
		self.Settings.CurrentStabilization().x_relative_path_loop = True
		self.Settings.CurrentStabilization().x_relative_path_invert_loop = True
		self.Settings.CurrentStabilization().y_relative_path_loop = True
		self.Settings.CurrentStabilization().y_relative_path_invert_loop = True
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 0 and coords["Y"]==200)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 62.5 and coords["Y"]==150)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,0)
		self.assertTrue(coords["X"] == 125 and coords["Y"]==100)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(1,1)
		self.assertTrue(coords["X"] == 187.5 and coords["Y"]==50)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,1)
		self.assertTrue(coords["X"] == 250 and coords["Y"]==0)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 187.5 and coords["Y"]==50)
		coords = snapshotGcodeGenerator.GetSnapshotPosition(0,0)
		self.assertTrue(coords["X"] == 125 and coords["Y"]==100)
	def test_GetSnapshotGcode_Fixed_AbsoluteCoordintes_ExtruderRelative(self):
		"""Test snapshot gcode in absolute coordinate system with relative extruder and fixed coordinate stabilization"""
		# adjust the settings for absolute position and create the snapshot gcode generator
		self.Settings.CurrentStabilization().x_type = "fixed_coordinate"
		self.Settings.CurrentStabilization().x_fixed_coordinate = 10
		self.Settings.CurrentStabilization().y_type = "fixed_coordinate"
		self.Settings.CurrentStabilization().y_fixed_coordinate = 20
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		self.Extruder.IsRetracted = True
		snapshotGcode = snapshotGcodeGenerator.CreateSnapshotGcode(0,0,0,False,True,self.Extruder,"SavedCommand")
		# verify the created gcode
		# this line should switch from absolute to relative for the ZHop
		self.assertTrue(snapshotGcode.GcodeCommands[0] == "G91")
		# this line should zhop by 0.500 mm
		self.assertTrue(snapshotGcode.GcodeCommands[1] == "G1 Z0.500 F7200")
		# this line should switch to absolute coordinates in prep for move
		self.assertTrue(snapshotGcode.GcodeCommands[2] == "G90")
		# this line should switch back to absolute coordinates
		self.assertTrue(snapshotGcode.GcodeCommands[3] == "G1 X10.000 Y20.000 F7200")
		# move back to the return position
		self.assertTrue(snapshotGcode.GcodeCommands[4] == "G1 X0.000 Y0.000 F7200")
		# change to relative coordinates
		self.assertTrue(snapshotGcode.GcodeCommands[5] == "G91")
		# this line should zhop by -0.500 mm
		self.assertTrue(snapshotGcode.GcodeCommands[6] == "G1 Z-0.500 F7200")
		# change back to the original coordinate system (absolute)
		self.assertTrue(snapshotGcode.GcodeCommands[7] == "G90")
		# the saved command
		self.assertTrue(snapshotGcode.GcodeCommands[8] == "SavedCommand")
		# verify the return commands
		self.assertTrue(snapshotGcode.ReturnCommands()[0] == "G1 X0.000 Y0.000 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[1] == "G91")
		self.assertTrue(snapshotGcode.ReturnCommands()[2] == "G1 Z-0.500 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[3] == "G90")
		self.assertTrue(snapshotGcode.ReturnCommands()[4] == "SavedCommand")
		# verify the snapshot commands
		self.assertTrue(snapshotGcode.SnapshotCommands()[0] == "G91")
		self.assertTrue(snapshotGcode.SnapshotCommands()[1] == "G1 Z0.500 F7200")
		self.assertTrue(snapshotGcode.SnapshotCommands()[2] == "G90")
		self.assertTrue(snapshotGcode.SnapshotCommands()[3] == "G1 X10.000 Y20.000 F7200")
		# verify the indexes of the generated gcode
		self.assertTrue(snapshotGcode.SnapshotIndex==3)
		self.assertTrue(snapshotGcode.EndIndex()==8)
		# verify the return coordinates
		self.assertTrue(snapshotGcode.ReturnX == 0)
		self.assertTrue(snapshotGcode.ReturnY == 0)
		self.assertTrue(snapshotGcode.ReturnZ == 0)
	def test_GetSnapshotGcode_RelativePath_RelativeCoordinates_ExtruderAbsolute_ZHop_Retraction(self):
		# test with relative paths, absolute extruder coordinates, retract and z hop
		# use relative coordinates for stabilizations
		self.Settings.CurrentStabilization().x_type = "relative_path"
		self.Settings.CurrentStabilization().x_relative_path = "50,100" #125,250
		self.Settings.CurrentStabilization().x_relative_path_loop = False
		self.Settings.CurrentStabilization().x_relative_path_invert_loop = False
		self.Settings.CurrentStabilization().y_type = "relative_path"
		self.Settings.CurrentStabilization().y_relative_path = "50,100"#100,200
		self.Settings.CurrentStabilization().y_relative_path_loop = False
		self.Settings.CurrentStabilization().y_relative_path_invert_loop = False
		self.Settings.CurrentSnapshot().retract_before_move = True
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		
		
		snapshotGcode = snapshotGcodeGenerator.CreateSnapshotGcode(10,10,10,True,False,self.Extruder,"SavedCommand")
		# verify the created gcode
		# this line should switch to absolute coordinates in prep for move
		

		self.assertTrue(snapshotGcode.GcodeCommands[0] == "M83")
		self.assertTrue(snapshotGcode.GcodeCommands[1] == "G1 E-4.000 F4800")
		self.assertTrue(snapshotGcode.GcodeCommands[2] == "G1 Z0.500 F7200")
		self.assertTrue(snapshotGcode.GcodeCommands[3] == "G90")
		self.assertTrue(snapshotGcode.GcodeCommands[4] == "G1 X125.000 Y100.000 F7200")
		# move back to the return position
		self.assertTrue(snapshotGcode.GcodeCommands[5] == "G1 X10.000 Y10.000 F7200")
		# change to relative coordinates
		self.assertTrue(snapshotGcode.GcodeCommands[6] == "G91")
		self.assertTrue(snapshotGcode.GcodeCommands[7] == "G1 Z-0.500 F7200")
		self.assertTrue(snapshotGcode.GcodeCommands[8] == "G1 E4.000 F4800")
		self.assertTrue(snapshotGcode.GcodeCommands[9] == "M82")
		# the saved command
		self.assertTrue(snapshotGcode.GcodeCommands[10] == "SavedCommand")

		# verify the return commands
		self.assertTrue(snapshotGcode.ReturnCommands()[0] == "G1 X10.000 Y10.000 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[1] == "G91")
		self.assertTrue(snapshotGcode.ReturnCommands()[2] == "G1 Z-0.500 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[3] == "G1 E4.000 F4800")
		self.assertTrue(snapshotGcode.ReturnCommands()[4] == "M82")
		self.assertTrue(snapshotGcode.ReturnCommands()[5] == "SavedCommand")
		# verify the snapshot commands
		self.assertTrue(snapshotGcode.SnapshotCommands()[0] == "M83")
		self.assertTrue(snapshotGcode.SnapshotCommands()[1] == "G1 E-4.000 F4800")
		self.assertTrue(snapshotGcode.SnapshotCommands()[2] == "G1 Z0.500 F7200")
		self.assertTrue(snapshotGcode.SnapshotCommands()[3] == "G90")
		self.assertTrue(snapshotGcode.SnapshotCommands()[4] == "G1 X125.000 Y100.000 F7200")
		# verify the indexes of the generated gcode
		self.assertTrue(snapshotGcode.SnapshotIndex==4)
		self.assertTrue(snapshotGcode.EndIndex()==10)
		# verify the return coordinates
		self.assertTrue(snapshotGcode.ReturnX == 10)
		self.assertTrue(snapshotGcode.ReturnY == 10)
		self.assertTrue(snapshotGcode.ReturnZ == 10)

		# test the second coordinate in the path
		snapshotGcode = snapshotGcodeGenerator.CreateSnapshotGcode(10,10,10,True,False,self.Extruder,"SavedCommand")
		# verify the created gcode
		# this line should switch to absolute coordinates in prep for move

		self.assertTrue(snapshotGcode.GcodeCommands[0] == "M83")
		self.assertTrue(snapshotGcode.GcodeCommands[1] == "G1 E-4.000 F4800")
		self.assertTrue(snapshotGcode.GcodeCommands[2] == "G1 Z0.500 F7200")
		self.assertTrue(snapshotGcode.GcodeCommands[3] == "G90")
		self.assertTrue(snapshotGcode.GcodeCommands[4] == "G1 X250.000 Y200.000 F7200")
		# move back to the return position
		self.assertTrue(snapshotGcode.GcodeCommands[5] == "G1 X10.000 Y10.000 F7200")
		# change to relative coordinates
		self.assertTrue(snapshotGcode.GcodeCommands[6] == "G91")
		self.assertTrue(snapshotGcode.GcodeCommands[7] == "G1 Z-0.500 F7200")
		self.assertTrue(snapshotGcode.GcodeCommands[8] == "G1 E4.000 F4800")
		self.assertTrue(snapshotGcode.GcodeCommands[9] == "M82")
		# the saved command
		self.assertTrue(snapshotGcode.GcodeCommands[10] == "SavedCommand")

		# verify the return commands
		self.assertTrue(snapshotGcode.ReturnCommands()[0] == "G1 X10.000 Y10.000 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[1] == "G91")
		self.assertTrue(snapshotGcode.ReturnCommands()[2] == "G1 Z-0.500 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[3] == "G1 E4.000 F4800")
		self.assertTrue(snapshotGcode.ReturnCommands()[4] == "M82")
		self.assertTrue(snapshotGcode.ReturnCommands()[5] == "SavedCommand")
		# verify the snapshot commands
		self.assertTrue(snapshotGcode.SnapshotCommands()[0] == "M83")
		self.assertTrue(snapshotGcode.SnapshotCommands()[1] == "G1 E-4.000 F4800")
		self.assertTrue(snapshotGcode.SnapshotCommands()[2] == "G1 Z0.500 F7200")
		self.assertTrue(snapshotGcode.SnapshotCommands()[3] == "G90")
		self.assertTrue(snapshotGcode.SnapshotCommands()[4] == "G1 X250.000 Y200.000 F7200")
		# verify the indexes of the generated gcode
		self.assertTrue(snapshotGcode.SnapshotIndex==4)
		self.assertTrue(snapshotGcode.EndIndex()==10)
		# verify the return coordinates
		self.assertTrue(snapshotGcode.ReturnX == 10)
		self.assertTrue(snapshotGcode.ReturnY == 10)
		self.assertTrue(snapshotGcode.ReturnZ == 10)
	def test_GetSnapshotGcode_FixedPath_RelativeCoordinates_ExtruderAbsolute_ZHop_AlreadyRetracted(self):
		# test with relative paths, absolute extruder coordinates, retract and z hop
		# use relative coordinates for stabilizations
		self.Settings.CurrentStabilization().x_type = "fixed_path"
		self.Settings.CurrentStabilization().x_fixed_path = "50,100" #125,250
		self.Settings.CurrentStabilization().x_fixed_path_loop = False
		self.Settings.CurrentStabilization().x_fixed_path_invert_loop = False
		self.Settings.CurrentStabilization().y_type = "fixed_path"
		self.Settings.CurrentStabilization().y_fixed_path = "50,100"#100,200
		self.Settings.CurrentStabilization().y_fixed_path_loop = False
		self.Settings.CurrentStabilization().y_fixed_path_invert_loop = False
		self.Settings.CurrentSnapshot().retract_before_move = True
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		self.Extruder.IsRetracted = True
		snapshotGcode = snapshotGcodeGenerator.CreateSnapshotGcode(100,50,0,True,False,self.Extruder,"SavedCommand")
		# verify the created gcode
		# this line should switch to absolute coordinates in prep for move
		self.assertTrue(snapshotGcode.GcodeCommands[0] == "G1 Z0.500 F7200")
		self.assertTrue(snapshotGcode.GcodeCommands[1] == "G90")
		self.assertTrue(snapshotGcode.GcodeCommands[2] == "G1 X50.000 Y50.000 F7200")
		# move back to the return position
		self.assertTrue(snapshotGcode.GcodeCommands[3] == "G1 X100.000 Y50.000 F7200")
		# change to relative coordinates
		self.assertTrue(snapshotGcode.GcodeCommands[4] == "G91")
		self.assertTrue(snapshotGcode.GcodeCommands[5] == "G1 Z-0.500 F7200")
		# the saved command
		self.assertTrue(snapshotGcode.GcodeCommands[6] == "SavedCommand")
		# verify the return commands
		self.assertTrue(snapshotGcode.ReturnCommands()[0] == "G1 X100.000 Y50.000 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[1] == "G91")
		self.assertTrue(snapshotGcode.ReturnCommands()[2] == "G1 Z-0.500 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[3] == "SavedCommand")
		# verify the snapshot commands
		self.assertTrue(snapshotGcode.SnapshotCommands()[0] == "G1 Z0.500 F7200")
		self.assertTrue(snapshotGcode.SnapshotCommands()[1] == "G90")
		self.assertTrue(snapshotGcode.SnapshotCommands()[2] == "G1 X50.000 Y50.000 F7200")

		# verify the indexes of the generated gcode
		self.assertTrue(snapshotGcode.SnapshotIndex==2)
		self.assertTrue(snapshotGcode.EndIndex()==6)
		# verify the return coordinates
		self.assertTrue(snapshotGcode.ReturnX == 100)
		self.assertTrue(snapshotGcode.ReturnY == 50)
		self.assertTrue(snapshotGcode.ReturnZ == 0)

		# Get the next coordinate in the path
		snapshotGcode = snapshotGcodeGenerator.CreateSnapshotGcode(101,51,0,True,False,self.Extruder,"SavedCommand")
		# verify the created gcode
		# this line should switch to absolute coordinates in prep for move
		self.assertTrue(snapshotGcode.GcodeCommands[0] == "G1 Z0.500 F7200")
		self.assertTrue(snapshotGcode.GcodeCommands[1] == "G90")
		self.assertTrue(snapshotGcode.GcodeCommands[2] == "G1 X100.000 Y100.000 F7200")
		# move back to the return position
		self.assertTrue(snapshotGcode.GcodeCommands[3] == "G1 X101.000 Y51.000 F7200")
		# change to relative coordinates
		self.assertTrue(snapshotGcode.GcodeCommands[4] == "G91")
		self.assertTrue(snapshotGcode.GcodeCommands[5] == "G1 Z-0.500 F7200")
		# the saved command
		self.assertTrue(snapshotGcode.GcodeCommands[6] == "SavedCommand")
		# verify the return commands
		self.assertTrue(snapshotGcode.ReturnCommands()[0] == "G1 X101.000 Y51.000 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[1] == "G91")
		self.assertTrue(snapshotGcode.ReturnCommands()[2] == "G1 Z-0.500 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[3] == "SavedCommand")
		# verify the snapshot commands
		self.assertTrue(snapshotGcode.SnapshotCommands()[0] == "G1 Z0.500 F7200")
		self.assertTrue(snapshotGcode.SnapshotCommands()[1] == "G90")
		self.assertTrue(snapshotGcode.SnapshotCommands()[2] == "G1 X100.000 Y100.000 F7200")
		# verify the indexes of the generated gcode
		self.assertTrue(snapshotGcode.SnapshotIndex==2)
		self.assertTrue(snapshotGcode.EndIndex()==6)
		# verify the return coordinates
		self.assertTrue(snapshotGcode.ReturnX == 101)
		self.assertTrue(snapshotGcode.ReturnY == 51)
		self.assertTrue(snapshotGcode.ReturnZ == 0)
		# test the second coordinate in the path
		snapshotGcode = snapshotGcodeGenerator.CreateSnapshotGcode(10,10,10,True,False,self.Extruder,"SavedCommand")
	def test_GetSnapshotGcode_Relative_RelativeCoordinates_AbsoluteExtruder_ZhopTooHigh(self):
		"""Test snapshot gcode with relative stabilization, relative coordinates, absolute extruder, z is too high to hop, no retraction"""
		
		# test with relative coordinates, absolute extruder coordinates, z hop impossible (current z height will not allow this since it puts things outside of the bounds)
		# use relative coordinates for stabilizations
		self.Settings.CurrentStabilization().x_type = "relative"
		self.Settings.CurrentStabilization().x_relative = 50 #125
		self.Settings.CurrentStabilization().y_type = "relative"
		self.Settings.CurrentStabilization().y_relative = 100 #200
		self.Settings.CurrentSnapshot().retract_before_move = False
		snapshotGcodeGenerator = SnapshotGcodeGenerator(self.Settings,self.CreateOctoprintPrinterProfile())
		# create 
		snapshotGcode = snapshotGcodeGenerator.CreateSnapshotGcode(10,10,200,True,False,self.Extruder,"SavedCommand")
		# verify the created gcode
		# this line should switch to absolute coordinates in prep for move
		self.assertTrue(snapshotGcode.GcodeCommands[0] == "G90")
		# this line should switch back to absolute coordinates
		self.assertTrue(snapshotGcode.GcodeCommands[1] == "G1 X125.000 Y200.000 F7200")
		# move back to the return position
		self.assertTrue(snapshotGcode.GcodeCommands[2] == "G1 X10.000 Y10.000 F7200")
		# change to relative coordinates
		self.assertTrue(snapshotGcode.GcodeCommands[3] == "G91")
		# the saved command
		self.assertTrue(snapshotGcode.GcodeCommands[4] == "SavedCommand")
		# verify the return commands
		self.assertTrue(snapshotGcode.ReturnCommands()[0] == "G1 X10.000 Y10.000 F7200")
		self.assertTrue(snapshotGcode.ReturnCommands()[1] == "G91")
		self.assertTrue(snapshotGcode.ReturnCommands()[2] == "SavedCommand")
		# verify the snapshot commands
		self.assertTrue(snapshotGcode.SnapshotCommands()[0] == "G90")
		self.assertTrue(snapshotGcode.SnapshotCommands()[1] == "G1 X125.000 Y200.000 F7200")
		# verify the indexes of the generated gcode
		self.assertTrue(snapshotGcode.SnapshotIndex==1)
		self.assertTrue(snapshotGcode.EndIndex()==4)
		# verify the return coordinates
		self.assertTrue(snapshotGcode.ReturnX == 10)
		self.assertTrue(snapshotGcode.ReturnY == 10)
		self.assertTrue(snapshotGcode.ReturnZ == 200)

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_SnapshotGcode)
	unittest.TextTestRunner(verbosity=3).run(suite)
