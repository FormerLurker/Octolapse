# coding=utf-8
import time
import utility
from .gcode import Commands, Command
from pprint import pprint
from .trigger import GcodeTrigger, TimerTrigger, LayerTrigger
import os
import sys
PROFILE_SNAPSHOT_GCODE_TYPE = "gcode"



def GetSettingsForOctoprint(octoprintLogger,settings):
		defaults = OctolapseSettings(octoprintLogger,None)
		if(settings is None):
			settings = defaults
		octoprintSettings = {	
			"is_octolapse_enabled": utility.getbool(settings.is_octolapse_enabled,defaults.is_octolapse_enabled),
			'current_profile_name' : utility.getstring(settings.current_profile_name,defaults.current_profile_name),

			'stabilization_options' :
			[
				dict(value='disabled',name='Disabled')
				,dict(value='fixed_coordinate',name='Fixed (Millimeters)')
				,dict(value='fixed_path',name='CSV Separated List of Y Coordinates (Millimeters)')
				,dict(value='relative',name='Relative to Bed(percent)')
				,dict(value='relative_path',name='Relative CSV (percent).')
			
			],
			'fps_calculation_options' : [
					dict(value='static',name='Static FPS (higher FPS = better quality/shorter videos)')
					,dict(value='duration',name='Fixed Run Length (FPS = Total Frames/Run Length Seconds)')
			],
			'debug' : {
				'enabled'					: utility.getbool(settings.debug.enabled,defaults.debug.enabled),
				'position_change'			: utility.getbool(settings.debug.position_change,defaults.debug.position_change),
				'position_command_received'	: utility.getbool(settings.debug.position_command_received,defaults.debug.position_command_received),
				'extruder_change'			: utility.getbool(settings.debug.extruder_change,defaults.debug.extruder_change),
				'extruder_triggered'		: utility.getbool(settings.debug.extruder_triggered,defaults.debug.extruder_triggered),
				'trigger_wait_state'		: utility.getbool(settings.debug.trigger_wait_state,defaults.debug.trigger_wait_state),
				'trigger_triggering'		: utility.getbool(settings.debug.trigger_triggering,defaults.debug.trigger_triggering),
				'trigger_triggering_state'	: utility.getbool(settings.debug.trigger_triggering_state,defaults.debug.trigger_triggering_state),
				'trigger_layer_zmin_reached': utility.getbool(settings.debug.trigger_layer_zmin_reached,defaults.debug.trigger_layer_zmin_reached),
				'trigger_layer_change'		: utility.getbool(settings.debug.trigger_layer_change,defaults.debug.trigger_layer_change),
				'trigger_height_change'		: utility.getbool(settings.debug.trigger_height_change,defaults.debug.trigger_height_change),
				'trigger_time_remaining'	: utility.getbool(settings.debug.trigger_time_remaining,defaults.debug.trigger_time_remaining),
				'trigger_time_unpaused'		: utility.getbool(settings.debug.trigger_time_unpaused,defaults.debug.trigger_time_unpaused),
				'trigger_zhop'				: utility.getbool(settings.debug.trigger_zhop,defaults.debug.trigger_zhop),
				'snapshot_gcode'			: utility.getbool(settings.debug.snapshot_gcode,defaults.debug.snapshot_gcode),
				'snapshot_gcode_endcommand' : utility.getbool(settings.debug.snapshot_gcode_endcommand,defaults.debug.snapshot_gcode_endcommand),
				'snapshot_position'			: utility.getbool(settings.debug.snapshot_position,defaults.debug.snapshot_position),
				'snapshot_position_return'	: utility.getbool(settings.debug.snapshot_position_return,defaults.debug.snapshot_position_return),
				'snapshot_save'				: utility.getbool(settings.debug.snapshot_save,defaults.debug.snapshot_save),
				'snapshot_download'			: utility.getbool(settings.debug.snapshot_download,defaults.debug.snapshot_download),
				'settings_save'				: utility.getbool(settings.debug.settings_save,defaults.debug.settings_save),
				'settings_load'				: utility.getbool(settings.debug.settings_load,defaults.debug.settings_load),
				'print_state_changed'		: utility.getbool(settings.debug.print_state_changed,defaults.debug.print_state_changed),

			},
			'printer' :
			{
				'retract_length' :  utility.getint(settings.printer.retract_length,defaults.printer.retract_length),
				'retract_speed' : utility.getint(settings.printer.retract_speed,defaults.printer.retract_speed),
				'movement_speed' : utility.getint(settings.printer.movement_speed,defaults.printer.movement_speed),
				'is_e_relative' : utility.getbool(settings.printer.is_e_relative, defaults.printer.is_e_relative),
				'z_hop' : utility.getfloat(settings.printer.z_hop, defaults.printer.z_hop),
				'z_min'				: utility.getfloat(settings.printer.z_min,defaults.printer.z_min),
				'snapshot_command' :  utility.getstring(settings.printer.snapshot_command,defaults.printer.snapshot_command),
			},
			'profiles' : []
		}
		
		defaultProfile = defaults.CurrentProfile()
		for key, profile in settings.profiles.items():
			newProfile = {
				'name' : utility.getstring(profile.name,defaultProfile.name),
				'description' : utility.getstring(profile.description,defaultProfile.description),
				'stabilization' : {
					'x_movement_speed' : utility.getint(profile.stabilization.x_movement_speed,defaultProfile.stabilization.x_movement_speed),
					'x_type' : utility.getstring(profile.stabilization.x_type,defaultProfile.stabilization.x_type),
					'x_fixed_coordinate' : utility.getfloat(profile.stabilization.x_fixed_coordinate,defaultProfile.stabilization.x_fixed_coordinate),
					'x_fixed_path' : utility.getobject(profile.stabilization.x_fixed_path,defaultProfile.stabilization.x_fixed_path),
					'x_fixed_path_loop' : utility.getbool(profile.stabilization.x_fixed_path_loop,defaultProfile.stabilization.x_fixed_path_loop),
					'x_relative' : utility.getfloat(profile.stabilization.x_relative,defaultProfile.stabilization.x_relative),
					'x_relative_print' : utility.getfloat(profile.stabilization.x_relative_print,defaultProfile.stabilization.x_relative_print),
					'x_relative_path' : utility.getobject(profile.stabilization.x_relative_path,defaultProfile.stabilization.x_relative_path),
					'x_relative_path_loop' : utility.getbool(profile.stabilization.x_relative_path_loop,defaultProfile.stabilization.x_relative_path_loop),
					'y_movement_speed_mms' : utility.getint(profile.stabilization.y_movement_speed_mms,defaultProfile.stabilization.y_movement_speed_mms),
					'y_type' : utility.getstring(profile.stabilization.y_type,defaultProfile.stabilization.y_type),
					'y_fixed_coordinate' : utility.getfloat(profile.stabilization.y_fixed_coordinate,defaultProfile.stabilization.y_fixed_coordinate),
					'y_fixed_path' : utility.getobject(profile.stabilization.y_fixed_path,defaultProfile.stabilization.y_fixed_path),
					'y_fixed_path_loop' : utility.getbool(profile.stabilization.y_fixed_path_loop,defaultProfile.stabilization.y_fixed_path_loop),
					'y_relative' : utility.getfloat(profile.stabilization.y_relative,defaultProfile.stabilization.y_relative),
					'y_relative_print' : utility.getfloat(profile.stabilization.y_relative_print,defaultProfile.stabilization.y_relative_print),
					'y_relative_path' : utility.getobject(profile.stabilization.y_relative_path,defaultProfile.stabilization.y_relative_path),
					'y_relative_path_loop' : utility.getbool(profile.stabilization.y_relative_path_loop,defaultProfile.stabilization.y_relative_path_loop),
					'z_movement_speed_mms' : utility.getint(profile.stabilization.z_movement_speed_mms,defaultProfile.stabilization.z_movement_speed_mms)
				},
				'snapshot' : {
					'gcode_trigger_enabled'				: utility.getbool(profile.snapshot.gcode_trigger_enabled,defaultProfile.snapshot.gcode_trigger_enabled),
					'gcode_trigger_require_zhop'		: utility.getbool(profile.snapshot.gcode_trigger_require_zhop,defaultProfile.snapshot.gcode_trigger_require_zhop),
					'gcode_trigger_on_extruding'		: utility.getbool(profile.snapshot.gcode_trigger_on_extruding,defaultProfile.snapshot.gcode_trigger_on_extruding),
					'gcode_trigger_on_extruding_start'	: utility.getbool(profile.snapshot.gcode_trigger_on_extruding_start,defaultProfile.snapshot.gcode_trigger_on_extruding_start),
					'gcode_trigger_on_primed'			: utility.getbool(profile.snapshot.gcode_trigger_on_primed,defaultProfile.snapshot.gcode_trigger_on_primed),
					'gcode_trigger_on_retracting'		: utility.getbool(profile.snapshot.gcode_trigger_on_retracting,defaultProfile.snapshot.gcode_trigger_on_retracting),
					'gcode_trigger_on_retracted'		: utility.getbool(profile.snapshot.gcode_trigger_on_retracted,defaultProfile.snapshot.gcode_trigger_on_retracted),
					'gcode_trigger_on_detracting'		: utility.getbool(profile.snapshot.gcode_trigger_on_detracting,defaultProfile.snapshot.gcode_trigger_on_detracting),
					'timer_trigger_enabled'				: utility.getbool(profile.snapshot.timer_trigger_enabled,defaultProfile.snapshot.timer_trigger_enabled),
					'timer_trigger_require_zhop'		: utility.getbool(profile.snapshot.timer_trigger_require_zhop,defaultProfile.snapshot.timer_trigger_require_zhop),
					'timer_trigger_seconds'				: utility.getint(profile.snapshot.timer_trigger_seconds,defaultProfile.snapshot.timer_trigger_seconds),
					'timer_trigger_on_extruding'		: utility.getbool(profile.snapshot.timer_trigger_on_extruding,defaultProfile.snapshot.timer_trigger_on_extruding),
					'timer_trigger_on_extruding_start'	: utility.getbool(profile.snapshot.timer_trigger_on_extruding_start,defaultProfile.snapshot.timer_trigger_on_extruding_start),
					'timer_trigger_on_primed'			: utility.getbool(profile.snapshot.timer_trigger_on_primed,defaultProfile.snapshot.timer_trigger_on_primed),
					'timer_trigger_on_retracting'		: utility.getbool(profile.snapshot.timer_trigger_on_retracting,defaultProfile.snapshot.timer_trigger_on_retracting),
					'timer_trigger_on_retracted'		: utility.getbool(profile.snapshot.timer_trigger_on_retracted,defaultProfile.snapshot.timer_trigger_on_retracted),
					'timer_trigger_on_detracting'		: utility.getbool(profile.snapshot.timer_trigger_on_detracting,defaultProfile.snapshot.timer_trigger_on_detracting),
					'layer_trigger_enabled'				: utility.getbool(profile.snapshot.layer_trigger_enabled,defaultProfile.snapshot.layer_trigger_enabled),
					'layer_trigger_height'				: utility.getfloat(profile.snapshot.layer_trigger_height,defaultProfile.snapshot.layer_trigger_height),
					'layer_trigger_require_zhop'		: utility.getbool(profile.snapshot.layer_trigger_require_zhop,defaultProfile.snapshot.layer_trigger_require_zhop),
					'layer_trigger_on_extruding'		: utility.getbool(profile.snapshot.layer_trigger_on_extruding,defaultProfile.snapshot.layer_trigger_on_extruding),
					'layer_trigger_on_extruding_start'	: utility.getbool(profile.snapshot.layer_trigger_on_extruding_start,defaultProfile.snapshot.layer_trigger_on_extruding_start),
					'layer_trigger_on_primed'			: utility.getbool(profile.snapshot.layer_trigger_on_primed,defaultProfile.snapshot.layer_trigger_on_primed),
					'layer_trigger_on_retracting'		: utility.getbool(profile.snapshot.layer_trigger_on_retracting,defaultProfile.snapshot.layer_trigger_on_retracting),
					'layer_trigger_on_retracted'		: utility.getbool(profile.snapshot.layer_trigger_on_retracted,defaultProfile.snapshot.layer_trigger_on_retracted),
					'layer_trigger_on_detracting'		: utility.getbool(profile.snapshot.layer_trigger_on_detracting,defaultProfile.snapshot.layer_trigger_on_detracting),
					'archive' : utility.getbool(profile.snapshot.archive,defaultProfile.snapshot.archive),
					'delay' : utility.getint(profile.snapshot.delay,defaultProfile.snapshot.delay),
					'output_format' : utility.getstring(profile.snapshot.output_format,defaultProfile.snapshot.output_format),
					'output_filename' :utility.getstring(profile.snapshot.output_filename,defaultProfile.snapshot.output_filename),
					'output_directory' : utility.getstring(profile.snapshot.output_directory,defaultProfile.snapshot.output_directory),
					'retract_before_move' : utility.getbool(profile.snapshot.retract_before_move,defaultProfile.snapshot.retract_before_move),
					'cleanup_before_print' : utility.getbool(profile.snapshot.cleanup_before_print,defaultProfile.snapshot.cleanup_before_print),
					'cleanup_after_print' : utility.getbool(profile.snapshot.cleanup_after_print,defaultProfile.snapshot.cleanup_after_print),
					'cleanup_after_cancel' : utility.getbool(profile.snapshot.cleanup_after_cancel,defaultProfile.snapshot.cleanup_after_cancel),
					'cleanup_before_close' :  utility.getbool(profile.snapshot.cleanup_before_close,defaultProfile.snapshot.cleanup_before_close),
					'cleanup_after_render_complete' : utility.getbool(profile.snapshot.cleanup_after_render_complete,defaultProfile.snapshot.cleanup_after_render_complete),
					'cleanup_after_render_fail' : utility.getbool(profile.snapshot.cleanup_after_render_fail,defaultProfile.snapshot.cleanup_after_render_fail),
					'custom_script_enabled' : utility.getbool(profile.snapshot.custom_script_enabled,defaultProfile.snapshot.custom_script_enabled),
					'script_path' : utility.getstring(profile.snapshot.script_path,defaultProfile.snapshot.script_path),
				},
				'rendering' : {
					'enabled' : utility.getbool(profile.rendering.enabled,defaultProfile.rendering.enabled),
					'fps_calculation_type' : utility.getstring(profile.rendering.fps_calculation_type,defaultProfile.rendering.fps_calculation_type),
					'run_length_seconds' : utility.getfloat(profile.rendering.run_length_seconds,defaultProfile.rendering.run_length_seconds),
					'fps' : utility.getfloat(profile.rendering.fps,defaultProfile.rendering.fps),
					'max_fps' : utility.getfloat(profile.rendering.max_fps,defaultProfile.rendering.max_fps),
					'min_fps' : utility.getfloat(profile.rendering.min_fps,defaultProfile.rendering.min_fps),
					'output_format' : utility.getstring(profile.rendering.output_format,defaultProfile.rendering.output_format),
					'output_filename' :utility.getstring(profile.rendering.output_filename,defaultProfile.rendering.output_filename),
					'output_directory' : utility.getstring(profile.rendering.output_directory,defaultProfile.rendering.output_directory),
					'sync_with_timelapse' : utility.getbool(profile.rendering.sync_with_timelapse,defaultProfile.rendering.sync_with_timelapse),
					'octoprint_timelapse_directory' : utility.getstring(profile.rendering.octoprint_timelapse_directory,defaultProfile.rendering.octoprint_timelapse_directory),
					'ffmpeg_path' : utility.getstring(profile.rendering.ffmpeg_path,defaultProfile.rendering.ffmpeg_path),
					'bitrate' : utility.getstring(profile.rendering.bitrate,defaultProfile.rendering.bitrate),
					'flip_h' :  utility.getbool(profile.rendering.flip_h,defaultProfile.rendering.flip_h),
					'flip_v' :  utility.getbool(profile.rendering.flip_v,defaultProfile.rendering.flip_v),
					'rotate_90' :  utility.getbool(profile.rendering.rotate_90,defaultProfile.rendering.rotate_90),
					'watermark' :  utility.getbool(profile.rendering.watermark,defaultProfile.rendering.watermark)
				},
				
				'camera' : {
					
					'address' : utility.getstring(profile.camera.address,defaultProfile.camera.address),
					'ignore_ssl_error' : utility.getbool(profile.camera.ignore_ssl_error,defaultProfile.camera.ignore_ssl_error),
					'password' : utility.getstring(profile.camera.password,defaultProfile.camera.password),
					'username' : utility.getstring(profile.camera.username,defaultProfile.camera.username),
					'brightness' : utility.getint(profile.camera.brightness,defaultProfile.camera.brightness),
					'contrast' : utility.getint(profile.camera.contrast,defaultProfile.camera.contrast),
					'saturation' : utility.getint(profile.camera.saturation,defaultProfile.camera.saturation),
					'white_balance_auto' : utility.getbool(profile.camera.white_balance_auto,defaultProfile.camera.white_balance_auto),
					'gain' : utility.getint(profile.camera.gain,defaultProfile.camera.gain),
					'powerline_frequency' : utility.getint(profile.camera.powerline_frequency,defaultProfile.camera.powerline_frequency),
					'white_balance_temperature' : utility.getint(profile.camera.white_balance_temperature,defaultProfile.camera.white_balance_temperature),
					'sharpness' : utility.getint(profile.camera.sharpness,defaultProfile.camera.sharpness),
					'backlight_compensation_enabled' :  utility.getbool(profile.camera.backlight_compensation_enabled,defaultProfile.camera.backlight_compensation_enabled),
					'exposure_type' : utility.getbool(profile.camera.exposure_type,defaultProfile.camera.exposure_type),
					'exposure' : utility.getint(profile.camera.exposure,defaultProfile.camera.exposure),
					'exposure_auto_priority_enabled' : utility.getbool(profile.camera.exposure_auto_priority_enabled,defaultProfile.camera.exposure_auto_priority_enabled),
					'pan' : utility.getint(profile.camera.pan,defaultProfile.camera.pan),
					'tilt' : utility.getint(profile.camera.tilt,defaultProfile.camera.tilt),
					'autofocus_enabled' : utility.getbool(profile.camera.autofocus_enabled,defaultProfile.camera.autofocus_enabled),
					'focus' : utility.getint(profile.camera.focus,defaultProfile.camera.focus),
					'zoom' : utility.getint(profile.camera.zoom,defaultProfile.camera.zoom),
					'led1_mode' :  utility.getstring(profile.camera.led1_mode,defaultProfile.camera.led1_mode),
					'led1_frequency' : utility.getint(profile.camera.led1_frequency,defaultProfile.camera.led1_frequency),
					'jpeg_quality' : utility.getint(profile.camera.jpeg_quality,defaultProfile.camera.jpeg_quality)
				}
			}
			octoprintSettings["profiles"].append(newProfile)

		return octoprintSettings


