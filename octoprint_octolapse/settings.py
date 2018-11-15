# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2017  Brad Hochgesang
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

import json
import logging
import math
import sys
import uuid
from datetime import datetime

import concurrent
from octoprint.plugin import PluginSettings

import octoprint_octolapse.utility as utility
from octoprint_octolapse.gcode_parser import Commands
PROFILE_SNAPSHOT_GCODE_TYPE = "gcode"


class PrintFeatureSetting(object):
    def __init__(self, speed_callback, layer_name, initial_layer_name, speed, under_speed, enabled, enabled_for_slow_layer):
        self.layer_name = layer_name
        self.slow_layer_name = initial_layer_name
        self.speed = speed
        self.under_speed = under_speed
        self._speed_callback = speed_callback
        self.enabled = enabled
        self.enabled_for_slow_layer = enabled_for_slow_layer
        self.calculated_speed = None
        self.calculated_layer_name = layer_name
        self.triggered = False
        self.detected = False

    def update(self, speed, num_slow_layers, layer_num, tolerance):
        self.detected = False
        self.triggered = False
        if layer_num == 0:
            layer_num = 1
        self.calculated_speed, self.calculated_layer_name = self._speed_callback(
            self.layer_name, self.slow_layer_name, self.speed, self.under_speed, num_slow_layers, layer_num
        )

        if self.calculated_speed is not None and utility.is_close(speed, self.calculated_speed, tolerance):
            self.detected = True
            if (self.enabled and num_slow_layers < layer_num) or self.enabled_for_slow_layer:
                self.triggered = True


def calculate_speed(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs):
    if speed is None:
        return None, layer_name

    if (
        layer_num is None
        or num_slow_layers < 1
        or layer_num > num_slow_layers
        or speed == under_speed
        or under_speed is None
    ):
        return speed, layer_name
    # calculate an underspeed
    return (
        under_speed + ((layer_num - 1) * (speed - under_speed) / num_slow_layers)
        , slow_layer_name
    )


def calculate_speed_slic3r_pe(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs):
    return calculate_speed(layer_name, slow_layer_name, speed, under_speed, 1, layer_num, *args, **kwargs)


def calculate_speed_cura(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs):
    return calculate_speed(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs)


def calculate_speed_simplify_3d(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs):
    return calculate_speed(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs)


class SlicerPrintFeatures(object):
    def __init__(self, printer_profile, snapshot_profile):
        assert(isinstance(printer_profile, Printer))
        assert (isinstance(snapshot_profile, Snapshot))

        self.speed_units = printer_profile.axis_speed_display_units
        self.num_slow_layers = printer_profile.num_slow_layers
        self.speed_tolerance = printer_profile.get_speed_tolerance_for_slicer_type()
        self.feature_detection_enabled = snapshot_profile.feature_restrictions_enabled
        self.features = []

        if printer_profile.slicer_type == 'other':
            self.create_other_slicer_feature_list(printer_profile, snapshot_profile)
        elif printer_profile.slicer_type == 'slic3r-pe':
            self.create_slic3r_pe_feature_list(printer_profile, snapshot_profile)
        elif printer_profile.slicer_type == 'cura':
            self.create_cura_feature_list(printer_profile, snapshot_profile)
        elif printer_profile.slicer_type == 'simplify-3d':
            self.create_simplify_3d_feature_list(printer_profile, snapshot_profile)

    def create_other_slicer_feature_list(self, printer_profile, snapshot_profile):
        movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed,
                "Movement",
                "Movement",
                movement_speed,
                movement_speed,
                snapshot_profile.feature_trigger_on_movement,
                snapshot_profile.feature_trigger_on_movement))

        z_movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.z_hop_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed,
                "Z Movement",
                "Z Movement",
                z_movement_speed,
                z_movement_speed,
                snapshot_profile.feature_trigger_on_z_movement,
                snapshot_profile.feature_trigger_on_z_movement))

        retract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Retraction",
                "Retraction",
                retract_speed,
                retract_speed,
                snapshot_profile.feature_trigger_on_retract,
                snapshot_profile.feature_trigger_on_retract))
        detract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.detract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Detraction",
                "Detraction",
                detract_speed,
                detract_speed,
                snapshot_profile.feature_trigger_on_detract,
                snapshot_profile.feature_trigger_on_detract))
        print_speed = printer_profile.get_speed_for_slicer_type(printer_profile.print_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Normal Print Speed",
                "Normal Print Speed",
                print_speed,
                print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed))
        perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Perimeters",
                "Perimeters",
                perimeter_speed,
                perimeter_speed,
                snapshot_profile.feature_trigger_on_perimeters,
                snapshot_profile.feature_trigger_on_perimeters))
        small_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.small_perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Small Perimeters",
                "Small Perimeters",
                small_perimeter_speed,
                small_perimeter_speed,
                snapshot_profile.feature_trigger_on_small_perimeters,
                snapshot_profile.feature_trigger_on_small_perimeters))
        external_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.external_perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "External Perimeters",
                "External Perimeters",
                external_perimeter_speed,
                external_perimeter_speed,
                snapshot_profile.feature_trigger_on_external_perimeters,
                snapshot_profile.feature_trigger_on_external_perimeters))

        infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Infill",
                "Infill",
                infill_speed,
                infill_speed,
                snapshot_profile.feature_trigger_on_infill,
                snapshot_profile.feature_trigger_on_infill))

        solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.solid_infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Solid Infill",
                "Solid Infill",
                solid_infill_speed,
                solid_infill_speed,
                snapshot_profile.feature_trigger_on_solid_infill,
                snapshot_profile.feature_trigger_on_solid_infill))

        top_solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.top_solid_infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Top Solid Infill",
                "Top Solid Infill",
                top_solid_infill_speed,
                top_solid_infill_speed,
                snapshot_profile.feature_trigger_on_top_solid_infill,
                snapshot_profile.feature_trigger_on_top_solid_infill))

        support_speed = printer_profile.get_speed_for_slicer_type(printer_profile.support_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Supports",
                "Supports",
                support_speed,
                support_speed,
                snapshot_profile.feature_trigger_on_supports,
                snapshot_profile.feature_trigger_on_supports))

        bridge_speed = printer_profile.get_speed_for_slicer_type(printer_profile.bridge_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Bridges",
                "Bridges",
                bridge_speed,
                bridge_speed,
                snapshot_profile.feature_trigger_on_bridges,
                snapshot_profile.feature_trigger_on_bridges))

        gap_fill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.gap_fill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Gap Fills",
                "Gap Fills",
                gap_fill_speed,
                gap_fill_speed,
                snapshot_profile.feature_trigger_on_gap_fills,
                snapshot_profile.feature_trigger_on_gap_fills))

        first_layer_speed = printer_profile.get_speed_for_slicer_type(printer_profile.first_layer_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "First Layer",
                "First Layer",
                first_layer_speed,
                first_layer_speed,
                snapshot_profile.feature_trigger_on_first_layer,
                snapshot_profile.feature_trigger_on_first_layer))

        above_raft_speed = printer_profile.get_speed_for_slicer_type(printer_profile.above_raft_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Above Raft",
                "Above Raft",
                above_raft_speed,
                above_raft_speed,
                snapshot_profile.feature_trigger_on_above_raft,
                snapshot_profile.feature_trigger_on_above_raft))

        ooze_shield_speed = printer_profile.get_speed_for_slicer_type(printer_profile.ooze_shield_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Ooze Shield",
                "Ooze Shield",
                ooze_shield_speed,
                ooze_shield_speed,
                snapshot_profile.feature_trigger_on_ooze_shield,
                snapshot_profile.feature_trigger_on_ooze_shield))

        prime_pillar_speed = printer_profile.get_speed_for_slicer_type(printer_profile.prime_pillar_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Prime Pillar",
                "Prime Pillar",
                prime_pillar_speed,
                prime_pillar_speed,
                snapshot_profile.feature_trigger_on_prime_pillar,
                snapshot_profile.feature_trigger_on_prime_pillar))

        skirt_brim_speed = printer_profile.get_speed_for_slicer_type(printer_profile.above_raft_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Skirt/Brim",
                "Skirt/Brim",
                skirt_brim_speed,
                skirt_brim_speed,
                snapshot_profile.feature_trigger_on_skirt_brim,
                snapshot_profile.feature_trigger_on_skirt_brim))

    def create_slic3r_pe_feature_list(self, printer_profile, snapshot_profile):

        # The retract and detract speeds are rounded to the nearest int
        retract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed, "retract_speed")
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Retraction",
                "Retraction",
                retract_speed,
                retract_speed,
                snapshot_profile.feature_trigger_on_retract,
                snapshot_profile.feature_trigger_on_retract))

        detract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.detract_speed, "detract_speed")
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Detraction",
                "Detraction",
                detract_speed,
                detract_speed,
                snapshot_profile.feature_trigger_on_detract,
                snapshot_profile.feature_trigger_on_detract))

        perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.perimeter_speed)
        perimeter_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.perimeter_speed, printer_profile.first_layer_speed_multiplier)
        # Perimeter Speed Feature
        perimeter_speed_feature = PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Perimeters",
                "Perimeters",
                perimeter_speed,
                perimeter_speed,
                snapshot_profile.feature_trigger_on_perimeters,
                snapshot_profile.feature_trigger_on_perimeters)
        if perimeter_underspeed:
            # there is a first layer speed multiplier so scale the current speed
            perimeter_speed_feature.slow_layer_name = "First Layer Perimeters"
            perimeter_speed_feature.under_speed = perimeter_underspeed
            perimeter_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_perimeters and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(perimeter_speed_feature)

        # Small Perimeter Feature
        small_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.small_perimeter_speed)
        small_perimeter_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.small_perimeter_speed, printer_profile.first_layer_speed_multiplier)
        small_perimeter_speed_feature = PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Small Perimeters",
                "Small Perimeters",
                small_perimeter_speed,
                small_perimeter_speed,
                snapshot_profile.feature_trigger_on_small_perimeters,
                snapshot_profile.feature_trigger_on_small_perimeters)
        if small_perimeter_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            small_perimeter_speed_feature.slow_layer_name = "First Layer Small Perimeters"
            small_perimeter_speed_feature.under_speed = small_perimeter_underspeed
            small_perimeter_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_small_perimeters and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(small_perimeter_speed_feature)

        # External Perimeter Feature
        external_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.external_perimeter_speed)
        external_perimeter_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.external_perimeter_speed, printer_profile.first_layer_speed_multiplier)
        external_perimeter_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "External Perimeters",
            "External Perimeters",
            external_perimeter_speed,
            external_perimeter_speed,
            snapshot_profile.feature_trigger_on_external_perimeters,
            snapshot_profile.feature_trigger_on_external_perimeters)
        if external_perimeter_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            external_perimeter_speed_feature.slow_layer_name = "First Layer External Perimeters"
            external_perimeter_speed_feature.under_speed = external_perimeter_underspeed
            external_perimeter_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_external_perimeters and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(external_perimeter_speed_feature)

        # infill Feature
        infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.infill_speed)
        infill_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.infill_speed, printer_profile.first_layer_speed_multiplier)
        infill_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Infill",
            "Infill",
            infill_speed,
            infill_speed,
            snapshot_profile.feature_trigger_on_infill,
            snapshot_profile.feature_trigger_on_infill)
        if infill_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            infill_speed_feature.slow_layer_name = "First Layer Infill"
            infill_speed_feature.under_speed = infill_underspeed
            infill_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_infill and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(infill_speed_feature)

        # solid_infill Feature
        solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.solid_infill_speed)
        solid_infill_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.solid_infill_speed, printer_profile.first_layer_speed_multiplier)
        solid_infill_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Solid Infill",
            "Solid Infill",
            solid_infill_speed,
            solid_infill_speed,
            snapshot_profile.feature_trigger_on_solid_infill,
            snapshot_profile.feature_trigger_on_solid_infill)
        if solid_infill_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            solid_infill_speed_feature.slow_layer_name = "First Layer Solid Infill"
            solid_infill_speed_feature.under_speed = solid_infill_underspeed
            solid_infill_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_solid_infill and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(solid_infill_speed_feature)

        top_solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.top_solid_infill_speed)
        top_solid_infill_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.top_solid_infill_speed, printer_profile.first_layer_speed_multiplier)
        # top top_solid_infill Feature
        top_solid_infill_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Top Solid Infill",
            "Top Solid Infill",
            top_solid_infill_speed,
            top_solid_infill_speed,
            snapshot_profile.feature_trigger_on_top_solid_infill,
            snapshot_profile.feature_trigger_on_top_solid_infill)
        if top_solid_infill_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            top_solid_infill_speed_feature.slow_layer_name = "First Layer Top Solid Infill"
            top_solid_infill_speed_feature.under_speed = top_solid_infill_underspeed
            top_solid_infill_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_top_solid_infill and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(top_solid_infill_speed_feature)

        # support Feature
        support_speed = printer_profile.get_speed_for_slicer_type(printer_profile.support_speed)
        support_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.support_speed, printer_profile.first_layer_speed_multiplier)
        support_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Supports",
            "Supports",
            support_speed,
            support_speed,
            snapshot_profile.feature_trigger_on_supports,
            snapshot_profile.feature_trigger_on_supports)
        if support_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            support_speed_feature.slow_layer_name = "First Layer Supports"
            support_speed_feature.under_speed = support_underspeed
            support_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_supports and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(support_speed_feature)

        # bridge Feature
        bridge_speed = printer_profile.get_speed_for_slicer_type(printer_profile.bridge_speed)
        bridge_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Bridges",
            "Bridges",
            bridge_speed,
            bridge_speed,
            snapshot_profile.feature_trigger_on_bridges,
            snapshot_profile.feature_trigger_on_bridges)
        self.features.append(bridge_speed_feature)

        # gaps Feature
        gap_fill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.gap_fill_speed)
        gap_fill_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.gap_fill_speed, printer_profile.first_layer_speed_multiplier)
        gap_fill_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Gaps",
            "Gaps",
            gap_fill_speed,
            gap_fill_speed,
            snapshot_profile.feature_trigger_on_gap_fills,
            snapshot_profile.feature_trigger_on_gap_fills)
        if gap_fill_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            gap_fill_speed_feature.slow_layer_name = "First Layer Gaps"
            gap_fill_speed_feature.under_speed = gap_fill_underspeed
            gap_fill_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_gap_fills and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(gap_fill_speed_feature)

        movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Movement",
                "Movement",
                movement_speed,
                movement_speed,
                snapshot_profile.feature_trigger_on_movement,
                snapshot_profile.feature_trigger_on_movement))

        wipe_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed * 0.8)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Wipe",
                "Wipe",
                wipe_speed,
                wipe_speed,
                snapshot_profile.feature_trigger_on_wipe,
                snapshot_profile.feature_trigger_on_wipe))

        if printer_profile.first_layer_speed_multiplier is None:
            first_layer_speed = printer_profile.get_speed_for_slicer_type(printer_profile.first_layer_speed)
            self.features.append(
                PrintFeatureSetting(
                    calculate_speed_slic3r_pe,
                    "First Layer",
                    "First Layer Speed",
                    first_layer_speed,
                    first_layer_speed,
                    snapshot_profile.feature_trigger_on_first_layer,
                    snapshot_profile.feature_trigger_on_first_layer))

    def create_cura_feature_list(self, printer_profile, snapshot_profile):
        print_speed = printer_profile.get_speed_for_slicer_type(printer_profile.print_speed)
        slow_layer_speed = printer_profile.get_speed_for_slicer_type(printer_profile.first_layer_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Print Speed",
                "Slow Layer Print Speed",
                print_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed and snapshot_profile.feature_trigger_on_first_layer))

        retract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Retract",
                "Retract",
                retract_speed,
                retract_speed,
                snapshot_profile.feature_trigger_on_retract,
                snapshot_profile.feature_trigger_on_retract and snapshot_profile.feature_trigger_on_first_layer))

        prime_speed = printer_profile.get_speed_for_slicer_type(printer_profile.detract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Prime",
                "Prime",
                prime_speed,
                prime_speed,
                snapshot_profile.feature_trigger_on_detract,
                snapshot_profile.feature_trigger_on_detract and snapshot_profile.feature_trigger_on_first_layer))

        infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Infill",
                "Slow Layer Infill",
                infill_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_infill,
                snapshot_profile.feature_trigger_on_infill and snapshot_profile.feature_trigger_on_first_layer))

        external_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.external_perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Outer Wall",
                "Slow Layer Outer Wall",
                external_perimeter_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_external_perimeters,
                snapshot_profile.feature_trigger_on_external_perimeters and snapshot_profile.feature_trigger_on_first_layer))

        perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Inner Wall",
                "Slow Layer Inner Wall",
                perimeter_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_perimeters,
                snapshot_profile.feature_trigger_on_perimeters and snapshot_profile.feature_trigger_on_first_layer))

        top_solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.top_solid_infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Top/Bottom",
                "Slow Layer Top/Bottom",
                top_solid_infill_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_top_solid_infill,
                snapshot_profile.feature_trigger_on_top_solid_infill and snapshot_profile.feature_trigger_on_first_layer))

        travel_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed)
        slow_travel_speed = printer_profile.get_speed_for_slicer_type(printer_profile.first_layer_travel_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Travel",
                "Slow Layer Travel",
                travel_speed,
                slow_travel_speed,
                snapshot_profile.feature_trigger_on_movement,
                snapshot_profile.feature_trigger_on_movement and snapshot_profile.feature_trigger_on_first_layer_travel))

        skirt_brim_speed = printer_profile.get_speed_for_slicer_type(printer_profile.skirt_brim_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Skirt/Brim",
                "Skirt/Brim",
                skirt_brim_speed,
                skirt_brim_speed,
                snapshot_profile.feature_trigger_on_skirt_brim,
                snapshot_profile.feature_trigger_on_skirt_brim))

        z_travel_speed = printer_profile.get_speed_for_slicer_type(printer_profile.z_hop_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Z Travel",
                "Z Travel",
                z_travel_speed,
                z_travel_speed,
                snapshot_profile.feature_trigger_on_z_movement,
                snapshot_profile.feature_trigger_on_z_movement))

    def create_simplify_3d_feature_list(self, printer_profile, snapshot_profile):

        retract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Retraction",
                "Retraction",
                retract_speed,
                retract_speed,
                snapshot_profile.feature_trigger_on_retract,
                snapshot_profile.feature_trigger_on_retract))

        above_raft_speed = printer_profile.get_speed_for_slicer_type(printer_profile.above_raft_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Above Raft",
                "Above Raft",
                above_raft_speed,
                above_raft_speed,
                snapshot_profile.feature_trigger_on_above_raft,
                snapshot_profile.feature_trigger_on_above_raft))

        prime_pillar_speed = printer_profile.get_speed_for_slicer_type(printer_profile.prime_pillar_speed)
        first_layer_prime_pillar_speed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.prime_pillar_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Prime Pillar",
                "First Layer Prime Pillar",
                prime_pillar_speed,
                first_layer_prime_pillar_speed,
                snapshot_profile.feature_trigger_on_prime_pillar,
                snapshot_profile.feature_trigger_on_prime_pillar and snapshot_profile.feature_trigger_on_first_layer))

        ooze_shield_speed =  printer_profile.get_speed_for_slicer_type(printer_profile.ooze_shield_speed)
        first_layer_ooze_shield_speed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.ooze_shield_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Ooze Shield",
                "First Layer Ooze Shield",
                ooze_shield_speed,
                first_layer_ooze_shield_speed,
                snapshot_profile.feature_trigger_on_ooze_shield,
                snapshot_profile.feature_trigger_on_ooze_shield and snapshot_profile.feature_trigger_on_first_layer))

        print_speed = printer_profile.get_speed_for_slicer_type(printer_profile.print_speed)
        first_layer_print_speed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.print_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Printing Speed",
                "First Layer Printing Speed",
                print_speed,
                first_layer_print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed and snapshot_profile.feature_trigger_on_first_layer))

        external_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.external_perimeter_speed)
        first_layer_external_perimeter_speed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.external_perimeter_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Exterior Outlines",
                "First Layer Exterior Outlines",
                external_perimeter_speed,
                first_layer_external_perimeter_speed,
                snapshot_profile.feature_trigger_on_external_perimeters,
                snapshot_profile.feature_trigger_on_external_perimeters and snapshot_profile.feature_trigger_on_first_layer))

        perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.perimeter_speed)
        first_layer_perimeter_speed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.perimeter_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Interior Outlines",
                "First Layer Interior Outlines",
                perimeter_speed,
                first_layer_perimeter_speed,
                snapshot_profile.feature_trigger_on_perimeters,
                snapshot_profile.feature_trigger_on_perimeters and snapshot_profile.feature_trigger_on_first_layer))

        solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.solid_infill_speed)
        first_layer_solid_infill_speed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.solid_infill_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Solid Infill",
                "First Layer Solid Infill",
                solid_infill_speed,
                first_layer_solid_infill_speed,
                snapshot_profile.feature_trigger_on_solid_infill,
                snapshot_profile.feature_trigger_on_solid_infill and snapshot_profile.feature_trigger_on_first_layer))

        support_speed = printer_profile.get_speed_for_slicer_type(printer_profile.support_speed)
        first_layer_support_speed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.support_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Supports",
                "First Layer Supports",
                support_speed,
                first_layer_support_speed,
                snapshot_profile.feature_trigger_on_supports,
                snapshot_profile.feature_trigger_on_supports and snapshot_profile.feature_trigger_on_first_layer))

        xy_movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "X/Y Movement",
                "X/Y Movement",
                xy_movement_speed,
                xy_movement_speed,
                snapshot_profile.feature_trigger_on_movement,
                snapshot_profile.feature_trigger_on_movement))

        z_movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.z_hop_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Z Movement",
                "Z Movement",
                z_movement_speed,
                z_movement_speed,
                snapshot_profile.feature_trigger_on_z_movement,
                snapshot_profile.feature_trigger_on_z_movement))

        bridge_speed = printer_profile.get_speed_for_slicer_type(printer_profile.bridge_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Bridging",
                "Bridging",
                bridge_speed,
                bridge_speed,
                snapshot_profile.feature_trigger_on_bridges,
                snapshot_profile.feature_trigger_on_bridges))

        first_prime_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed * 0.3)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "First Prime",
                "First Prime",
                first_prime_speed,
                first_prime_speed,
                snapshot_profile.feature_trigger_on_detract and snapshot_profile.feature_trigger_on_first_layer,
                snapshot_profile.feature_trigger_on_detract and snapshot_profile.feature_trigger_on_first_layer))

    def update(self, speed, layer_num):
        for feature in self.features:
            assert (isinstance(feature, PrintFeatureSetting))
            feature.update(speed, self.num_slow_layers, layer_num, self.speed_tolerance)

    def is_one_feature_enabled(self):
        if not self.feature_detection_enabled:
            return True

        for feature in self.features:
            assert (isinstance(feature, PrintFeatureSetting))
            if feature.triggered:
                return True
        return False

    def get_printing_features_list(self):
        printing_features = []
        if self.feature_detection_enabled:
            for feature in self.features:
                assert (isinstance(feature, PrintFeatureSetting))
                if feature.detected:
                    printing_features.append(feature.calculated_layer_name)
        if len(printing_features) == 0:
            printing_features = []
        return printing_features


