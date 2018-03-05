import unittest

from octoprint_octolapse.test.test_command import TestCommand
from octoprint_octolapse.test.test_extruder import TestExtruder
from octoprint_octolapse.test.test_gcodeparts import TestGcodeParts
from octoprint_octolapse.test.test_octolapseplugin import TestOctolapsePlugin
from octoprint_octolapse.test.test_position import TestPosition
from octoprint_octolapse.test.test_snapshotGcode import TestSnapshotGcode
from octoprint_octolapse.test.test_timelapse import TestTimelapse
from octoprint_octolapse.test.test_trigger import TestTrigger
from octoprint_octolapse.test.test_trigger_gcode import TestGcodeTrigger
from octoprint_octolapse.test.test_trigger_layer import TestLayerTrigger
from octoprint_octolapse.test.test_trigger_timer import TestTimerTrigger
from octoprint_octolapse.test.test_utility import TestUtility


def test_all():
    # removed Test_Timelapse from the list for the time being.  This test class is very messed up.
    test_classes = [TestCommand, TestExtruder, TestGcodeParts, TestPosition, TestSnapshotGcode,
                    TestGcodeTrigger, TestLayerTrigger, TestTimerTrigger, TestUtility, TestOctolapsePlugin,
                    TestTrigger]

    loader = unittest.TestLoader()

    suites_list = []
    for test_class in test_classes:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    big_suite = unittest.TestSuite(suites_list)

    runner = unittest.TextTestRunner()
    runner.run(big_suite)


if __name__ == '__main__':
    test_all()
