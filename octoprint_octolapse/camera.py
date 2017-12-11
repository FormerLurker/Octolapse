# coding=utf-8
import requests
import threading
import logging
import uuid
from requests.auth import HTTPBasicAuth

import sys

def FormatRequestTemplate(cameraAddress, template,value):
		return template.format(camera_address=cameraAddress,value=value )


class CameraControl(object):
	def __init__(self,octolapseSettings,onSuccess = None, onFail = None, onComplete = None):
		self.Settings = octolapseSettings
		self.Camera = self.Settings.CurrentCamera()
		self.TimeoutSeconds = 5
		self.OnSuccess = onSuccess
		self.OnFail = onFail
		self.OnComplete = onComplete
	def ApplySettings(self):
		cameraSettingRequests = []
		cameraSettingRequests.append({'template':self.Camera.brightness_request_template , 'value':self.Camera.brightness, 'name':'brightness'})
	
		cameraSettingRequests.append({'template':self.Camera.contrast_request_template, 'value':self.Camera.contrast, 'name':'contrast'})
		cameraSettingRequests.append({'template':self.Camera.saturation_request_template, 'value':self.Camera.saturation, 'name':'saturation' })
		cameraSettingRequests.append({'template':self.Camera.white_balance_auto_request_template, 'value':self.Camera.white_balance_auto, 'name':'auto white balance' })
		cameraSettingRequests.append({'template':self.Camera.gain_request_template, 'value':self.Camera.gain, 'name':'gain' })
		cameraSettingRequests.append({'template':self.Camera.powerline_frequency_request_template, 'value':self.Camera.powerline_frequency, 'name':'powerline frequency' })
		cameraSettingRequests.append({'template':self.Camera.white_balance_temperature_request_template, 'value':self.Camera.white_balance_temperature, 'name':'white balance temperature' })
		cameraSettingRequests.append({'template':self.Camera.sharpness_request_template, 'value':self.Camera.sharpness, 'name':'sharpness' })
		cameraSettingRequests.append({'template':self.Camera.backlight_compensation_enabled_request_template, 'value':self.Camera.backlight_compensation_enabled, 'name':'set backlight compensation enabled' })
		cameraSettingRequests.append({'template':self.Camera.exposure_type_request_template, 'value':self.Camera.exposure_type, 'name':'exposure type' })
		cameraSettingRequests.append({'template':self.Camera.exposure_request_template, 'value':self.Camera.exposure, 'name':'exposure' })
		cameraSettingRequests.append({'template':self.Camera.exposure_auto_priority_enabled_request_template, 'value':self.Camera.exposure_auto_priority_enabled, 'name':'set auto priority enabled' })
		cameraSettingRequests.append({'template':self.Camera.pan_request_template, 'value':self.Camera.pan, 'name':'pan' })
		cameraSettingRequests.append({'template':self.Camera.tilt_request_template, 'value':self.Camera.tilt, 'name':'tilt' })
		cameraSettingRequests.append({'template':self.Camera.autofocus_enabled_request_template, 'value':self.Camera.autofocus_enabled, 'name':'set autofocus enabled' })
		cameraSettingRequests.append({'template':self.Camera.focus_request_template, 'value':self.Camera.focus, 'name':'focus' })
		cameraSettingRequests.append({'template':self.Camera.zoom_request_template, 'value':self.Camera.zoom, 'name':'zoom' })
		cameraSettingRequests.append({'template':self.Camera.led1_mode_request_template, 'value':self.Camera.led1_mode, 'name':'led 1 mode' })
		cameraSettingRequests.append({'template':self.Camera.led1_frequency_request_template, 'value':self.Camera.led1_frequency, 'name':'led 1 frequency' })
		cameraSettingRequests.append({'template':self.Camera.jpeg_quality_request_template, 'value':self.Camera.jpeg_quality, 'name':'jpeg quality'})
		#TODO:  Move the static timeout value to settings
		CameraSettingJob(self.Settings, cameraSettingRequests, 5, onSuccess = self.OnSuccess, onFail = self.OnFail, onComplete = self.OnComplete).ProcessAsync()

class CameraSettingJob(object):
	camera_job_lock = threading.RLock()

	def __init__(self, Settings, cameraSettingRequests, timeout = 5, onSuccess = None, onFail = None, onComplete = None):

		
		camera = Settings.CurrentCamera()
		self.Settings = Settings
		self.CameraSettingRequests = cameraSettingRequests
		self.Address = camera.address
		self.Username = camera.username
		self.Password = camera.password
		self.IgnoreSslError = camera.ignore_ssl_error
		self.TimeoutSeconds = timeout
		self._on_success = onSuccess
		self._on_fail = onFail
		self._on_complete = onComplete
		
	def ProcessAsync(self):
		self._thread = threading.Thread(target=self._process,
		                                name="CameraSettingChangeJob_{name}".format(name = str(uuid.uuid4())))
		self._thread.daemon = True
		self._thread.start()
	def _process(self):
		with self.camera_job_lock:
			
			errorMessages = []
			success = None
			for request in self.CameraSettingRequests:
				template = request['template']
				value = request['value']
				settingName = request['name']
				url = FormatRequestTemplate(self.Address, template,value)
				try:
					if(len(self.Username)>0):
						r=requests.get(url, auth=HTTPBasicAuth(self.Username, self.Password),verify = not self.IgnoreSslError,timeout=float(self.TimeoutSeconds))
					else:
						r=requests.get(url,verify = not self.IgnoreSslError,timeout=float(self.TimeoutSeconds))

					if r.status_code != requests.codes.ok:
						success = False
						errorMessages.append("Camera - Updated Settings - {0}:{1}, status code received was not OK.  StatusCode:{1}, URL:{2}".format(settingName, value))
				except:
					type = sys.exc_info()[0]
					value = sys.exc_info()[1]
					success = False
					errorMessages.append("Camera Settings Apply- An exception of type:{0} was raised while adjusting camera {1} at the following URL:{2}, Error:{3}, Stack Trace:{4}".format(type, settingName, url, value,traceback.print_stack()))

			if(success != False):
				success = True
			
			if(success):
				self._notify_callback("success", len(self.CameraSettingRequests))
			else:
				self._notify_callback("fail", len(self.CameraSettingRequests), errorMessages)

			self._notify_callback("complete")
	def _notify_callback(self, callback, *args, **kwargs):
		"""Notifies registered callbacks of type `callback`."""
		name = "_on_{}".format(callback)
		method = getattr(self, name, None)
		if method is not None and callable(method):
			method(*args, **kwargs)
