Three types of cameras are supported in Octolapse:  Webcams, external (script/DSLR) cameras, and Gcode triggered cameras.  Typically 'Webcam' is selected here.


### Webcams
Webcams must be accessible via http or https and must deliver jpg images (currently).  Octolapse supports mjpg_streamer, yawcam, or any other streaming server or camera that can provide an image via a browser link.

### Script

This camera type can be used to call a script when a snapshot needs to be taken.  The primary use here is for DSLR cameras that support external triggering, though there are lots of interesting things you could probably do here.  People have been able to trigger external cameras via GPIO and possibly other things I haven't heard about.

[See this beta guide](https://github.com/FormerLurker/Octolapse/wiki/Configuring-an-External-Camera) for setting up a DSLR camera on Linux using [gPhoto2](http://gphoto.org/).  I have also gotten this to work on Windows using [digiCamControl](http://digicamcontrol.com/), but have not finished up the guide for that part yet.

### Gcode Camera
If your printer contains an internal camera that can be triggered via gcode, normally via M240, you can use this camera type to take trigger your printer's camera.  I've actually not tested this except through the debugger since I do not have a printer with a built-in camera, so I'm not 100% sure it will work.  For this reason I'd welcome any feedback on this camera type!

Note:  You can use a Gcode camera to send gcode commands to your printer while taking snapshots.  The gcode is sent after snapshots are initiated on any other enabled cameras.
