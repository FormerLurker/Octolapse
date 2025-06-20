This is a **beta** feature, use at your own risk.

Normally, Octolapse sends an M400 command before taking a snapshot in order to stabilize the snapshot.  This flushes the gcode buffer, and introduces a slight pause in the print.  However, this is absolutely necessary to get a perfectly smooth timelapse.  Disabling this option prevents a pause caused by the M400 command, but will result in a jerky timelapse, similar to the stock timelapse plugin.  Additionally, Octolapse will not retract, lift, or travel when this option is disabled.

Normally, when taking a snapshot Octolapse will execute before and after snapshot scripts synchronously, meaning it will wait for the script to exit before it continues.  When wait for moves is disabled, Octolapse will NOT wait for these scripts to complete before continuing.  This can cause some problems for your before/after snapshot scripts depending on what they do, so use caution here.

Wait for moves to finish can be enabled/disabled within the stabilization profile.

*Note*: Disabling **Wait For Moves To Finish** is not the same as disabling stabilization on each axis.
