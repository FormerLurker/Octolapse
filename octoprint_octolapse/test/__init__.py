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

import unittest

from octoprint_octolapse.test.test_command import TestCommand
from octoprint_octolapse.test.test_extruder import TestExtruder
# from octoprint_octolapse.test.test_gcodeparts import TestGcodeParts
from octoprint_octolapse.test.test_octolapseplugin import TestOctolapsePlugin
from octoprint_octolapse.test.test_position import TestPosition
from octoprint_octolapse.test.test_snapshotGcode import TestSnapshotGcode
from octoprint_octolapse.test.test_timelapse import TestTimelapse
from octoprint_octolapse.test.test_trigger import TestTrigger
from octoprint_octolapse.test.test_trigger_gcode import TestGcodeTrigger
from octoprint_octolapse.test.test_trigger_layer import TestLayerTrigger
from octoprint_octolapse.test.test_trigger_timer import TestTimerTrigger
from octoprint_octolapse.test.test_utility import TestUtility
from octoprint_octolapse.test.printers.test_makerbot_replicator_2 import TestMakerbotReplicator2


def test_all():
    # removed Test_Timelapse from the list for the time being.  This test class is very messed up.
    test_classes = [TestCommand, TestExtruder,
                    # TestGcodeParts,
                    TestPosition, TestSnapshotGcode,
                    TestGcodeTrigger, TestLayerTrigger, TestTimerTrigger, TestUtility, TestOctolapsePlugin,
                    TestTrigger, TestMakerbotReplicator2]

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
