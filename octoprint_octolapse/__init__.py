# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import time
import os
import sys

class OctolapsePlugin(octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
			octoprint.plugin.StartupPlugin):
	
	##~~ After Startup
	def on_after_startup(self):
		self._logger.info("Octolapse has been loaded and is active.")
	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		self._logger.info("Octolapse is creating default settings.")
		return dict(
			enabled = True,
			selected_profile_index = 1,
			profiles=
			[
				dict(
					name= "default",
					description= "Fixed XY at back left - relative stabilization (0,100)",
					printer = dict(
						bed_x_max= -1, 
						bed_y_max= -1, 
						bed_z_max= -1
					),
					stabilization = dict(
						x_movement_speed= 0,
						x_type = 'fixed',
						x_fixed_coordinate = 0,
						x_fixed_path= [],
						x_fixed_path_loop= True,
						x_relative= 100,
						x_relative_print= 100,
						x_relative_path= [],
						x_relative_path_loop= True,
						y_movement_speed_mms= 0, 
						y_type = 'fixed',
						y_fixed_coordinate = 0,
						y_fixed_path= [],
						y_fixed_path_loop= True,
						y_relative= 100,
						y_relative_print= 100,
						y_relative_path= [],
						y_relative_path_loop= True,
						z_movement_speed_mms= 0
					),
					snapshot =dict(
						trigger_type = 'layer_change',
						length = 0.2,
						seconds = 30,
						archive = True,
						delay = 1000,
						retract_before_move= False
					),
					rendering = dict(
						enabled = True,
						fps_calculation_type = 'duration',
						run_length_seconds = 10,
						fps = 30,
						max_fps = 120.0,
						min_fps = 1.0,
						output_format = 'mp4'
					),
					file_options = dict(
						output_filename="{FILENAME}_{DATETIMESTAMP}.{OUTPUTFILEEXTENSION}",
						sync_with_timelapse = True,
						cleanup_before_print=True,
						cleanup_after_print=False,
						cleanup_after_cancel=True,
						cleanup_before_close=True,
						cleanup_after_render=False
					),
					camera = dict(
						brightness=128,
						contrast=128,
						saturation=128,
						white_balance_auto= True,
						gain= 0,
						powerline_frequency=60,
						white_balance_temperature= 4000,
						sharpness= 128,
						backlight_compensation_enabled= False,
						exposure_type= True,
						exposure= 250,
						exposure_auto_priority_enabled = True,
						pan=0,
						tilt=0,
						autofocus_enabled= True,
						focus=35,
						zoom=100,
						led1_mode= 'auto',
						led1_frequency= 0,
						jpeg_quality= 80
					)
				)
			]
		)


	def get_template_configs(self):
		self._logger.info("Octolapse is loading template configurations.")
		return [dict(type="settings", custom_bindings=False)]

	##~~ AssetPlugin mixin

	def get_assets(self):
		self._logger.info("Octolapse is loading assets.")
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(js = ["js/octolapse.js"],
			css = ["css/octolapse.css"],
			less = ["less/octolapse.less"])

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here.  See
		# https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		self._logger.info("Octolapse is geting update information.")
		return dict(octolapse = dict(displayName="Octolapse Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="FormerLurker",
				repo="Octolapse",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/FormerLurker/Octolapse/archive/{target_version}.zip"))


# If you want your plugin to be registered within OctoPrint under a different
# name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here.  Same goes for the
# other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties.  See the
# documentation for that.
__plugin_name__ = "Octolapse Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = OctolapsePlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