class Printer(object):
    # Globals
    # feture names

    def __init__(self, printer=None, name="New Printer", guid=None):
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        # flag that is false until the profile has been saved by the user at least once
        # this is used to show a warning to the user if a new printer profile is used
        # without being configured
        self.has_been_saved_by_user = False

        # Slicer Settings
        self.slicer_type = "other"
        self.retract_length = 2.0
        self.retract_speed = 6000
        self.detract_speed = 3000
        self.movement_speed = 6000
        self.z_hop = .5
        self.z_hop_speed = 6000
        self.retract_speed = 4000
        # misc speeds
        self.maximum_z_speed = None
        self.print_speed = None
        self.perimeter_speed = None
        self.small_perimeter_speed = None
        self.external_perimeter_speed = None
        self.infill_speed = None
        self.solid_infill_speed = None
        self.top_solid_infill_speed = None
        self.support_speed = None
        self.bridge_speed = None
        self.gap_fill_speed = None
        self.first_layer_speed = None
        self.first_layer_travel_speed = None
        self.skirt_brim_speed = None
        self.above_raft_speed = None
        self.ooze_shield_speed = None
        self.prime_pillar_speed = None
        self.speed_tolerance = 0.6
        self.num_slow_layers = 0;
        # simplify 3d/slic3r speed multipliers
        self.first_layer_speed_multiplier = 100
        self.above_raft_speed_multiplier = 100
        self.prime_pillar_speed_multiplier = 100
        self.ooze_shield_speed_multiplier = 100
        self.outline_speed_multiplier = 100
        self.solid_infill_speed_multiplier = 100
        self.support_structure_speed_multiplier = 100
        self.bridging_speed_multiplier = 100
        self.small_perimeter_speed_multiplier = 100
        self.external_perimeter_speed_multiplier = 100
        self.top_solid_infill_speed_multiplier = 100
        # Slic3r only settings - Percent or mm/s text
        self.small_perimeter_speed_text = None
        self.external_perimeter_speed_text = None
        self.solid_infill_speed_text = None
        self.top_solid_infill_speed_text = None
        self.first_layer_speed_text = None

        self.snapshot_command = "snap"
        self.suppress_snapshot_command_always = True
        self.printer_position_confirmation_tolerance = 0.001
        self.auto_detect_position = True
        self.origin_x = None
        self.origin_y = None
        self.origin_z = None
        self.abort_out_of_bounds = True
        self.override_octoprint_print_volume = False
        self.min_x = 0.0
        self.max_x = 0.0
        self.min_y = 0.0
        self.max_y = 0.0
        self.min_z = 0.0
        self.max_z = 0.0
        self.auto_position_detection_commands = ""
        self.priming_height = 0.75
        self.e_axis_default_mode = 'require-explicit'  # other values are 'relative' and 'absolute'
        self.g90_influences_extruder = 'use-octoprint-settings'  # other values are 'true' and 'false'
        self.xyz_axes_default_mode = 'require-explicit'  # other values are 'relative' and 'absolute'
        self.units_default = 'millimeters'
        self.axis_speed_display_units = 'mm-min'
        self.default_firmware_retractions = False
        self.default_firmware_retractions_zhop = False
        if printer is not None:
            if isinstance(printer, Printer):
                self.guid = printer.guid
                self.name = printer.name
                self.description = printer.description
                self.has_been_saved_by_user = printer.has_been_saved_by_user
                self.slicer_type = printer.slicer_type
                self.retract_length = printer.retract_length
                self.retract_speed = printer.retract_speed
                self.detract_speed = printer.detract_speed
                self.movement_speed = printer.movement_speed
                self.z_hop = printer.z_hop
                self.z_hop_speed = printer.z_hop_speed
                self.maximum_z_speed = printer.maximum_z_speed
                self.print_speed = printer.print_speed
                self.perimeter_speed = printer.perimeter_speed
                self.small_perimeter_speed = printer.small_perimeter_speed
                self.external_perimeter_speed = printer.external_perimeter_speed
                self.infill_speed = printer.infill_speed
                self.solid_infill_speed = printer.solid_infill_speed
                self.top_solid_infill_speed = printer.top_solid_infill_speed
                self.support_speed = printer.support_speed
                self.bridge_speed = printer.bridge_speed
                self.gap_fill_speed = printer.gap_fill_speed
                self.first_layer_speed = printer.first_layer_speed
                self.first_layer_travel_speed = printer.first_layer_travel_speed
                self.skirt_brim_speed = printer.skirt_brim_speed
                self.above_raft_speed = printer.above_raft_speed
                self.ooze_shield_speed = printer.ooze_shield_speed
                self.prime_pillar_speed = printer.prime_pillar_speed
                self.speed_tolerance = printer.speed_tolerance
                self.num_slow_layers = printer.num_slow_layers
                # print speed multipliers
                self.first_layer_speed_multiplier = printer.first_layer_speed_multiplier
                self.above_raft_speed_multiplier = printer.above_raft_speed_multiplier
                self.prime_pillar_speed_multiplier = printer.prime_pillar_speed_multiplier
                self.ooze_shield_speed_multiplier = printer.ooze_shield_speed_multiplier
                self.outline_speed_multiplier = printer.outline_speed_multiplier
                self.solid_infill_speed_multiplier = printer.solid_infill_speed_multiplier
                self.support_structure_speed_multiplier = printer.support_structure_speed_multiplier
                self.bridging_speed_multiplier = printer.bridging_speed_multiplier
                self.small_perimeter_speed_multiplier = printer.small_perimeter_speed_multiplier
                self.external_perimeter_speed_multiplier = printer.external_perimeter_speed_multiplier
                self.top_solid_infill_speed_multiplier = printer.top_solid_infill_speed_multiplier
                # Slic3r only settings - Percent or mm/s text
                self.small_perimeter_speed_text = printer.small_perimeter_speed_text
                self.external_perimeter_speed_text = printer.external_perimeter_speed_text
                self.solid_infill_speed_text = printer.solid_infill_speed_text
                self.top_solid_infill_speed_text = printer.top_solid_infill_speed_text
                self.first_layer_speed_text = printer.first_layer_speed_text

                self.snapshot_command = printer.snapshot_command
                self.suppress_snapshot_command_always = printer.suppress_snapshot_command_always
                self.printer_position_confirmation_tolerance = printer.printer_position_confirmation_tolerance
                self.auto_detect_position = printer.auto_detect_position
                self.auto_position_detection_commands = printer.auto_position_detection_commands
                self.origin_x = printer.origin_x
                self.origin_y = printer.origin_y
                self.origin_z = printer.origin_z
                self.abort_out_of_bounds = printer.abort_out_of_bounds
                self.override_octoprint_print_volume = printer.override_octoprint_print_volume
                self.min_x = printer.min_x
                self.max_x = printer.max_x
                self.min_y = printer.min_y
                self.max_y = printer.max_y
                self.min_z = printer.min_z
                self.max_z = printer.max_z
                self.priming_height = printer.priming_height
                self.e_axis_default_mode = printer.e_axis_default_mode
                self.g90_influences_extruder = printer.g90_influences_extruder
                self.xyz_axes_default_mode = printer.xyz_axes_default_mode
                self.units_default = printer.units_default
                self.axis_speed_display_units = printer.axis_speed_display_units
                self.default_firmware_retractions = printer.default_firmware_retractions
                self.default_firmware_retractions_zhop = printer.default_firmware_retractions_zhop

            else:
                self.update(printer)

    def update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        if "has_been_saved_by_user" in changes.keys():
            self.has_been_saved_by_user = utility.get_bool(
                changes["has_been_saved_by_user"], self.has_been_saved_by_user)
        if "slicer_type" in changes.keys():
            self.slicer_type = utility.get_string(
                changes["slicer_type"], self.slicer_type)
        if "retract_length" in changes.keys():
            self.retract_length = utility.get_float(
                changes["retract_length"], self.retract_length)
        if "retract_speed" in changes.keys():
            self.retract_speed = utility.get_float(
                changes["retract_speed"], self.retract_speed)
        if "detract_speed" in changes.keys():
            self.detract_speed = utility.get_float(
                changes["detract_speed"], self.detract_speed)
        if "movement_speed" in changes.keys():
            self.movement_speed = utility.get_float(
                changes["movement_speed"], self.movement_speed)
        if "perimeter_speed" in changes.keys():
            self.perimeter_speed = utility.get_nullable_float(
                changes["perimeter_speed"], self.perimeter_speed)
        if "small_perimeter_speed" in changes.keys():
            self.small_perimeter_speed = utility.get_nullable_float(
                changes["small_perimeter_speed"], self.small_perimeter_speed)
        if "external_perimeter_speed" in changes.keys():
            self.external_perimeter_speed = utility.get_nullable_float(
                changes["external_perimeter_speed"], self.external_perimeter_speed)
        if "infill_speed" in changes.keys():
            self.infill_speed = utility.get_nullable_float(
                changes["infill_speed"], self.infill_speed)
        if "solid_infill_speed" in changes.keys():
            self.solid_infill_speed = utility.get_nullable_float(
                changes["solid_infill_speed"], self.solid_infill_speed)
        if "top_solid_infill_speed" in changes.keys():
            self.top_solid_infill_speed = utility.get_nullable_float(
                changes["top_solid_infill_speed"], self.top_solid_infill_speed)
        if "support_speed" in changes.keys():
            self.support_speed = utility.get_nullable_float(
                changes["support_speed"], self.support_speed)
        if "bridge_speed" in changes.keys():
            self.bridge_speed = utility.get_nullable_float(
                changes["bridge_speed"], self.bridge_speed)
        if "gap_fill_speed" in changes.keys():
            self.gap_fill_speed = utility.get_nullable_float(
                changes["gap_fill_speed"], self.gap_fill_speed)
        if "first_layer_speed" in changes.keys():
            self.first_layer_speed = utility.get_nullable_float(
                changes["first_layer_speed"], self.first_layer_speed)

        if "first_layer_travel_speed" in changes.keys():
            self.first_layer_travel_speed = utility.get_nullable_float(
                changes["first_layer_travel_speed"], self.first_layer_travel_speed)
        if "skirt_brim_speed" in changes.keys():
            self.skirt_brim_speed = utility.get_nullable_float(
                changes["skirt_brim_speed"], self.skirt_brim_speed)
        if "above_raft_speed" in changes.keys():
            self.above_raft_speed = utility.get_nullable_float(
                changes["above_raft_speed"], self.above_raft_speed)
        if "ooze_shield_speed" in changes.keys():
            self.ooze_shield_speed = utility.get_nullable_float(
                changes["ooze_shield_speed"], self.ooze_shield_speed)
        if "prime_pillar_speed" in changes.keys():
            self.prime_pillar_speed = utility.get_nullable_float(
                changes["prime_pillar_speed"], self.prime_pillar_speed)
        if "speed_tolerance" in changes.keys():
            self.speed_tolerance = utility.get_float(
                changes["speed_tolerance"], self.speed_tolerance)

        if "num_slow_layers" in changes.keys():
            self.num_slow_layers = utility.get_int(
                changes["num_slow_layers"], self.num_slow_layers)

        # simplify 3d speed multipliers
        if "first_layer_speed_multiplier" in changes.keys():
            self.first_layer_speed_multiplier = utility.get_nullable_float(
                changes["first_layer_speed_multiplier"], self.first_layer_speed_multiplier)
        if "above_raft_speed_multiplier" in changes.keys():
            self.above_raft_speed_multiplier = utility.get_nullable_float(
                changes["above_raft_speed_multiplier"], self.above_raft_speed_multiplier)
        if "prime_pillar_speed_multiplier" in changes.keys():
            self.prime_pillar_speed_multiplier = utility.get_nullable_float(
                changes["prime_pillar_speed_multiplier"], self.prime_pillar_speed_multiplier)
        if "ooze_shield_speed_multiplier" in changes.keys():
            self.ooze_shield_speed_multiplier = utility.get_nullable_float(
                changes["ooze_shield_speed_multiplier"], self.ooze_shield_speed_multiplier)
        if "outline_speed_multiplier" in changes.keys():
            self.outline_speed_multiplier = utility.get_nullable_float(
                changes["outline_speed_multiplier"], self.outline_speed_multiplier)
        if "solid_infill_speed_multiplier" in changes.keys():
            self.solid_infill_speed_multiplier = utility.get_nullable_float(
                changes["solid_infill_speed_multiplier"], self.solid_infill_speed_multiplier)
        if "support_structure_speed_multiplier" in changes.keys():
            self.support_structure_speed_multiplier = utility.get_nullable_float(
                changes["support_structure_speed_multiplier"], self.support_structure_speed_multiplier)
        if "bridging_speed_multiplier" in changes.keys():
            self.bridging_speed_multiplier = utility.get_nullable_float(
                changes["bridging_speed_multiplier"], self.bridging_speed_multiplier)

        if "small_perimeter_speed_multiplier" in changes.keys():
            self.small_perimeter_speed_multiplier = utility.get_nullable_float(
                changes["small_perimeter_speed_multiplier"], self.small_perimeter_speed_multiplier)
        if "external_perimeter_speed_multiplier" in changes.keys():
            self.external_perimeter_speed_multiplier = utility.get_nullable_float(
                changes["external_perimeter_speed_multiplier"], self.external_perimeter_speed_multiplier)
        if "top_solid_infill_speed_multiplier" in changes.keys():
            self.top_solid_infill_speed_multiplier = utility.get_nullable_float(
                changes["top_solid_infill_speed_multiplier"], self.top_solid_infill_speed_multiplier)

        # Slic3r only settings - Percent or mm/s text
        if "small_perimeter_speed_text" in changes.keys():
            # note that the snapshot command is stripped of comments.
            self.small_perimeter_speed_text = utility.get_string(
                changes["small_perimeter_speed_text"], self.small_perimeter_speed_text)
        if "external_perimeter_speed_text" in changes.keys():
            # note that the snapshot command is stripped of comments.
            self.external_perimeter_speed_text = utility.get_string(
                changes["external_perimeter_speed_text"], self.external_perimeter_speed_text)
        if "solid_infill_speed_text" in changes.keys():
            # note that the snapshot command is stripped of comments.
            self.solid_infill_speed_text = utility.get_string(
                changes["solid_infill_speed_text"], self.solid_infill_speed_text)
        if "top_solid_infill_speed_text" in changes.keys():
            # note that the snapshot command is stripped of comments.
            self.top_solid_infill_speed_text = utility.get_string(
                changes["top_solid_infill_speed_text"], self.top_solid_infill_speed_text)
        if "first_layer_speed_text" in changes.keys():
            # note that the snapshot command is stripped of comments.
            self.first_layer_speed_text = utility.get_string(
                changes["first_layer_speed_text"], self.first_layer_speed_text)

        if "snapshot_command" in changes.keys():
            # note that the snapshot command is stripped of comments.
            self.snapshot_command = utility.get_string(
                Commands.strip_comments(changes["snapshot_command"]), self.snapshot_command)
        if "suppress_snapshot_command_always" in changes.keys():
            self.suppress_snapshot_command_always = utility.get_bool(
                changes["suppress_snapshot_command_always"], self.suppress_snapshot_command_always)
        if "z_hop" in changes.keys():
            self.z_hop = utility.get_float(changes["z_hop"], self.z_hop)
        if "z_hop_speed" in changes.keys():
            self.z_hop_speed = utility.get_float(
                changes["z_hop_speed"], self.z_hop_speed)
        if "maximum_z_speed" in changes.keys():
            self.maximum_z_speed = utility.get_float(
                changes["maximum_z_speed"], self.maximum_z_speed)
        if "print_speed" in changes.keys():
            self.print_speed = utility.get_float(
                changes["print_speed"], self.print_speed)

        if "printer_position_confirmation_tolerance" in changes.keys():
            self.printer_position_confirmation_tolerance = utility.get_float(
                changes["printer_position_confirmation_tolerance"], self.printer_position_confirmation_tolerance)
        if "auto_position_detection_commands" in changes.keys():
            self.auto_position_detection_commands = utility.get_string(
                changes["auto_position_detection_commands"], self.auto_position_detection_commands)
        if "auto_detect_position" in changes.keys():
            self.auto_detect_position = utility.get_bool(
                changes["auto_detect_position"], self.auto_detect_position)
        if "origin_x" in changes.keys():
            self.origin_x = utility.get_nullable_float(
                changes["origin_x"], self.origin_x)
        if "origin_y" in changes.keys():
            self.origin_y = utility.get_nullable_float(
                changes["origin_y"], self.origin_y)
        if "origin_z" in changes.keys():
            self.origin_z = utility.get_nullable_float(
                changes["origin_z"], self.origin_z)
        if "abort_out_of_bounds" in changes.keys():
            self.abort_out_of_bounds = utility.get_bool(
                changes["abort_out_of_bounds"], self.abort_out_of_bounds)
        if "override_octoprint_print_volume" in changes.keys():
            self.override_octoprint_print_volume = utility.get_bool(
                changes["override_octoprint_print_volume"], self.override_octoprint_print_volume)
        if "min_x" in changes.keys():
            self.min_x = utility.get_float(changes["min_x"], self.min_x)
        if "max_x" in changes.keys():
            self.max_x = utility.get_float(changes["max_x"], self.max_x)
        if "min_y" in changes.keys():
            self.min_y = utility.get_float(changes["min_y"], self.min_y)
        if "max_y" in changes.keys():
            self.max_y = utility.get_float(changes["max_y"], self.max_y)
        if "min_z" in changes.keys():
            self.min_z = utility.get_float(changes["min_z"], self.min_z)
        if "max_z" in changes.keys():
            self.max_z = utility.get_float(changes["max_z"], self.max_z)
        if "priming_height" in changes.keys():
            self.priming_height = utility.get_float(changes["priming_height"], self.priming_height)
        if "e_axis_default_mode" in changes.keys():
            self.e_axis_default_mode = utility.get_string(
                changes["e_axis_default_mode"], self.e_axis_default_mode)
        if "g90_influences_extruder" in changes.keys():
            self.g90_influences_extruder = utility.get_string(
                changes["g90_influences_extruder"], self.g90_influences_extruder)
        if "xyz_axes_default_mode" in changes.keys():
            self.xyz_axes_default_mode = utility.get_string(
                changes["xyz_axes_default_mode"], self.xyz_axes_default_mode)
        if "units_default" in changes.keys():
            self.units_default = utility.get_string(
                changes["units_default"], self.units_default
            )
        if "axis_speed_display_units" in changes.keys():
            self.axis_speed_display_units = utility.get_string(
                changes["axis_speed_display_units"], self.axis_speed_display_units
            )
        if "default_firmware_retractions" in changes.keys():
            self.default_firmware_retractions = utility.get_bool(
                changes["default_firmware_retractions"], self.default_firmware_retractions
            )
        if "default_firmware_retractions_zhop" in changes.keys():
            self.default_firmware_retractions_zhop = utility.get_bool(
                changes["default_firmware_retractions_zhop"], self.default_firmware_retractions_zhop
            )

    def to_dict(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'has_been_saved_by_user': self.has_been_saved_by_user,
            'slicer_type': self.slicer_type,
            'retract_length': self.retract_length,
            'retract_speed': self.retract_speed,
            'detract_speed': self.detract_speed,
            'movement_speed': self.movement_speed,
            'z_hop': self.z_hop,
            'z_hop_speed': self.z_hop_speed,
            'maximum_z_speed': self.maximum_z_speed,
            'print_speed': self.print_speed,
            'perimeter_speed': self.perimeter_speed,
            'small_perimeter_speed': self.small_perimeter_speed,
            'external_perimeter_speed': self.external_perimeter_speed,
            'infill_speed': self.infill_speed,
            'solid_infill_speed': self.solid_infill_speed,
            'top_solid_infill_speed': self.top_solid_infill_speed,
            'support_speed': self.support_speed,
            'bridge_speed': self.bridge_speed,
            'gap_fill_speed': self.gap_fill_speed,
            'first_layer_speed': self.first_layer_speed,
            'first_layer_travel_speed': self.first_layer_travel_speed,
            'skirt_brim_speed': self.skirt_brim_speed,
            'above_raft_speed': self.above_raft_speed,
            'ooze_shield_speed': self.ooze_shield_speed,
            'prime_pillar_speed': self.prime_pillar_speed,
            'speed_tolerance': self.speed_tolerance,
            'num_slow_layers': self.num_slow_layers,
            'first_layer_speed_multiplier': self.first_layer_speed_multiplier,
            'above_raft_speed_multiplier': self.above_raft_speed_multiplier,
            'prime_pillar_speed_multiplier': self.prime_pillar_speed_multiplier,
            'ooze_shield_speed_multiplier': self.ooze_shield_speed_multiplier,
            'outline_speed_multiplier': self.outline_speed_multiplier,
            'solid_infill_speed_multiplier': self.solid_infill_speed_multiplier,
            'support_structure_speed_multiplier': self.support_structure_speed_multiplier,
            'bridging_speed_multiplier': self.bridging_speed_multiplier,
            'small_perimeter_speed_multiplier': self.small_perimeter_speed_multiplier,
            'external_perimeter_speed_multiplier': self.external_perimeter_speed_multiplier,
            'top_solid_infill_speed_multiplier': self.top_solid_infill_speed_multiplier,
            # Slic3r only settings - Percent or mm/s text
            'small_perimeter_speed_text':self.small_perimeter_speed_text,
            'external_perimeter_speed_text':self.external_perimeter_speed_text,
            'solid_infill_speed_text':self.solid_infill_speed_text,
            'top_solid_infill_speed_text':self.top_solid_infill_speed_text,
            'first_layer_speed_text':self.first_layer_speed_text,
            'snapshot_command': self.snapshot_command,
            'suppress_snapshot_command_always': self.suppress_snapshot_command_always,
            'printer_position_confirmation_tolerance': self.printer_position_confirmation_tolerance,
            'auto_detect_position': self.auto_detect_position,
            'auto_position_detection_commands': self.auto_position_detection_commands,
            'origin_x': self.origin_x,
            'origin_y': self.origin_y,
            'origin_z': self.origin_z,
            'abort_out_of_bounds': self.abort_out_of_bounds,
            'override_octoprint_print_volume': self.override_octoprint_print_volume,
            'min_x': self.min_x,
            'max_x': self.max_x,
            'min_y': self.min_y,
            'max_y': self.max_y,
            'min_z': self.min_z,
            'max_z': self.max_z,
            'priming_height': self.priming_height,
            'e_axis_default_mode': self.e_axis_default_mode,
            'g90_influences_extruder': self.g90_influences_extruder,
            'xyz_axes_default_mode': self.xyz_axes_default_mode,
            'units_default': self.units_default,
            'axis_speed_display_units': self.axis_speed_display_units,
            'default_firmware_retractions': self.default_firmware_retractions,
            'default_firmware_retractions_zhop': self.default_firmware_retractions_zhop
        }

    # Round and return speed in mm/min
    def get_speed_from_settings_slic3r_pe(self, speed, speed_name=None):
        if speed is None:
            return None

        # For some reason retract and detract speeds are rounded to the nearest mm/sec
        if speed_name is not None and speed_name in ["retract_speed", "detract_speed"]:
            speed = utility.round_to(speed, 1)

        # Convert speed to mm/min
        speed = speed * 60.0
        # round to .001

        return utility.round_to(speed, 0.01)

    def get_speed_from_settings_simplify_3d(self, speed, speed_name=None):
        if speed is None:
            return None
        speed -= 0.1
        return utility.round_to(speed, 1)

    def get_speed_from_settings_cura(self, speed, speed_nam=None):
        if speed is None:
            return None
        # Convert speed to mm/min
        speed = speed * 60.0
        # round to .1
        return utility.round_to(speed, 0.1)

    def get_speed_from_settings_other_slicer(self, speed, speed_name=None):
        if self.axis_speed_display_units == "mm-sec":
            speed = speed * 60.0
        # Todo - Look at this, we need to round prob.
        return speed

    def get_speed_for_slicer_type(self, speed, speed_name=None):
        if speed is None:
            return None
        if self.slicer_type == 'slic3r-pe':
            return self.get_speed_from_settings_slic3r_pe(speed, speed_name)
        elif self.slicer_type == 'simplify-3d':
            return self.get_speed_from_settings_simplify_3d(speed, speed_name)
        elif self.slicer_type == 'cura':
            return self.get_speed_from_settings_cura(speed, speed_name)
        elif self.slicer_type == 'other':
            return self.get_speed_from_settings_other_slicer(speed, speed_name)
        return speed

    def get_speed_tolerance_for_slicer_type(self):
        if self.slicer_type == 'slic3r-pe':
            return self.speed_tolerance * 60.0
        elif self.slicer_type == 'simplify-3d':
            return self.speed_tolerance
        elif self.slicer_type == 'cura':
            return self.speed_tolerance * 60.0
        elif self.slicer_type == 'other':
            if self.axis_speed_display_units == 'mm-sec':
                return self.speed_tolerance * 60
            return self.speed_tolerance
        return self.speed_tolerance


    def get_speed_by_multiple_for_simplify_3d(self, speed, multiple):
        if speed is None or multiple is None:
            return None
        return self.get_speed_from_settings_simplify_3d(speed * multiple / 100.0)

    def get_speed_by_multiple_for_cura(self, speed, multiple):
        if speed is None or multiple is None:
            return None
        return self.get_speed_from_settings_cura(speed * multiple / 100.0)

    def get_speed_by_multiple_for_slic3r_pe(self, speed, multiple):
        if speed is None or multiple is None:
            return None
        # round the speed multiplier to a multiple of 1
        return self.get_speed_from_settings_slic3r_pe(speed * multiple / 100.0)

    def get_speed_by_multiple_for_other_slicer(self, speed, multiple):
        if speed is None or multiple is None:
            return None
        return self.get_speed_from_settings_other_slicer(speed * multiple / 100.0)

    def get_speed_by_multiple_for_slicer_type(self, speed, multiple):
        if self.slicer_type == 'slic3r-pe':
            return self.get_speed_by_multiple_for_slic3r_pe(speed, multiple)
        if self.slicer_type == 'simplify-3d':
            return self.get_speed_by_multiple_for_simplify_3d(speed, multiple)
        if self.slicer_type == 'cura':
            return self.get_speed_by_multiple_for_cura(speed, multiple)
        return self.get_speed_by_multiple_for_other_slicer(speed, multiple)


    def get_retract_length_for_slicer_type(self):
        if self.slicer_type == 'slic3r-pe':
            return utility.round_to(self.retract_length, 0.00001)
        return self.retract_length

    def get_z_hop_for_slicer_type(self):
        if self.slicer_type == 'slic3r-pe':
            return utility.round_to(self.z_hop, 0.001)
        return self.z_hop

