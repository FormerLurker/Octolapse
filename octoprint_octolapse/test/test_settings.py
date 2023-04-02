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

from octoprint_octolapse.settings import OctolapseSettings, RenderingProfile

import json
class TestSettings(unittest.TestCase):
    def setUp(self):
        self.octolapse_settings = OctolapseSettings(NamedTemporaryFile().name)

    def tearDown(self):
        pass

    def test_renderingSettings(self):
        rendering = Rendering()
        for k in ['guid', 'name', 'description', 'enabled', 'fps', 'output_format']:
            self.assertIn(k, json.loads(rendering.to_json()))
        rendering.update({'fps': 10})
        self.assertRaises(InvalidSettingsKeyException, lambda: rendering.update({'keyDoesntExist': 'value'}))
