# coding=utf-8
import time
import utility
from .gcode import Commands, Command
from pprint import pprint
from .trigger import GcodeTrigger, TimerTrigger, LayerTrigger
import os
import sys
import uuid
PROFILE_SNAPSHOT_GCODE_TYPE = "gcode"



def GetSettingsForOctoprint(octoprintLogger,settings):
		defaults = OctolapseSettings(octoprintLogger,None)
		if(settings is None):
			settings = defaults
		octoprintSettings = {
			'version' :  utility.getstring(settings.version,defaults.version),
			"is_octolapse_enabled": utility.getbool(settings.is_octolapse_enabled,defaults.is_octolapse_enabled),
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
				'trigger_create'			: utility.getbool(settings.debug.trigger_create,defaults.debug.trigger_create),
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
				'render_start'				: utility.getbool(settings.debug.render_start,defaults.debug.render_start),
				'render_complete'			: utility.getbool(settings.debug.render_complete,defaults.debug.render_complete),
				'render_fail'				: utility.getbool(settings.debug.render_fail,defaults.debug.render_fail),
				'render_sync'				: utility.getbool(settings.debug.render_sync,defaults.debug.render_sync),
				'snapshot_clean'			: utility.getbool(settings.debug.snapshot_clean,defaults.debug.snapshot_clean),
				'settings_save'				: utility.getbool(settings.debug.settings_save,defaults.debug.settings_save),
				'settings_load'				: utility.getbool(settings.debug.settings_load,defaults.debug.settings_load),
				'print_state_changed'		: utility.getbool(settings.debug.print_state_changed,defaults.debug.print_state_changed),
				'camera_settings_apply'		: utility.getbool(settings.debug.camera_settings_apply,defaults.debug.camera_settings_apply)
			},
			'current_printer_guid' : utility.getstring(settings.current_printer_guid,defaults.current_printer_guid),
			'printers' : [],
			'current_stabilization_guid' : utility.getstring(settings.current_stabilization_guid,defaults.current_stabilization_guid),
			'stabilizations' : [],
			'current_snapshot_guid' : utility.getstring(settings.current_snapshot_guid,defaults.current_snapshot_guid),
			'snapshots' : [],
			'current_rendering_guid' : utility.getstring(settings.current_rendering_guid,defaults.current_rendering_guid),
			'renderings' : [],
			'current_camera_guid' : utility.getstring(settings.current_camera_guid,defaults.current_camera_guid),
			'cameras'	: []

		}

		defaultPrinter = defaults.CurrentPrinter()
		for key,printer in settings.printers.items():
			newPrinter = {
				'name'				: utility.getstring(printer.name,defaultPrinter.name),
				'guid'				: utility.getstring(printer.guid,defaultPrinter.guid),
				'retract_length'	: utility.getint(printer.retract_length,defaultPrinter.retract_length),
				'retract_speed'		: utility.getint(printer.retract_speed,defaultPrinter.retract_speed),
				'movement_speed'	: utility.getint(printer.movement_speed,defaultPrinter.movement_speed),
				'is_e_relative'		: utility.getbool(printer.is_e_relative, defaultPrinter.is_e_relative),
				'z_hop'				: utility.getfloat(printer.z_hop, defaultPrinter.z_hop),
				'z_min'				: utility.getfloat(printer.z_min,defaultPrinter.z_min),
				'snapshot_command'	: utility.getstring(printer.snapshot_command,defaultPrinter.snapshot_command),
			}

			octoprintSettings["printers"].append(newPrinter)

		defaultStabilization = defaults.CurrentStabilization()
		for key,stabilization in settings.stabilizations.items():
			newStabilization = {
				'name'					: utility.getstring(stabilization.name,defaultStabilization.name),
				'guid'					: utility.getstring(stabilization.guid,defaultStabilization.guid),
				'x_movement_speed'		: utility.getint(stabilization.x_movement_speed,defaultStabilization.x_movement_speed),
				'x_type'				: utility.getstring(stabilization.x_type,defaultStabilization.x_type),
				'x_fixed_coordinate'	: utility.getfloat(stabilization.x_fixed_coordinate,defaultStabilization.x_fixed_coordinate),
				'x_fixed_path'			: utility.getobject(stabilization.x_fixed_path,defaultStabilization.x_fixed_path),
				'x_fixed_path_loop'		: utility.getbool(stabilization.x_fixed_path_loop,defaultStabilization.x_fixed_path_loop),
				'x_relative'			: utility.getfloat(stabilization.x_relative,defaultStabilization.x_relative),
				'x_relative_print'		: utility.getfloat(stabilization.x_relative_print,defaultStabilization.x_relative_print),
				'x_relative_path'		: utility.getobject(stabilization.x_relative_path,defaultStabilization.x_relative_path),
				'x_relative_path_loop'	: utility.getbool(stabilization.x_relative_path_loop,defaultStabilization.x_relative_path_loop),
				'y_movement_speed_mms'	: utility.getint(stabilization.y_movement_speed_mms,defaultStabilization.y_movement_speed_mms),
				'y_type'				: utility.getstring(stabilization.y_type,defaultStabilization.y_type),
				'y_fixed_coordinate'	: utility.getfloat(stabilization.y_fixed_coordinate,defaultStabilization.y_fixed_coordinate),
				'y_fixed_path'			: utility.getobject(stabilization.y_fixed_path,defaultStabilization.y_fixed_path),
				'y_fixed_path_loop'		: utility.getbool(stabilization.y_fixed_path_loop,defaultStabilization.y_fixed_path_loop),
				'y_relative'			: utility.getfloat(stabilization.y_relative,defaultStabilization.y_relative),
				'y_relative_print'		: utility.getfloat(stabilization.y_relative_print,defaultStabilization.y_relative_print),
				'y_relative_path'		: utility.getobject(stabilization.y_relative_path,defaultStabilization.y_relative_path),
				'y_relative_path_loop'	: utility.getbool(stabilization.y_relative_path_loop,defaultStabilization.y_relative_path_loop),
				'z_movement_speed_mms'	: utility.getint(stabilization.z_movement_speed_mms,defaultStabilization.z_movement_speed_mms)
			}
			octoprintSettings["stabilizations"].append(newStabilization)

		defaultSnapshot = defaults.CurrentSnapshot()
		for key,snapshot in settings.snapshots.items():
			newSnapshot = {
				'name'								: utility.getstring(snapshot.name,defaultSnapshot.name),
				'guid'								: utility.getstring(snapshot.guid,defaultSnapshot.guid),
				'gcode_trigger_enabled'				: utility.getbool(snapshot.gcode_trigger_enabled,defaultSnapshot.gcode_trigger_enabled),
				'gcode_trigger_require_zhop'		: utility.getbool(snapshot.gcode_trigger_require_zhop,defaultSnapshot.gcode_trigger_require_zhop),
				'gcode_trigger_on_extruding'		: utility.getbool(snapshot.gcode_trigger_on_extruding,defaultSnapshot.gcode_trigger_on_extruding),
				'gcode_trigger_on_extruding_start'	: utility.getbool(snapshot.gcode_trigger_on_extruding_start,defaultSnapshot.gcode_trigger_on_extruding_start),
				'gcode_trigger_on_primed'			: utility.getbool(snapshot.gcode_trigger_on_primed,defaultSnapshot.gcode_trigger_on_primed),
				'gcode_trigger_on_retracting'		: utility.getbool(snapshot.gcode_trigger_on_retracting,defaultSnapshot.gcode_trigger_on_retracting),
				'gcode_trigger_on_retracted'		: utility.getbool(snapshot.gcode_trigger_on_retracted,defaultSnapshot.gcode_trigger_on_retracted),
				'gcode_trigger_on_detracting'		: utility.getbool(snapshot.gcode_trigger_on_detracting,defaultSnapshot.gcode_trigger_on_detracting),
				'timer_trigger_enabled'				: utility.getbool(snapshot.timer_trigger_enabled,defaultSnapshot.timer_trigger_enabled),
				'timer_trigger_require_zhop'		: utility.getbool(snapshot.timer_trigger_require_zhop,defaultSnapshot.timer_trigger_require_zhop),
				'timer_trigger_seconds'				: utility.getint(snapshot.timer_trigger_seconds,defaultSnapshot.timer_trigger_seconds),
				'timer_trigger_on_extruding'		: utility.getbool(snapshot.timer_trigger_on_extruding,defaultSnapshot.timer_trigger_on_extruding),
				'timer_trigger_on_extruding_start'	: utility.getbool(snapshot.timer_trigger_on_extruding_start,defaultSnapshot.timer_trigger_on_extruding_start),
				'timer_trigger_on_primed'			: utility.getbool(snapshot.timer_trigger_on_primed,defaultSnapshot.timer_trigger_on_primed),
				'timer_trigger_on_retracting'		: utility.getbool(snapshot.timer_trigger_on_retracting,defaultSnapshot.timer_trigger_on_retracting),
				'timer_trigger_on_retracted'		: utility.getbool(snapshot.timer_trigger_on_retracted,defaultSnapshot.timer_trigger_on_retracted),
				'timer_trigger_on_detracting'		: utility.getbool(snapshot.timer_trigger_on_detracting,defaultSnapshot.timer_trigger_on_detracting),
				'layer_trigger_enabled'				: utility.getbool(snapshot.layer_trigger_enabled,defaultSnapshot.layer_trigger_enabled),
				'layer_trigger_height'				: utility.getfloat(snapshot.layer_trigger_height,defaultSnapshot.layer_trigger_height),
				'layer_trigger_require_zhop'		: utility.getbool(snapshot.layer_trigger_require_zhop,defaultSnapshot.layer_trigger_require_zhop),
				'layer_trigger_on_extruding'		: utility.getbool(snapshot.layer_trigger_on_extruding,defaultSnapshot.layer_trigger_on_extruding),
				'layer_trigger_on_extruding_start'	: utility.getbool(snapshot.layer_trigger_on_extruding_start,defaultSnapshot.layer_trigger_on_extruding_start),
				'layer_trigger_on_primed'			: utility.getbool(snapshot.layer_trigger_on_primed,defaultSnapshot.layer_trigger_on_primed),
				'layer_trigger_on_retracting'		: utility.getbool(snapshot.layer_trigger_on_retracting,defaultSnapshot.layer_trigger_on_retracting),
				'layer_trigger_on_retracted'		: utility.getbool(snapshot.layer_trigger_on_retracted,defaultSnapshot.layer_trigger_on_retracted),
				'layer_trigger_on_detracting'		: utility.getbool(snapshot.layer_trigger_on_detracting,defaultSnapshot.layer_trigger_on_detracting),
				'delay'								: utility.getint(snapshot.delay,defaultSnapshot.delay),
				'output_format'						: utility.getstring(snapshot.output_format,defaultSnapshot.output_format),
				'output_filename'					: utility.getstring(snapshot.output_filename,defaultSnapshot.output_filename),
				'output_directory'					: utility.getstring(snapshot.output_directory,defaultSnapshot.output_directory),
				'retract_before_move'				: utility.getbool(snapshot.retract_before_move,defaultSnapshot.retract_before_move),
				'cleanup_before_print'				: utility.getbool(snapshot.cleanup_before_print,defaultSnapshot.cleanup_before_print),
				'cleanup_after_print'				: utility.getbool(snapshot.cleanup_after_print,defaultSnapshot.cleanup_after_print),
				'cleanup_after_cancel'				: utility.getbool(snapshot.cleanup_after_cancel,defaultSnapshot.cleanup_after_cancel),
				'cleanup_after_fail'				: utility.getbool(snapshot.cleanup_after_fail,defaultSnapshot.cleanup_after_fail),
				'cleanup_before_close'				: utility.getbool(snapshot.cleanup_before_close,defaultSnapshot.cleanup_before_close),
				'cleanup_after_render_complete'		: utility.getbool(snapshot.cleanup_after_render_complete,defaultSnapshot.cleanup_after_render_complete),
				'cleanup_after_render_fail'			: utility.getbool(snapshot.cleanup_after_render_fail,defaultSnapshot.cleanup_after_render_fail),
				'custom_script_enabled'				: utility.getbool(snapshot.custom_script_enabled,defaultSnapshot.custom_script_enabled),
				'script_path'						: utility.getstring(snapshot.script_path,defaultSnapshot.script_path)
			}
			octoprintSettings["snapshots"].append(newSnapshot)

		defaultRendering = defaults.CurrentRendering()
		for key,rendering in settings.renderings.items():
			newRendering = {
				'name'								: utility.getstring(rendering.name,defaultRendering.name),
				'guid'								: utility.getstring(rendering.guid,defaultRendering.guid),
				'enabled'							: utility.getbool(rendering.enabled,defaultRendering.enabled),
				'fps_calculation_type'				: utility.getstring(rendering.fps_calculation_type,defaultRendering.fps_calculation_type),
				'run_length_seconds'				: utility.getfloat(rendering.run_length_seconds,defaultRendering.run_length_seconds),
				'fps'								: utility.getfloat(rendering.fps,defaultRendering.fps),
				'max_fps'							: utility.getfloat(rendering.max_fps,defaultRendering.max_fps),
				'min_fps'							: utility.getfloat(rendering.min_fps,defaultRendering.min_fps),
				'output_format'						: utility.getstring(rendering.output_format,defaultRendering.output_format),
				'output_filename'					: utility.getstring(rendering.output_filename,defaultRendering.output_filename),
				'output_directory'					: utility.getstring(rendering.output_directory,defaultRendering.output_directory),
				'sync_with_timelapse'				: utility.getbool(rendering.sync_with_timelapse,defaultRendering.sync_with_timelapse),
				'octoprint_timelapse_directory'		: utility.getstring(rendering.octoprint_timelapse_directory,defaultRendering.octoprint_timelapse_directory),
				'ffmpeg_path'						: utility.getstring(rendering.ffmpeg_path,defaultRendering.ffmpeg_path),
				'bitrate'							: utility.getstring(rendering.bitrate,defaultRendering.bitrate),
				'flip_h'							: utility.getbool(rendering.flip_h,defaultRendering.flip_h),
				'flip_v'							: utility.getbool(rendering.flip_v,defaultRendering.flip_v),
				'rotate_90'							: utility.getbool(rendering.rotate_90,defaultRendering.rotate_90),
				'watermark'							: utility.getbool(rendering.watermark,defaultRendering.watermark)
			}
			octoprintSettings["renderings"].append(newRendering)

		defaultCamera = defaults.CurrentCamera()
		for key,camera in settings.cameras.items():
			newCamera = {
				'name'												: utility.getstring(camera.name,defaultCamera.name),
				'guid'												: utility.getstring(camera.guid,defaultCamera.guid),
				'address'											: utility.getstring(camera.address,defaultCamera.address),
				'snapshot_request_template'							: utility.getstring(camera.snapshot_request_template,defaultCamera.snapshot_request_template),
				'apply_settings_before_print'						: utility.getbool(camera.apply_settings_before_print,defaultCamera.apply_settings_before_print),
				'ignore_ssl_error'									: utility.getbool(camera.ignore_ssl_error,defaultCamera.ignore_ssl_error),
				'password'											: utility.getstring(camera.password,defaultCamera.password),
				'username'											: utility.getstring(camera.username,defaultCamera.username),
				'brightness'										: utility.getint(camera.brightness,defaultCamera.brightness),
				'contrast'											: utility.getint(camera.contrast,defaultCamera.contrast),
				'saturation'										: utility.getint(camera.saturation,defaultCamera.saturation),
				'white_balance_auto'								: utility.getbool(camera.white_balance_auto,defaultCamera.white_balance_auto),
				'gain'												: utility.getint(camera.gain,defaultCamera.gain),
				'powerline_frequency'								: utility.getint(camera.powerline_frequency,defaultCamera.powerline_frequency),
				'white_balance_temperature'							: utility.getint(camera.white_balance_temperature,defaultCamera.white_balance_temperature),
				'sharpness'											: utility.getint(camera.sharpness,defaultCamera.sharpness),
				'backlight_compensation_enabled'					: utility.getbool(camera.backlight_compensation_enabled,defaultCamera.backlight_compensation_enabled),
				'exposure_type'										: utility.getbool(camera.exposure_type,defaultCamera.exposure_type),
				'exposure'											: utility.getint(camera.exposure,defaultCamera.exposure),
				'exposure_auto_priority_enabled'					: utility.getbool(camera.exposure_auto_priority_enabled,defaultCamera.exposure_auto_priority_enabled),
				'pan'												: utility.getint(camera.pan,defaultCamera.pan),
				'tilt'												: utility.getint(camera.tilt,defaultCamera.tilt),
				'autofocus_enabled'									: utility.getbool(camera.autofocus_enabled,defaultCamera.autofocus_enabled),
				'focus'												: utility.getint(camera.focus,defaultCamera.focus),
				'zoom'												: utility.getint(camera.zoom,defaultCamera.zoom),
				'led1_mode'											: utility.getstring(camera.led1_mode,defaultCamera.led1_mode),
				'led1_frequency'									: utility.getint(camera.led1_frequency,defaultCamera.led1_frequency),
				'jpeg_quality'										: utility.getint(camera.jpeg_quality,defaultCamera.jpeg_quality),
				'brightness_request_template'						: utility.getstring(camera.brightness_request_template,defaultCamera.brightness_request_template),
				'contrast_request_template'							: utility.getstring(camera.contrast_request_template,defaultCamera.contrast_request_template),
				'saturation_request_template'						: utility.getstring(camera.saturation_request_template,defaultCamera.saturation_request_template),
				'white_balance_auto_request_template'				: utility.getstring(camera.white_balance_auto_request_template,defaultCamera.white_balance_auto_request_template),
				'gain_request_template'								: utility.getstring(camera.gain_request_template,defaultCamera.gain_request_template),
				'powerline_frequency_request_template'				: utility.getstring(camera.powerline_frequency_request_template,defaultCamera.powerline_frequency_request_template),
				'white_balance_temperature_request_template'		: utility.getstring(camera.white_balance_temperature_request_template,defaultCamera.white_balance_temperature_request_template),
				'sharpness_request_template'						: utility.getstring(camera.sharpness_request_template,defaultCamera.sharpness_request_template),
				'backlight_compensation_enabled_request_template'	: utility.getstring(camera.backlight_compensation_enabled_request_template,defaultCamera.backlight_compensation_enabled_request_template),
				'exposure_type_request_template'					: utility.getstring(camera.exposure_type_request_template,defaultCamera.exposure_type_request_template),
				'exposure_request_template'							: utility.getstring(camera.exposure_request_template,defaultCamera.exposure_request_template),
				'exposure_auto_priority_enabled_request_template'	: utility.getstring(camera.exposure_auto_priority_enabled_request_template,defaultCamera.exposure_auto_priority_enabled_request_template),
				'pan_request_template'								: utility.getstring(camera.pan_request_template,defaultCamera.pan_request_template),
				'tilt_request_template'								: utility.getstring(camera.tilt_request_template,defaultCamera.tilt_request_template),
				'autofocus_enabled_request_template'				: utility.getstring(camera.autofocus_enabled_request_template,defaultCamera.autofocus_enabled_request_template),
				'focus_request_template'							: utility.getstring(camera.focus_request_template,defaultCamera.focus_request_template),
				'zoom_request_template'								: utility.getstring(camera.zoom_request_template,defaultCamera.zoom_request_template),
				'led1_mode_request_template'						: utility.getstring(camera.led1_mode_request_template,defaultCamera.led1_mode_request_template),
				'led1_frequency_request_template'					: utility.getstring(camera.led1_frequency_request_template,defaultCamera.led1_frequency_request_template),
				'jpeg_quality_request_template'						: utility.getstring(camera.jpeg_quality_request_template,defaultCamera.jpeg_quality_request_template)
			}
			octoprintSettings["cameras"].append(newCamera)

		return octoprintSettings