class StabilizationPath(object):
    def __init__(self):
        self.Axis = ""
        self.Path = []
        self.CoordinateSystem = ""
        self.Index = 0
        self.Loop = True
        self.InvertLoop = True
        self.Increment = 1
        self.CurrentPosition = None
        self.Type = 'disabled'
        self.Options = {}


class Stabilization(object):

    def __init__(self, stabilization=None, guid=None, name="Default Stabilization"):
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        self.x_type = "relative"
        self.x_fixed_coordinate = 0.0
        self.x_fixed_path = "0"
        self.x_fixed_path_loop = True
        self.x_fixed_path_invert_loop = True
        self.x_relative = 50.0
        self.x_relative_print = 50.0
        self.x_relative_path = "50.0"
        self.x_relative_path_loop = True
        self.x_relative_path_invert_loop = True
        self.y_type = 'relative'
        self.y_fixed_coordinate = 0.0
        self.y_fixed_path = "0"
        self.y_fixed_path_loop = True
        self.y_fixed_path_invert_loop = True
        self.y_relative = 50.0
        self.y_relative_print = 50.0
        self.y_relative_path = "50"
        self.y_relative_path_loop = True
        self.y_relative_path_invert_loop = True

        if stabilization is not None:
            self.update(stabilization)

    def update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)

        if "x_type" in changes.keys():
            self.x_type = utility.get_string(changes["x_type"], self.x_type)
        if "x_fixed_coordinate" in changes.keys():
            self.x_fixed_coordinate = utility.get_float(
                changes["x_fixed_coordinate"], self.x_fixed_coordinate)
        if "x_fixed_path" in changes.keys():
            self.x_fixed_path = utility.get_string(
                changes["x_fixed_path"], self.x_fixed_path)
        if "x_fixed_path_loop" in changes.keys():
            self.x_fixed_path_loop = utility.get_bool(
                changes["x_fixed_path_loop"], self.x_fixed_path_loop)
        if "x_fixed_path_invert_loop" in changes.keys():
            self.x_fixed_path_invert_loop = utility.get_bool(
                changes["x_fixed_path_invert_loop"], self.x_fixed_path_invert_loop)
        if "x_relative" in changes.keys():
            self.x_relative = utility.get_float(
                changes["x_relative"], self.x_relative)
        if "x_relative_print" in changes.keys():
            self.x_relative_print = utility.get_float(
                changes["x_relative_print"], self.x_relative_print)
        if "x_relative_path" in changes.keys():
            self.x_relative_path = utility.get_string(
                changes["x_relative_path"], self.x_relative_path)
        if "x_relative_path_loop" in changes.keys():
            self.x_relative_path_loop = utility.get_bool(
                changes["x_relative_path_loop"], self.x_relative_path_loop)
        if "x_relative_path_invert_loop" in changes.keys():
            self.x_relative_path_invert_loop = utility.get_bool(
                changes["x_relative_path_invert_loop"], self.x_relative_path_invert_loop)
        if "y_type" in changes.keys():
            self.y_type = utility.get_string(changes["y_type"], self.y_type)
        if "y_fixed_coordinate" in changes.keys():
            self.y_fixed_coordinate = utility.get_float(
                changes["y_fixed_coordinate"], self.y_fixed_coordinate)
        if "y_fixed_path" in changes.keys():
            self.y_fixed_path = utility.get_string(
                changes["y_fixed_path"], self.y_fixed_path)
        if "y_fixed_path_loop" in changes.keys():
            self.y_fixed_path_loop = utility.get_bool(
                changes["y_fixed_path_loop"], self.y_fixed_path_loop)
        if "y_fixed_path_invert_loop" in changes.keys():
            self.y_fixed_path_invert_loop = utility.get_bool(
                changes["y_fixed_path_invert_loop"], self.y_fixed_path_invert_loop)
        if "y_relative" in changes.keys():
            self.y_relative = utility.get_float(
                changes["y_relative"], self.y_relative)
        if "y_relative_print" in changes.keys():
            self.y_relative_print = utility.get_float(
                changes["y_relative_print"], self.y_relative_print)
        if "y_relative_path" in changes.keys():
            self.y_relative_path = utility.get_string(
                changes["y_relative_path"], self.y_relative_path)
        if "y_relative_path_loop" in changes.keys():
            self.y_relative_path_loop = utility.get_bool(
                changes["y_relative_path_loop"], self.y_relative_path_loop)
        if "y_relative_path_invert_loop" in changes.keys():
            self.y_relative_path_invert_loop = utility.get_bool(
                changes["y_relative_path_invert_loop"], self.y_relative_path_invert_loop)

    def to_dict(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'x_type': self.x_type,
            'x_fixed_coordinate': self.x_fixed_coordinate,
            'x_fixed_path': self.x_fixed_path,
            'x_fixed_path_loop': self.x_fixed_path_loop,
            'x_fixed_path_invert_loop': self.x_fixed_path_invert_loop,
            'x_relative': self.x_relative,
            'x_relative_print': self.x_relative_print,
            'x_relative_path': self.x_relative_path,
            'x_relative_path_loop': self.x_relative_path_loop,
            'x_relative_path_invert_loop': self.x_relative_path_invert_loop,
            'y_type': self.y_type,
            'y_fixed_coordinate': self.y_fixed_coordinate,
            'y_fixed_path': self.y_fixed_path,
            'y_fixed_path_loop': self.y_fixed_path_loop,
            'y_fixed_path_invert_loop': self.y_fixed_path_invert_loop,
            'y_relative': self.y_relative,
            'y_relative_print': self.y_relative_print,
            'y_relative_path': self.y_relative_path,
            'y_relative_path_loop': self.y_relative_path_loop,
            'y_relative_path_invert_loop': self.y_relative_path_invert_loop
        }

    def get_stabilization_paths(self):
        x_stabilization_path = StabilizationPath()
        x_stabilization_path.Axis = "X"
        x_stabilization_path.Type = self.x_type
        if self.x_type == 'fixed_coordinate':
            x_stabilization_path.Path.append(self.x_fixed_coordinate)
            x_stabilization_path.CoordinateSystem = 'absolute'
        elif self.x_type == 'relative':
            x_stabilization_path.Path.append(self.x_relative)
            x_stabilization_path.CoordinateSystem = 'bed_relative'
        elif self.x_type == 'fixed_path':
            x_stabilization_path.Path = self.parse_csv_path(self.x_fixed_path)
            x_stabilization_path.CoordinateSystem = 'absolute'
            x_stabilization_path.Loop = self.x_fixed_path_loop
            x_stabilization_path.InvertLoop = self.x_fixed_path_invert_loop
        elif self.x_type == 'relative_path':
            x_stabilization_path.Path = self.parse_csv_path(self.x_relative_path)
            x_stabilization_path.CoordinateSystem = 'bed_relative'
            x_stabilization_path.Loop = self.x_relative_path_loop
            x_stabilization_path.InvertLoop = self.x_relative_path_invert_loop

        y_stabilization_path = StabilizationPath()
        y_stabilization_path.Axis = "Y"
        y_stabilization_path.Type = self.y_type
        if self.y_type == 'fixed_coordinate':
            y_stabilization_path.Path.append(self.y_fixed_coordinate)
            y_stabilization_path.CoordinateSystem = 'absolute'
        elif self.y_type == 'relative':
            y_stabilization_path.Path.append(self.y_relative)
            y_stabilization_path.CoordinateSystem = 'bed_relative'
        elif self.y_type == 'fixed_path':
            y_stabilization_path.Path = self.parse_csv_path(self.y_fixed_path)
            y_stabilization_path.CoordinateSystem = 'absolute'
            y_stabilization_path.Loop = self.y_fixed_path_loop
            y_stabilization_path.InvertLoop = self.y_fixed_path_invert_loop
        elif self.y_type == 'relative_path':
            y_stabilization_path.Path = self.parse_csv_path(self.y_relative_path)
            y_stabilization_path.CoordinateSystem = 'bed_relative'
            y_stabilization_path.Loop = self.y_relative_path_loop
            y_stabilization_path.InvertLoop = self.y_relative_path_invert_loop

        return dict(
            X=x_stabilization_path,
            Y=y_stabilization_path
        )

    @staticmethod
    def parse_csv_path(path_csv):
        """Converts a list of floats separated by commas into an array of floats."""
        path = []
        items = path_csv.split(',')
        for item in items:
            item = item.strip()
            if len(item) > 0:
                path.append(float(item))
        return path


