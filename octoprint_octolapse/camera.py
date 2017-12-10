# coding=utf-8
import requests
import threading
import logging

from requests.auth import HTTPBasicAuth

import sys

def FormatRequestTemplate(cameraAddress, template,value):
		return template.format(camera_address=cameraAddress,value=value )


class CameraControl(object):
	def __init__(self,octolapseSettings):
		self.Settings = octolapseSettings
		self.Camera = self.Settings.CurrentCamera()
		self.TimeoutSeconds = 5
	def ApplySettings(self):
		CameraSettingJob(self.Settings, self.Camera.brightness_request_template , self.Camera.brightness,'brightness').ProcessAsync()
		
		CameraSettingJob(self.Settings, self.Camera.contrast_request_template , self.Camera.contrast,'contrast').ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.saturation_request_template , self.Camera.saturation,'saturation' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.white_balance_auto_request_template , self.Camera.white_balance_auto, 'auto white balance' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.gain_request_template , self.Camera.gain,'gain' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.powerline_frequency_request_template , self.Camera.powerline_frequency,'powerline frequency' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.white_balance_temperature_request_template , self.Camera.white_balance_temperature,'white balance temperature' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.sharpness_request_template  , self.Camera.sharpness,'sharpness' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.backlight_compensation_enabled_request_template , self.Camera.backlight_compensation_enabled,'set backlight compensation enabled' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.exposure_type_request_template , self.Camera.exposure_type,'exposure type' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.exposure_request_template , self.Camera.exposure, 'exposure' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.exposure_auto_priority_enabled_request_template , self.Camera.exposure_auto_priority_enabled,'set auto priority enabled' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.pan_request_template , self.Camera.pan,'pan' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.tilt_request_template , self.Camera.tilt,'tilt' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.autofocus_enabled_request_template , self.Camera.autofocus_enabled,'set autofocus enabled' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.focus_request_template , self.Camera.focus,'focus' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.zoom_request_template , self.Camera.zoom,'zoom' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.led1_mode_request_template , self.Camera.led1_mode,'led 1 mode' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.led1_frequency_request_template , self.Camera.led1_frequency,'led 1 frequency' ).ProcessAsync()
		CameraSettingJob(self.Settings, self.Camera.jpeg_quality_request_template ,self.Camera.jpeg_quality,'jpeg quality').ProcessAsync()
		

class CameraSettingJob(object):
	camera_job_lock = threading.RLock()

	def __init__(self, Settings, template, value, settingName, timeout = 5):
		camera = Settings.CurrentCamera()
		self.Settings = Settings
		self.Address = camera.address
		self.Username = camera.username
		self.Password = camera.password
		self.IgnoreSslError = camera.ignore_ssl_error
		self.TimeoutSeconds = timeout
		
		self.Template = template
		self.Value = value
		self.SettingName = settingName
	def ProcessAsync(self):
		self._thread = threading.Thread(target=self._process,
		                                name="CameraSettingChangeJob_{name}".format(name = self.SettingName))
		self._thread.daemon = True
		self._thread.start()
	def _process(self):
		with self.camera_job_lock:
			url = FormatRequestTemplate(self.Address, self.Template,self.Value)	
			try:
				if(len(self.Username)>0):
					self.Settings.CurrentDebugProfile().LogCameraSettingsApply("Camera Settings Apply - {0} - Authenticating and applying settings at {1:s}.".format(self.SettingName,url))
					r=requests.get(url, auth=HTTPBasicAuth(self.Username, self.Password),verify = not self.IgnoreSslError,timeout=float(self.TimeoutSeconds))
				else:
					self.Settings.CurrentDebugProfile().LogCameraSettingsApply("Camera Settings Apply - {0} - Applying settings at {1:s}.".format(self.SettingName,url))
					r=requests.get(url,verify = not self.IgnoreSslError,timeout=float(self.TimeoutSeconds))

				if r.status_code != requests.codes.ok:
					self.Settings.CurrentDebugProfile().LogCameraSettingsApply("Camera - Updated Settings - {0}:{1}, status code received was not OK.  StatusCode:{1}, URL:{2}".format(self.SettingName, self.Value))
				else:
					self.Settings.CurrentDebugProfile().LogCameraSettingsApply("Camera - Unable to adjust settings for {0}, status code received was not OK.  StatusCode:{1}, URL:{2}".format(self.SettingName, r.status_code, url))
			except:
				type = sys.exc_info()[0]
				self.Value = sys.exc_info()[1]
				self.Settings.CurrentDebugProfile().LogError("Camera Settings Apply- An exception of type:{0} was raised while adjusting camera {1} at the following URL:{2}, Error:{3}".format(type, self.SettingName, url, self.Value))
				return