class Printer(object):
	
	def __init__(self,printer):
		self.retract_length = 4.0
		self.retract_speed = 4800
		self.movement_speed = 7200
		self.z_hop = 0.5
		self.z_min = 0.2
		self.snapshot_command = "snap"
		self.is_e_relative = True
		if(printer is not None):
			if("retract_length" in printer.keys()):
				self.retract_length = utility.getfloat(printer["retract_length"],self.retract_length)
			if("retract_speed" in printer.keys()):
				self.retract_speed = utility.getint(printer["retract_speed"],self.retract_speed)
			if("movement_speed" in printer.keys()):
				self.movement_speed = utility.getint(printer["movement_speed"],self.movement_speed)
			if("snapshot_command" in printer.keys()):
				self.snapshot_command = utility.getstring(printer["snapshot_command"],self.snapshot_command)
			if("is_e_relative" in printer.keys()):
				self.is_e_relative = utility.getbool(printer["is_e_relative"],self.is_e_relative)
			if("z_hop" in printer.keys()):
				self.z_hop = utility.getfloat(printer["z_hop"],self.z_hop)
			if("z_min" in printer.keys()):
				self.z_min = utility.getfloat(printer["z_min"],self.z_min)
class Stabilization(object):

	def __init__(self,stabilization):
		self.x_movement_speed = 0
		self.x_type = "fixed_coordinate"
		self.x_fixed_coordinate = 0.0
		self.x_fixed_path = []
		self.x_fixed_path_loop = True
		self.x_relative = 100.0
		self.x_relative_print = 100.0
		self.x_relative_path = []
		self.x_relative_path_loop = True
		self.y_movement_speed_mms = 0
		self.y_type = 'fixed_coordinate'
		self.y_fixed_coordinate = 0.0
		self.y_fixed_path = []
		self.y_fixed_path_loop = True
		self.y_relative = 100.0
		self.y_relative_print = 100.0
		self.y_relative_path = []
		self.y_relative_path_loop = True
		self.z_movement_speed_mms = 0
		
		if(stabilization is not None):
			if("x_movement_speed" in stabilization.keys()):
				self.x_movement_speed = utility.getint(stabilization["x_movement_speed"],self.x_movement_speed)
			if("x_type" in stabilization.keys()):
				self.x_type = utility.getstring(stabilization["x_type"],self.x_type)
			if("x_fixed_coordinate" in stabilization.keys()):
				self.x_fixed_coordinate = utility.getfloat(stabilization["x_fixed_coordinate"],self.x_fixed_coordinate)
			if("x_fixed_path" in stabilization.keys()):
				self.x_fixed_path = utility.getstring(stabilization["x_fixed_path"],self.x_fixed_path)
			if("x_fixed_path_loop" in stabilization.keys()):
				self.x_fixed_path_loop = utility.getbool(stabilization["x_fixed_path_loop"],self.x_fixed_path_loop)
			if("x_relative" in stabilization.keys()):
				self.x_relative = utility.getfloat(stabilization["x_relative"],self.x_relative)
			if("x_relative_print" in stabilization.keys()):
				self.x_relative_print = utility.getfloat(stabilization["x_relative_print"],self.x_relative_print)
			if("x_relative_path" in stabilization.keys()):
				self.x_relative_path = utility.getstring(stabilization["x_relative_path"],self.x_relative_path)
			if("x_relative_path_loop" in stabilization.keys()):
				self.x_relative_path_loop = utility.getbool(stabilization["x_relative_path_loop"],self.x_relative_path_loop)
			if("y_movement_speed_mms" in stabilization.keys()):
				self.y_movement_speed_mms = utility.getint(stabilization["y_movement_speed_mms"],self.y_movement_speed_mms)
			if("y_type" in stabilization.keys()):
				self.y_type = utility.getstring(stabilization["y_type"],self.y_type)
			if("y_fixed_coordinate" in stabilization.keys()):
				self.y_fixed_coordinate = utility.getfloat(stabilization["y_fixed_coordinate"],self.y_fixed_coordinate)
			if("y_fixed_path" in stabilization.keys()):
				self.y_fixed_path = utility.getstring(stabilization["y_fixed_path"],self.y_fixed_path)
			if("y_fixed_path_loop" in stabilization.keys()):
				self.y_fixed_path_loop = utility.getbool(stabilization["y_fixed_path_loop"],self.y_fixed_path_loop)
			if("y_relative" in stabilization.keys()):
				self.y_relative = utility.getfloat(stabilization["y_relative"],self.y_relative)
			if("y_relative_print" in stabilization.keys()):
				self.y_relative_print = utility.getfloat(stabilization["y_relative_print"],self.y_relative_print)
			if("y_relative_path" in stabilization.keys()):
				self.y_relative_path = utility.getstring(stabilization["y_relative_path"],self.y_relative_path)
			if("y_relative_path_loop" in stabilization.keys()):
				self.y_relative_path_loop = utility.getbool(stabilization["y_relative_path_loop"],self.y_relative_path_loop)
			if("z_movement_speed_mms" in stabilization.keys()):
				self.z_movement_speed_mms = utility.getint(stabilization["z_movement_speed_mms"],self.z_movement_speed_mms)
