Octolapse expected more snapshots than were returned by the smart trigger.

### Why did Octolapse miss snapshots, and how do I fix it?

There are a few things that can cause this:

1.  You are using the **High Quality** smart layer trigger, but retraction is disabled in your slicer.  Either switch to the **Compatibility** smart layer trigger, or reslice your gcode with retraction enabled.
2.  You are using the **High Quality** smart layer trigger while printing in **Vase Mode**.  In this case I recommend you switch to the **Snap To Print** smart layer trigger.  However, it is possible to use the **Compatibility** smart layer trigger, though this could significantly affect print quality.  In general, I do not recommend using Octolapse when printing in **Vase Mode**.
3.  Your **End GCode** gcode lifts the extruder at the end of the print, then purges filament.  Octolapse will see this as a layer change, and will detect a missed snapshot between the end of your print and where the purge took place.  To solve this problem simply add the following to the very beginning of your **End GCode** in your **slicer** (NOT in Octoprint):
```
@OCTOLAPSE STOP-SNAPSHOTS
```

This will prevent Octolapse from taking any snapshots after your end gcode starts.

