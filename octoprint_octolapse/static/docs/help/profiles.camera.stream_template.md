This setting is used to create a live camera stream for adjusting webcam settings.  The format is generally a bit different than the snapshot address since the url is used by your browser to connect to the camera stream.

The default value is ```/webcam/?action=stream```, and should work fine as long as you are using the default OctoPi installation (using mjpegstreamer), and your camera is connected directly to the raspberry pi that is running Octoprint.  You can also use the full stream address here, but the exact address depends on your raspberry pi's IP address, and/or your DNS settings.  For example, if your IP address is 192.168.0.100, and you are using OctoPi + mjpegstreamer, you could use this value: ```http://192.168.0.100/webcam/?action=stream```

However, it's possible that your IP address will change over time, so it's recommended that you use the default address, which is independant of your IP address.
