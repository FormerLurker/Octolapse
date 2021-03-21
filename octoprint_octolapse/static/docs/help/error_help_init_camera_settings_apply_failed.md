Octolapse was unable to apply your custom camera preferences.  Custom image preferences allow you to control things like contrast, focus, zoom, exposure, and other controls depending on the type of camera you are using.  The exact solution depends on the type of camera you are using.

**Important Note**: Custom image preferences are only supported when streaming with **mjpgstreamer** using a **UVC driver**.  If you are using some other streaming server, or a different driver, custom image preferences will not work yet.

#### I'm Using a Raspberry Pi Camera

If you've received this error, it's likely that Octolapse can connect to your camera, but some additional steps might be required in order to apply custom image preferences.  [See this detailed guide](https://github.com/FormerLurker/Octolapse/wiki/V0.4---Configuring-a-Raspberry-Pi-Camera) for step by step instructions for enabling custom camera preferences

#### I'm using a USB camera

If you've received this error, it's likely that Octolapse can connect to your camera, but some additional steps might be required in order to apply custom image preferences.  [This guide](https://github.com/FormerLurker/Octolapse/wiki/V0.4---Enabling-Camera-Controls) explains how to enable access to mjpgstreamer's control.htm page, which is used to control the camera settings.

#### I'm Stuck, and Just Want to Print

If all else fails, open your Camera profile.  Find the **Custom Image Preferences** section and uncheck **Apply Preferences Before Print Start**.  That will prevent Octolapse from applying any custom preferences before you print starts, which will bypass this error.
