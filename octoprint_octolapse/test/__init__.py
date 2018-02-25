from octoprint_octolapse.test.test_command import Test_Command
from octoprint_octolapse.test.test_extruder import Test_Extruder
from octoprint_octolapse.test.test_gcodeparts import Test_GcodeParts
from octoprint_octolapse.test.test_position import Test_Position
from octoprint_octolapse.test.test_snapshotGcode import Test_SnapshotGcode
from octoprint_octolapse.test.test_trigger_gcode import Test_GcodeTrigger
from octoprint_octolapse.test.test_trigger_layer import Test_LayerTrigger
from octoprint_octolapse.test.test_trigger_timer import Test_TimerTrigger
from octoprint_octolapse.test.test_utility import Test_Utility
from octoprint_octolapse.test.test_timelapse import Test_Timelapse
from octoprint_octolapse.test.test_octolapseplugin import Test_OctolapsePlugin
import unittest


def TestAll():
    # removed Test_Timelapse from the list for the time being.  This test class is very messed up.
    testClasses = [Test_Command, Test_Extruder, Test_GcodeParts, Test_Position, Test_SnapshotGcode,
                   Test_GcodeTrigger, Test_LayerTrigger, Test_TimerTrigger, Test_Utility, Test_OctolapsePlugin]

    loader = unittest.TestLoader()

    suites_list = []
    for test_class in testClasses:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)

    runner = unittest.TextTestRunner()
    results = runner.run(big_suite)


if __name__ == '__main__':
    TestAll()
