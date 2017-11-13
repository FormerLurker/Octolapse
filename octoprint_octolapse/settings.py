# coding=utf-8
import time
import utility
PROFILE_SNAPSHOT_GCODE_TYPE = "gcode"

def GetOctoprintDefaultSettings():
	settings = OctolapseSettings(None)
	return GetOctoprintSettings(settings)

def GetOctoprintSettings(settings):
		defaults = OctolapseSettings(None)
		print (settings)
		octoprintSettings = { "is_octolapse_enabled" : utility.getbool(settings.is_octolapse_enabled,defaults.is_octolapse_enabled),
			'current_profile_name' : utility.getstring(settings.current_profile_name,defaults.current_profile_name),
			'stabilization_options' : [
				dict(
					value='disabled'
					,name='Disabled'
				),dict(
					value='fixed_coordinate'
					,name='Fixed (Millimeters)'
				),dict(
					value='fixed_path'
					,name='CSV Separated List of Y Coordinates (Millimeters)'
				)
				,dict(
					value='relative'
					,name='Relative to Bed(percent)'
				)
				,dict(
					value='relative_path'
					,name='Relative CSV (percent).'
				)
			],
			'fps_calculation_options' : [
				dict(
					value='static'
					,name='Static FPS (higher FPS = better quality/shorter videos)'
				),dict(
					value='duration'
					,name='Fixed Run Length (FPS = Total Frames/Run Length Seconds)'
				)
			],
			'printer' : {
				'retract_length' :  utility.getint(settings.printer.retract_length,defaults.printer.retract_length),
				'retract_speed' : utility.getint(settings.printer.retract_speed,defaults.printer.retract_speed),
				'movement_speed' : utility.getint(settings.printer.movement_speed,defaults.printer.movement_speed),
				'snapshot_command' :  utility.getstring(settings.printer.snapshot_command,defaults.printer.snapshot_command),
				'snapshot_gcode' : utility.getstring(settings.printer.snapshot_gcode,defaults.printer.snapshot_gcode)
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
					'gcode_trigger_on_extruding'		: utility.getbool(profile.snapshot.gcode_trigger_on_extruding,defaultProfile.snapshot.gcode_trigger_on_extruding),
					'gcode_trigger_on_extruding_start'	: utility.getbool(profile.snapshot.gcode_trigger_on_extruding_start,defaultProfile.snapshot.gcode_trigger_on_extruding_start),
					'gcode_trigger_on_primed'			: utility.getbool(profile.snapshot.gcode_trigger_on_primed,defaultProfile.snapshot.gcode_trigger_on_primed),
					'gcode_trigger_on_retracting'		: utility.getbool(profile.snapshot.gcode_trigger_on_retracting,defaultProfile.snapshot.gcode_trigger_on_retracting),
					'gcode_trigger_on_retracted'		: utility.getbool(profile.snapshot.gcode_trigger_on_retracted,defaultProfile.snapshot.gcode_trigger_on_retracted),
					'gcode_trigger_on_detracting'		: utility.getbool(profile.snapshot.gcode_trigger_on_detracting,defaultProfile.snapshot.gcode_trigger_on_detracting),
					'timer_trigger_enabled'				: utility.getbool(profile.snapshot.timer_trigger_enabled,defaultProfile.snapshot.timer_trigger_enabled),
					'timer_trigger_seconds'				: utility.getint (profile.snapshot.timer_trigger_seconds,defaultProfile.snapshot.timer_trigger_seconds),
					'timer_trigger_on_extruding'		: utility.getbool(profile.snapshot.timer_trigger_on_extruding,defaultProfile.snapshot.timer_trigger_on_extruding),
					'timer_trigger_on_extruding_start'	: utility.getbool(profile.snapshot.timer_trigger_on_extruding_start,defaultProfile.snapshot.timer_trigger_on_extruding_start),
					'timer_trigger_on_primed'			: utility.getbool(profile.snapshot.timer_trigger_on_primed,defaultProfile.snapshot.timer_trigger_on_primed),
					'timer_trigger_on_retracting'		: utility.getbool(profile.snapshot.timer_trigger_on_retracting,defaultProfile.snapshot.timer_trigger_on_retracting),
					'timer_trigger_on_retracted'		: utility.getbool(profile.snapshot.timer_trigger_on_retracted,defaultProfile.snapshot.timer_trigger_on_retracted),
					'timer_trigger_on_detracting'		: utility.getbool(profile.snapshot.timer_trigger_on_detracting,defaultProfile.snapshot.timer_trigger_on_detracting),
					'layer_trigger_enabled'				: utility.getbool(profile.snapshot.layer_trigger_enabled,defaultProfile.snapshot.layer_trigger_enabled),
					'layer_trigger_height'				: utility.getint (profile.snapshot.layer_trigger_height,defaultProfile.snapshot.layer_trigger_height),
					'layer_trigger_zmin'				: utility.getint (profile.snapshot.layer_trigger_zmin,defaultProfile.snapshot.layer_trigger_zmin),
					'layer_trigger_on_extruding'		: utility.getbool(profile.snapshot.layer_trigger_on_extruding,defaultProfile.snapshot.layer_trigger_on_extruding),
					'layer_trigger_on_extruding_start'	: utility.getbool(profile.snapshot.layer_trigger_on_extruding_start,defaultProfile.snapshot.layer_trigger_on_extruding_start),
					'layer_trigger_on_primed'			: utility.getbool(profile.snapshot.layer_trigger_on_primed,defaultProfile.snapshot.layer_trigger_on_primed),
					'layer_trigger_on_retracting'		: utility.getbool(profile.snapshot.layer_trigger_on_retracting,defaultProfile.snapshot.layer_trigger_on_retracting),
					'layer_trigger_on_retracted'		: utility.getbool(profile.snapshot.layer_trigger_on_retracted,defaultProfile.snapshot.layer_trigger_on_retracted),
					'layer_trigger_on_detracting'		: utility.getbool(profile.snapshot.layer_trigger_on_detracting,defaultProfile.snapshot.layer_trigger_on_detracting),
					'archive' : utility.getbool(profile.snapshot.archive,defaultProfile.snapshot.archive ),
					'delay' : utility.getint(profile.snapshot.delay,defaultProfile.snapshot.delay ),
					'output_format' : utility.getstring(profile.snapshot.output_format,defaultProfile.snapshot.output_format ),
					'output_filename' :utility.getstring( profile.snapshot.output_filename,defaultProfile.snapshot.output_filename ),
					'output_directory' : utility.getstring(profile.snapshot.output_directory,defaultProfile.snapshot.output_directory ),
					'retract_before_move' : utility.getbool(profile.snapshot.retract_before_move,defaultProfile.snapshot.retract_before_move ),
					'cleanup_before_print' : utility.getbool(profile.snapshot.cleanup_before_print,defaultProfile.snapshot.cleanup_before_print ),
					'cleanup_after_print' : utility.getbool(profile.snapshot.cleanup_after_print,defaultProfile.snapshot.cleanup_after_print ),
					'cleanup_after_cancel' : utility.getbool(profile.snapshot.cleanup_after_cancel,defaultProfile.snapshot.cleanup_after_cancel ),
					'cleanup_before_close' :  utility.getbool(profile.snapshot.cleanup_before_close,defaultProfile.snapshot.cleanup_before_close ),
					'cleanup_after_render' : utility.getbool(profile.snapshot.cleanup_after_render,defaultProfile.snapshot.cleanup_after_render ),
					'custom_script_enabled' : utility.getbool(profile.snapshot.custom_script_enabled,defaultProfile.snapshot.custom_script_enabled),
					'script_path' : utility.getstring(profile.snapshot.script_path,defaultProfile.snapshot.script_path),
				},
				'rendering' : {
					'enabled' : utility.getbool(profile.rendering.enabled,defaultProfile.rendering.enabled ),
					'fps_calculation_type' : utility.getstring(profile.rendering.fps_calculation_type,defaultProfile.rendering.fps_calculation_type ),
					'run_length_seconds' : utility.getfloat(profile.rendering.run_length_seconds,defaultProfile.rendering.run_length_seconds ),
					'fps' : utility.getfloat(profile.rendering.fps,defaultProfile.rendering.fps ),
					'max_fps' : utility.getfloat(profile.rendering.max_fps,defaultProfile.rendering.max_fps ),
					'min_fps' : utility.getfloat(profile.rendering.min_fps,defaultProfile.rendering.min_fps ),
					'output_format' : utility.getstring(profile.rendering.output_format,defaultProfile.rendering.output_format ),
					'output_filename' :utility.getstring( profile.rendering.output_filename,defaultProfile.rendering.output_filename ),
					'output_directory' : utility.getstring(profile.rendering.output_directory,defaultProfile.rendering.output_directory ),
					'sync_with_timelapse' :  utility.getbool(profile.rendering.sync_with_timelapse,defaultProfile.rendering.sync_with_timelapse )
				},
				
				'camera' : {
					
					'address' : utility.getstring(profile.camera.address,defaultProfile.camera.address),
					'ignore_ssl_error' : utility.getbool(profile.camera.ignore_ssl_error,defaultProfile.camera.ignore_ssl_error),
					'password' : utility.getstring(profile.camera.password,defaultProfile.camera.password),
					'username' : utility.getstring(profile.camera.username,defaultProfile.camera.username),
					'brightness' : utility.getint(profile.camera.brightness,defaultProfile.camera.brightness ),
					'contrast' : utility.getint(profile.camera.contrast,defaultProfile.camera.contrast ),
					'saturation' : utility.getint(profile.camera.saturation,defaultProfile.camera.saturation ),
					'white_balance_auto' : utility.getbool(profile.camera.white_balance_auto,defaultProfile.camera.white_balance_auto ),
					'gain' : utility.getint(profile.camera.gain,defaultProfile.camera.gain ),
					'powerline_frequency' : utility.getint(profile.camera.powerline_frequency,defaultProfile.camera.powerline_frequency ),
					'white_balance_temperature' : utility.getint(profile.camera.white_balance_temperature,defaultProfile.camera.white_balance_temperature ),
					'sharpness' : utility.getint(profile.camera.sharpness,defaultProfile.camera.sharpness ),
					'backlight_compensation_enabled' :  utility.getbool(profile.camera.backlight_compensation_enabled,defaultProfile.camera.backlight_compensation_enabled ),
					'exposure_type' : utility.getbool(profile.camera.exposure_type,defaultProfile.camera.exposure_type ),
					'exposure' : utility.getint(profile.camera.exposure,defaultProfile.camera.exposure ),
					'exposure_auto_priority_enabled' : utility.getbool(profile.camera.exposure_auto_priority_enabled,defaultProfile.camera.exposure_auto_priority_enabled ),
					'pan' : utility.getint(profile.camera.pan,defaultProfile.camera.pan ),
					'tilt' : utility.getint(profile.camera.tilt,defaultProfile.camera.tilt ),
					'autofocus_enabled' : utility.getbool(profile.camera.autofocus_enabled,defaultProfile.camera.autofocus_enabled ),
					'focus' : utility.getint(profile.camera.focus,defaultProfile.camera.focus ),
					'zoom' : utility.getint(profile.camera.zoom,defaultProfile.camera.zoom ),
					'led1_mode' :  utility.getstring(profile.camera.led1_mode,defaultProfile.camera.led1_mode ),
					'led1_frequency' : utility.getint(profile.camera.led1_frequency,defaultProfile.camera.led1_frequency ),
					'jpeg_quality' : utility.getint(profile.camera.jpeg_quality,defaultProfile.camera.jpeg_quality )
				}
			}
			octoprintSettings["profiles"].append(newProfile)

		octoprintSettings["printer"]["snapshot_gcode"] = []
		if(settings.printer.snapshot_gcode is not None):
			for str in settings.printer.snapshot_gcode:
				octoprintSettings["printer"]["snapshot_gcode"].append(str)
		else:
			for str in defaults.printer.snapshot_gcode:
				octoprintSettings["printer"]["snapshot_gcode"].append(str)
		return octoprintSettings


