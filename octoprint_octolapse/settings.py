# coding=utf-8

PROFILE_SNAPSHOT_GCODE_TYPE = "gcode"

def GetOctoprintDefaultSettings():
	settings = OctolapseSettings(None)
	return GetOctoprintSettings(settings)

def GetOctoprintSettings(settings):
		octoprintSettings = { "is_enabled" : settings.is_enabled,
			'current_profile_name' : settings.current_profile_name,
			'printer' : {
				'retract_length' :  settings.printer.retract_length,
				'retract_speed' : settings.printer.retract_speed,
				'movement_speed' : settings.printer.movement_speed,
				'snapshot_command' :  settings.printer.snapshot_command,
				'snapshot_gcode' : settings.printer.snapshot_gcode,
			},
			'profiles' : []
		}
		for key, profile in settings.profiles.items():
			stabilization = profile.stabilization
			snapshot = profile.snapshot
			rendering = profile.rendering
			file_options = profile.file_options
			camera = profile.camera
			newProfile = {
				'name' : profile.name,
				'description' : profile.description,
				'stabilization' : {
					'x_movement_speed' : stabilization.x_movement_speed,
					'x_type' : stabilization.x_type,
					'x_fixed_coordinate' : stabilization.x_fixed_coordinate,
					'x_fixed_path' : stabilization.x_fixed_path,
					'x_fixed_path_loop' : stabilization.x_fixed_path_loop,
					'x_relative' : stabilization.x_relative,
					'x_relative_print' : stabilization.x_relative_print,
					'x_relative_path' : stabilization.x_relative_path,
					'x_relative_path_loop' : stabilization.x_relative_path_loop,
					'y_movement_speed_mms' : stabilization.y_movement_speed_mms,
					'y_type' : stabilization.y_type,
					'y_fixed_coordinate' : stabilization.y_fixed_coordinate,
					'y_fixed_path' : stabilization.y_fixed_path,
					'y_fixed_path_loop' : stabilization.y_fixed_path_loop,
					'y_relative' : stabilization.y_relative,
					'y_relative_print' : stabilization.y_relative_print,
					'y_relative_path' : stabilization.y_relative_path,
					'y_relative_path_loop' : stabilization.y_relative_path_loop,
					'z_movement_speed_mms' : stabilization.z_movement_speed_mms
				},
				'snapshot' : {
					'trigger_type' : snapshot.trigger_type,
					'length' : snapshot.length,
					'seconds' : snapshot.seconds,
					'archive' : snapshot.archive,
					'delay' : snapshot.delay,
					'retract_before_move' : snapshot.retract_before_move
				},
				'rendering' : {
					'enabled' : rendering.enabled,
					'fps_calculation_type' : rendering.fps_calculation_type,
					'run_length_seconds' : rendering.run_length_seconds,
					'fps' : rendering.fps,
					'max_fps' : rendering.max_fps,
					'min_fps' : rendering.min_fps,
					'output_format' : rendering.output_format
				},
				'file_options' : {
					'output_filename' : file_options.output_filename,
					'sync_with_timelapse' :  file_options.sync_with_timelapse,
					'cleanup_before_print' : file_options.cleanup_before_print,
					'cleanup_after_print' : file_options.cleanup_after_print,
					'cleanup_after_cancel' : file_options.cleanup_after_cancel,
					'cleanup_before_close' :  file_options.cleanup_before_close,
					'cleanup_after_render' : file_options.cleanup_after_render
				},
				'camera' : {
					'brightness' : camera.brightness,
					'contrast' : camera.contrast,
					'saturation' : camera.saturation,
					'white_balance_auto' : camera.white_balance_auto,
					'gain' : camera.gain,
					'powerline_frequency' : camera.powerline_frequency,
					'white_balance_temperature' : camera.white_balance_temperature,
					'sharpness' : camera.sharpness,
					'backlight_compensation_enabled' :  camera.backlight_compensation_enabled,
					'exposure_type' : camera.exposure_type,
					'exposure' : camera.exposure,
					'exposure_auto_priority_enabled' : camera.exposure_auto_priority_enabled,
					'pan' : camera.pan,
					'tilt' : camera.tilt,
					'autofocus_enabled' : camera.autofocus_enabled,
					'focus' : camera.focus,
					'zoom' : camera.zoom,
					'led1_mode' :  camera.led1_mode,
					'led1_frequency' : camera.led1_frequency,
					'jpeg_quality' : camera.jpeg_quality
				}
			}
			octoprintSettings["profiles"].append(newProfile)
		octoprintSettings["printer"]["snapshot_gcode"] = []
		for str in settings.printer.snapshot_gcode:
			octoprintSettings["printer"]["snapshot_gcode"].append(str)

		return octoprintSettings