class SnapshotPositionRestrictions(object):
    def __init__(self, restriction_type, shape, x, y, x2=None, y2=None, r=None, calculate_intersections=False):

        self.Type = restriction_type.lower()
        if self.Type not in ["forbidden", "required"]:
            raise TypeError("SnapshotPosition type must be 'forbidden' or 'required'")

        self.Shape = shape.lower()

        if self.Shape not in ["rect", "circle"]:
            raise TypeError("SnapshotPosition shape must be 'rect' or 'circle'")
        if x is None or y is None:
            raise TypeError(
                "SnapshotPosition requires that x and y are not None")
        if self.Shape == 'rect' and (x2 is None or y2 is None):
            raise TypeError(
                "SnapshotPosition shape=rect requires that x2 and y2 are not None")
        if self.Shape == 'circle' and r is None:
            raise TypeError(
                "SnapshotPosition shape=circle requires that r is not None")

        self.Type = restriction_type
        self.Shape = shape
        self.X = float(x)
        self.Y = float(y)
        self.X2 = float(x2)
        self.Y2 = float(y2)
        self.R = float(r)
        self.CalculateIntersections = calculate_intersections

    def to_dict(self):
        return {
            'Type': self.Type,
            'Shape': self.Shape,
            'X': self.X,
            'Y': self.Y,
            'X2': self.X2,
            'Y2': self.Y2,
            'R': self.R,
            'CalculateIntersections': self.CalculateIntersections
        }

    def get_intersections(self, x, y, previous_x, previous_y):
        if not self.CalculateIntersections:
            return False

        if x is None or y is None or previous_x is None or previous_y is None:
            return False

        if self.Shape == 'rect':
            intersections = utility.get_intersections_rectangle(previous_x, previous_y, x, y, self.X, self.Y, self.X2, self.Y2)
        elif self.Shape == 'circle':
            intersections = utility.get_intersections_circle(previous_x, previous_y, x, y, self.X, self.Y, self.R)
        else:
            raise TypeError("SnapshotPosition shape must be 'rect' or 'circle'.")

        if not intersections:
            return False

        return intersections

    def is_in_position(self, x, y, tolerance):
        if x is None or y is None:
            return False

        if self.Shape == 'rect':
            return self.X <= x <= self.X2 and self.Y <= y <= self.Y2
        elif self.Shape == 'circle':
            lsq = math.pow(x - self.X, 2) + math.pow(y - self.Y, 2)
            rsq = math.pow(self.R, 2)
            return utility.is_close(lsq, rsq , tolerance) or lsq < rsq
        else:
            raise TypeError("SnapshotPosition shape must be 'rect' or 'circle'.")


class Snapshot(object):
    # globals
    # Extruder Trigger Options
    ExtruderTriggerIgnoreValue = ""
    ExtruderTriggerRequiredValue = "trigger_on"
    ExtruderTriggerForbiddenValue = "forbidden"
    ExtruderTriggerOptions = [
        dict(value=ExtruderTriggerIgnoreValue, name='Ignore', visible=True),
        dict(value=ExtruderTriggerRequiredValue, name='Trigger', visible=True),
        dict(value=ExtruderTriggerForbiddenValue, name='Forbidden', visible=True)
    ]

    LayerTriggerType = 'layer'
    TimerTriggerType = 'timer'
    GcodeTriggerType = 'gcode'

    def __init__(self, snapshot=None, guid=None, name="Default Snapshot"):
        self.guid = guid if guid else str(uuid.uuid4())
        self.is_default = False
        self.name = name
        self.description = ""
        self.trigger_type = self.LayerTriggerType
        # timer trigger settings
        self.timer_trigger_seconds = 30
        # layer trigger settings
        self.layer_trigger_height = 0.0

        # Position Restrictions
        self.position_restrictions_enabled = False
        self.position_restrictions = []

        # Quality Settings
        self.require_zhop = False
        # Extruder State
        self.extruder_state_requirements_enabled = False
        self.trigger_on_extruding_start = None
        self.trigger_on_extruding = None
        self.trigger_on_primed = None
        self.trigger_on_retracting_start = None
        self.trigger_on_retracting = None
        self.trigger_on_partially_retracted = None
        self.trigger_on_retracted = None
        self.trigger_on_detracting_start = None
        self.trigger_on_detracting = None
        self.trigger_on_detracted = None
        self.feature_trigger_on_wipe = None
        # Feature Detection
        self.feature_restrictions_enabled = False
        self.feature_trigger_on_detract = False
        self.feature_trigger_on_retract = False
        self.feature_trigger_on_movement = False
        self.feature_trigger_on_z_movement = False
        self.feature_trigger_on_perimeters = True
        self.feature_trigger_on_small_perimeters = False
        self.feature_trigger_on_external_perimeters = False
        self.feature_trigger_on_infill = True
        self.feature_trigger_on_solid_infill = True
        self.feature_trigger_on_top_solid_infill = True
        self.feature_trigger_on_supports = False
        self.feature_trigger_on_bridges = False
        self.feature_trigger_on_gap_fills = True
        self.feature_trigger_on_first_layer = True
        self.feature_trigger_on_above_raft = False
        self.feature_trigger_on_ooze_shield = False
        self.feature_trigger_on_prime_pillar = True
        self.feature_trigger_on_normal_print_speed = False
        self.feature_trigger_on_skirt_brim = False
        self.feature_trigger_on_first_layer_travel = False
        # Lift and retract before move
        self.lift_before_move = True
        self.retract_before_move = True

        # Snapshot Cleanup
        self.cleanup_after_render_complete = True
        self.cleanup_after_render_fail = False

        if snapshot is not None:
            if isinstance(snapshot, Snapshot):
                self.name = snapshot.name
                self.description = snapshot.description
                self.guid = snapshot.guid
                self.is_default = snapshot.is_default
                self.trigger_type = snapshot.trigger_type
                # timer trigger members
                self.timer_trigger_seconds = snapshot.timer_trigger_seconds
                # layer trigger members
                self.layer_trigger_height = snapshot.layer_trigger_height
                # quality settings
                self.require_zhop = snapshot.require_zhop
                # extruder state
                self.extruder_state_requirements_enabled = snapshot.extruder_state_requirements_enabled
                self.trigger_on_extruding_start = snapshot.trigger_on_extruding_start
                self.trigger_on_extruding = snapshot.trigger_on_extruding
                self.trigger_on_primed = snapshot.trigger_on_primed
                self.trigger_on_retracting_start = snapshot.trigger_on_retracting_start
                self.trigger_on_retracting = snapshot.trigger_on_retracting
                self.trigger_on_partially_retracted = snapshot.trigger_on_partially_retracted
                self.trigger_on_retracted = snapshot.trigger_on_retracted
                self.trigger_on_detracting_start = snapshot.trigger_on_detracting_start
                self.trigger_on_detracting = snapshot.trigger_on_detracting
                self.trigger_on_detracted = snapshot.trigger_on_detracted
                # position restrictions
                self.position_restrictions = snapshot.position_restrictions
                self.position_restrictions_enabled = snapshot.position_restrictions_enabled
                # feature detection
                self.feature_restrictions_enabled = snapshot.feature_restrictions_enabled
                self.feature_trigger_on_detract = snapshot.feature_trigger_on_detract
                self.feature_trigger_on_retract = snapshot.feature_trigger_on_retract
                self.feature_trigger_on_movement = snapshot.feature_trigger_on_movement
                self.feature_trigger_on_z_movement = snapshot.feature_trigger_on_z_movement
                self.feature_trigger_on_perimeters = snapshot.feature_trigger_on_perimeters
                self.feature_trigger_on_small_perimeters = snapshot.feature_trigger_on_small_perimeters
                self.feature_trigger_on_external_perimeters = snapshot.feature_trigger_on_external_perimeters
                self.feature_trigger_on_infill = snapshot.feature_trigger_on_infill
                self.feature_trigger_on_solid_infill = snapshot.feature_trigger_on_solid_infill
                self.feature_trigger_on_top_solid_infill = snapshot.feature_trigger_on_top_solid_infill
                self.feature_trigger_on_supports = snapshot.feature_trigger_on_supports
                self.feature_trigger_on_bridges = snapshot.feature_trigger_on_bridges
                self.feature_trigger_on_gap_fills = snapshot.feature_trigger_on_gap_fills
                self.feature_trigger_on_first_layer = snapshot.feature_trigger_on_first_layer
                self.feature_trigger_on_above_raft = snapshot.feature_trigger_on_above_raft
                self.feature_trigger_on_ooze_shield = snapshot.feature_trigger_on_ooze_shield
                self.feature_trigger_on_prime_pillar = snapshot.feature_trigger_on_prime_pillar
                self.feature_trigger_on_normal_print_speed = snapshot.feature_trigger_on_normal_print_speed
                self.feature_trigger_on_skirt_brim = snapshot.feature_trigger_on_skirt_brim
                self.feature_trigger_on_first_layer_travel = snapshot.feature_trigger_on_first_layer_travel
                self.feature_trigger_on_wipe = snapshot.feature_trigger_on_wipe
                # lift and retract before move
                self.lift_before_move = snapshot.lift_before_move
                self.retract_before_move = snapshot.retract_before_move

                # Snapshot Cleanup
                self.cleanup_after_render_complete = snapshot.cleanup_after_render_complete
                self.cleanup_after_render_fail = snapshot.cleanup_after_render_fail

            else:
                self.update(snapshot)

    def update(self, changes):
        # Initialize all values according to the provided changes, use defaults if
        # the values are null or incorrectly formatted
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "is_default" in changes.keys():
            self.is_default = utility.get_bool(
                changes["is_default"], self.is_default)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        if "trigger_type" in changes.keys():
            self.trigger_type = utility.get_string(
                changes["trigger_type"], self.trigger_type)
        # timer trigger members
        if "timer_trigger_seconds" in changes.keys():
            self.timer_trigger_seconds = utility.get_int(
                changes["timer_trigger_seconds"], self.timer_trigger_seconds)
        # layer trigger members
        if "layer_trigger_height" in changes.keys():
            self.layer_trigger_height = utility.get_float(
                changes["layer_trigger_height"], self.layer_trigger_height)
        # position restrictions
        if "position_restrictions_enabled" in changes.keys():
            self.position_restrictions_enabled = utility.get_bool(
                changes["position_restrictions_enabled"], self.position_restrictions_enabled)
        if "position_restrictions" in changes.keys():
            self.position_restrictions = self.get_trigger_position_restrictions(
                changes["position_restrictions"])
        # quality settiings
        if "require_zhop" in changes.keys():
            self.require_zhop = utility.get_bool(
                changes["require_zhop"], self.require_zhop)
        # extruder state restrictions
        if "extruder_state_requirements_enabled" in changes.keys():
            self.extruder_state_requirements_enabled = utility.get_bool(
                changes["extruder_state_requirements_enabled"], self.extruder_state_requirements_enabled)

        if "trigger_on_extruding_start" in changes.keys():
            self.trigger_on_extruding_start = self.get_extruder_trigger_value(
                changes["trigger_on_extruding_start"])
        if "trigger_on_extruding" in changes.keys():
            self.trigger_on_extruding = self.get_extruder_trigger_value(
                changes["trigger_on_extruding"])
        if "trigger_on_primed" in changes.keys():
            self.trigger_on_primed = self.get_extruder_trigger_value(
                changes["trigger_on_primed"])
        if "trigger_on_retracting_start" in changes.keys():
            self.trigger_on_retracting_start = self.get_extruder_trigger_value(
                changes["trigger_on_retracting_start"])
        if "trigger_on_retracting" in changes.keys():
            self.trigger_on_retracting = self.get_extruder_trigger_value(
                changes["trigger_on_retracting"])
        if "trigger_on_partially_retracted" in changes.keys():
            self.trigger_on_partially_retracted = self.get_extruder_trigger_value(
                changes["trigger_on_partially_retracted"])
        if "trigger_on_retracted" in changes.keys():
            self.trigger_on_retracted = self.get_extruder_trigger_value(
                changes["trigger_on_retracted"])
        if "trigger_on_detracting_start" in changes.keys():
            self.trigger_on_detracting_start = self.get_extruder_trigger_value(
                changes["trigger_on_detracting_start"])
        if "trigger_on_detracting" in changes.keys():
            self.trigger_on_detracting = self.get_extruder_trigger_value(
                changes["trigger_on_detracting"])
        if "trigger_on_detracted" in changes.keys():
            self.trigger_on_detracted = self.get_extruder_trigger_value(
                changes["trigger_on_detracted"])
        # feature detection
        if "feature_restrictions_enabled" in changes.keys():
            self.feature_restrictions_enabled = utility.get_bool(
                changes["feature_restrictions_enabled"], self.feature_restrictions_enabled)
        if "feature_trigger_on_detract" in changes.keys():
            self.feature_trigger_on_detract = utility.get_bool(
                changes["feature_trigger_on_detract"], self.feature_trigger_on_detract)
        if "feature_trigger_on_retract" in changes.keys():
            self.feature_trigger_on_retract = utility.get_bool(
                changes["feature_trigger_on_retract"], self.feature_trigger_on_retract)
        if "feature_trigger_on_movement" in changes.keys():
            self.feature_trigger_on_movement = utility.get_bool(
                changes["feature_trigger_on_movement"], self.feature_trigger_on_movement)
        if "feature_trigger_on_z_movement" in changes.keys():
            self.feature_trigger_on_z_movement = utility.get_bool(
                changes["feature_trigger_on_z_movement"], self.feature_trigger_on_z_movement)
        if "feature_trigger_on_perimeters" in changes.keys():
            self.feature_trigger_on_perimeters = utility.get_bool(
                changes["feature_trigger_on_perimeters"], self.feature_trigger_on_perimeters)
        if "feature_trigger_on_small_perimeters" in changes.keys():
            self.feature_trigger_on_small_perimeters = utility.get_bool(
                changes["feature_trigger_on_small_perimeters"], self.feature_trigger_on_small_perimeters)
        if "feature_trigger_on_external_perimeters" in changes.keys():
            self.feature_trigger_on_external_perimeters = utility.get_bool(
                changes["feature_trigger_on_external_perimeters"], self.feature_trigger_on_external_perimeters)
        if "feature_trigger_on_infill" in changes.keys():
            self.feature_trigger_on_infill = utility.get_bool(
                changes["feature_trigger_on_infill"], self.feature_trigger_on_infill)
        if "feature_trigger_on_solid_infill" in changes.keys():
            self.feature_trigger_on_solid_infill = utility.get_bool(
                changes["feature_trigger_on_solid_infill"], self.feature_trigger_on_solid_infill)
        if "feature_trigger_on_top_solid_infill" in changes.keys():
            self.feature_trigger_on_top_solid_infill = utility.get_bool(
                changes["feature_trigger_on_top_solid_infill"], self.feature_trigger_on_top_solid_infill)
        if "feature_trigger_on_supports" in changes.keys():
            self.feature_trigger_on_supports = utility.get_bool(
                changes["feature_trigger_on_supports"], self.feature_trigger_on_supports)
        if "feature_trigger_on_bridges" in changes.keys():
            self.feature_trigger_on_bridges = utility.get_bool(
                changes["feature_trigger_on_bridges"], self.feature_trigger_on_bridges)
        if "feature_trigger_on_gap_fills" in changes.keys():
            self.feature_trigger_on_gap_fills = utility.get_bool(
                changes["feature_trigger_on_gap_fills"], self.feature_trigger_on_gap_fills)
        if "feature_trigger_on_first_layer" in changes.keys():
            self.feature_trigger_on_first_layer = utility.get_bool(
                changes["feature_trigger_on_first_layer"], self.feature_trigger_on_first_layer)
        if "feature_trigger_on_first_layer_travel" in changes.keys():
            self.feature_trigger_on_first_layer_travel = utility.get_bool(
                changes["feature_trigger_on_first_layer_travel"], self.feature_trigger_on_first_layer_travel)
        if "feature_trigger_on_above_raft" in changes.keys():
            self.feature_trigger_on_above_raft = utility.get_bool(
                changes["feature_trigger_on_above_raft"], self.feature_trigger_on_above_raft)
        if "feature_trigger_on_ooze_shield" in changes.keys():
            self.feature_trigger_on_ooze_shield = utility.get_bool(
                changes["feature_trigger_on_ooze_shield"], self.feature_trigger_on_ooze_shield)
        if "feature_trigger_on_prime_pillar" in changes.keys():
            self.feature_trigger_on_prime_pillar = utility.get_bool(
                changes["feature_trigger_on_prime_pillar"], self.feature_trigger_on_prime_pillar)
        if "feature_trigger_on_normal_print_speed" in changes.keys():
            self.feature_trigger_on_normal_print_speed = utility.get_bool(
                changes["feature_trigger_on_normal_print_speed"], self.feature_trigger_on_normal_print_speed)
        if "feature_trigger_on_skirt_brim" in changes.keys():
            self.feature_trigger_on_skirt_brim = utility.get_bool(
                changes["feature_trigger_on_skirt_brim"], self.feature_trigger_on_skirt_brim)
        if "feature_trigger_on_wipe" in changes.keys():
            self.feature_trigger_on_wipe = utility.get_bool(
                changes["feature_trigger_on_wipe"], self.feature_trigger_on_wipe)

        # Lift and retract before move
        if "lift_before_move" in changes.keys():
            self.lift_before_move = utility.get_bool(
                changes["lift_before_move"], self.lift_before_move)
        if "retract_before_move" in changes.keys():
            self.retract_before_move = utility.get_bool(
                changes["retract_before_move"], self.retract_before_move)
        #Snapshot Cleanup
        if "cleanup_after_render_complete" in changes.keys():
            self.cleanup_after_render_complete = utility.get_bool(
                changes["cleanup_after_render_complete"], self.cleanup_after_render_complete)
        if "cleanup_after_render_fail" in changes.keys():
            self.cleanup_after_render_fail = utility.get_bool(
                changes["cleanup_after_render_fail"], self.cleanup_after_render_fail)

    def get_extruder_trigger_value_string(self, value):
        if value is None:
            return self.ExtruderTriggerIgnoreValue
        elif value:
            return self.ExtruderTriggerRequiredValue
        elif not value:
            return self.ExtruderTriggerForbiddenValue

    def get_extruder_trigger_value(self, value):
        if isinstance(value, basestring):
            if value is None:
                return None
            elif value.lower() == self.ExtruderTriggerRequiredValue:
                return True
            elif value.lower() == self.ExtruderTriggerForbiddenValue:
                return False
            else:
                return None
        else:
            return bool(value)

    @staticmethod
    def get_trigger_position_restrictions(value):
        restrictions = []
        for restriction in value:
            restrictions.append(
                SnapshotPositionRestrictions(
                    restriction["Type"], restriction["Shape"],
                    restriction["X"], restriction["Y"],
                    restriction["X2"], restriction["Y2"],
                    restriction["R"], restriction["CalculateIntersections"]
                )
            )
        return restrictions

    @staticmethod
    def get_trigger_position_restrictions_value_string(values):
        restrictions = []
        for restriction in values:
            restrictions.append(restriction.to_dict())
        return restrictions

    def to_dict(self):
        get_vr = self.get_extruder_trigger_value_string
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'trigger_type': self.trigger_type,
            # Gcode Trigger
            # None
            # Timer Trigger
            'timer_trigger_seconds': self.timer_trigger_seconds,
            # Layer Trigger
            'layer_trigger_height': self.layer_trigger_height,

            # Quality Settings
            'require_zhop': self.require_zhop,
            # Extruder State
            'extruder_state_requirements_enabled': self.extruder_state_requirements_enabled,
            'trigger_on_extruding_start': get_vr(self.trigger_on_extruding_start),
            'trigger_on_extruding': get_vr(self.trigger_on_extruding),
            'trigger_on_primed': get_vr(self.trigger_on_primed),
            'trigger_on_retracting_start': get_vr(self.trigger_on_retracting_start),
            'trigger_on_retracting': get_vr(self.trigger_on_retracting),
            'trigger_on_partially_retracted': get_vr(self.trigger_on_partially_retracted),
            'trigger_on_retracted': get_vr(self.trigger_on_retracted),
            'trigger_on_detracting_start': get_vr(self.trigger_on_detracting_start),
            'trigger_on_detracting': get_vr(self.trigger_on_detracting),
            'trigger_on_detracted': get_vr(self.trigger_on_detracted),
            # Position Restrictions
            'position_restrictions_enabled': self.position_restrictions_enabled,
            'position_restrictions': self.get_trigger_position_restrictions_value_string(
                self.position_restrictions),
            # Feature Detection
            'feature_restrictions_enabled': self.feature_restrictions_enabled,
            'feature_trigger_on_detract': self.feature_trigger_on_detract,
            'feature_trigger_on_retract': self.feature_trigger_on_retract,
            'feature_trigger_on_movement': self.feature_trigger_on_movement,
            'feature_trigger_on_z_movement': self.feature_trigger_on_z_movement,
            'feature_trigger_on_perimeters': self.feature_trigger_on_perimeters,
            'feature_trigger_on_small_perimeters': self.feature_trigger_on_small_perimeters,
            'feature_trigger_on_external_perimeters': self.feature_trigger_on_external_perimeters,
            'feature_trigger_on_infill': self.feature_trigger_on_infill,
            'feature_trigger_on_solid_infill': self.feature_trigger_on_solid_infill,
            'feature_trigger_on_top_solid_infill': self.feature_trigger_on_top_solid_infill,
            'feature_trigger_on_supports': self.feature_trigger_on_supports,
            'feature_trigger_on_bridges': self.feature_trigger_on_bridges,
            'feature_trigger_on_gap_fills': self.feature_trigger_on_gap_fills,
            'feature_trigger_on_first_layer': self.feature_trigger_on_first_layer,
            'feature_trigger_on_first_layer_travel': self.feature_trigger_on_first_layer_travel,
            'feature_trigger_on_above_raft': self.feature_trigger_on_above_raft,
            'feature_trigger_on_ooze_shield': self.feature_trigger_on_ooze_shield,
            'feature_trigger_on_prime_pillar': self.feature_trigger_on_prime_pillar,
            'feature_trigger_on_normal_print_speed': self.feature_trigger_on_normal_print_speed,
            'feature_trigger_on_skirt_brim': self.feature_trigger_on_skirt_brim,
            'feature_trigger_on_wipe': self.feature_trigger_on_wipe,
            # Lift and Retract Before Move
            'lift_before_move': self.lift_before_move,
            'retract_before_move': self.retract_before_move,

            # snapshot cleanup
            'cleanup_after_render_complete': self.cleanup_after_render_complete,
            'cleanup_after_render_fail': self.cleanup_after_render_fail,
        }