class Snapshot(object):
	def __init__(self,snapshot):
		#Initialize defaults
		#Gcode Trigger
		self.gcode_trigger_enabled = True
		self.gcode_trigger_require_zhop = True
		self.gcode_trigger_on_extruding = True
		self.gcode_trigger_on_extruding_start = True
		self.gcode_trigger_on_primed = True
		self.gcode_trigger_on_retracting = True
		self.gcode_trigger_on_retracted = True
		self.gcode_trigger_on_detracting = True
		#Timer Trigger
		self.timer_trigger_enabled = False
		self.timer_trigger_seconds = 60
		self.timer_trigger_require_zhop = True
		self.timer_trigger_on_extruding = True
		self.timer_trigger_on_extruding_start = False
		self.timer_trigger_on_primed = True
		self.timer_trigger_on_retracting = False
		self.timer_trigger_on_retracted = True
		self.timer_trigger_on_detracting = True
		#Layer Trigger
		self.layer_trigger_enabled = True
		self.layer_trigger_height = 0.0
		self.layer_trigger_require_zhop = True
		self.layer_trigger_on_extruding = False
		self.layer_trigger_on_extruding_start = False
		self.layer_trigger_on_primed = True
		self.layer_trigger_on_retracting = False
		self.layer_trigger_on_retracted = True
		self.layer_trigger_on_detracting = True
		# other settings
		self.archive = True
		self.delay = 1000
		self.retract_before_move = False
		self.output_format = "jpg"
		self.output_filename = "{FILENAME}_{SNAPSHOTNUMBER}.{OUTPUTFILEEXTENSION}"
		self.output_directory = "/home/pi/Octolapse/snapshots/{FILENAME}_{PRINTSTARTTIME}/"
		if (sys.platform == "win32"):
			self.output_directory = "c:\\temp\\snapshots\\{FILENAME}_{PRINTSTARTTIME}\\"
		self.cleanup_before_print = True
		self.cleanup_after_print = False
		self.cleanup_after_cancel = True
		self.cleanup_after_fail = True
		self.cleanup_before_close = False
		self.cleanup_after_render_complete = True
		self.cleanup_after_render_fail = False
		self.custom_script_enabled = False
		self.script_path = ""
		
		if(snapshot is not None):
			#Initialize all values according to the provided snapshot, use defaults if
			#the values are null or incorrectly formatted
			if("gcode_trigger_enabled" in snapshot.keys()):
				self.gcode_trigger_enabled = utility.getbool(snapshot["gcode_trigger_enabled"],self.gcode_trigger_enabled)
			if("gcode_trigger_require_zhop" in snapshot.keys()):
				self.gcode_trigger_require_zhop = utility.getbool(snapshot["gcode_trigger_require_zhop"],self.gcode_trigger_require_zhop)
			if("gcode_trigger_on_extruding" in snapshot.keys()):
				self.gcode_trigger_on_extruding = utility.getbool(snapshot["gcode_trigger_on_extruding"],self.gcode_trigger_on_extruding)
			if("gcode_trigger_on_extruding_start" in snapshot.keys()):
				self.gcode_trigger_on_extruding_start = utility.getbool(snapshot["gcode_trigger_on_extruding_start"],self.gcode_trigger_on_extruding_start)
			if("gcode_trigger_on_primed" in snapshot.keys()):
				self.gcode_trigger_on_primed = utility.getbool(snapshot["gcode_trigger_on_primed"],self.gcode_trigger_on_primed)
			if("gcode_trigger_on_retracting" in snapshot.keys()):
				self.gcode_trigger_on_retracting = utility.getbool(snapshot["gcode_trigger_on_retracting"],self.gcode_trigger_on_retracting)
			if("gcode_trigger_on_retracted" in snapshot.keys()):
				self.gcode_trigger_on_retracted = utility.getbool(snapshot["gcode_trigger_on_retracted"],self.gcode_trigger_on_retracted)
			if("gcode_trigger_on_detracting" in snapshot.keys()):
				self.gcode_trigger_on_detracting = utility.getbool(snapshot["gcode_trigger_on_detracting"],self.gcode_trigger_on_detracting)
			if("timer_trigger_enabled" in snapshot.keys()):
				self.timer_trigger_enabled = utility.getbool(snapshot["timer_trigger_enabled"],self.timer_trigger_enabled)
			if("timer_trigger_require_zhop" in snapshot.keys()):
				self.timer_trigger_require_zhop = utility.getbool(snapshot["timer_trigger_require_zhop"],self.timer_trigger_require_zhop)
			if("timer_trigger_seconds" in snapshot.keys()):
				self.timer_trigger_seconds = utility.getint(snapshot["timer_trigger_seconds"],self.timer_trigger_seconds)
			if("timer_trigger_on_extruding" in snapshot.keys()):
				self.timer_trigger_on_extruding = utility.getbool(snapshot["timer_trigger_on_extruding"],self.timer_trigger_on_extruding)
			if("timer_trigger_on_extruding_start" in snapshot.keys()):
				self.timer_trigger_on_extruding_start = utility.getbool(snapshot["timer_trigger_on_extruding_start"],self.timer_trigger_on_extruding_start)
			if("timer_trigger_on_primed" in snapshot.keys()):
				self.timer_trigger_on_primed = utility.getbool(snapshot["timer_trigger_on_primed"],self.timer_trigger_on_primed)
			if("timer_trigger_on_retracting" in snapshot.keys()):
				self.timer_trigger_on_retracting = utility.getbool(snapshot["timer_trigger_on_retracting"],self.timer_trigger_on_retracting)
			if("timer_trigger_on_retracted" in snapshot.keys()):
				self.timer_trigger_on_retracted = utility.getbool(snapshot["timer_trigger_on_retracted"],self.timer_trigger_on_retracted)
			if("timer_trigger_on_detracting" in snapshot.keys()):
				self.timer_trigger_on_detracting = utility.getbool(snapshot["timer_trigger_on_detracting"],self.timer_trigger_on_detracting)
			if("layer_trigger_enabled" in snapshot.keys()):
				self.layer_trigger_enabled = utility.getbool(snapshot["layer_trigger_enabled"],self.layer_trigger_enabled)
			if("layer_trigger_height" in snapshot.keys()):
				self.layer_trigger_height = utility.getfloat(snapshot["layer_trigger_height"],self.layer_trigger_height)
			if("layer_trigger_require_zhop" in snapshot.keys()):
				self.layer_trigger_require_zhop = utility.getbool(snapshot["layer_trigger_require_zhop"],self.layer_trigger_require_zhop)
			else:
				print ('Key not found!')
			if("layer_trigger_on_extruding" in snapshot.keys()):
				self.layer_trigger_on_extruding = utility.getbool(snapshot["layer_trigger_on_extruding"],self.layer_trigger_on_extruding)
			if("layer_trigger_on_extruding_start" in snapshot.keys()):
				self.layer_trigger_on_extruding_start = utility.getbool(snapshot["layer_trigger_on_extruding_start"],self.layer_trigger_on_extruding_start)
			if("layer_trigger_on_primed" in snapshot.keys()):
				self.layer_trigger_on_primed = utility.getbool(snapshot["layer_trigger_on_primed"],self.layer_trigger_on_primed)
			if("layer_trigger_on_retracting" in snapshot.keys()):
				self.layer_trigger_on_retracting = utility.getbool(snapshot["layer_trigger_on_retracting"],self.layer_trigger_on_retracting)
			if("layer_trigger_on_retracted" in snapshot.keys()):
				self.layer_trigger_on_retracted = utility.getbool(snapshot["layer_trigger_on_retracted"],self.layer_trigger_on_retracted)
			if("layer_trigger_on_detracting" in snapshot.keys()):
				self.layer_trigger_on_detracting = utility.getbool(snapshot["layer_trigger_on_detracting"],self.layer_trigger_on_detracting)
			if("archive" in snapshot.keys()):
				self.archive = utility.getbool(snapshot["archive"],self.archive)
			if("delay" in snapshot.keys()):
				self.delay = utility.getint(snapshot["delay"],self.delay)
			if("retract_before_move" in snapshot.keys()):
				self.retract_before_move = utility.getbool(snapshot["retract_before_move"],self.retract_before_move)
			if("output_format" in snapshot.keys()):
				self.output_format = utility.getstring(snapshot["output_format"],self.output_format)
			if("output_filename" in snapshot.keys()):
				self.output_filename = utility.getstring(snapshot["output_filename"],self.output_filename)
			if("output_directory" in snapshot.keys()):
				self.output_directory = utility.getstring(snapshot["output_directory"],self.output_directory)
			if("cleanup_before_print" in snapshot.keys()):
				self.cleanup_before_print = utility.getbool(snapshot["cleanup_before_print"],self.cleanup_before_print)
			if("cleanup_after_print" in snapshot.keys()):
				self.cleanup_after_print = utility.getbool(snapshot["cleanup_after_print"],self.cleanup_after_print)
			if("cleanup_after_cancel" in snapshot.keys()):
				self.cleanup_after_cancel = utility.getbool(snapshot["cleanup_after_cancel"],self.cleanup_after_cancel)
			if("cleanup_after_fail" in snapshot.keys()):
				self.cleanup_after_fail = utility.getbool(snapshot["cleanup_after_fail"],self.cleanup_after_fail)
			if("cleanup_before_close" in snapshot.keys()):
				self.cleanup_before_close = utility.getbool(snapshot["cleanup_before_close"],self.cleanup_before_close)
			if("cleanup_after_render_complete" in snapshot.keys()):
				self.cleanup_after_render_complete = utility.getbool(snapshot["cleanup_after_render_complete"],self.cleanup_after_render_complete)
			if("cleanup_after_render_fail" in snapshot.keys()):
				self.cleanup_after_render_fail = utility.getbool(snapshot["cleanup_after_render_fail"],self.cleanup_after_render_fail)
			if("custom_script_enabled" in snapshot.keys()):
				self.custom_script_enabled = utility.getbool(snapshot["custom_script_enabled"],self.custom_script_enabled)
			if("script_path" in snapshot.keys()):
				self.script_path = utility.getstring(snapshot["script_path"],self.script_path)