class Printer(object):
	
	def __init__(self,printer):
		self.guid = str(uuid.uuid4())
		self.name = "Default"
		self.retract_length = 4.0
		self.retract_speed = 4800
		self.movement_speed = 7200
		self.z_hop = 0.5
		self.z_min = 0.2
		self.snapshot_command = "snap"
		self.is_e_relative = True
		if(printer is not None):
			if("guid" in printer):
				self.guid = utility.getstring(printer["guid"],self.guid)
			if("name" in printer.keys()):
				self.name = utility.getstring(printer["name"],self.guid)
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
		self.guid = str(uuid.uuid4())
		self.name = "Default"
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
			if("guid" in stabilization.keys()):
				self.guid = utility.getstring(stabilization["guid"],self.guid)
			if("name" in stabilization.keys()):
				self.name = utility.getstring(stabilization["name"],self.name)
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
		self.guid = str(uuid.uuid4())
		self.name = "Default"
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
			if("guid" in snapshot.keys()):
				self.guid = utility.getstring(snapshot["guid"],self.guid)
			if("name" in snapshot.keys()):
				self.name = utility.getstring(snapshot["name"],self.name)
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
		self.guid = str(uuid.uuid4())
		self.name = "Default"
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
			if("guid" in rendering.keys()):
				self.guid = utility.getstring(rendering["guid"],self.guid)
			if("name" in rendering.keys()):
				self.name = utility.getstring(rendering["name"],self.name)
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
		self.guid = str(uuid.uuid4())
		self.name = "Default"
		self.apply_settings_before_print = True
		self.address = "http://127.0.0.1/webcam/"
		self.snapshot_request_template = "{camera_address}?action=snapshot"
		self.ignore_ssl_error = False
		self.username = ""
		self.password = ""
		self.brightness = 128
		self.brightness_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=9963776&group=1&value={value}"
		self.contrast = 128
		self.contrast_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=9963777&group=1&value={value}"
		self.saturation = 128
		self.saturation_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=9963778&group=1&value={value}"
		self.white_balance_auto = True
		self.white_balance_auto_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=9963788&group=1&value={value}"
		self.gain = 0
		self.gain_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=9963795&group=1&value={value}"
		self.powerline_frequency = 60
		self.powerline_frequency_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=9963800&group=1&value={value}"
		self.white_balance_temperature = 4000
		self.white_balance_temperature_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=9963802&group=1&value={value}"
		self.sharpness = 128
		self.sharpness_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=9963803&group=1&value={value}"
		self.backlight_compensation_enabled = False
		self.backlight_compensation_enabled_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=9963804&group=1&value={value}"
		self.exposure_type = True
		self.exposure_type_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=10094849&group=1&value={value}"
		self.exposure = 250
		self.exposure_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=10094850&group=1&value={value}"
		self.exposure_auto_priority_enabled = True
		self.exposure_auto_priority_enabled_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=10094851&group=1&value={value}"
		self.pan = 0
		self.pan_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=10094856&group=1&value={value}"
		self.tilt = 0
		self.tilt_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=10094857&group=1&value={value}"
		self.autofocus_enabled = True
		self.autofocus_enabled_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=10094860&group=1&value={value}"
		self.focus = 35
		self.focus_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=10094858&group=1&value={value}"
		self.zoom = 100
		self.zoom_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=10094861&group=1&value={value}"
		self.led1_mode = 'auto'
		self.led1_mode_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=168062213&group=1&value={value}"
		self.led1_frequency = 0
		self.led1_frequency_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=168062214&group=1&value={value}"
		self.jpeg_quality = 80
		self.jpeg_quality_request_template = "{camera_address}?action=command&dest=0&plugin=0&id=1&group=3&value={value}"

		if(not camera is None):
			if("guid" in camera.keys()):
				self.guid = utility.getstring(camera["guid"],self.guid)
			if("name" in camera.keys()):
				self.name = utility.getstring(camera["name"],self.name)
			if("address" in camera.keys()):
				self.address = utility.getstring(camera["address"],self.address)
			if("apply_settings_before_print" in camera.keys()):
				self.apply_settings_before_print = utility.getbool(camera["apply_settings_before_print"],self.apply_settings_before_print)
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
			if("snapshot_request_template" in camera.keys()):
				self.snapshot_request_template = utility.getstring(camera["snapshot_request_template"],self.snapshot_request_template)
			if("brightness_request_template" in camera.keys()):
				self.brightness_request_template = utility.getstring(camera["brightness_request_template"],self.brightness_request_template)
			if("contrast_request_template" in camera.keys()):
				self.contrast_request_template = utility.getstring(camera["contrast_request_template"],self.contrast_request_template)
			if("saturation_request_template" in camera.keys()):
				self.saturation_request_template = utility.getstring(camera["saturation_request_template"],self.saturation_request_template)
			if("white_balance_auto_request_template" in camera.keys()):
				self.white_balance_auto_request_template = utility.getstring(camera["white_balance_auto_request_template"],self.white_balance_auto_request_template)
			if("gain_request_template" in camera.keys()):
				self.gain_request_template = utility.getstring(camera["gain_request_template"],self.gain_request_template)
			if("powerline_frequency_request_template" in camera.keys()):
				self.powerline_frequency_request_template = utility.getstring(camera["powerline_frequency_request_template"],self.powerline_frequency_request_template)
			if("white_balance_temperature_request_template" in camera.keys()):
				self.white_balance_temperature_request_template = utility.getstring(camera["white_balance_temperature_request_template"],self.white_balance_temperature_request_template)
			if("sharpness_request_template" in camera.keys()):
				self.sharpness_request_template = utility.getstring(camera["sharpness_request_template"],self.sharpness_request_template)
			if("backlight_compensation_enabled_request_template" in camera.keys()):
				self.backlight_compensation_enabled_request_template = utility.getstring(camera["backlight_compensation_enabled_request_template"],self.backlight_compensation_enabled_request_template)
			if("exposure_type_request_template" in camera.keys()):
				self.exposure_type_request_template = utility.getstring(camera["exposure_type_request_template"],self.exposure_type_request_template)
			if("exposure_request_template" in camera.keys()):
				self.exposure_request_template = utility.getstring(camera["exposure_request_template"],self.exposure_request_template)
			if("exposure_auto_priority_enabled_request_template" in camera.keys()):
				self.exposure_auto_priority_enabled_request_template = utility.getstring(camera["exposure_auto_priority_enabled_request_template"],self.exposure_auto_priority_enabled_request_template)
			if("pan_request_template" in camera.keys()):
				self.pan_request_template = utility.getstring(camera["pan_request_template"],self.pan_request_template)
			if("tilt_request_template" in camera.keys()):
				self.tilt_request_template = utility.getstring(camera["tilt_request_template"],self.tilt_request_template)
			if("autofocus_enabled_request_template" in camera.keys()):
				self.autofocus_enabled_request_template = utility.getstring(camera["autofocus_enabled_request_template"],self.autofocus_enabled_request_template)
			if("focus_request_template" in camera.keys()):
				self.focus_request_template = utility.getstring(camera["focus_request_template"],self.focus_request_template)
			if("led1_mode_request_template" in camera.keys()):
				self.led1_mode_request_template = utility.getstring(camera["led1_mode_request_template"],self.led1_mode_request_template)
			if("led1_frequency_request_template" in camera.keys()):
				self.led1_frequency_request_template = utility.getstring(camera["led1_frequency_request_template"],self.led1_frequency_request_template)
			if("jpeg_quality_request_template" in camera.keys()):
				self.jpeg_quality_request_template = utility.getstring(camera["jpeg_quality_request_template"],self.jpeg_quality_request_template)
			if("zoom_request_template" in camera.keys()):
				self.zoom_request_template = utility.getstring(camera["zoom_request_template"],self.zoom_request_template)
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
		self.trigger_create = False
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
		self.render_start = False
		self.render_complete = False
		self.render_fail = False
		self.render_sync = False
		self.snapshot_clean = False
		self.settings_save = False
		self.settings_load = False
		self.print_state_changed = False
		self.camera_settings_apply = False
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
			if("trigger_create" in debug.keys()):
				self.trigger_create = utility.getbool(debug["trigger_create"],self.trigger_create)
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
			if("render_start" in debug.keys()):
				self.render_start = utility.getbool(debug["render_start"],self.snapshot_download)
			if("render_complete" in debug.keys()):
				self.render_complete = utility.getbool(debug["render_complete"],self.render_complete)
			if("render_fail" in debug.keys()):
				self.render_fail = utility.getbool(debug["render_fail"],self.snapshot_download)
			if("render_sync" in debug.keys()):
				self.render_sync = utility.getbool(debug["render_sync"],self.snapshot_download)
			if("snapshot_clean" in debug.keys()):
				self.snapshot_clean = utility.getbool(debug["snapshot_clean"],self.snapshot_clean)
			if("settings_save" in debug.keys()):
				self.settings_save = utility.getbool(debug["settings_save"],self.settings_save)
			if("settings_load" in debug.keys()):
				self.settings_save = utility.getbool(debug["settings_load"],self.settings_save)
			if("print_state_changed" in debug.keys()):
				self.print_state_changed = utility.getbool(debug["print_state_changed"],self.print_state_changed)
			if("camera_settings_apply" in debug.keys()):
				self.camera_settings_apply = utility.getbool(debug["camera_settings_apply"],self.camera_settings_apply)
			
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
	def LogTriggerCreate(self,message):
		if(self.trigger_create):
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
	def LogRenderStart(self,message):
		if(self.render_start):
			self.LogInfo(message)
	def LogRenderComplete(self,message):
		if(self.render_complete):
			self.LogInfo(message)
	def LogRenderFail(self,message):
		if(self.render_fail):
			self.LogInfo(message)
	def LogRenderSync(self,message):
		if(self.render_sync):
			self.LogInfo(message)
	def LogSnapshotClean(self,message):
		if(self.snapshot_clean):
			self.LogInfo(message)

	def LogSettingsSave(self,message):
		if(self.settings_save):
			self.LogInfo(message)
	def LogPrintStateChange(self,message):
		if(self.print_state_changed):
			self.LogInfo(message)
	def LogCameraSettingsApply(self,message):
		if(self.camera_settings_apply):
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
		self.version = "0.1.0"
		
		self.is_octolapse_enabled = True
		self.debug = DebugSettings(octoprintLogger,None)

		printer = Printer(None)
		self.current_printer_guid = printer.guid
		self.printers = {printer.guid : printer}

		stabilization = Stabilization(None)
		self.current_stabilization_guid = stabilization.guid
		self.stabilizations = {stabilization.guid:stabilization}

		snapshot = Snapshot(None)
		self.current_snapshot_guid = snapshot.guid
		self.snapshots = {snapshot.guid:snapshot}

		rendering = Rendering(None)
		self.current_rendering_guid = rendering.guid
		self.renderings = {rendering.guid:rendering}

		camera = Camera(None)
		self.current_camera_guid = camera.guid
		self.cameras = {camera.guid:camera}


		if(settings is not None):
			self.is_octolapse_enabled = utility.getbool(settings.get(["is_octolapse_enabled"]),self.is_octolapse_enabled)
			self.debug = DebugSettings(octoprintLogger,settings.get(["debug"]))
			self.printer = Printer(settings.get(["printer"]))
			self.current_printer_guid = utility.getstring(settings.get(["current_printer_guid"]),self.current_printer_guid)
			_printers = settings.get(["printers"])
			if(_printers is not None):
				self.printers = {}
				for printer in _printers:
					#octoprintLogger.info("Creating printer '{0}' with guid '{1}'".format(printer["name"], printer["guid"]))
					self.printers[printer["guid"]] = Printer(printer)
				if(self.current_printer_guid not in self.printers.keys()):
					self.current_printer_guid = self.printers[0].guid

			self.current_stabilization_guid = utility.getstring(settings.get(["current_stabilization_guid"]),self.current_stabilization_guid)
			_stabilizations = settings.get(["stabilizations"])
			if(_stabilizations is not None):
				self.stabilization = {}
				for stabilization in _stabilizations:
					#octoprintLogger.info("Creating stabilization: {0}-{1}".format(stabilization["name"], stabilization["guid"]))
					self.stabilizations[stabilization["guid"]] = Stabilization(stabilization)
				if(self.current_stabilization_guid not in self.stabilizations.keys()):
					self.current_stabilization_guid = self.stabilizations[0].guid

			self.current_snapshot_guid = utility.getstring(settings.get(["current_snapshot_guid"]),self.current_snapshot_guid)
			_snapshots = settings.get(["snapshots"])
			if(_snapshots is not None):
				self.snapshots = {}
				for snapshot in _snapshots:
					#octoprintLogger.info("Creating snapshot: {0} - {1}".format(snapshot["name"], snapshot["guid"]))
					self.snapshots[snapshot["guid"]] = Snapshot(snapshot)
				if(self.current_snapshot_guid not in self.snapshots.keys()):
					self.current_snapshot_guid = self.snapshots[0].guid
			self.current_rendering_guid = utility.getstring(settings.get(["current_rendering_guid"]),self.current_rendering_guid)
			_renderings = settings.get(["renderings"])
			if(_renderings is not None):
				self.renderings = {}
				for rendering in _renderings:
					#octoprintLogger.info("Creating rendering: {0} - {1}".format(rendering["name"],rendering["guid"]))
					self.renderings[rendering["guid"]] = Rendering(rendering)
				if(self.current_rendering_guid not in self.renderings.keys()):
					self.current_rendering_guid = self.renderings[0].guid

			self.current_camera_guid = utility.getstring(settings.get(["current_camera_guid"]),self.current_camera_guid)
			_cameras = settings.get(["cameras"])
			if(_cameras is not None):
				self.cameras = {}
				for camera in _cameras:
					#octoprintLogger.info("Creating camera: {0} - {1}".format(camera["name"],camera["guid"]))
					self.cameras[camera["guid"]] = Camera(camera)
				if(self.current_camera_guid not in self.cameras.keys()):
					self.current_camera_guid = self.cameras[0].guid
	def CurrentStabilization(self):
		if(len(self.stabilizations.keys()) == 0):
			stabilization = Stabilization(None)
			self.stabilizations[stabilization.guid] = stabilization
			self.current_stabilization_guid = stabilization.guid
		return self.stabilizations[self.current_stabilization_guid]
	def CurrentSnapshot(self):
		if(len(self.snapshots.keys()) == 0):
			snapshot = Snapshot(None)
			self.snapshots[snapshot.guid] = snapshot
			self.current_snapshot_guid = snapshot.guid
		return self.snapshots[self.current_snapshot_guid]
	def CurrentRendering(self):
		if(len(self.renderings.keys()) == 0):
			rendering = Rendering(None)
			self.renderings[rendering.guid] = rendering
			self.current_rendering_guid = rendering.guid
		return self.renderings[self.current_rendering_guid]
	def CurrentPrinter(self):
		if(len(self.printers.keys()) == 0):
			printer = Printer(None)
			self.printers[printer.guid] = printer
			self.current_printer_guid = printer.guid
		return self.printers[self.current_printer_guid]
	def CurrentCamera(self):
		if(len(self.cameras.keys()) == 0):
			camera = Camera(None)
			self.cameras[camera.guid] = camera
			self.current_camera_guid = camera.guid
		return self.cameras[self.current_camera_guid]

	