class Printer(object):
	def __init__(self,printer):
		self.retract_length = 2.0
		self.retract_speed = 3600
		self.movement_speed = 3600
		self.snapshot_command = 'snap'
		self.snapshot_gcode=[ "G90; abs coord","G0 X{0:f} Y{1:f} F{2:d}; Move fast","M400; Wait for command to finish","G4 P{3:d} ; Wait a bit longer to allow the camera to stabilize" ]
		if(printer is not None):
			self.printer.snapshot_gcode = printer["snapshot_gcode"]
			self.printer.retract_length = getfloat(printer["retract_length"],self.retract_length)
			self.printer.retract_speed = getint(printer["retract_speed"],self.retract_speed)
			self.printer.movement_speed = getint(printer["movement_speed"],self.movement_speed)
			self.printer.snapshot_command = printer["snapshot_command"]
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
			self.x_movement_speed = getint(stabilization["x_movement_speed"],self.x_movement_speed)
			self.x_type = stabilization["x_type"]
			self.x_fixed_coordinate = getfloat(stabilization["x_fixed_coordinate"],self.x_fixed_coordinate)
			self.x_fixed_path = stabilization["x_fixed_path"]
			self.x_fixed_path_loop = getbool(stabilization["x_fixed_path_loop"],self.x_fixed_path_loop)
			self.x_relative = getfloat(stabilization["x_relative"],self.x_relative)
			self.x_relative_print = getfloat(stabilization["x_relative_print"],self.x_relative_print)
			self.x_relative_path = stabilization["x_relative_path"]
			self.x_relative_path_loop = getbool(stabilization["x_relative_path_loop"],self.x_relative_path_loop)
			self.y_movement_speed_mms = getint(stabilization["y_movement_speed_mms"],self.y_movement_speed_mms)
			self.y_type = stabilization["y_type"]
			self.y_fixed_coordinate = getfloat(stabilization["y_fixed_coordinate"],self.y_fixed_coordinate)
			self.y_fixed_path = stabilization["y_fixed_path"]
			self.y_fixed_path_loop = getbool(stabilization["y_fixed_path_loop"],self.y_fixed_path_loop)
			self.y_relative = getfloat(stabilization["y_relative"],self.y_relative)
			self.y_relative_print = getfloat(stabilization["y_relative_print"],self.y_relative_print)
			self.y_relative_path = stabilization["y_relative_path"]
			self.y_relative_path_loop = getbool(stabilization["y_relative_path_loop"],self.y_relative_path_loop)
			self.z_movement_speed_mms = getint(stabilization["z_movement_speed_mms"],self.z_movement_speed_mms)
class Snapshot(object):

	def __init__(self,snapshot):
		self.trigger_type = 'gcode'
		self.length = 0.2
		self.seconds = 30
		self.archive = True
		self.delay = 1000
		self.retract_before_move = False
		if(snapshot is not None):
			self.trigger_type = snapshot["trigger_type"]
			self.length = getfloat(snapshot["length"],self.length)
			self.seconds = getint(snapshot["seconds"],self.seconds)
			self.archive = getbool(snapshot["archive"],self.archive)
			self.delay = getint(snapshot["delay"],self.delay)
			self.retract_before_move = getbool(snapshot["retract_before_move"],self.retract_before_move)
class Rendering(object):	
	def __init__(self,rendering):
		self.enabled = True
		self.fps_calculation_type = 'duration'
		self.run_length_seconds = 10
		self.fps = 30
		self.max_fps = 120.0
		self.min_fps = 1.0
		self.output_format = 'mp4'
		if(rendering is not None):
			self.enabled = getbool(rendering["enabled"],self.enabled)
			self.fps_calculation_type = rendering["fps_calculation_type"]
			self.run_length_seconds = getfloat(rendering["run_length_seconds"],self.run_length_seconds)
			self.fps = getfloat(rendering["fps"],self.fps)
			self.max_fps = getfloat(rendering["max_fps"],self.max_fps)
			self.min_fps = getfloat(rendering["min_fps"],self.min_fps)
			self.output_format = rendering["output_format"]

