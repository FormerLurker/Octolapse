Enabling custom image preferences will allow you to edit many of your webcam settings (if they are supported) like contrast, zoom, focus, etc.

As of Octolapse V0.3.4, Custom Image Preferences are only supported if you are using a webcam stream with mjpg_streamer.

### Required boot/octopi.txt changes to use custom image preferences

_**these changes are required in order to use the custom image preferences**_

In recent versions of Octopi, the default mjpegstreamer control.htm page is disabled. In order to automatically adjust camera settings, Octolapse needs access to control.htm.

To enable access you must connect to a terminal to access your raspberry pi.  Then enter the following command to edit your octopi.txt file:
```
sudo nano /boot/octopi.txt
```

Find the following section in the file (press the down arrow to scroll down):
```
### Configuration of camera HTTP output
#
# Usually you should NOT need to change this at all! Only touch if you
# know what you are doing and what the parameters mean.
#
# Below settings are used in the mjpg-streamer call like this:
#
#   -o "output_http.so -w $camera_http_webroot $camera_http_options"
#
# Current working directory is the mjpg-streamer base directory.
#
#camera_http_webroot="./www-octopi"
#camera_http_options="-n"
```
Change the following lines:
```
#camera_http_webroot="./www-octopi"

#camera_http_options="-n"
```
to this:
```
camera_http_webroot="./www"

camera_http_options=""
```

### Required etc/modules and boot/octopi.txt changes for Raspberry Pi Camera Module

A detailed guide for configuring the raspberry pi camera can be found [here](https://github.com/FormerLurker/Octolapse/wiki/V0.4---Configuring-a-Raspberry-Pi-Camera).  Brief instructions can be found below.

The first step is to update your raspberry pi.  If you skip this step, the camera driver may not work properly.

Connect to a terminal window on your raspberry pi and enter the following command followed by the Enter key:

```
sudo apt-get update
```

Enter your password if you are prompted.  You also might be asked to confirm the updates at some point. If so, press Y to confirm.  This command may take a while to finish.

Next we will upgrade the distribution. Enter the following command and press the Enter key.

```
sudo apt-get dist-upgrade
```

You might be asked to confirm the updates at some point. If so, press Y to confirm.

Now reboot your pi for the update to take effect by entering the following command, followed by the Enter key:

```
sudo reboot
```

Wait for your pi to reboot (this usually takes a few minutes), then reconnect to a terminal window on your raspberry pi and edit the /etc/modules file with the following command:

```sudo nano /etc/modules```

Enter your password if prompted.  After the nano editor opens, add the following line to the end of the modules file:

```bcm2835-v4l2```

Your modules file should now look something like this:
```
# /etc/modules: kernel modules to load at boot time.
#
# This file contains the names of kernel modules that should be loaded
# at boot time, one per line. Lines beginning with "#" are ignored.
bcm2835-v4l2
```

Press Ctrl+O (the letter O) to save the file and press Ctrl+X to exit.
Now edit your octopi.txt file with the following command:

```sudo nano /boot/octopi.txt```

Find this in the file (it may look slightly different):
```
### Configure which camera to use
#
# Available options are:
# - auto: tries first usb webcam, if that's not available tries raspi cam
# - usb: only tries usb webcam
# - raspi: only tries raspi cam
#
# Defaults to auto
#
camera="auto"
```
And change it to this:
```
### Configure which camera to use
#
# Available options are:
# - auto: tries first usb webcam, if that's not available tries raspi cam
# - usb: only tries usb webcam
# - raspi: only tries raspi cam
#
# Defaults to auto
#
camera="usb"
```
Make sure the line that says ```camera=usb``` is NOT commented out.  It must not start with a #!

Next find the section that looks similar to this
```
### Additional options to supply to MJPG Streamer for the USB camera
#
# See https://github.com/foosel/OctoPrint/wiki/MJPG-Streamer-configuration
# for available options
#
# Defaults to a resolution of 640x480 px and a framerate of 10 fps
#
camera_usb_options=""
```
and change the camera_usb_options to this:

```
### Additional options to supply to MJPG Streamer for the USB camera
#
# See https://github.com/foosel/OctoPrint/wiki/MJPG-Streamer-configuration
# for available options
#
# Defaults to a resolution of 640x480 px and a framerate of 10 fps
#
camera_usb_options="-r 1920x1080 -f 10"
```
note that you can add other options, or select a different resolution, but this should get you started at 1080P 10FPS.

Finally press Ctrl+O (the letter O) to save and Ctrl+X to exit.  Then enter the following command to reboot your pi:

```sudo reboot```

When your pi comes back online, you should see your raspicam working!