class Rendering(object):
	def __init__(self,rendering):
		self.enabled = True
		self.fps_calculation_type = 'duration'
		self.run_length_seconds = 10
		self.fps = 30
		self.max_fps = 120.0
		self.min_fps = 1.0
		self.output_format = 'mp4'
		self.output_filename = "{FILENAME}_{DATETIMESTAMP}.{OUTPUTFILEEXTENSION}"
		self.output_directory = "/home/pi/Octolapse/timelapse/{FILENAME}_{PRINTSTARTTIME}/"
		if (sys.platform == "win32"):
			self.output_directory = "c:\\temp\\{FILENAME}_{PRINTSTARTTIME}"
		self.sync_with_timelapse = False
		self.octoprint_timelapse_directory = "/home/pi/.octoprint/timelapse/"
		if(sys.platform == "win32"):
			self.octoprint_timelapse_directory = "{0}{1}".format(os.getenv('APPDATA'), "\\Octoprint\\timelapse")
		self.ffmpeg_path = "/usr/bin/avconv"
		if sys.platform == "win32":
			self.ffmpeg_path  = "\"C:\Program Files (x86)\\FFMpeg\\bin\\ffmpeg.exe\""
		self.bitrate = "2000K"
		self.flip_h = False
		self.flip_v = False
		self.rotate_90 = False
		self.watermark = False
		if(rendering is not None):
			if("enabled" in rendering.keys()):
				self.enabled = utility.getbool(rendering["enabled"],self.enabled)
			if("fps_calculation_type" in rendering.keys()):
				self.fps_calculation_type = rendering["fps_calculation_type"]
			if("run_length_seconds" in rendering.keys()):
				self.run_length_seconds = utility.getfloat(rendering["run_length_seconds"],self.run_length_seconds)
			if("fps" in rendering.keys()):
				self.fps = utility.getfloat(rendering["fps"],self.fps)
			if("max_fps" in rendering.keys()):
				self.max_fps = utility.getfloat(rendering["max_fps"],self.max_fps)
			if("min_fps" in rendering.keys()):
				self.min_fps = utility.getfloat(rendering["min_fps"],self.min_fps)
			if("output_format" in rendering.keys()):
				self.output_format = utility.getstring(rendering["output_format"],self.output_format)
			if("output_filename" in rendering.keys()):
				self.output_filename = utility.getstring(rendering["output_filename"],self.output_format)
			if("output_directory" in rendering.keys()):
				self.output_directory = utility.getstring(rendering["output_directory"],self.output_directory)
			if("sync_with_timelapse" in rendering.keys()):
				self.sync_with_timelapse = utility.getbool(rendering["sync_with_timelapse"],self.sync_with_timelapse)
			if("octoprint_timelapse_directory" in rendering.keys()):
				self.octoprint_timelapse_directory = utility.getstring(rendering["octoprint_timelapse_directory"],self.octoprint_timelapse_directory)
			if("ffmpeg_path" in rendering.keys()):
				self.ffmpeg_path = utility.getstring(rendering["ffmpeg_path"],self.ffmpeg_path)
			if("bitrate" in rendering.keys()):
				self.bitrate = utility.getstring(rendering["bitrate"],self.bitrate)
			if("flip_h" in rendering.keys()):
				self.flip_h = utility.getbool(rendering["flip_h"],self.flip_h)
			if("flip_v" in rendering.keys()):
				self.flip_v = utility.getbool(rendering["flip_v"],self.flip_v)
			if("rotate_90" in rendering.keys()):
				self.rotate_90 = utility.getbool(rendering["rotate_90"],self.rotate_90)
			if("watermark" in rendering.keys()):
				self.watermark = utility.getbool(rendering["watermark"],self.watermark)