class Printer(object):
	
	def __init__(self,printer):
		self.retract_length = 2.0
		self.retract_speed = 3600
		self.movement_speed = 3600
		self.snapshot_command = 'snap'
		self.snapshot_gcode = [ "G90; abs coord","G0 X{0:f} Y{1:f} F{2:d}; Move fast","M400; Wait for command to finish","G4 P{3:d} ; Wait a bit longer to allow the camera to stabilize" ]
		if(printer is not None):
			self.retract_length = utility.getfloat(printer["retract_length"],self.retract_length)
			self.retract_speed = utility.getint(printer["retract_speed"],self.retract_speed)
			self.movement_speed = utility.getint(printer["movement_speed"],self.movement_speed)
			self.snapshot_command = utility.getstring(printer["snapshot_command"],self.snapshot_command)
			self.snapshot_gcode = utility.getstring(printer["snapshot_gcode"],self.snapshot_gcode)
		
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
			self.x_movement_speed = utility.getint(stabilization["x_movement_speed"],self.x_movement_speed)
			self.x_type = utility.getstring(stabilization["x_type"],self.x_type)
			self.x_fixed_coordinate = utility.getfloat(stabilization["x_fixed_coordinate"],self.x_fixed_coordinate)
			self.x_fixed_path = utility.getstring(stabilization["x_fixed_path"],self.x_fixed_path)
			self.x_fixed_path_loop = utility.getbool(stabilization["x_fixed_path_loop"],self.x_fixed_path_loop)
			self.x_relative = utility.getfloat(stabilization["x_relative"],self.x_relative)
			self.x_relative_print = utility.getfloat(stabilization["x_relative_print"],self.x_relative_print)
			self.x_relative_path = utility.getstring(stabilization["x_relative_path"],self.x_relative_path)
			self.x_relative_path_loop = utility.getbool(stabilization["x_relative_path_loop"],self.x_relative_path_loop)
			self.y_movement_speed_mms = utility.getint(stabilization["y_movement_speed_mms"],self.y_movement_speed_mms)
			self.y_type = utility.getstring(stabilization["y_type"],self.y_type)
			self.y_fixed_coordinate = utility.getfloat(stabilization["y_fixed_coordinate"],self.y_fixed_coordinate)
			self.y_fixed_path = utility.getstring(stabilization["y_fixed_path"],self.y_fixed_path)
			self.y_fixed_path_loop = utility.getbool(stabilization["y_fixed_path_loop"],self.y_fixed_path_loop)
			self.y_relative = utility.getfloat(stabilization["y_relative"],self.y_relative)
			self.y_relative_print = utility.getfloat(stabilization["y_relative_print"],self.y_relative_print)
			self.y_relative_path = utility.getstring(stabilization["y_relative_path"],self.y_relative_path)
			self.y_relative_path_loop = utility.getbool(stabilization["y_relative_path_loop"],self.y_relative_path_loop)
			self.z_movement_speed_mms = utility.getint(stabilization["z_movement_speed_mms"],self.z_movement_speed_mms)



