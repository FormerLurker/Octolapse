**Warning:  This is an experimental feature.  You might experience unexpected errors when enabling this setting.**

When stream download is enabled, octolapse will acquire one packet of data from the webcam and will then continue to process the gcode file while downloading the image in the background.  For large images, this can substantially reduce the time it takes to acquire an image, reducing print time and increasing quality, especially when using the smart trigger with snap-to-print enabled.

However, it is also possible that Octolapse will acquire an old image, resulting in a jittery timelapse, where some snapshots come from a previous frame.  However, if you are primarily concerned with print quality and are less interested in timelapse quality, you may want to consider enabling this feature.

Note that this setting only affects webcam download, and not external or gcode camera types.