class Rendering(object):
    def __init__(self, rendering=None, guid=None, name="Default Rendering"):
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        self.enabled = True
        self.fps_calculation_type = 'duration'
        self.run_length_seconds = 5
        self.fps = 30
        self.max_fps = 120.0
        self.min_fps = 2.0
        self.output_format = 'mp4'
        self.sync_with_timelapse = True
        self.bitrate = "8000K"
        self.post_roll_seconds = 0
        self.pre_roll_seconds = 0
        self.output_template = "{FAILEDFLAG}{FAILEDSEPARATOR}{GCODEFILENAME}_{PRINTENDTIME}"
        self.enable_watermark = False
        self.selected_watermark = ""
        self.overlay_text_template = ""
        self.overlay_font_path = ""
        self.overlay_font_size = 10
        self.overlay_text_pos = [10, 10]
        self.overlay_text_alignment = "left"  # Text alignment between lines in the overlay.
        self.overlay_text_valign = "top"  # Overall alignment of text box vertically.
        self.overlay_text_halign = "left"  # Overall alignment of text box horizontally.
        self.overlay_text_color = [255, 255, 255, 128]
        self.thread_count = 1

        if rendering is not None:
            if isinstance(rendering, Rendering):
                self.guid = rendering.guid
                self.name = rendering.name
                self.description = rendering.description
                self.enabled = rendering.enabled
                self.fps_calculation_type = rendering.fps_calculation_type
                self.run_length_seconds = rendering.run_length_seconds
                self.fps = rendering.fps
                self.max_fps = rendering.max_fps
                self.min_fps = rendering.min_fps
                self.output_format = rendering.output_format
                self.sync_with_timelapse = rendering.sync_with_timelapse
                self.bitrate = rendering.bitrate
                self.enable_watermark = rendering.enable_watermark
                self.post_roll_seconds = rendering.post_roll_seconds
                self.pre_roll_seconds = rendering.pre_roll_seconds
                self.output_template = rendering.output_template
                self.selected_watermark = rendering.selected_watermark
                self.overlay_text_template = rendering.overlay_text_template
                self.overlay_font_path = rendering.overlay_font_path
                self.overlay_font_size = rendering.overlay_font_size
                self.overlay_text_pos = rendering.overlay_text_pos
                self.overlay_text_alignment = rendering.overlay_text_alignment
                self.overlay_text_valign = rendering.overlay_text_valign
                self.overlay_text_halign = rendering.overlay_text_halign
                self.overlay_text_color = rendering.overlay_text_color
                self.thread_count = rendering.thread_count
            else:
                self.update(rendering)

    def update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        if "enabled" in changes.keys():
            self.enabled = utility.get_bool(changes["enabled"], self.enabled)
        if "fps_calculation_type" in changes.keys():
            self.fps_calculation_type = changes["fps_calculation_type"]
        if "run_length_seconds" in changes.keys():
            self.run_length_seconds = utility.get_float(
                changes["run_length_seconds"], self.run_length_seconds)
        if "fps" in changes.keys():
            self.fps = utility.get_float(changes["fps"], self.fps)
        if "max_fps" in changes.keys():
            self.max_fps = utility.get_float(changes["max_fps"], self.max_fps)
        if "min_fps" in changes.keys():
            self.min_fps = utility.get_float(changes["min_fps"], self.min_fps)
        if "output_format" in changes.keys():
            self.output_format = utility.get_string(
                changes["output_format"], self.output_format)

        if "sync_with_timelapse" in changes.keys():
            self.sync_with_timelapse = utility.get_bool(
                changes["sync_with_timelapse"], self.sync_with_timelapse)
        if "bitrate" in changes.keys():
            self.bitrate = utility.get_bitrate(changes["bitrate"], self.bitrate)

        if "post_roll_seconds" in changes.keys():
            self.post_roll_seconds = utility.get_float(
                changes["post_roll_seconds"], self.post_roll_seconds)
        if "pre_roll_seconds" in changes.keys():
            self.pre_roll_seconds = utility.get_float(
                changes["pre_roll_seconds"], self.pre_roll_seconds)
        if "output_template" in changes.keys():
            self.output_template = utility.get_string(
                changes["output_template"], self.output_template)

        if "enable_watermark" in changes.keys():
            self.enable_watermark = utility.get_bool(
                changes["enable_watermark"], self.enable_watermark)
        if "selected_watermark" in changes.keys():
            self.selected_watermark = utility.get_string(
                changes["selected_watermark"], self.selected_watermark)
        if "overlay_text_template" in changes.keys():
            self.overlay_text_template = utility.get_string(changes["overlay_text_template"],
                                                            self.overlay_text_template)
        if "overlay_font_path" in changes.keys():
            self.overlay_font_path = utility.get_string(changes["overlay_font_path"], self.overlay_font_path)
        self.overlay_font_size = int(changes.get("overlay_font_size", self.overlay_font_size))
        self.overlay_text_pos = changes.get("overlay_text_pos", self.overlay_text_pos)
        if isinstance(self.overlay_text_pos, str) or isinstance(self.overlay_text_pos, unicode):
            self.overlay_text_pos = json.loads(self.overlay_text_pos)
        self.overlay_text_alignment = changes.get("overlay_text_alignment", self.overlay_text_alignment)
        self.overlay_text_valign = changes.get("overlay_text_valign", self.overlay_text_valign)
        self.overlay_text_halign = changes.get("overlay_text_halign", self.overlay_text_halign)
        self.overlay_text_color = changes.get("overlay_text_color", self.overlay_text_color)
        if isinstance(self.overlay_text_color, str) or isinstance(self.overlay_text_color, unicode):
            self.overlay_text_color = json.loads(self.overlay_text_color)
        if "thread_count" in changes.keys():
            self.thread_count = utility.get_int(
                changes["thread_count"], self.thread_count)

    def to_dict(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'fps_calculation_type': self.fps_calculation_type,
            'run_length_seconds': self.run_length_seconds,
            'fps': self.fps,
            'max_fps': self.max_fps,
            'min_fps': self.min_fps,
            'output_format': self.output_format,
            'sync_with_timelapse': self.sync_with_timelapse,
            'bitrate': self.bitrate,
            'post_roll_seconds': self.post_roll_seconds,
            'pre_roll_seconds': self.pre_roll_seconds,
            'output_template': self.output_template,
            'enable_watermark': self.enable_watermark,
            'selected_watermark': self.selected_watermark,
            'overlay_text_template': self.overlay_text_template,
            'overlay_font_path': self.overlay_font_path,
            'overlay_font_size': self.overlay_font_size,
            'overlay_text_pos': str(self.overlay_text_pos),
            'overlay_text_alignment': self.overlay_text_alignment,
            'overlay_text_valign': self.overlay_text_valign,
            'overlay_text_halign': self.overlay_text_halign,
            'overlay_text_color': str(self.overlay_text_color),
            'thread_count': self.thread_count
        }


