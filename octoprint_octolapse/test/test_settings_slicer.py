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
from tempfile import NamedTemporaryFile
import octoprint_octolapse.settings as settings

class TestSettingsSlicer(unittest.TestCase):

    def test_renderingSettings(self):
        octolapse_settings = settings.OctolapseSettings.create_from("C:\\Temp\\Octolapse\\settings\\settings_feature_detection_test_slic3r.json")
        octolapse_settings_dict = octolapse_settings.to_dict()
        print("Settings as Dict")
        print(octolapse_settings_dict)
        octolapse_settings_json = octolapse_settings.to_json()
        print("Settings as JSON")
        print(octolapse_settings_json)

        test = OctolapseSettings.create_from("c:\\teemp\\temp.log", "unknown", octolapse_settings_dict)
        test = OctolapseSettings.from_json("c:\\teemp\\temp.log", "unknown", octolapse_settings_json)
        print("Complete")

    def test_json_file_load(self):
        file_path = "C:\\Users\\Brad\\AppData\\Roaming\\OctoPrint\\data\\octolapse\\settings.json"
        with open(file_path) as settingsJson:
            data = json.load(settingsJson)
            loaded_settings = OctolapseSettings.create_from("c:\\temp\\temp.log", "0.3.4", data)
            self.assertNotEqual(loaded_settings.profiles.logging[0].name, "Default Logging")
