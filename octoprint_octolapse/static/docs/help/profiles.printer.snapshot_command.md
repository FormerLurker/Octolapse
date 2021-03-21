When using either the **Gcode Trigger** or the **Smart Gcode Trigger**, Octolapse will take a snapshot when it encounters a snapshot command within your gcode file.  Since Octolapse v0.4, the default snapshot command is ```@OCTOLAPSE TAKE-SNAPSHOT```, and this command can always be used to trigger a snapshot.  However, Octolapse allows you to use any custom command that you choose to initiate a snapshot, with some minor limitations.  The command must include at least one non-whitespace character, and may include a comment if you desire.

**Warning:** Do **NOT** use a command that is required by your printer as the alternative snapshot command, because it WILL NOT be sent to the printer.  For example, do NOT EVER use ```G28```, ```G90```, or any similar commands.  This **WILL** cause major problems.

**Why would I not just use default snapshot command ```@OCTOLAPSE TAKE-SNAPSHOT``` to initiate a snapshot?**

Great question!  Though the default command will always work when printing from OctoPrint, and will NEVER be sent to your printer by OctoPrint, some printers with misbehaving firmware will not handle unknown gcodes when printing direct from the printer (via internal SD reader).  For this reason some people choose to use other gocdes to trigger a snapshot, like ```G4 P1```.  That command would  normally would tell the printer to wait for 0 Milliseconds, so it effectively does nothing, and will not alter the print in any way, even if you're printing straight off of your printer's SD card.

However, in my experience it is pretty unusual that a printer would malfunction when encountering the default snapshot command (```@OCTOLAPSE TAKE-SNAPSHOT```).  If you have a printer that misbehaves, consider using ```G4 P1``` as your alternative snapshot command.  Better yet, just upgrade your firmware with one that is a bit more tolerant.

**A note about comments and case:**

Snapshot commands are NOT case sensitive in Octolapse V0.4+.  Please note that all comments are stripped from the alternative snapshot command while Octolapse is running.  For example, if you use

```SNAP ; THIS IS A SNAPSHOT```

as your snapshot command, Octolapse will strip the comment and will trigger on any occurrence of

```SNAP```

Since comments are ignored in OctoPrint, Octolapse would also trigger if the following line appears within your gcode file:

```SNAP ; NOTICE HOW THIS IS A DIFFERENT COMMENT!```

In other words, comments are ignored both within the alternative snapshot command, and within the gcode file.

**Will the snapshot command be sent to the printer?**

Octolapse will automatically prevent both the default snapshot command and the alternative snapshot command from being sent to the printer while it is running.  By default, it will remove the snapshot gcode EVEN WHILE OCTOLAPSE IS DISABLED to prevent snapshot commands from mistakenly being sent to the printer.  See the main settings for this optional setting that can be used to prevent all snapshot commands from being sent to the printer as long as Octolapse is installed.
