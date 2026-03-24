Octolapse expected more snapshots than were returned by the smart trigger.

### Why did Octolapse miss snapshots, and how do I fix it?

There are a few things that can cause this:

1.  You are using the **High Quality** smart layer trigger, but retraction is disabled in your slicer.  Either switch to the **Compatibility** smart layer trigger, or reslice your gcode with retraction enabled.
2.  You are using the **High Quality** smart layer trigger while printing in **Vase Mode**.  In this case I recommend you switch to the **Snap To Print** smart layer trigger.  However, it is possible to use the **Compatibility** smart layer trigger, though this could significantly affect print quality.  In general, I do not recommend using Octolapse when printing in **Vase Mode**.

