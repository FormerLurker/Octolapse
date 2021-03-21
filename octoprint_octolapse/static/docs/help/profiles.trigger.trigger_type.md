There are two options for trigger type availiable currently:
### Real-Time
This is the 'Classic' octolapse trigger type.  When selected, Octolapse will read your gcodes before they are sent to your 3D printer and decide when to take a snapshot in real-time (hence the name).  These triggers are battle hardened, and have been widely used and tested.  However, because Octolapse has no knowledge of what gcodes have not yet been sent to the printer, there are some limitations, both in quality and print speed.  However, the Gcode and Timer triggers ONLY work when using real-time processing.
### Smart Layer Trigger
 This is a brand new trigger type that allows Octolapse to read your entire Gcode file BEFORE printing, which allows us to pick better stabilization points.  This trigger type can improve print quality and reduce the time that Octolapse adds to your print.  It can also provide you with an (optional) preview of every snapshot that will be taken BEFORE your printer starts printing.  This allows you to cancel if you don't like the results, and to play with various stabilization/trigger/printer settings before running your print.  It will even show you an estimate of how much travel distance you saved vrs using the regular layer trigger!

 However, pre-processing large gcode files takes some time, and you'll have to wait for it to complete before printing.  I've created the vast majority of the smart layer trigger with some great effort in C++ so that it runs as fast as possible.  Generally the time saved by using the smart trigger will be much higher than the amount of time you'll have to wait for the process to complete.  However, how much time you save is highly dependant on the shape and placement of your print, the current stabilization location, and the trigger options.  If you REALLY want to save time check out the snap-to-print smart layer trigger option!

The smart layer trigger is new, and is not as well tested as the real-time triggers, but it solves lots of issues, and offers tons of benefits.  I recommend you try it out, but please report any issues you find [here](https://github.com/FormerLurker/Octolapse/issues) so that I can fix them!

### Smart Gcode Trigger
This trigger functions in the same way as the Real-Time (classic) gcode trigger except that your gcode will be preprocessed.  Just like the **Smart Layer Trigger** you will be able to preview all of the snapshots Octolapse will take before your print starts.  Also, Just like the **Smart Layer Trigger**, this option uses fewer resources while printing, but pre-processing can take a while to complete.

When using this trigger, you can initiate a snapshot by including the following command in your gcode file:

```@OCTOLAPSE TAKE-SNAPSHOT```

You can also use any custom command you desire by setting the **Alternative Snapshot Command** within your Octolapse printer profile.
