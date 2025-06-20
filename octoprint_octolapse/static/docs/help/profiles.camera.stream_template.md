This setting is used to create a live camera stream for adjusting webcam settings.  The format is generally a bit different than the snapshot address since the url is used by your browser to connect to the camera stream.

The default value is ```/webcam/?action=stream```, which is a relative address.  This is translated into a full url by your browser.  For example, octoprint is running on http://192.168.1.100, this relative URL will be translated to ```http://192.168.1.100/webcam/?action=stream```.  You could also use the full URL, but it will stop working if your IP address changes.  

The default address should work fine as long as you are using the default OctoPi installation (using mjpg_streamer), and your camera is connected directly to the raspberry pi that is running Octoprint.

If you are using an external webcam server, use whatever URL you use to view the camera stream within the browser and paste it here.  If it works in your browser it will likely work in Octolapse (but not necessarily).