class Snapshot(object):

	def __init__(self,snapshot):

		#Initialize defaults
		#Gcode Trigger
		self.gcode_trigger_enabled		= True
		self.gcode_trigger_on_extruding = True
		self.gcode_trigger_on_extruding_start = True
		self.gcode_trigger_on_primed = True
		self.gcode_trigger_on_retracting = True
		self.gcode_trigger_on_retracted = True
		self.gcode_trigger_on_detracting = True
		#Timer Trigger
		self.timer_trigger_enabled = False
		self.timer_trigger_seconds = 60
		self.timer_trigger_on_extruding = True
		self.timer_trigger_on_extruding_start = True
		self.timer_trigger_on_primed = True
		self.timer_trigger_on_retracting = False
		self.timer_trigger_on_retracted = True
		self.timer_trigger_on_detracting = True
		#Layer Trigger
		self.layer_trigger_enabled = True
		self.layer_trigger_height = 0
		self.layer_trigger_zmin = 0.5
		self.layer_trigger_on_extruding = True
		self.layer_trigger_on_extruding_start = True
		self.layer_trigger_on_primed = False
		self.layer_trigger_on_retracting = False
		self.layer_trigger_on_retracted = False
		self.layer_trigger_on_detracting = False
		# other settings
		self.archive = True
		self.delay = 1000
		self.retract_before_move = False
		self.output_format = "jpg";
		self.output_filename = "{FILENAME}_{DATETIMESTAMP}.{OUTPUTFILEEXTENSION}"
		self.output_directory = "./snapshots/{FILENAME}_{PRINTSTARTTIME}/"
		self.cleanup_before_print = True
		self.cleanup_after_print = False
		self.cleanup_after_cancel = True
		self.cleanup_before_close = False
		self.cleanup_after_render = True
		self.custom_script_enabled = False
		self.script_path = ""
		
		if(snapshot is not None):
			#Initialize all values according to the provided snapshot, use defaults if the values are null or incorrectly formatted
			self.gcode_trigger_enabled				= utility.getbool(snapshot["gcode_trigger_enabled"],self.gcode_trigger_enabled)
			self.gcode_trigger_on_extruding			= utility.getbool(snapshot["gcode_trigger_on_extruding"],self.gcode_trigger_on_extruding)
			self.gcode_trigger_on_extruding_start	= utility.getbool(snapshot["gcode_trigger_on_extruding_start"],self.gcode_trigger_on_extruding_start)
			self.gcode_trigger_on_primed			= utility.getbool(snapshot["gcode_trigger_on_primed"],self.gcode_trigger_on_primed)
			self.gcode_trigger_on_retracting		= utility.getbool(snapshot["gcode_trigger_on_retracting"],self.gcode_trigger_on_retracting)
			self.gcode_trigger_on_retracted			= utility.getbool(snapshot["gcode_trigger_on_retracted"],self.gcode_trigger_on_retracted)
			self.gcode_trigger_on_detracting		= utility.getbool(snapshot["gcode_trigger_on_detracting"],self.gcode_trigger_on_detracting)
			self.timer_trigger_enabled				= utility.getbool(snapshot["timer_trigger_enabled"],self.timer_trigger_enabled)
			self.timer_trigger_seconds				= utility.getint(snapshot["timer_trigger_seconds"],self.timer_trigger_seconds)
			self.timer_trigger_on_extruding			= utility.getbool(snapshot["timer_trigger_on_extruding"],self.timer_trigger_on_extruding)
			self.timer_trigger_on_extruding_start	= utility.getbool(snapshot["timer_trigger_on_extruding_start"],self.timer_trigger_on_extruding_start)
			self.timer_trigger_on_primed			= utility.getbool(snapshot["timer_trigger_on_primed"],self.timer_trigger_on_primed)
			self.timer_trigger_on_retracting		= utility.getbool(snapshot["timer_trigger_on_retracting"],self.timer_trigger_on_retracting)
			self.timer_trigger_on_retracted			= utility.getbool(snapshot["timer_trigger_on_retracted"],self.timer_trigger_on_retracted)
			self.timer_trigger_on_detracting		= utility.getbool(snapshot["timer_trigger_on_detracting"],self.timer_trigger_on_detracting)
			self.layer_trigger_enabled				= utility.getbool(snapshot["layer_trigger_enabled"],self.layer_trigger_enabled)
			self.layer_trigger_height				= utility.getint(snapshot["layer_trigger_height"],self.layer_trigger_height)
			self.layer_trigger_zmin					= utility.getint(snapshot["layer_trigger_zmin"],self.layer_trigger_zmin)
			self.layer_trigger_on_extruding			= utility.getbool(snapshot["layer_trigger_on_extruding"],self.layer_trigger_on_extruding)
			self.layer_trigger_on_extruding_start	= utility.getbool(snapshot["layer_trigger_on_extruding_start"],self.layer_trigger_on_extruding_start)
			self.layer_trigger_on_primed			= utility.getbool(snapshot["layer_trigger_on_primed"],self.layer_trigger_on_primed)
			self.layer_trigger_on_retracting		= utility.getbool(snapshot["layer_trigger_on_retracting"],self.layer_trigger_on_retracting)
			self.layer_trigger_on_retracted			= utility.getbool(snapshot["layer_trigger_on_retracted"],self.layer_trigger_on_retracted)
			self.layer_trigger_on_detracting		= utility.getbool(snapshot["layer_trigger_on_detracting"],self.layer_trigger_on_detracting)
			self.archive							= utility.getbool(snapshot["archive"],self.archive)
			self.delay								= utility.getint(snapshot["delay"],self.delay)
			self.retract_before_move				= utility.getbool(snapshot["retract_before_move"],self.retract_before_move)
			self.output_format						= utility.getstring(snapshot["output_format"],self.output_format )
			self.output_filename					= utility.getstring(snapshot["output_filename"],self.output_filename )
			self.output_directory					= utility.getstring(snapshot["output_directory"],self.output_directory )
			self.cleanup_before_print				= utility.getbool(snapshot["cleanup_before_print"],self.cleanup_before_print )
			self.cleanup_after_print				= utility.getbool(snapshot["cleanup_after_print"],self.cleanup_after_print )
			self.cleanup_after_cancel				= utility.getbool(snapshot["cleanup_after_cancel"],self.cleanup_after_cancel )
			self.cleanup_before_close				= utility.getbool(snapshot["cleanup_before_close"],self.cleanup_before_close )
			self.cleanup_after_render				= utility.getbool(snapshot["cleanup_after_render"],self.cleanup_after_render )
			self.cleanup_before_print				= utility.getbool(snapshot["cleanup_before_print"],self.cleanup_before_print)
			self.cleanup_after_print				= utility.getbool(snapshot["cleanup_after_print"],self.cleanup_after_print)
			self.cleanup_after_cancel				= utility.getbool(snapshot["cleanup_after_cancel"],self.cleanup_after_cancel)
			self.cleanup_before_close				= utility.getbool(snapshot["cleanup_before_close"],self.cleanup_before_close)
			self.cleanup_after_render				= utility.getbool(snapshot["cleanup_after_render"],self.cleanup_after_render)
			self.custom_script_enabled				= utility.getbool(snapshot["custom_script_enabled"],self.custom_script_enabled)
			self.script_path						= utility.getstring(snapshot["script_path"],self.script_path)
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
		self.output_directory = "./timelapse/{FILENAME}_{PRINTENDTIME}/"
		self.sync_with_timelapse =  False
		if(rendering is not None):
			self.enabled = utility.getbool(rendering["enabled"],self.enabled)
			self.fps_calculation_type = rendering["fps_calculation_type"]
			self.run_length_seconds = utility.getfloat(rendering["run_length_seconds"],self.run_length_seconds)
			self.fps = utility.getfloat(rendering["fps"],self.fps)
			self.max_fps = utility.getfloat(rendering["max_fps"],self.max_fps)
			self.min_fps = utility.getfloat(rendering["min_fps"],self.min_fps)
			self.output_format = utility.getstring(rendering["output_format"],self.output_format)
			self.sync_with_timelapse =  utility.getbool(rendering["sync_with_timelapse"],self.sync_with_timelapse )



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
			self.address = utility.getstring(camera["address"],self.address)
			self.ignore_ssl_error = utility.getbool(camera["ignore_ssl_error"],self.ignore_ssl_error)
			self.username = utility.getstring(camera["username"],self.username)
			self.password = utility.getstring(camera["password"],self.password)
			self.brightness = utility.getint(camera["brightness"],self.brightness)
			self.contrast = utility.getint(camera["contrast"],self.contrast)
			self.saturation = utility.getint(camera["saturation"],self.saturation)
			self.white_balance_auto = utility.getbool(camera["white_balance_auto"],self.white_balance_auto)
			self.gain = utility.getint(camera["gain"],self.gain)
			self.powerline_frequency = utility.getint(camera["powerline_frequency"],self.powerline_frequency)
			self.white_balance_temperature = utility.getint(camera["white_balance_temperature"],self.white_balance_temperature)
			self.sharpness = utility.getint(camera["sharpness"],self.sharpness)
			self.backlight_compensation_enabled = utility.getbool(camera["backlight_compensation_enabled"],self.backlight_compensation_enabled)
			self.exposure_type = utility.getbool(camera["exposure_type"],self.exposure_type)
			self.exposure = utility.getint(camera["exposure"],self.exposure)
			self.exposure_auto_priority_enabled = utility.getbool(camera["exposure_auto_priority_enabled"],self.exposure_auto_priority_enabled)
			self.pan = utility.getint(camera["pan"],self.pan)
			self.tilt = utility.getint(camera["tilt"],self.tilt)
			self.autofocus_enabled = utility.getbool(camera["autofocus_enabled"],self.autofocus_enabled)
			self.focus = utility.getint(camera["focus"],self.focus)
			self.zoom = utility.getint(camera["zoom"],self.zoom)
			self.led1_mode = utility.getstring(camera["led1_mode"],self.led1_frequency)
			self.led1_frequency = utility.getint(camera["led1_frequency"],self.led1_frequency)
			self.jpeg_quality = utility.getint(camera["jpeg_quality"],self.jpeg_quality)

