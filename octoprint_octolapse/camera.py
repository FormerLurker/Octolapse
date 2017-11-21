# coding=utf-8
import requests
import threading
from requests.auth import HTTPBasicAuth
from .settings import Camera
import sys

def FormatRequestTemplate(cameraAddress, template,value):
		return template.format(camera_address=cameraAddress,value=value )


class CameraControl(object):
	def __init__(self,cameraSettings,debug):
		self.CameraSettings = cameraSettings
		self.Debug = debug
		self.TimeoutSeconds = 5
	def ApplySettings(self):

		if(not self.RequestCameraSettingChange( self.CameraSettings.brightness_request_template , self.CameraSettings.brightness,'brightness' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera brightness!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.contrast_request_template , self.CameraSettings.contrast,'contrast')):
			self.Debug.LogCameraSettingsApply("Unable to change the camera contrast!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.saturation_request_template , self.CameraSettings.saturation,'saturation' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera saturation!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.white_balance_auto_request_template , self.CameraSettings.white_balance_auto, 'auto white balance' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera white balance auto setting!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.gain_request_template , self.CameraSettings.gain,'gain' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera gain!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.powerline_frequency_request_template , self.CameraSettings.powerline_frequency,'powerline frequency' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera powerline frequency!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.white_balance_temperature_request_template , self.CameraSettings.white_balance_temperature,'white balance temperature' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera white balance temperature!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.sharpness_request_template  , self.CameraSettings.sharpness,'sharpness' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera sharpness!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.backlight_compensation_enabled_request_template , self.CameraSettings.backlight_compensation_enabled,'set backlight compensation enabled' )):
			self.Debug.LogCameraSettingsApply("Unable to enable the camera's backlight compensation!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.exposure_type_request_template , self.CameraSettings.exposure_type,'exposure type' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera exposure type!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.exposure_request_template , self.CameraSettings.exposure, 'exposure' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera exposure!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.exposure_auto_priority_enabled_request_template , self.CameraSettings.exposure_auto_priority_enabled,'set auto priority enabled' )):
			self.Debug.LogCameraSettingsApply("Unable to enable the camera's auto priority mode!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.pan_request_template , self.CameraSettings.pan,'pan' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera pan!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.tilt_request_template , self.CameraSettings.tilt,'tilt' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera tilt!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.autofocus_enabled_request_template , self.CameraSettings.autofocus_enabled,'set autofocus enabled' )):
			self.Debug.LogCameraSettingsApply("Unable to enable the camera's autofocus mode!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.focus_request_template , self.CameraSettings.focus,'focus' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera focus!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.zoom_request_template , self.CameraSettings.zoom,'zoom' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera zoon!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.led1_mode_request_template , self.CameraSettings.led1_mode,'led 1 mode' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera's led 1 mode!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.led1_frequency_request_template , self.CameraSettings.led1_frequency,'led 1 frequency' )):
			self.Debug.LogCameraSettingsApply("Unable to change the camera's led1 frequency!")
		if(not self.RequestCameraSettingChange( self.CameraSettings.jpeg_quality_request_template ,self.CameraSettings.jpeg_quality,'jpeg quality')):
			self.Debug.LogCameraSettingsApply("Unable to change the jpeg quality!")


	
	def RequestCameraSettingChange(self, template,value,settingName):
			url = FormatRequestTemplate(self.CameraSettings.address, template,value)
			try:
				if(len(self.CameraSettings.username)>0):
					self.Debug.LogCameraSettingsApply("Camera Settings Apply - {0} - Authenticating and applying settings at {1:s}.".format(settingName,url))
					r=requests.get(url, auth=HTTPBasicAuth(self.CameraSettings.username, self.CameraSettings.password),verify = not self.CameraSettings.ignore_ssl_error,timeout=float(self.TimeoutSeconds))
				else:
					self.Debug.LogCameraSettingsApply("Camera Settings Apply - {0} - Applying settings at {1:s}.".format(settingName,url))
					r=requests.get(url,verify = not self.CameraSettings.ignore_ssl_error,timeout=float(self.TimeoutSeconds))
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				self.Debug.LogError("Camera Settings Apply- An exception of type:{0} was raised while adjusting camera settings at the following URL:{1}, Error:{2}".format(type, url, value))
				return
			if r.status_code == requests.codes.ok:
				return True
			else:
				return False