class Camera(object):
	
	def __init__(self,camera):

		
		self.address = "http://127.0.0.1/webcam/?action=snapshot"
		self.ignore_ssl_error = False
		self.username = ""
		self.password = ""
		self.brightness = 128
		self.contrast = 128
		self.saturation = 128
		self.white_balance_auto = True
		self.gain = 0
		self.powerline_frequency = 60
		self.white_balance_temperature = 4000
		self.sharpness = 128
		self.backlight_compensation_enabled = False
		self.exposure_type = True
		self.exposure = 250
		self.exposure_auto_priority_enabled = True
		self.pan = 0
		self.tilt = 0
		self.autofocus_enabled = True
		self.focus = 35
		self.zoom = 100
		self.led1_mode = 'auto'
		self.led1_frequency = 0
		self.jpeg_quality = 80
		if(not camera is None):
			if("address" in camera.keys()):
				self.address = utility.getstring(camera["address"],self.address)
			if("ignore_ssl_error" in camera.keys()):
				self.ignore_ssl_error = utility.getbool(camera["ignore_ssl_error"],self.ignore_ssl_error)
			if("username" in camera.keys()):
				self.username = utility.getstring(camera["username"],self.username)
			if("password" in camera.keys()):
				self.password = utility.getstring(camera["password"],self.password)
			if("brightness" in camera.keys()):
				self.brightness = utility.getint(camera["brightness"],self.brightness)
			if("contrast" in camera.keys()):
				self.contrast = utility.getint(camera["contrast"],self.contrast)
			if("saturation" in camera.keys()):
				self.saturation = utility.getint(camera["saturation"],self.saturation)
			if("white_balance_auto" in camera.keys()):
				self.white_balance_auto = utility.getbool(camera["white_balance_auto"],self.white_balance_auto)
			if("gain" in camera.keys()):
				self.gain = utility.getint(camera["gain"],self.gain)
			if("powerline_frequency" in camera.keys()):
				self.powerline_frequency = utility.getint(camera["powerline_frequency"],self.powerline_frequency)
			if("white_balance_temperature" in camera.keys()):
				self.white_balance_temperature = utility.getint(camera["white_balance_temperature"],self.white_balance_temperature)
			if("sharpness" in camera.keys()):
				self.sharpness = utility.getint(camera["sharpness"],self.sharpness)
			if("backlight_compensation_enabled" in camera.keys()):
				self.backlight_compensation_enabled = utility.getbool(camera["backlight_compensation_enabled"],self.backlight_compensation_enabled)
			if("exposure_type" in camera.keys()):
				self.exposure_type = utility.getbool(camera["exposure_type"],self.exposure_type)
			if("exposure" in camera.keys()):
				self.exposure = utility.getint(camera["exposure"],self.exposure)
			if("exposure_auto_priority_enabled" in camera.keys()):
				self.exposure_auto_priority_enabled = utility.getbool(camera["exposure_auto_priority_enabled"],self.exposure_auto_priority_enabled)
			if("pan" in camera.keys()):
				self.pan = utility.getint(camera["pan"],self.pan)
			if("tilt" in camera.keys()):
				self.tilt = utility.getint(camera["tilt"],self.tilt)
			if("autofocus_enabled" in camera.keys()):
				self.autofocus_enabled = utility.getbool(camera["autofocus_enabled"],self.autofocus_enabled)
			if("focus" in camera.keys()):
				self.focus = utility.getint(camera["focus"],self.focus)
			if("zoom" in camera.keys()):
				self.zoom = utility.getint(camera["zoom"],self.zoom)
			if("led1_mode" in camera.keys()):
				self.led1_mode = utility.getstring(camera["led1_mode"],self.led1_frequency)
			if("led1_frequency" in camera.keys()):
				self.led1_frequency = utility.getint(camera["led1_frequency"],self.led1_frequency)
			if("jpeg_quality" in camera.keys()):
				self.jpeg_quality = utility.getint(camera["jpeg_quality"],self.jpeg_quality)
