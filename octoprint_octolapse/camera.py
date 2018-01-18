# coding=utf-8
import requests
import threading
import logging
import uuid
from requests.auth import HTTPBasicAuth
import sys

def FormatRequestTemplate(cameraAddress, template,value):
		return template.format(camera_address=cameraAddress,value=value )

def TestCamera(cameraProfile, timeoutSeconds=2):
		url = FormatRequestTemplate(cameraProfile.address, cameraProfile.snapshot_request_template,"")
		try:
			if(len(cameraProfile.username)>0):
				r=requests.get(url, auth=HTTPBasicAuth(cameraProfile.username, cameraProfile.password),verify = not cameraProfile.ignore_ssl_error,timeout=float(timeoutSeconds))
			else:
				r=requests.get(url,verify = not cameraProfile.ignore_ssl_error,timeout=float(timeoutSeconds))

			if (r.status_code == requests.codes.ok):
				if('content-length' in r.headers and r.headers["content-length"]==0):
					failReason = "Camera Test failed - The request contained no data"
				elif("image/jpeg" not in r.headers["content-type"].lower()):
					failReason = "Camera test failed - The returned data was not an image"
				else:
					return True,""
				

			else:
				failReason = "Camera Test Failed - An invalid status code was returned from the camera:{0}".format(r.status_code)
		except:
			type = sys.exc_info()[0]
			value = sys.exc_info()[1]
			failReason = "Camera Test Failed - An exception of type:{0} was raised during the test!  Error:{1}".format(type, value)

		return False, failReason

class CameraControl(object):
	def __init__(self,camera,onSuccess = None, onFail = None, onComplete = None, timeoutSeconds = 2.0):
		self.Camera = camera
		self.TimeoutSeconds = timeoutSeconds
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
		for request in cameraSettingRequests:
			CameraSettingJob(self.Camera, request, self.TimeoutSeconds, onSuccess = self.OnSuccess, onFail = self.OnFail, onComplete = self.OnComplete).ProcessAsync()

class CameraSettingJob(object):
	#camera_job_lock = threading.RLock()

	def __init__(self, camera, cameraSettingRequest, timeout, onSuccess = None, onFail = None, onComplete = None):
		camera = camera
		self.Request = cameraSettingRequest
		self.Address = camera.address
		self.Username = camera.username
		self.Password = camera.password
		self.IgnoreSslError = camera.ignore_ssl_error
		self.TimeoutSeconds = timeout
		self._on_success = onSuccess
		self._on_fail = onFail
		self._on_complete = onComplete
		
	def ProcessAsync(self):
		self._thread = threading.Thread(target=self._process,name="CameraSettingChangeJob_{name}".format(name = str(uuid.uuid4())))
		self._thread.daemon = True
		self._thread.start()
	def _process(self):
		#with self.camera_job_lock:
			
		errorMessages = []
		success = None
			
		template = self.Request['template']
		value = self.Request['value']
		settingName = self.Request['name']
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
			errorMessages.append("Camera Settings Apply- An exception of type:{0} was raised while adjusting camera {1} at the following URL:{2}, Error:{3}".format(type, settingName, url, value))

		if(success != False):
			success = True
			
		if(success):
			self._notify_callback("success", value, settingName, template)
		else:
			self._notify_callback("fail", value, settingName, template, errorMessages)

		self._notify_callback("complete")
	def _notify_callback(self, callback, *args, **kwargs):
		"""Notifies registered callbacks of type `callback`."""
		name = "_on_{}".format(callback)
		method = getattr(self, name, None)
		if method is not None and callable(method):
			method(*args, **kwargs)