class Camera(object):

    def __init__(self, camera=None, guid=None, name="Default Camera"):
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.enabled = True
        self.description = ""
        self.camera_type = "webcam"
        self.gcode_camera_script = ""
        self.on_print_start_script = ""
        self.on_before_snapshot_script = ""
        self.external_camera_snapshot_script = ""
        self.on_after_snapshot_script = ""
        self.on_before_render_script = ""
        self.on_after_render_script = ""
        self.delay = 125
        self.timeout_ms = 5000
        self.apply_settings_before_print = False
        self.address = "http://127.0.0.1/webcam/"
        self.snapshot_request_template = "{camera_address}?action=snapshot"
        self.snapshot_transpose = ""
        self.ignore_ssl_error = False
        self.username = ""
        self.password = ""
        self.brightness = 128
        self.brightness_request_template = self.template_to_string(0, 0, 9963776, 1)
        self.contrast = 128
        self.contrast_request_template = self.template_to_string(0, 0, 9963777, 1)
        self.saturation = 128
        self.saturation_request_template = self.template_to_string(0, 0, 9963778, 1)
        self.white_balance_auto = True
        self.white_balance_auto_request_template = self.template_to_string(0, 0, 9963788, 1)
        self.gain = 100
        self.gain_request_template = self.template_to_string(0, 0, 9963795, 1)
        self.powerline_frequency = 60
        self.powerline_frequency_request_template = self.template_to_string(0, 0, 9963800, 1)
        self.white_balance_temperature = 4000
        self.white_balance_temperature_request_template = self.template_to_string(0, 0, 9963802, 1)
        self.sharpness = 128
        self.sharpness_request_template = self.template_to_string(0, 0, 9963803, 1)
        self.backlight_compensation_enabled = False
        self.backlight_compensation_enabled_request_template = self.template_to_string(0, 0, 9963804, 1)
        self.exposure_type = 1
        self.exposure_type_request_template = self.template_to_string(0, 0, 10094849, 1)
        self.exposure = 250
        self.exposure_request_template = self.template_to_string(0, 0, 10094850, 1)
        self.exposure_auto_priority_enabled = True
        self.exposure_auto_priority_enabled_request_template = self.template_to_string(0, 0, 10094851, 1)
        self.pan = 0
        self.pan_request_template = self.template_to_string(0, 0, 10094856, 1)
        self.tilt = 0
        self.tilt_request_template = self.template_to_string(0, 0, 10094857, 1)
        self.autofocus_enabled = True
        self.autofocus_enabled_request_template = self.template_to_string(0, 0, 10094860, 1)
        self.focus = 28
        self.focus_request_template = self.template_to_string(0, 0, 10094858, 1)
        self.zoom = 100
        self.zoom_request_template = self.template_to_string(0, 0, 10094861, 1)
        self.led1_mode = 'auto'
        self.led1_mode_request_template = self.template_to_string(0, 0, 168062213, 1)
        self.led1_frequency = 0
        self.led1_frequency_request_template = self.template_to_string(0, 0, 168062214, 1)
        self.jpeg_quality = 90
        self.jpeg_quality_request_template = self.template_to_string(0, 0, 1, 3)

        if camera is not None:
            if isinstance(camera, Camera):
                self.guid = camera.guid
                self.name = camera.name
                self.enabled = camera.enabled
                self.description = camera.description
                self.camera_type = camera.camera_type
                self.gcode_camera_script = camera.gcode_camera_script
                self.on_print_start_script = camera.on_print_start_script
                self.on_before_snapshot_script = camera.on_before_snapshot_script
                self.external_camera_snapshot_script = camera.external_camera_snapshot_script
                self.on_after_snapshot_script = camera.on_after_snapshot_script
                self.on_before_render_script = camera.on_before_render_script
                self.on_after_render_script = camera.on_after_render_script
                self.delay = camera.delay
                self.timeout_ms = camera.timeout_ms
                self.apply_settings_before_print = camera.apply_settings_before_print
                self.address = camera.address
                self.snapshot_request_template = camera.snapshot_request_template
                self.snapshot_transpose = camera.snapshot_transpose
                self.ignore_ssl_error = camera.ignore_ssl_error
                self.username = camera.username
                self.password = camera.password
                self.brightness = camera.brightness
                self.brightness_request_template = camera.brightness_request_template
                self.contrast = camera.contrast
                self.contrast_request_template = camera.contrast_request_template
                self.saturation = camera.saturation
                self.saturation_request_template = camera.saturation_request_template
                self.white_balance_auto = camera.white_balance_auto
                self.white_balance_auto_request_template = camera.white_balance_auto_request_template
                self.gain = camera.gain
                self.gain_request_template = camera.gain_request_template
                self.powerline_frequency = camera.powerline_frequency
                self.powerline_frequency_request_template = camera.powerline_frequency_request_template
                self.white_balance_temperature = camera.white_balance_temperature
                self.white_balance_temperature_request_template = camera.white_balance_temperature_request_template
                self.sharpness = camera.sharpness
                self.sharpness_request_template = camera.sharpness_request_template
                self.backlight_compensation_enabled = camera.backlight_compensation_enabled
                self.backlight_compensation_enabled_request_template = camera.backlight_compensation_enabled_request_template
                self.exposure_type = camera.exposure_type
                self.exposure_type_request_template = camera.exposure_type_request_template
                self.exposure = camera.exposure
                self.exposure_request_template = camera.exposure_request_template
                self.exposure_auto_priority_enabled = camera.exposure_auto_priority_enabled
                self.exposure_auto_priority_enabled_request_template = camera.exposure_auto_priority_enabled_request_template
                self.pan = camera.pan
                self.pan_request_template = camera.pan_request_template
                self.tilt = camera.tilt
                self.tilt_request_template = camera.tilt_request_template
                self.autofocus_enabled = camera.autofocus_enabled
                self.autofocus_enabled_request_template = camera.autofocus_enabled_request_template
                self.focus = camera.focus
                self.focus_request_template = camera.focus_request_template
                self.zoom = camera.zoom
                self.zoom_request_template = camera.zoom_request_template
                self.led1_mode = camera.led1_mode
                self.led1_mode_request_template = camera.led1_mode_request_template
                self.led1_frequency = camera.led1_frequency
                self.led1_frequency_request_template = camera.led1_frequency_request_template
                self.jpeg_quality = camera.jpeg_quality
                self.jpeg_quality_request_template = camera.jpeg_quality_request_template
            else:
                self.update(camera)

    @staticmethod
    def template_to_string(destination, plugin, setting_id, group):
        return (
            "{camera_address}?action=command&"
            + "dest=" + str(destination)
            + "&plugin=" + str(plugin)
            + "&id=" + str(setting_id)
            + "&group=" + str(group)
            + "&value={value}"
        )

    def update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "enabled" in changes.keys():
            self.enabled = utility.get_bool(changes["enabled"], self.enabled)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        if "camera_type" in changes.keys():
            self.camera_type = utility.get_string(
                changes["camera_type"], self.camera_type)
        if "gcode_camera_script" in changes.keys():
            self.gcode_camera_script = utility.get_string(
                changes["gcode_camera_script"], self.gcode_camera_script)
        if "on_print_start_script" in changes.keys():
            self.on_print_start_script = utility.get_string(
                changes["on_print_start_script"], self.on_print_start_script)
        if "on_before_snapshot_script" in changes.keys():
            self.on_before_snapshot_script = utility.get_string(
                changes["on_before_snapshot_script"], self.on_before_snapshot_script)
        if "external_camera_snapshot_script" in changes.keys():
            self.external_camera_snapshot_script = utility.get_string(
                changes["external_camera_snapshot_script"], self.external_camera_snapshot_script)
        if "on_after_snapshot_script" in changes.keys():
            self.on_after_snapshot_script = utility.get_string(
                changes["on_after_snapshot_script"], self.on_after_snapshot_script)
        if "on_before_render_script" in changes.keys():
            self.on_before_render_script = utility.get_string(
                changes["on_before_render_script"], self.on_before_render_script)
        if "on_after_render_script" in changes.keys():
            self.on_after_render_script = utility.get_string(
                changes["on_after_render_script"], self.on_after_render_script)
        if "delay" in changes.keys():
            self.delay = utility.get_int(
                changes["delay"], self.delay)
        if "timeout_ms" in changes.keys():
            self.timeout_ms = utility.get_int(
                changes["timeout_ms"], self.timeout_ms)
        if "address" in changes.keys():
            self.address = utility.get_string(changes["address"], self.address)
        if "snapshot_request_template" in changes.keys():
            self.snapshot_request_template = utility.get_string(
                changes["snapshot_request_template"], self.snapshot_request_template)
        if "snapshot_transpose" in changes.keys():
            self.snapshot_transpose = utility.get_string(
                changes["snapshot_transpose"], self.snapshot_transpose)
        if "apply_settings_before_print" in changes.keys():
            self.apply_settings_before_print = utility.get_bool(
                changes["apply_settings_before_print"], self.apply_settings_before_print)
        if "ignore_ssl_error" in changes.keys():
            self.ignore_ssl_error = utility.get_bool(
                changes["ignore_ssl_error"], self.ignore_ssl_error)
        if "username" in changes.keys():
            self.username = utility.get_string(
                changes["username"], self.username)
        if "password" in changes.keys():
            self.password = utility.get_string(
                changes["password"], self.password)

        if "brightness" in changes.keys():
            self.brightness = utility.get_int(
                changes["brightness"], self.brightness)
        if "contrast" in changes.keys():
            self.contrast = utility.get_int(changes["contrast"], self.contrast)
        if "saturation" in changes.keys():
            self.saturation = utility.get_int(
                changes["saturation"], self.saturation)
        if "white_balance_auto" in changes.keys():
            self.white_balance_auto = utility.get_bool(
                changes["white_balance_auto"], self.white_balance_auto)
        if "gain" in changes.keys():
            self.gain = utility.get_int(changes["gain"], self.gain)
        if "powerline_frequency" in changes.keys():
            self.powerline_frequency = utility.get_int(
                changes["powerline_frequency"], self.powerline_frequency)
        if "white_balance_temperature" in changes.keys():
            self.white_balance_temperature = utility.get_int(
                changes["white_balance_temperature"], self.white_balance_temperature)
        if "sharpness" in changes.keys():
            self.sharpness = utility.get_int(
                changes["sharpness"], self.sharpness)
        if "backlight_compensation_enabled" in changes.keys():
            self.backlight_compensation_enabled = utility.get_bool(
                changes["backlight_compensation_enabled"], self.backlight_compensation_enabled)
        if "exposure_type" in changes.keys():
            self.exposure_type = utility.get_int(
                changes["exposure_type"], self.exposure_type)
        if "exposure" in changes.keys():
            self.exposure = utility.get_int(changes["exposure"], self.exposure)
        if "exposure_auto_priority_enabled" in changes.keys():
            self.exposure_auto_priority_enabled = utility.get_bool(
                changes["exposure_auto_priority_enabled"], self.exposure_auto_priority_enabled)
        if "pan" in changes.keys():
            self.pan = utility.get_int(changes["pan"], self.pan)
        if "tilt" in changes.keys():
            self.tilt = utility.get_int(changes["tilt"], self.tilt)
        if "autofocus_enabled" in changes.keys():
            self.autofocus_enabled = utility.get_bool(
                changes["autofocus_enabled"], self.autofocus_enabled)
        if "focus" in changes.keys():
            self.focus = utility.get_int(changes["focus"], self.focus)
        if "zoom" in changes.keys():
            self.zoom = utility.get_int(changes["zoom"], self.zoom)
        if "led1_mode" in changes.keys():
            self.led1_mode = utility.get_string(
                changes["led1_mode"], self.led1_frequency)
        if "led1_frequency" in changes.keys():
            self.led1_frequency = utility.get_int(
                changes["led1_frequency"], self.led1_frequency)
        if "jpeg_quality" in changes.keys():
            self.jpeg_quality = utility.get_int(
                changes["jpeg_quality"], self.jpeg_quality)

        if "brightness_request_template" in changes.keys():
            self.brightness_request_template = utility.get_string(
                changes["brightness_request_template"], self.brightness_request_template)
        if "contrast_request_template" in changes.keys():
            self.contrast_request_template = utility.get_string(
                changes["contrast_request_template"], self.contrast_request_template)
        if "saturation_request_template" in changes.keys():
            self.saturation_request_template = utility.get_string(
                changes["saturation_request_template"], self.saturation_request_template)
        if "white_balance_auto_request_template" in changes.keys():
            self.white_balance_auto_request_template = utility.get_string(
                changes["white_balance_auto_request_template"], self.white_balance_auto_request_template)
        if "gain_request_template" in changes.keys():
            self.gain_request_template = utility.get_string(
                changes["gain_request_template"], self.gain_request_template)
        if "powerline_frequency_request_template" in changes.keys():
            self.powerline_frequency_request_template = utility.get_string(
                changes["powerline_frequency_request_template"], self.powerline_frequency_request_template)
        if "white_balance_temperature_request_template" in changes.keys():
            self.white_balance_temperature_request_template = utility.get_string(
                changes["white_balance_temperature_request_template"], self.white_balance_temperature_request_template)
        if "sharpness_request_template" in changes.keys():
            self.sharpness_request_template = utility.get_string(
                changes["sharpness_request_template"], self.sharpness_request_template)
        if "backlight_compensation_enabled_request_template" in changes.keys():
            self.backlight_compensation_enabled_request_template = utility.get_string(
                changes["backlight_compensation_enabled_request_template"],
                self.backlight_compensation_enabled_request_template
            )
        if "exposure_type_request_template" in changes.keys():
            self.exposure_type_request_template = utility.get_string(
                changes["exposure_type_request_template"], self.exposure_type_request_template)
        if "exposure_request_template" in changes.keys():
            self.exposure_request_template = utility.get_string(
                changes["exposure_request_template"], self.exposure_request_template)
        if "exposure_auto_priority_enabled_request_template" in changes.keys():
            self.exposure_auto_priority_enabled_request_template = utility.get_string(
                changes["exposure_auto_priority_enabled_request_template"],
                self.exposure_auto_priority_enabled_request_template
            )
        if "pan_request_template" in changes.keys():
            self.pan_request_template = utility.get_string(
                changes["pan_request_template"], self.pan_request_template)
        if "tilt_request_template" in changes.keys():
            self.tilt_request_template = utility.get_string(
                changes["tilt_request_template"], self.tilt_request_template)
        if "autofocus_enabled_request_template" in changes.keys():
            self.autofocus_enabled_request_template = utility.get_string(
                changes["autofocus_enabled_request_template"], self.autofocus_enabled_request_template)
        if "focus_request_template" in changes.keys():
            self.focus_request_template = utility.get_string(
                changes["focus_request_template"], self.focus_request_template)
        if "led1_mode_request_template" in changes.keys():
            self.led1_mode_request_template = utility.get_string(
                changes["led1_mode_request_template"], self.led1_mode_request_template)
        if "led1_frequency_request_template" in changes.keys():
            self.led1_frequency_request_template = utility.get_string(
                changes["led1_frequency_request_template"], self.led1_frequency_request_template)
        if "jpeg_quality_request_template" in changes.keys():
            self.jpeg_quality_request_template = utility.get_string(
                changes["jpeg_quality_request_template"], self.jpeg_quality_request_template)
        if "zoom_request_template" in changes.keys():
            self.zoom_request_template = utility.get_string(
                changes["zoom_request_template"], self.zoom_request_template)

    def to_dict(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'enabled': self.enabled,
            'description': self.description,
            'camera_type': self.camera_type,
            'gcode_camera_script': self.gcode_camera_script,
            'on_print_start_script': self.on_print_start_script,
            'on_before_snapshot_script': self.on_before_snapshot_script,
            'external_camera_snapshot_script': self.external_camera_snapshot_script,
            'on_after_snapshot_script': self.on_after_snapshot_script,
            'on_before_render_script': self.on_before_render_script,
            'on_after_render_script': self.on_after_render_script,
            'delay': self.delay,
            'timeout_ms': self.timeout_ms,
            'address': self.address,
            'snapshot_request_template': self.snapshot_request_template,
            'snapshot_transpose': self.snapshot_transpose,
            'apply_settings_before_print': self.apply_settings_before_print,
            'ignore_ssl_error': self.ignore_ssl_error,
            'password': self.password,
            'username': self.username,
            'brightness': self.brightness,
            'contrast': self.contrast,
            'saturation': self.saturation,
            'white_balance_auto': self.white_balance_auto,
            'gain': self.gain,
            'powerline_frequency': self.powerline_frequency,
            'white_balance_temperature': self.white_balance_temperature,
            'sharpness': self.sharpness,
            'backlight_compensation_enabled': self.backlight_compensation_enabled,
            'exposure_type': self.exposure_type,
            'exposure': self.exposure,
            'exposure_auto_priority_enabled': self.exposure_auto_priority_enabled,
            'pan': self.pan,
            'tilt': self.tilt,
            'autofocus_enabled': self.autofocus_enabled,
            'focus': self.focus,
            'zoom': self.zoom,
            'led1_mode': self.led1_mode,
            'led1_frequency': self.led1_frequency,
            'jpeg_quality': self.jpeg_quality,
            'brightness_request_template': self.brightness_request_template,
            'contrast_request_template': self.contrast_request_template,
            'saturation_request_template': self.saturation_request_template,
            'white_balance_auto_request_template': self.white_balance_auto_request_template,
            'gain_request_template': self.gain_request_template,
            'powerline_frequency_request_template': self.powerline_frequency_request_template,
            'white_balance_temperature_request_template': self.white_balance_temperature_request_template,
            'sharpness_request_template': self.sharpness_request_template,
            'backlight_compensation_enabled_request_template': self.backlight_compensation_enabled_request_template,
            'exposure_type_request_template': self.exposure_type_request_template,
            'exposure_request_template': self.exposure_request_template,
            'exposure_auto_priority_enabled_request_template': self.exposure_auto_priority_enabled_request_template,
            'pan_request_template': self.pan_request_template,
            'tilt_request_template': self.tilt_request_template,
            'autofocus_enabled_request_template': self.autofocus_enabled_request_template,
            'focus_request_template': self.focus_request_template,
            'zoom_request_template': self.zoom_request_template,
            'led1_mode_request_template': self.led1_mode_request_template,
            'led1_frequency_request_template': self.led1_frequency_request_template,
            'jpeg_quality_request_template': self.jpeg_quality_request_template,
        }