class FileOptions(object):
	def __init__(self,file_options):
		self.output_filename = "{FILENAME}_{DATETIMESTAMP}.{OUTPUTFILEEXTENSION}"
		self.sync_with_timelapse = True
		self.cleanup_before_print = True
		self.cleanup_after_print = False
		self.cleanup_after_cancel = True
		self.cleanup_before_close = True
		self.cleanup_after_render = False
		if(file_options is not None):
			self.sync_with_timelapse = getbool(file_options["sync_with_timelapse"],self.sync_with_timelapse)
			self.cleanup_before_print = getbool(file_options["cleanup_before_print"],self.cleanup_before_print)
			self.cleanup_after_print = getbool(file_options["cleanup_after_print"],self.cleanup_after_print)
			self.cleanup_after_cancel = getbool(file_options["cleanup_after_cancel"],self.cleanup_after_cancel)
			self.cleanup_before_close = getbool(file_options["cleanup_before_close"],self.cleanup_before_close)
			self.cleanup_after_render = getbool(file_options["cleanup_after_render"],self.cleanup_after_render)


class Camera(object):

	def __init__(self,camera):
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
			self.brightness = getint(camera["brightness"],self.brightness)
			self.contrast = getint(camera["contrast"],self.contrast)
			self.saturation = getint(camera["saturation"],self.saturation)
			self.white_balance_auto = getbool(camera["white_balance_auto"],self.white_balance_auto)
			self.gain = getint(camera["gain"],self.gain)
			self.powerline_frequency = getint(camera["powerline_frequency"],self.powerline_frequency)
			self.white_balance_temperature = getint(camera["white_balance_temperature"],self.white_balance_temperature)
			self.sharpness = getint(camera["sharpness"],self.sharpness)
			self.backlight_compensation_enabled = getbool(camera["backlight_compensation_enabled"],self.backlight_compensation_enabled)
			self.exposure_type = getbool(camera["exposure_type"],self.exposure_type)
			self.exposure = getint(camera["exposure"],self.exposure)
			self.exposure_auto_priority_enabled = getbool(camera["exposure_auto_priority_enabled"],self.exposure_auto_priority_enabled)
			self.pan = getint(camera["pan"],self.pan)
			self.tilt = getint(camera["tilt"],self.tilt)
			self.autofocus_enabled = getbool(camera["autofocus_enabled"],self.autofocus_enabled)
			self.focus = getint(camera["focus"],self.focus)
			self.zoom = getint(camera["zoom"],self.zoom)
			self.led1_mode = camera["led1_mode"]
			self.led1_frequency = getint(camera["led1_frequency"],self.led1_frequency)
			self.jpeg_quality = getint(camera["jpeg_quality"],self.jpeg_quality)

class Profile(object):
	def __init__(self,profile):
		self.name = "Default"
		self.description = "Fixed XY at back left - relative stabilization (0,100)"
		self.stabilization = Stabilization(None)
		self.snapshot = Snapshot(None)
		self.rendering = Rendering(None)
		self.file_options = FileOptions(None)
		self.camera = Camera(None)
		if(profile is not None):
			self.name = profile["name"]
			self.description = profile["description"]
			self.stabilization = Stabilization(profile["stabilization"])
			self.snapshot = Snapshot(profile["snapshot"])
			self.rendering = Rendering(profile["rendering"])
			self.file_options = FileOptions(profile["file_options"])
			self.camera = Camera(profile["camera"])

class OctolapseSettings(object):
	current_profile_name = "Default"
	is_enabled = False
	printer = Printer(None)

	# constants
	def __init__(self, settings = None):
		self.profiles = { "Default" : Profile(None) }
		if(settings is not None):
			current_profile_name = settings.get(["current_profile_name"])
			is_enabled = settings.get(["is_enabled"])
			printer = settings.get(["printer"])
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
	
def getfloat(value,default):
	try:
		return float(value)
	except ValueError:
		return float(default)

def getint(value,default):
	try:
		return int(value)
	except ValueError:
		return default

def getbool(value,default):
	try:
		return bool(value)
	except ValueError:
		return default
