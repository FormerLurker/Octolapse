import unittest
import octoprint_octolapse.utility as utility


class Test_Utility(unittest.TestCase):
	def setUp(self):
		self.OctoprintPrinterProfile = self.CreateOctoprintPrinterProfile()

	def tearDown(self):
		del self.OctoprintPrinterProfile

	def CreateOctoprintPrinterProfile(self):
		return {
			"volume": {
				"custom_box":False,
				"width": 250,
				"depth": 200,
				"height": 200
			}
		}

	def test_IsInBounds(self):
		"""Test the IsInBounds function to make sure the program will not attempt to operate after being told to move out of bounds."""

		# Initial test, should return false without any coordinates
		self.assertTrue(not utility.IsInBounds(None, None, None, self.OctoprintPrinterProfile))

		# test the origin (min), should return true
		self.assertTrue(utility.IsInBounds(0, 0, 0, self.OctoprintPrinterProfile))

		# move X out of bounds of the min
		self.assertTrue(not utility.IsInBounds(-0.0001, 0, 0, self.OctoprintPrinterProfile))
		# move X out of bounds of the max
		self.assertTrue(not utility.IsInBounds(250.0001, 0, 0, self.OctoprintPrinterProfile))
		# move X to the max of bounds of the max
		self.assertTrue(utility.IsInBounds(250.0000, 0, 0, self.OctoprintPrinterProfile))

		# move Y out of bounds of the min
		self.assertTrue(not utility.IsInBounds(0, -0.0001, 0, self.OctoprintPrinterProfile))
		# move Y out of bounds of the max
		self.assertTrue(not utility.IsInBounds(0, 200.0001, 0, self.OctoprintPrinterProfile))
		# move Y to the max of bounds of the max
		self.assertTrue(utility.IsInBounds(0, 200.0000, 0, self.OctoprintPrinterProfile))

		# move Z out of bounds of the min
		self.assertTrue(not utility.IsInBounds(0, 0, -0.0001, self.OctoprintPrinterProfile))
		# move Z out of bounds of the max
		self.assertTrue(not utility.IsInBounds(0, 0, 200.0001, self.OctoprintPrinterProfile))
		# move Z to the max of bounds of the max
		self.assertTrue(utility.IsInBounds(0, 0, 200.0000, self.OctoprintPrinterProfile))

	def test_IsInBounds_CustomBox(self):
		
		"""Test the IsInBounds function to make sure the program will not attempt to operate after being told to move out of bounds."""
		# test custom box with values above zero
		customBox = {
			"volume": {
				"custom_box": {
					"x_min": 1,
					"x_max": 200,
					"y_min": 1,
					"y_max": 200,
					"z_min": 1,
					"z_max": 200
				}
			}
		}

		# Initial test, should return false without any coordinates
		self.assertTrue(not utility.IsInBounds(None, None, None, customBox))

		# test the origin (min), should return false
		self.assertTrue(not utility.IsInBounds(0, 0, 0, customBox))

		# test 1,1,1 - True
		self.assertTrue(utility.IsInBounds(1, 1, 1, customBox))


		# move X out of bounds - Min
		self.assertTrue(not utility.IsInBounds(.9999, 1, 1, customBox))
		# move X out of bounds - Max
		self.assertTrue(not utility.IsInBounds(200.0001, 1, 1, customBox))
		# move X in bounds - Max
		self.assertTrue(utility.IsInBounds(200.0000, 1, 1, customBox))
		# move X in bounds - Middle
		self.assertTrue(utility.IsInBounds(100.5000, 1, 1, customBox))

		# move Y out of bounds - Min
		self.assertTrue(not utility.IsInBounds(1,.9999, 1, customBox))
		# move Y out of bounds - Max
		self.assertTrue(not utility.IsInBounds(1,200.0001, 1, customBox))
		# move Y in bounds - Max
		self.assertTrue(utility.IsInBounds(1,200.0000, 1, customBox))
		# move Y in bounds - Middle
		self.assertTrue(utility.IsInBounds(1,100.5000, 1, customBox))

		# move Z out of bounds - Min
		self.assertTrue(not utility.IsInBounds(1, 1, .9999, customBox))
		# move Z out of bounds - Max
		self.assertTrue(not utility.IsInBounds(1, 1, 200.0001, customBox))
		# move Z in bounds - Max
		self.assertTrue(utility.IsInBounds(1, 1, 200.0000, customBox))
		# move Z in bounds - Middle
		self.assertTrue(utility.IsInBounds(1, 1, 100.5000, customBox))

		
		# test custom box with negative min values
		customBox = {
			"volume": {
				"custom_box": {
					"x_min": -1,
					"x_max": 250,
					"y_min": -2,
					"y_max": 200,
					"z_min": -3,
					"z_max": 200
				}
			}
		}
		# move X out of bounds - Min
		self.assertTrue(not utility.IsInBounds(-1.0001, 1, 1, customBox))
		# move X out of bounds - Max
		self.assertTrue(not utility.IsInBounds(250.0001, 1, 1, customBox))
		# move X in bounds - Max
		self.assertTrue(utility.IsInBounds(250.0000, 1, 1, customBox))
		# move X in bounds - Middle
		self.assertTrue(utility.IsInBounds(123.5000, 1, 1, customBox))

		# move Y out of bounds - Min
		self.assertTrue(not utility.IsInBounds(1,-2.0001, 1, customBox))
		# move Y out of bounds - Max
		self.assertTrue(not utility.IsInBounds(1,200.0001, 1, customBox))
		# move Y in bounds - Max
		self.assertTrue(utility.IsInBounds(1,200.0000, 1, customBox))
		# move Y in bounds - Middle
		self.assertTrue(utility.IsInBounds(1,99.0000, 1, customBox))

		# move Z out of bounds - Min
		self.assertTrue(not utility.IsInBounds(1, 1, -3.0001, customBox))
		# move Z out of bounds - Max
		self.assertTrue(not utility.IsInBounds(1, 1, 200.0001, customBox))
		# move Z in bounds - Max
		self.assertTrue(utility.IsInBounds(1, 1, 200.0000, customBox))
		# move Z in bounds - Middle
		self.assertTrue(utility.IsInBounds(1, 1, 98.5000, customBox))


		# test custom box with all negative min values
		customBox = {
			"volume": {
				"custom_box": {
					"x_min": -100,
					"x_max": -50,
					"y_min": -100,
					"y_max": -50,
					"z_min": -100,
					"z_max": -50
				}
			}
		}
		# test X axis
		# move out of bounds - Min
		self.assertTrue(not utility.IsInBounds(-100.0001, -100, -100, customBox))
		# move out of bounds - Max
		self.assertTrue(not utility.IsInBounds(-49.9999, -100, -100, customBox))
		# move in bounds - Max
		self.assertTrue(utility.IsInBounds(-50.0000, -100, -100, customBox))
		# move in bounds - Middle
		self.assertTrue(utility.IsInBounds(-75.0000, -100, -100, customBox))

		# test Y axis
		# move out of bounds - Min
		self.assertTrue(not utility.IsInBounds(-100,-100.0001, -100, customBox))
		# move out of bounds - Max
		self.assertTrue(not utility.IsInBounds(-100,-49.9999, -100, customBox))
		# move in bounds - Max
		self.assertTrue(utility.IsInBounds(-100,-50.0000, -100, customBox))
		# move in bounds - Middle
		self.assertTrue(utility.IsInBounds(-100,-75.0000, -100, customBox))
		
		# test Z axis
		# move out of bounds - Min
		self.assertTrue(not utility.IsInBounds(-100, -100, -100.0001, customBox))
		# move out of bounds - Max
		self.assertTrue(not utility.IsInBounds(-100, -100,-49.9999, customBox))
		# move in bounds - Max
		self.assertTrue(utility.IsInBounds(-100, -100,-50.0000, customBox))
		# move in bounds - Middle
		self.assertTrue(utility.IsInBounds(-100, -100,-75.0000, customBox))

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_Utility)
	nittest.TextTestRunner(verbosity=3).run(suite)