class DebugProfile(object):
    Logger = None
    FormatString = '%(asctime)s - %(levelname)s - %(message)s'
    ConsoleFormatString = '{asctime} - {levelname} - {message}'
    Logging_Executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def get_logger(self):
        _logger = logging.getLogger(
            "octoprint.plugins.octolapse")

        from octoprint.logging.handlers import CleaningTimedRotatingFileHandler
        octoprint_logging_handler = CleaningTimedRotatingFileHandler(
            self.logFilePath, when="D", backupCount=3)

        octoprint_logging_handler.setFormatter(
            logging.Formatter("%(asctime)s %(message)s"))
        octoprint_logging_handler.setLevel(logging.DEBUG)
        _logger.addHandler(octoprint_logging_handler)
        _logger.propagate = False
        # we are controlling our logging via settings, so set to debug so that nothing is filtered
        _logger.setLevel(logging.DEBUG)

        return _logger

    def __init__(self, log_file_path, debug_profile=None, guid=None, name="Default Debug Profile"):
        self.logFilePath = log_file_path
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        # Configure the logger if it has not been created
        if DebugProfile.Logger is None:
            DebugProfile.Logger = self.get_logger()

        self.log_to_console = False
        self.enabled = False
        self.is_test_mode = False
        self.position_change = False
        self.position_command_received = False
        self.extruder_change = False
        self.extruder_triggered = False
        self.trigger_create = False
        self.trigger_wait_state = False
        self.trigger_triggering = False
        self.trigger_triggering_state = False
        self.trigger_layer_change = False
        self.trigger_height_change = False
        self.trigger_zhop = False
        self.trigger_time_unpaused = False
        self.trigger_time_remaining = False
        self.snapshot_gcode = False
        self.snapshot_gcode_endcommand = False
        self.snapshot_position = False
        self.snapshot_position_return = False
        self.snapshot_position_resume_print = False
        self.snapshot_save = False
        self.snapshot_download = False
        self.render_start = False
        self.render_complete = False
        self.render_fail = False
        self.render_sync = False
        self.snapshot_clean = False
        self.settings_save = False
        self.settings_load = False
        self.print_state_changed = False
        self.camera_settings_apply = False
        self.gcode_sent_all = False
        self.gcode_queuing_all = False
        self.gcode_received_all = False

        if debug_profile is not None:
            self.update(debug_profile)

    def update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        if "enabled" in changes.keys():
            self.enabled = utility.get_bool(changes["enabled"], self.enabled)
        if "is_test_mode" in changes.keys():
            self.is_test_mode = utility.get_bool(
                changes["is_test_mode"], self.enabled)
        if "log_to_console" in changes.keys():
            self.log_to_console = utility.get_bool(
                changes["log_to_console"], self.log_to_console)
        if "position_change" in changes.keys():
            self.position_change = utility.get_bool(
                changes["position_change"], self.position_change)
        if "position_command_received" in changes.keys():
            self.position_command_received = utility.get_bool(
                changes["position_command_received"], self.position_command_received)
        if "extruder_change" in changes.keys():
            self.extruder_change = utility.get_bool(
                changes["extruder_change"], self.extruder_change)
        if "extruder_triggered" in changes.keys():
            self.extruder_triggered = utility.get_bool(
                changes["extruder_triggered"], self.extruder_triggered)
        if "trigger_create" in changes.keys():
            self.trigger_create = utility.get_bool(
                changes["trigger_create"], self.trigger_create)
        if "trigger_wait_state" in changes.keys():
            self.trigger_wait_state = utility.get_bool(
                changes["trigger_wait_state"], self.trigger_wait_state)
        if "trigger_triggering" in changes.keys():
            self.trigger_triggering = utility.get_bool(
                changes["trigger_triggering"], self.trigger_triggering)
        if "trigger_triggering_state" in changes.keys():
            self.trigger_triggering_state = utility.get_bool(
                changes["trigger_triggering_state"], self.trigger_triggering_state)
        if "trigger_layer_change" in changes.keys():
            self.trigger_layer_change = utility.get_bool(
                changes["trigger_layer_change"], self.trigger_layer_change)
        if "trigger_height_change" in changes.keys():
            self.trigger_height_change = utility.get_bool(
                changes["trigger_height_change"], self.trigger_height_change)
        if "trigger_time_remaining" in changes.keys():
            self.trigger_time_remaining = utility.get_bool(
                changes["trigger_time_remaining"], self.trigger_time_remaining)
        if "trigger_time_unpaused" in changes.keys():
            self.trigger_time_unpaused = utility.get_bool(
                changes["trigger_time_unpaused"], self.trigger_time_unpaused)
        if "trigger_zhop" in changes.keys():
            self.trigger_zhop = utility.get_bool(
                changes["trigger_zhop"], self.trigger_zhop)
        if "snapshot_gcode" in changes.keys():
            self.snapshot_gcode = utility.get_bool(
                changes["snapshot_gcode"], self.snapshot_gcode)
        if "snapshot_gcode_endcommand" in changes.keys():
            self.snapshot_gcode_endcommand = utility.get_bool(
                changes["snapshot_gcode_endcommand"], self.snapshot_gcode_endcommand)
        if "snapshot_position" in changes.keys():
            self.snapshot_position = utility.get_bool(
                changes["snapshot_position"], self.snapshot_position)
        if "snapshot_position_return" in changes.keys():
            self.snapshot_position_return = utility.get_bool(
                changes["snapshot_position_return"], self.snapshot_position_return)
        if "snapshot_position_resume_print" in changes.keys():
            self.snapshot_position_resume_print = utility.get_bool(
                changes["snapshot_position_resume_print"], self.snapshot_position_resume_print)
        if "snapshot_save" in changes.keys():
            self.snapshot_save = utility.get_bool(
                changes["snapshot_save"], self.snapshot_save)
        if "snapshot_download" in changes.keys():
            self.snapshot_download = utility.get_bool(
                changes["snapshot_download"], self.snapshot_download)
        if "render_start" in changes.keys():
            self.render_start = utility.get_bool(
                changes["render_start"], self.snapshot_download)
        if "render_complete" in changes.keys():
            self.render_complete = utility.get_bool(
                changes["render_complete"], self.render_complete)
        if "render_fail" in changes.keys():
            self.render_fail = utility.get_bool(
                changes["render_fail"], self.snapshot_download)
        if "render_sync" in changes.keys():
            self.render_sync = utility.get_bool(
                changes["render_sync"], self.snapshot_download)
        if "snapshot_clean" in changes.keys():
            self.snapshot_clean = utility.get_bool(
                changes["snapshot_clean"], self.snapshot_clean)
        if "settings_save" in changes.keys():
            self.settings_save = utility.get_bool(
                changes["settings_save"], self.settings_save)
        if "settings_load" in changes.keys():
            self.settings_load = utility.get_bool(
                changes["settings_load"], self.settings_load)
        if "print_state_changed" in changes.keys():
            self.print_state_changed = utility.get_bool(
                changes["print_state_changed"], self.print_state_changed)
        if "camera_settings_apply" in changes.keys():
            self.camera_settings_apply = utility.get_bool(
                changes["camera_settings_apply"], self.camera_settings_apply)
        if "gcode_sent_all" in changes.keys():
            self.gcode_sent_all = utility.get_bool(
                changes["gcode_sent_all"], self.gcode_sent_all)
        if "gcode_queuing_all" in changes.keys():
            self.gcode_queuing_all = utility.get_bool(
                changes["gcode_queuing_all"], self.gcode_queuing_all)
        if "gcode_received_all" in changes.keys():
            self.gcode_received_all = utility.get_bool(
                changes["gcode_received_all"], self.gcode_received_all)

    def to_dict(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'is_test_mode': self.is_test_mode,
            'log_to_console': self.log_to_console,
            'position_change': self.position_change,
            'position_command_received': self.position_command_received,
            'extruder_change': self.extruder_change,
            'extruder_triggered': self.extruder_triggered,
            'trigger_create': self.trigger_create,
            'trigger_wait_state': self.trigger_wait_state,
            'trigger_triggering': self.trigger_triggering,
            'trigger_triggering_state': self.trigger_triggering_state,
            'trigger_layer_change': self.trigger_layer_change,
            'trigger_height_change': self.trigger_height_change,
            'trigger_time_remaining': self.trigger_time_remaining,
            'trigger_time_unpaused': self.trigger_time_unpaused,
            'trigger_zhop': self.trigger_zhop,
            'snapshot_gcode': self.snapshot_gcode,
            'snapshot_gcode_endcommand': self.snapshot_gcode_endcommand,
            'snapshot_position': self.snapshot_position,
            'snapshot_position_return': self.snapshot_position_return,
            'snapshot_position_resume_print': self.snapshot_position_resume_print,
            'snapshot_save': self.snapshot_save,
            'snapshot_download': self.snapshot_download,
            'render_start': self.render_start,
            'render_complete': self.render_complete,
            'render_fail': self.render_fail,
            'render_sync': self.render_sync,
            'snapshot_clean': self.snapshot_clean,
            'settings_save': self.settings_save,
            'settings_load': self.settings_load,
            'print_state_changed': self.print_state_changed,
            'camera_settings_apply': self.camera_settings_apply,
            'gcode_sent_all': self.gcode_sent_all,
            'gcode_queuing_all': self.gcode_queuing_all,
            'gcode_received_all': self.gcode_received_all
        }

    def log_console(self, level_name, message, force=False):
        if self.log_to_console or force:
            print(DebugProfile.ConsoleFormatString.format(asctime=str(
                datetime.now()), levelname=level_name, message=message))

    def log_info(self, message):
        if self.enabled:
            DebugProfile.Logging_Executor.submit(self.Logger.info, message)
            self.log_console('info', message)

    def log_warning(self, message):
        if self.enabled:
            DebugProfile.Logging_Executor.submit(self.Logger.warning, message)
            self.log_console('warn', message)

    def log_exception(self, exception):
        message = utility.exception_to_string(exception)
        DebugProfile.Logging_Executor.submit(self.Logger.error, message)
        self.log_console('error', message)

    def log_error(self, message):
        DebugProfile.Logging_Executor.submit(self.Logger.error, message)
        self.log_console('error', message)

    def log_position_change(self, message):
        if self.position_change:
            self.log_info(message)

    def log_position_command_received(self, message):
        if self.position_command_received:
            self.log_info(message)

    def log_extruder_change(self, message):
        if self.extruder_change:
            self.log_info(message)

    def log_extruder_triggered(self, message):
        if self.extruder_triggered:
            self.log_info(message)

    def log_trigger_create(self, message):
        if self.trigger_create:
            self.log_info(message)

    def log_trigger_wait_state(self, message):
        if self.trigger_wait_state:
            self.log_info(message)

    def log_triggering(self, message):
        if self.trigger_triggering:
            self.log_info(message)

    def log_triggering_state(self, message):
        if self.trigger_triggering_state:
            self.log_info(message)

    def log_trigger_height_change(self, message):
        if self.trigger_height_change:
            self.log_info(message)

    def log_position_layer_change(self, message):
        if self.position_change:
            self.log_info(message)

    def log_position_height_change(self, message):
        if self.position_change:
            self.log_info(message)

    def log_position_zhop(self, message):
        if self.trigger_zhop:
            self.log_info(message)

    def log_timer_trigger_unpaused(self, message):
        if self.trigger_time_unpaused:
            self.log_info(message)

    def log_trigger_time_remaining(self, message):
        if self.trigger_time_remaining:
            self.log_info(message)

    def log_snapshot_gcode(self, message):
        if self.snapshot_gcode:
            self.log_info(message)

    def log_snapshot_gcode_end_command(self, message):
        if self.snapshot_gcode_endcommand:
            self.log_info(message)

    def log_snapshot_position(self, message):
        if self.snapshot_position:
            self.log_info(message)

    def log_snapshot_return_position(self, message):
        if self.snapshot_position_return:
            self.log_info(message)

    def log_snapshot_resume_position(self, message):
        if self.snapshot_position_resume_print:
            self.log_info(message)

    def log_snapshot_save(self, message):
        if self.snapshot_save:
            self.log_info(message)

    def log_snapshot_download(self, message):
        if self.snapshot_download:
            self.log_info(message)

    def log_render_start(self, message):
        if self.render_start:
            self.log_info(message)

    def log_render_complete(self, message):
        if self.render_complete:
            self.log_info(message)

    def log_render_fail(self, message):
        if self.render_fail:
            self.log_info(message)

    def log_render_sync(self, message):
        if self.render_sync:
            self.log_info(message)

    def log_snapshot_clean(self, message):
        if self.snapshot_clean:
            self.log_info(message)

    def log_settings_save(self, message):
        if self.settings_save:
            self.log_info(message)

    def log_settings_load(self, message):
        if self.settings_load:
            self.log_info(message)

    def log_print_state_change(self, message):
        if self.print_state_changed:
            self.log_info(message)

    def log_camera_settings_apply(self, message):
        if self.camera_settings_apply:
            self.log_info(message)

    def log_gcode_sent(self, message):
        if self.gcode_sent_all:
            self.log_info(message)

    def log_gcode_queuing(self, message):
        if self.gcode_queuing_all:
            self.log_info(message)

    def log_gcode_received(self, message):
        if self.gcode_received_all:
            self.log_info(message)