class Profile(object):
	
	
	def __init__(self,profile):
		self.name = "Default"
		self.description = "Fixed XY at back left - relative stabilization (0,100)"
		self.stabilization = Stabilization(None)
		self.snapshot = Snapshot(None)
		self.rendering = Rendering(None)
		self.camera = Camera(None)
		if(profile is not None ):
			self.name = utility.getstring(profile["name"],self.name)
			self.description = utility.getstring(profile["description"],self.description)
			self.stabilization = Stabilization(profile["stabilization"])
			self.snapshot = Snapshot(profile["snapshot"])
			self.rendering = Rendering(profile["rendering"])
			self.camera = Camera(profile["camera"])

class OctolapseSettings(object):
	
	# constants
	def __init__(self, settings = None):
		self.current_profile_name = "Default"
		self.is_octolapse_enabled = True
		self.printer = Printer(None)
		self.profiles = { "Default" : Profile(None) }
		if(settings is not None):
			self.current_profile_name = utility.getstring(settings.get(["current_profile_name"]),self.current_profile_name)
			self.is_octolapse_enabled = utility.getbool(settings.get(["is_octolapse_enabled"]),self.is_octolapse_enabled)
			self.printer = Printer(settings.get(["printer"]))
			for profile in settings.get(["profiles"]):
				self.profiles[profile["name"]] = Profile(profile)
				
    # Profiles
	def CurrentProfile(self):
		if(len(self.profiles.keys())==0):
			profile = Profile()
			self.Proflies[profile.name] = profile
			self.current_profile_name = profile.name
			
			return profile
		if(self.current_profile_name not in self.profiles.keys()):
			self.current_profile_name = self.profiles.itervalues().next().name
		return self.profiles[self.current_profile_name]

	def Profile(self,profileName):
		return self.profiles[profileName]
	