class Profile(object):
	def __init__(self,profile):
		self.name = "Default"
		self.description = "Fixed XY at back left - relative stabilization (0,100)"
		self.stabilization = Stabilization(None)
		self.snapshot = Snapshot(None)
		self.rendering = Rendering(None)
		self.camera = Camera(None)
		if(profile is not None):

			self.name = utility.getstring(profile["name"],self.name)
			if("description" in profile.keys()):
				self.description = utility.getstring(profile["description"],self.description)
			if("stabilization" in profile.keys()):
				self.stabilization = Stabilization(profile["stabilization"])
			if("snapshot" in profile.keys()):
				self.snapshot = Snapshot(profile["snapshot"])
			if("rendering" in profile.keys()):
				self.rendering = Rendering(profile["rendering"])
			if("camera" in profile.keys()):
				self.camera = Camera(profile["camera"])

class DebugSettings(object):
	Logger = None
	def __init__(self,octoprintLogger,debug):
		self.Logger = octoprintLogger
		self.Commands = Commands()
		self.enabled = False
		self.position_change = False
		self.position_command_received = False
		self.extruder_change = False
		self.extruder_triggered = False
		self.trigger_wait_state = False
		self.trigger_triggering = False
		self.trigger_triggering_state = False
		self.trigger_layer_zmin_reached = False
		self.trigger_layer_change = False
		self.trigger_height_change = False
		self.trigger_zhop = False
		self.trigger_time_unpaused = False
		self.trigger_time_remaining = False
		self.snapshot_gcode = False
		self.snapshot_gcode_endcommand = False
		self.snapshot_position = False
		self.snapshot_position_return = False
		self.snapshot_save = False
		self.snapshot_download = False
		self.settings_save = False
		self.settings_load = False
		self.print_state_changed = False
		if(debug is not None):
			if("enabled" in debug.keys()):
				self.enabled = utility.getbool(debug["enabled"],self.enabled)
			if("position_change" in debug.keys()):
				self.position_change = utility.getbool(debug["position_change"],self.position_change)
			if("position_command_received" in debug.keys()):
				self.position_command_received = utility.getbool(debug["position_command_received"],self.position_command_received)
			if("extruder_change" in debug.keys()):
				self.extruder_change = utility.getbool(debug["extruder_change"],self.extruder_change)
			if("extruder_triggered" in debug.keys()):
				self.extruder_triggered = utility.getbool(debug["extruder_triggered"],self.extruder_triggered)
			if("trigger_wait_state" in debug.keys()):
				self.trigger_wait_state = utility.getbool(debug["trigger_wait_state"],self.trigger_wait_state)
			if("trigger_triggering" in debug.keys()):
				self.trigger_triggering = utility.getbool(debug["trigger_triggering"],self.trigger_triggering)
			if("trigger_triggering_state" in debug.keys()):
				self.trigger_triggering_state = utility.getbool(debug["trigger_triggering_state"],self.trigger_triggering_state)
			if("trigger_layer_zmin_reached" in debug.keys()):
				self.trigger_layer_zmin_reached = utility.getbool(debug["trigger_layer_zmin_reached"],self.trigger_layer_zmin_reached)
			if("trigger_layer_change" in debug.keys()):
				self.trigger_layer_change = utility.getbool(debug["trigger_layer_change"],self.trigger_layer_change)
			if("trigger_height_change" in debug.keys()):
				self.trigger_height_change = utility.getbool(debug["trigger_height_change"],self.trigger_height_change)
			if("trigger_time_remaining" in debug.keys()):
				self.trigger_time_remaining = utility.getbool(debug["trigger_time_remaining"],self.trigger_time_remaining)
			if("trigger_time_unpaused" in debug.keys()):
				self.trigger_time_unpaused = utility.getbool(debug["trigger_time_unpaused"],self.trigger_time_unpaused)
			if("trigger_zhop" in debug.keys()):
				self.trigger_zhop = utility.getbool(debug["trigger_zhop"],self.trigger_zhop )
			if("snapshot_gcode" in debug.keys()):
				self.snapshot_gcode = utility.getbool(debug["snapshot_gcode"],self.snapshot_gcode)
			if("snapshot_gcode_endcommand" in debug.keys()):
				self.snapshot_gcode_endcommand = utility.getbool(debug["snapshot_gcode_endcommand"],self.snapshot_gcode_endcommand) 
			if("snapshot_position" in debug.keys()):
				self.snapshot_position = utility.getbool(debug["snapshot_position"],self.snapshot_position)
			if("snapshot_position_return" in debug.keys()):
				self.snapshot_position_return = utility.getbool(debug["snapshot_position_return"],self.snapshot_position_return)
			if("snapshot_save" in debug.keys()):
				self.snapshot_save = utility.getbool(debug["snapshot_save"],self.snapshot_save)
			if("snapshot_download" in debug.keys()):
				self.snapshot_download = utility.getbool(debug["snapshot_download"],self.snapshot_download)
			if("settings_save" in debug.keys()):
				self.settings_save = utility.getbool(debug["settings_save"],self.settings_save)
			if("settings_load" in debug.keys()):
				self.settings_save = utility.getbool(debug["settings_load"],self.settings_save)
			if("print_state_changed" in debug.keys()):
				self.print_state_changed = utility.getbool(debug["print_state_changed"],self.print_state_changed)

	def LogInfo(self,message):
		if(self.enabled):
			self.Logger.info(message)
	def LogWarning(self,message):
		if(self.enabled):
			self.Logger.warning(message)
	def LogError(self,message):
		if(self.enabled):
			self.Logger.error(message)
	def LogPositionChange(self,message):
		if(self.position_change ):
			self.LogInfo(message)
	def LogPositionCommandReceived(self,message):
		if(self.position_command_received):
			self.LogInfo(message)
	def LogExtruderChange(self,message):
		if(self.extruder_change):
			self.LogInfo(message)
	def LogExtruderTriggered(self,message):
		if(self.extruder_triggered):
			self.LogInfo(message)
	def LogTriggerWaitState(self,message):
		if(self.trigger_wait_state):
			self.LogInfo(message)
	def LogTriggering(self,message):
		if(self.trigger_triggering):
			self.LogInfo(message)
	def LogTriggerTriggeringState(self, message):
		if(self.trigger_triggering_state):
			self.LogInfo(message)
	def LogPositionZminReached(self, message):
		if(self.trigger_layer_zmin_reached):
			self.LogInfo(message)
	def LogPositionLayerChange(self,message):
		if(self.trigger_layer_change):
			self.LogInfo(message)
	def LogPositionHeightChange(self,message):
		if(self.trigger_height_change):
			self.LogInfo(message)
	def LogPositionZHop(self,message):
		if(self.trigger_zhop):
			self.LogInfo(message)
	def LogTimerTriggerUnpaused(self,message):
		if(self.trigger_time_unpaused):
			self.LogInfo(message)
	def LogTriggerTimeRemaining(self,message):
		if(self.trigger_time_remaining):
			self.LogInfo(message)
	def LogTriggerTimeRemaining(self,message):
		if(self.trigger_time_remaining):
			self.LogInfo(message)
	def LogSnapshotGcode(self,message):
		if(self.snapshot_gcode):
			self.LogInfo(message)
	def LogSnapshotGcodeEndcommand(self,message):
		if(self.snapshot_gcode_endcommand):
			self.LogInfo(message)
	def LogSnapshotPosition(self,message):
		if(self.snapshot_position):
			self.LogInfo(message)
	def LogSnapshotPositionReturn(self,message):
		if(self.snapshot_position_return):
			self.LogInfo(message)
	def LogSnapshotSave(self,message):
		if(self.snapshot_save):
			self.LogInfo(message)
	def LogSnapshotDownload(self,message):
		if(self.snapshot_download):
			self.LogInfo(message)
	def LogSettingsSave(self,message):
		if(self.settings_save):
			self.LogInfo(message)
	def LogPrintStateChange(self,message):
		if(self.print_state_changed):
			self.LogInfo(message)
	def ApplyCommands(self, cmd, triggers, isSnapshot):
		# see if the command is our debug command
		command = Command()
		command = self.Commands.GetCommand(cmd)
		if(command is not None):
			if(command.Command == Commands.Debug_Assert.Command):
				# make sure our assert conditions are true or throw an exception
				command.Parse(cmd)
				snapshot = command.Parameters["Snapshot"]
				
				gcodeTrigger = command.Parameters["GcodeTrigger"]
				gcodeTriggerWait = command.Parameters["GcodeTriggerWait"]
				timerTrigger = command.Parameters["TimerTrigger"]
				timerTriggerWait = command.Parameters["TimerTriggerWait"]
				layerTrigger = command.Parameters["LayerTrigger"]
				layerTriggerWait = command.Parameters["LayerTriggerWait"]
				if(snapshot is not None):
					assert isSnapshot == snapshot
				for trigger in triggers:
					if(isinstance(trigger,GcodeTrigger)):
						if(gcodeTrigger is not None):
							assert trigger.IsTriggered == gcodeTrigger
						if(gcodeTriggerWait is not None):
							assert trigger.IsWaiting == gcodeTriggerWait
					if(isinstance(trigger,TimerTrigger)):
						if(timerTrigger is not None):
							assert trigger.IsTriggered == timerTrigger
						if(timerTriggerWait is not None):
							assert trigger.IsWaiting == timerTriggerWait
					if(isinstance(trigger,LayerTrigger)):
						if(layerTrigger is not None):
							assert trigger.IsTriggered == layerTrigger
						if(layerTriggerWait is not None):
							assert trigger.IsWaiting == layerTriggerWait