class OctolapseSettings(object):
    DefaultDebugProfile = None
    Logger = None

    # constants

    def __init__(self, log_file_path, settings=None, plugin_version="unknown"):
        self.rendering_file_templates = [
            "FAILEDFLAG",
            "FAILEDSTATE",
            "FAILEDSEPARATOR",
            "PRINTSTATE",
            "GCODEFILENAME",
            "DATETIMESTAMP",
            "PRINTENDTIME",
            "PRINTENDTIMESTAMP",
            "PRINTSTARTTIME",
            "PRINTSTARTTIMESTAMP",
            "SNAPSHOTCOUNT",
            "FPS"
        ]
        self.overlay_text_templates = [
            "snapshot_number",
            "current_time",
            "time_elapsed",
        ]
        self.overlay_text_alignment_options = [
            "left",
            "center",
            "right",
        ]
        self.overlay_text_valign_options = [
            "top",
            "middle",
            "bottom",
        ]
        self.overlay_text_halign_options = [
            "left",
            "center",
            "right",
        ]
        self.DefaultPrinter = Printer(
            name="Default Printer", guid="5d39248f-5e11-4c42-b7f4-810c7acc287e")
        self.DefaultStabilization = Stabilization(
            name="Default Stabilization", guid="3a94e945-f5d5-4655-909a-e61c1122cc1f")
        self.DefaultSnapshot = Snapshot(
            name="Default Snapshot", guid="5d16f0cb-512c-476a-b32d-a10191ad0d0e")
        self.DefaultRendering = Rendering(
            name="Default Rendering", guid="32d6ad28-0314-4a14-974c-0d7d92325f17")
        self.DefaultCamera = Camera(
            name="Default Camera", guid="6b3361a7-82b7-4abf-b3d1-e3046d457d8c")
        self.DefaultDebugProfile = DebugProfile(
            log_file_path=log_file_path, name="Default Debug", guid="08ad284a-76cc-4854-b8a0-f2658b784dd7")
        self.LogFilePath = log_file_path

        self.version = plugin_version
        self.show_navbar_icon = True
        self.show_navbar_when_not_printing = True
        self.is_octolapse_enabled = True
        self.auto_reload_latest_snapshot = True
        self.auto_reload_frames = 5
        self.show_position_state_changes = False
        self.show_position_changes = False
        self.show_extruder_state_changes = False
        self.show_trigger_state_changes = False
        self.current_printer_profile_guid = None
        self.show_real_snapshot_time = False
        self.cancel_print_on_startup_error = True
        self.printers = {}

        stabilization = self.DefaultStabilization
        self.current_stabilization_profile_guid = stabilization.guid
        self.stabilizations = {stabilization.guid: stabilization}

        snapshot = self.DefaultSnapshot
        self.current_snapshot_profile_guid = snapshot.guid
        self.snapshots = {snapshot.guid: snapshot}

        rendering = self.DefaultRendering
        self.current_rendering_profile_guid = rendering.guid
        self.renderings = {rendering.guid: rendering}

        camera = self.DefaultCamera
        # there is no current camera profile guid.
        self.current_camera_profile_guid = camera.guid
        self.cameras = {camera.guid: camera}

        debug_profile = self.DefaultDebugProfile
        self.current_debug_profile_guid = debug_profile.guid
        self.debug_profiles = {debug_profile.guid: debug_profile}

        if settings is not None:
            self.update(settings)

    def active_cameras(self):
        _active_cameras = []
        for key in self.cameras:
            _current_camera = self.cameras[key]
            if _current_camera.enabled:
                _active_cameras.append(_current_camera)

        return _active_cameras

    def current_stabilization(self):
        if len(self.stabilizations.keys()) == 0:
            stabilization = Stabilization(None)
            self.stabilizations[stabilization.guid] = stabilization
            self.current_stabilization_profile_guid = stabilization.guid
        return self.stabilizations[self.current_stabilization_profile_guid]

    def current_snapshot(self):
        if len(self.snapshots.keys()) == 0:
            snapshot = Snapshot(None)
            self.snapshots[snapshot.guid] = snapshot
            self.current_snapshot_profile_guid = snapshot.guid
        return self.snapshots[self.current_snapshot_profile_guid]

    def current_rendering(self):
        if len(self.renderings.keys()) == 0:
            rendering = Rendering(None)
            self.renderings[rendering.guid] = rendering
            self.current_rendering_profile_guid = rendering.guid
        return self.renderings[self.current_rendering_profile_guid]

    def current_printer(self):
        if self.current_printer_profile_guid is None or self.current_printer_profile_guid not in self.printers:
            return None
        return self.printers[self.current_printer_profile_guid]

    def current_camera_profile(self):
        if len(self.cameras.keys()) == 0:
            camera = Camera(None)
            self.cameras[camera.guid] = camera
            self.current_camera_profile_guid = camera.guid
        return self.debug_profiles[self.current_camera_profile_guid]

    def current_debug_profile(self):
        if len(self.debug_profiles.keys()) == 0:
            debug_profile = DebugProfile(self.LogFilePath)
            self.debug_profiles[debug_profile.guid] = debug_profile
            self.current_debug_profile_guid = debug_profile.guid
        return self.debug_profiles[self.current_debug_profile_guid]

    def update(self, changes):

        if has_key(changes, "is_octolapse_enabled"):
            self.is_octolapse_enabled = bool(
                get_value(changes, "is_octolapse_enabled", self.is_octolapse_enabled))
        if has_key(changes, "auto_reload_latest_snapshot"):
            self.auto_reload_latest_snapshot = bool(get_value(
                changes, "auto_reload_latest_snapshot", self.auto_reload_latest_snapshot))
        if has_key(changes, "auto_reload_frames"):
            self.auto_reload_frames = int(
                get_value(changes, "auto_reload_frames", self.auto_reload_frames))
        if has_key(changes, "show_navbar_icon"):
            self.show_navbar_icon = bool(
                get_value(changes, "show_navbar_icon", self.show_navbar_icon))
        if has_key(changes, "show_navbar_when_not_printing"):
            self.show_navbar_when_not_printing = bool(get_value(
                changes, "show_navbar_when_not_printing", self.show_navbar_when_not_printing))
        if has_key(changes, "show_position_state_changes"):
            self.show_position_state_changes = bool(get_value(
                changes, "show_position_state_changes", self.show_position_state_changes))
        if has_key(changes, "show_position_changes"):
            self.show_position_changes = bool(
                get_value(changes, "show_position_changes", self.show_position_changes))
        if has_key(changes, "show_extruder_state_changes"):
            self.show_extruder_state_changes = bool(get_value(
                changes, "show_extruder_state_changes", self.show_extruder_state_changes))
        if has_key(changes, "show_trigger_state_changes"):
            self.show_trigger_state_changes = bool(get_value(
                changes, "show_trigger_state_changes", self.show_trigger_state_changes))
        if has_key(changes, "current_printer_profile_guid"):
            self.current_printer_profile_guid = get_value(
                changes, "current_printer_profile_guid", self.current_printer_profile_guid
            )
        if has_key(changes, "current_stabilization_profile_guid"):
            self.current_stabilization_profile_guid = str(get_value(
                changes, "current_stabilization_profile_guid", self.current_stabilization_profile_guid))
        if has_key(changes, "current_snapshot_profile_guid"):
            self.current_snapshot_profile_guid = str(get_value(
                changes, "current_snapshot_profile_guid", self.current_snapshot_profile_guid))
        if has_key(changes, "current_rendering_profile_guid"):
            self.current_rendering_profile_guid = str(get_value(
                changes, "current_rendering_profile_guid", self.current_rendering_profile_guid))
        if has_key(changes, "current_camera_profile_guid"):
            self.current_camera_profile_guid = str(get_value(
                changes, "current_camera_profile_guid", self.current_camera_profile_guid))
        if has_key(changes, "current_debug_profile_guid"):
            self.current_debug_profile_guid = str(get_value(
                changes, "current_debug_profile_guid", self.current_debug_profile_guid))
        if has_key(changes, "show_real_snapshot_time"):
            self.show_real_snapshot_time = bool(
                get_value(changes, "show_real_snapshot_time", self.show_real_snapshot_time))
        if has_key(changes, "cancel_print_on_startup_error"):
            self.cancel_print_on_startup_error = bool(
                get_value(changes, "cancel_print_on_startup_error", self.cancel_print_on_startup_error))


        if has_key(changes, "printers"):
            self.printers = {}
            printers = get_value(changes, "printers", None)
            for printer in printers:
                if printer["guid"] == "":
                    printer["guid"] = str(uuid.uuid4())
                self.printers.update({printer["guid"]: Printer(printer=printer)})
        if has_key(changes, "stabilizations"):
            self.stabilizations = {}
            stabilizations = get_value(changes, "stabilizations", None)
            for stabilization in stabilizations:
                if stabilization["guid"] == "":
                    stabilization["guid"] = str(uuid.uuid4())
                self.stabilizations.update({stabilization["guid"]: Stabilization(stabilization=stabilization)})

        if has_key(changes, "snapshots"):
            self.snapshots = {}
            snapshots = get_value(changes, "snapshots", None)
            for snapshot in snapshots:
                if snapshot["guid"] == "":
                    snapshot["guid"] = str(uuid.uuid4())
                self.snapshots.update({snapshot["guid"]: Snapshot(snapshot=snapshot)})

        if has_key(changes, "renderings"):
            self.renderings = {}
            renderings = get_value(changes, "renderings", None)
            for rendering in renderings:
                if rendering["guid"] == "":
                    rendering["guid"] = str(uuid.uuid4())
                self.renderings.update({rendering["guid"]: Rendering(
                    rendering=rendering)})

        if has_key(changes, "cameras"):
            self.cameras = {}
            cameras = get_value(changes, "cameras", None)
            for camera in cameras:
                if camera["guid"] == "":
                    camera["guid"] = str(uuid.uuid4())
                self.cameras.update({camera["guid"]: Camera(camera=camera)})

        if has_key(changes, "debug_profiles"):
            self.debug_profiles = {}
            debug_profiles = get_value(changes, "debug_profiles", None)
            for debugProfile in debug_profiles:
                if debugProfile["guid"] == "":
                    debugProfile["guid"] = str(uuid.uuid4())
                self.debug_profiles.update(
                    {debugProfile["guid"]: DebugProfile(self.LogFilePath, debug_profile=debugProfile)})

    def get_profiles_dict(self):
        profiles_dict = {
            'current_printer_profile_guid': self.current_printer_profile_guid,
            'current_stabilization_profile_guid': self.current_stabilization_profile_guid,
            'current_snapshot_profile_guid': self.current_snapshot_profile_guid,
            'current_rendering_profile_guid': self.current_rendering_profile_guid,
            'current_camera_profile_guid': self.current_camera_profile_guid,
            'current_debug_profile_guid': self.current_debug_profile_guid,
            'printers': [],
            'stabilizations': [],
            'snapshots': [],
            'renderings': [],
            'cameras': [],
            'debug_profiles': []
        }

        for key, printer in self.printers.items():
            profiles_dict["printers"].append({
                "name": printer.name,
                "guid": printer.guid,
                "has_been_saved_by_user": printer.has_been_saved_by_user
            })

        for key, stabilization in self.stabilizations.items():
            profiles_dict["stabilizations"].append({
                "name": stabilization.name,
                "guid": stabilization.guid
            })

        for key, snapshot in self.snapshots.items():
            profiles_dict["snapshots"].append({
                "name": snapshot.name,
                "guid": snapshot.guid
            })

        for key, rendering in self.renderings.items():
            profiles_dict["renderings"].append({
                "name": rendering.name,
                "guid": rendering.guid
            })

        for key, camera in self.cameras.items():
            profiles_dict["cameras"].append({
                "name": camera.name,
                "guid": camera.guid,
                "enabled": camera.enabled
            })

        for key, debugProfile in self.debug_profiles.items():
            profiles_dict["debug_profiles"].append({
                "name": debugProfile.name,
                "guid": debugProfile.guid
            })
        return profiles_dict

    def to_dict(self, ):
        defaults = OctolapseSettings(self.LogFilePath, self.version)

        settings_dict = {
            'version': utility.get_string(
                self.version, defaults.version
            ),
            "is_octolapse_enabled": utility.get_bool(
                self.is_octolapse_enabled, defaults.is_octolapse_enabled
            ),
            "auto_reload_latest_snapshot": utility.get_bool(
                self.auto_reload_latest_snapshot, defaults.auto_reload_latest_snapshot
            ),
            "auto_reload_frames": utility.get_int(
                self.auto_reload_frames, defaults.auto_reload_frames
            ),
            "show_navbar_icon": utility.get_bool(
                self.show_navbar_icon, defaults.show_navbar_icon
            ),
            "show_navbar_when_not_printing": utility.get_bool(
                self.show_navbar_when_not_printing, defaults.show_navbar_when_not_printing
            ),
            "show_position_changes": utility.get_bool(
                self.show_position_changes, defaults.show_position_changes
            ),
            "show_position_state_changes": utility.get_bool(
                self.show_position_state_changes, defaults.show_position_state_changes
            ),
            "show_extruder_state_changes": utility.get_bool(
                self.show_extruder_state_changes, defaults.show_extruder_state_changes
            ),
            "show_trigger_state_changes": utility.get_bool(
                self.show_trigger_state_changes, defaults.show_trigger_state_changes
            ),
            "show_real_snapshot_time": utility.get_bool(
                self.show_real_snapshot_time, defaults.show_real_snapshot_time
            ),
            "cancel_print_on_startup_error": utility.get_bool(
                self.cancel_print_on_startup_error, defaults.cancel_print_on_startup_error
            ),
            "platform": sys.platform,
            'slicer_type_options': [
                dict(value='cura', name='Cura'),
                dict(value='simplify-3d', name='Simplify 3D'),
                dict(value='slic3r-pe', name='Slic3r Prusa Edition'),
                dict(value='other', name='Other Slicer')
            ],
            'e_axis_default_mode_options': [
                dict(value='require-explicit', name='Require Explicit M82/M83'),
                dict(value='relative', name='Default To Relative'),
                dict(value='absolute', name='Default To Absolute'),
                #dict(value='force-absolute', name='Force Absolute (send M82 at print start)'),
                #dict(value='force-relative', name='Force Relative (send M83 at print start)')
            ],
            'axis_speed_display_unit_options': [
                dict(value='mm-min', name='Millimeters per Minute (mm/min)'),
                dict(value='mm-sec', name='Millimeters per Second (mm/sec)')
            ],

            'g90_influences_extruder_options': [
                dict(value='use-octoprint-settings', name='Use Octoprint Settings'),
                dict(value='true', name='True'),
                dict(value='false', name='False'),
            ],
            'xyz_axes_default_mode_options': [
                dict(value='require-explicit', name='Require Explicit G90/G91'),
                dict(value='relative', name='Default To Relative'),
                dict(value='absolute', name='Default To Absolute'),
                #dict(value='force-absolute', name='Force Absolute (send G90 at print start)'),
                #dict(value='force-relative', name='Force Relative (send G91 at print start)')
            ],
            'units_default_options': [
                dict(value='require-explicit', name='Require Explicit G21'),
                dict(value='inches', name='Inches'),
                dict(value='millimeters', name='Millimeters')
            ],
            'stabilization_type_options': [
                dict(value='disabled', name='Disabled'),
                dict(value='fixed_coordinate', name='Fixed Coordinate'),
                dict(value='fixed_path', name='List of Fixed Coordinates'),
                dict(value='relative', name='Relative Coordinate (0-100)'),
                dict(value='relative_path', name='List of Relative Coordinates')
            ],
            'trigger_types': [
                dict(value=Snapshot.LayerTriggerType, name="Layer/Height"),
                dict(value=Snapshot.TimerTriggerType, name="Timer"),
                dict(value=Snapshot.GcodeTriggerType, name="Gcode")
            ],
            'position_restriction_shapes': [
                dict(value="rect", name="Rectangle"),
                dict(value="circle", name="Circle")
            ],
            'position_restriction_types': [
                dict(value="required", name="Must be inside"),
                dict(value="forbidden", name="Cannot be inside")
            ],
            'snapshot_extruder_trigger_options': Snapshot.ExtruderTriggerOptions,
            'rendering_fps_calculation_options': [
                dict(value='static', name='Static FPS'),
                dict(value='duration', name='Fixed Run Length')
            ],
            'rendering_output_format_options': [
                dict(value='avi', name='AVI'),
                dict(value='flv', name='FLV'),
                dict(value='gif', name='GIF'),
                dict(value='h264', name='H.264/MPEG-4 AVC'),
                dict(value='mp4', name='MP4 (libxvid)'),
                dict(value='mpeg', name='MPEG'),
                dict(value='vob', name='VOB'),
            ],
            'rendering_file_templates': self.rendering_file_templates,
            'overlay_text_templates': self.overlay_text_templates,
            'overlay_text_alignment_options': self.overlay_text_alignment_options,
            'overlay_text_valign_options': self.overlay_text_valign_options,
            'overlay_text_halign_options': self.overlay_text_halign_options,
            'camera_powerline_frequency_options': [
                dict(value='50', name='50 HZ (Europe, China, India, etc)'),
                dict(value='60', name='60 HZ (North/South America, Japan, etc)')
            ],
            'camera_exposure_type_options': [
                dict(value='0', name='Unknown - Let me know if you know what this option does.'),
                dict(value='1', name='Manual'),
                dict(value='2', name='Unknown - Let me know if you know what this option does.'),
                dict(value='3', name='Auto - Aperture Priority Mode')
            ],
            'camera_led_1_mode_options': [
                dict(value='on', name='On'),
                dict(value='off', name='Off'),
                dict(value='blink', name='Blink'),
                dict(value='auto', name='Auto')
            ],
            'snapshot_transpose_options': [
                dict(value='', name='None'),
                dict(value='flip_left_right', name='Flip Left and Right'),
                dict(value='flip_top_bottom', name='Flip Top and Bottom'),
                dict(value='rotate_90', name='Rotate 90 Degrees'),
                dict(value='rotate_180', name='Rotate 180 Degrees'),
                dict(value='rotate_270', name='Rotate 270 Degrees'),
                dict(value='transpose', name='Transpose')
            ],
            'current_printer_profile_guid': utility.get_string(
                self.current_printer_profile_guid, defaults.current_printer_profile_guid
            ),
            'printers': [],
            'current_stabilization_profile_guid': utility.get_string(
                self.current_stabilization_profile_guid, defaults.current_stabilization_profile_guid
            ),
            'stabilizations': [],
            'current_snapshot_profile_guid': utility.get_string(
                self.current_snapshot_profile_guid, defaults.current_snapshot_profile_guid
            ),
            'snapshots': [],
            'current_rendering_profile_guid': utility.get_string(
                self.current_rendering_profile_guid, defaults.current_rendering_profile_guid
            ),
            'renderings': [],
            'cameras': [],
            'current_camera_profile_guid': utility.get_string(
                self.current_camera_profile_guid, defaults.current_camera_profile_guid
            ),
            'current_debug_profile_guid': utility.get_string(
                self.current_debug_profile_guid, defaults.current_debug_profile_guid
            ),
            'camera_type_options': [
                dict(value='webcam', name='Webcam'),
                dict(value='external-script', name='External Camera - Script'),
                dict(value='printer-gcode', name='Gcode Camera (built into printer)')
            ],
            'debug_profiles': []
        }

        for key, printer in self.printers.items():
            settings_dict["printers"].append(printer.to_dict())
        settings_dict["default_printer_profile"] = self.DefaultPrinter.to_dict()

        for key, stabilization in self.stabilizations.items():
            settings_dict["stabilizations"].append(stabilization.to_dict())
        settings_dict["default_stabilization_profile"] = self.DefaultStabilization.to_dict()

        for key, snapshot in self.snapshots.items():
            settings_dict["snapshots"].append(snapshot.to_dict())
        settings_dict["default_snapshot_profile"] = self.DefaultSnapshot.to_dict()

        for key, rendering in self.renderings.items():
            settings_dict["renderings"].append(rendering.to_dict())
        settings_dict["default_rendering_profile"] = self.DefaultRendering.to_dict()

        for key, camera in self.cameras.items():
            settings_dict["cameras"].append(camera.to_dict())
        settings_dict["default_camera_profile"] = self.DefaultCamera.to_dict()

        for key, debugProfile in self.debug_profiles.items():
            settings_dict["debug_profiles"].append(debugProfile.to_dict())
        settings_dict["default_debug_profile"] = self.DefaultDebugProfile.to_dict()

        return settings_dict

    def get_main_settings_dict(self):
        return {
            'is_octolapse_enabled': self.is_octolapse_enabled,
            'version': self.version,
            'auto_reload_latest_snapshot': self.auto_reload_latest_snapshot,
            'auto_reload_frames': int(self.auto_reload_frames),
            'show_navbar_icon': self.show_navbar_icon,
            'show_navbar_when_not_printing': self.show_navbar_when_not_printing,
            'show_position_state_changes': self.show_position_state_changes,
            'show_position_changes': self.show_position_changes,
            'show_extruder_state_changes': self.show_extruder_state_changes,
            'show_trigger_state_changes': self.show_trigger_state_changes,
            'show_real_snapshot_time': self.show_real_snapshot_time,
            'cancel_print_on_startup_error': self.cancel_print_on_startup_error
        }

    # Add/Update/Remove/set current profile

    def add_update_profile(self, profile_type, profile):
        # check the guid.  If it is null or empty, assign a new value.
        guid = profile["guid"]
        if guid is None or guid == "":
            guid = str(uuid.uuid4())
            profile["guid"] = guid

        if profile_type == "Printer":
            new_profile = Printer(profile)
            self.printers[guid] = new_profile
            if len(self.printers) == 1:
                self.current_printer_profile_guid = new_profile.guid
        elif profile_type == "Stabilization":
            new_profile = Stabilization(profile)
            self.stabilizations[guid] = new_profile
        elif profile_type == "Snapshot":
            new_profile = Snapshot(profile)
            self.snapshots[guid] = new_profile
        elif profile_type == "Rendering":
            new_profile = Rendering(profile)
            self.renderings[guid] = new_profile
        elif profile_type == "Camera":
            new_profile = Camera(profile)
            self.cameras[guid] = new_profile
        elif profile_type == "Debug":
            new_profile = DebugProfile(self.LogFilePath, debug_profile=profile)
            self.debug_profiles[guid] = new_profile
        else:
            raise ValueError('An unknown profile type ' +
                             str(profile_type) + ' was received.')

        return new_profile

    def remove_profile(self, profile_type, guid):

        if profile_type == "Printer":
            if self.current_printer_profile_guid == guid:
                return False
            del self.printers[guid]
        elif profile_type == "Stabilization":
            if self.current_stabilization_profile_guid == guid:
                return False
            del self.stabilizations[guid]
        elif profile_type == "Snapshot":
            if self.current_snapshot_profile_guid == guid:
                return False
            del self.snapshots[guid]
        elif profile_type == "Rendering":
            if self.current_rendering_profile_guid == guid:
                return False
            del self.renderings[guid]
        elif profile_type == "Camera":
            del self.cameras[guid]
        elif profile_type == "Debug":
            if self.current_debug_profile_guid == guid:
                return False
            del self.debug_profiles[guid]
        else:
            raise ValueError('An unknown profile type ' +
                             str(profile_type) + ' was received.')

        return True

    def set_current_profile(self, profile_type, guid):

        if profile_type == "Printer":
            if guid == "":
                guid = None
            self.current_printer_profile_guid = guid
        elif profile_type == "Stabilization":
            self.current_stabilization_profile_guid = guid
        elif profile_type == "Snapshot":
            self.current_snapshot_profile_guid = guid
        elif profile_type == "Rendering":
            self.current_rendering_profile_guid = guid
        elif profile_type == "Camera":
            self.current_camera_profile_guid = guid
        elif profile_type == "Debug":
            self.current_debug_profile_guid = guid
        else:
            raise ValueError('An unknown profile type ' +
                             str(profile_type) + ' was received.')


def has_key(obj, key):
    if isinstance(obj, dict):
        return key in obj
    elif isinstance(obj, PluginSettings):
        return obj.has([key])


def get_value(obj, key, default=None):
    if isinstance(obj, dict) and key in obj:
        return obj[key]
    elif isinstance(obj, PluginSettings) and obj.has([key]):
        return obj.get([key])
    else:
        return default
