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


def get_printer_profile():
    return {
          "default_firmware_retractions_zhop": False,
          "description": "Genuine Prusa Mk2/Mk2S With Multi-Material",
          "e_axis_default_mode": "require-explicit",
          "g90_influences_extruder": "use-octoprint-settings",
          "movement_speed": 10800.0,
          "home_y": 0,
          "home_x": 0,
          "priming_height": 0.75,
          "min_x": 0.0,
          "guid": "42d2f5ec-7cc8-4d65-aec8-9015ecff7db6",
          "retract_speed": 4800.0,
          "min_y": 0.0,
          "axis_speed_display_units": "mm-min",
          "auto_position_detection_commands": "",
          "name": "Prusa Mk2/Mk2S Multi Material",
          "min_z": 0.0,
          "z_hop_speed": 7200.0,
          "retract_length": 4.0,
          "xyz_axes_default_mode": "require-explicit",
          "snapshot_command": "snap",
          "override_octoprint_profile_settings": False,
          "z_hop": 0.5,
          "deretract_speed": 3000.0,
          "default_firmware_retractions": True,
          "units_default": "millimeters",
          "max_y": 0.0,
          "max_z": 0.0,
          "auto_detect_position": False,
          "max_x": 0.0,
          "home_z": 0
    }