class OctolapseSettings(object):
	
	# constants
	def __init__(self, octoprintLogger,settings=None):
		
		self.current_profile_name = "Default"
		self.is_octolapse_enabled = True
		self.printer = Printer(None)
		self.profiles = { "Default" : Profile(None) }
		self.debug = DebugSettings(octoprintLogger,None)
		
		if(settings is not None):
			self.current_profile_name = utility.getstring(settings.get(["current_profile_name"]),self.current_profile_name)
			self.is_octolapse_enabled = utility.getbool(settings.get(["is_octolapse_enabled"]),self.is_octolapse_enabled)
			self.debug = DebugSettings(octoprintLogger,settings.get(["debug"]))
			self.printer = Printer(settings.get(["printer"]))
			profiles = settings.get(["profiles"])
			if(profiles is not None):
				for profile in profiles:
					if("name" in profile.keys()):
						octoprintLogger.info("Creating profile: {0}".format(profile["name"]))
						self.profiles[profile["name"]] = Profile(profile)

    # Profiles
	def CurrentProfile(self):
		if(len(self.profiles.keys()) == 0):
			profile = Profile()
			self.Proflies[profile.name] = profile
			self.current_profile_name = profile.name
			
			return profile
		if(self.current_profile_name not in self.profiles.keys()):
			self.current_profile_name = self.profiles.itervalues().next().name
		return self.profiles[self.current_profile_name]

	def Profile(self,profileName):
		return self.profiles[profileName]
	

