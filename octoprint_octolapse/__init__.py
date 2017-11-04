# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

class OctolapsePlugin(octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
			octoprint.plugin.StartupPlugin):

	##~~ After Startup
	def on_after_startup(self):
        	self._logger.info("Octolapse has been loaded and is active.")
	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			# put your plugin's default settings here
		)

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/octolapse.js"],
			css=["css/octolapse.css"],
			less=["less/octolapse.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			octolapse=dict(
				displayName="Octolapse Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="FormerLurker",
				repo="Octolapse",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/FormerLurker/Octolapse/archive/{target_version}.zip"
			)
		)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Octolapse Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = OctolapsePlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

