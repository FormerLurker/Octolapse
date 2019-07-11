When you reboot your OctoPrint server, typically the webcam settings return to the defaults.  When this option is enabled, OctoLapse will attempt to apply your saved webcam image preferences to your camera when OctoPrint starts.  This will keep your image settings constant across reboots.

As of Octolapse V0.3.4, Custom Image Preferences are only supported if you are using a webcam stream with mjpg_streamer.  Octolapse will NOT let you enable these features unless it detects that the camera is running from mjpg_streamer and that control.htm is accessible (read the notes below to see how to do this).

### Required octopi.txt changes to use custom image preferences

_**these changes are required in order to use the custom image preferences**_

If you are using octopi, to use the custom image preferences you'll need to make a small adjustment to your boot/octopi.txt file.  [See this troubleshooting guide](https://github.com/FormerLurker/Octolapse/wiki/Troubleshooting#why-cant-i-change-contrast-zoom-focus-etc) to enable custom printer settings by allowing access to webcam/control.htm.
