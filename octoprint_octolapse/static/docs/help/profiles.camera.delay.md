This value is in milliseconds, where 1000 milliseconds = 1 second.  The delay will be applied after Octolapse moves the bed and extruder into position, but before a snapshot is taken.  This can be used to give the camera enough time to adjust, keeping your images clear.  If you set this value too high, you're prints will take longer and you may have stringing/quality issues.  The default value is 125, but I've gotten good results with significantly lower values.

For best results, I recommend starting out with a delay of 0 and working up to a max of ```1000 / FrameRate```.

When using the _Snap to Print_ smart layer trigger you want this as low as possible!  I recommend 0 delay when using _Snap to Print_ and only increasing it if absolutely necessary.

When using an external DSLR, set this value to 0.  Delay is almost never necessary when using a DSLR, so only increase it as a last resort.

If you require a large delay (more than 150MS) In general if your delay needs to be very high in order to get a clear image, there may be a few other things going on:

1.  Autofocus is enabled - It takes some time to autofocus.  You will be able to lower your delay by manually focusing your camera.
2.  Other automatic settings - some of these may also impact the delay, but this is unknown.
3.  Low light conditions - some cameras require more light than others, and some cameras automatically adjust the exposure. 
 Increasing the lighting and reducing the exposure time can lower the required delay and improve the output video quality significantly.
4.  SECURE YOUR CAMERA!  A loose or wobbly camera will affect your timelapse.  There is no way to get a smooth timelapse if the camera is bouncing around or sliding.
5.  Consider mounting your camera to your printer.  If your camera is mounted securely, it will wobble along with your printer, reducing shaky frames.
