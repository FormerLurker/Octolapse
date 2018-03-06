# Octolapse

* This plugin is in Beta, which means it is still a work-in-progress.  Please carefully read all of the instructions below before use.  Install and use at your own risk!  

## Description
Octolapse is a plugin for Octoprint, a well-known 3D print server.  It is designed to make stabilized timelapses of your prints, and it's extremely configurable.  Every effort has been made to maintain print quality when using Octolapse.

Octolapse monitors the GCode sent to your printer from Octoprint while printing locally, and takes snapshots either at height increments/layer changes, after a period of time has elapsed, when certain GCodes are detected, or a combination of the three.  Octolapse monitors the position of each axis and attempts to determine the extruder state in order to detect the optimal time to take a snapshot.  There are lots of settings to customize exactly when a snapshot should be taken and when they are not allowed.

Once it's time to take a snapshot, Octolapse pauses the print and executes a series of GCode commands to move the bed and extruder to the proper position.  It will optionally ensure that the extruder is retracted in order to reduce stringing and oozing, and will lift if possible.  The snapshot position can be customized for each in a variety of ways, and can even be animated.

Once printing is finished, a timelapse is rendered according to your specifications.  Timelapses can be either fixed framerate, or fixed length.  Pre and post-roll frames can be added so that your timelapses don't start and end abruptly.  Renderings can be rotated, reversed, and more.  Multiple video formats are currently supported.  Your timelapse can optionally moved to the default timelapse plugin, making it easy and convenient to view, sort, and download your timelapses.  Currently Octolapse has no native file browser/viewer, so this is HIGHLY recommended.

Octolapse also allows you to define camera settings that can be applied at the start of a print.  This allows you to ensure consistent images by controlling things like focus, zoom, pan, and exposure, making your snapshots as crisp and clear as possible.  You can also use multiple cameras, though currently Octolapse only allows one camera to be used at a time.

## Installation
Currently Octolapse is not listed in the [plugin repository](https://plugins.octoprint.org/), but it can be installed either manually or via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager).

### Steps prior to installation
1.  Make sure your webcam is correctly configured within Octoprint.  Octolapse will try to discover your webcam settings when it is first installed, which will make setup easier.
2.  Make sure FFMpeg is installed.  [It can be found here.](https://ffmpeg.org/)  If you can currently generate timelapses with Octoprint, it is likely already installed.
3.  Make sure your FFMpeg path is correct in the Octoprint 'Timelapse Recordings' settings.  Again, if the built-in timelapse plugin is working, FFMpeg is likely correctly configured.
4.  It's a good idea to look at the [known issues](https://github.com/FormerLurker/Octolapse/issues) before installing Octolapse, especially the [Prusa MK2/MK2S/MK3 firmware issue](https://github.com/FormerLurker/Octolapse/issues/11) since it affects the only printers I've tested.  It just might save you some trouble even if you aren't using Octolapse!

### Steps to install via the plugin manager
1.  Open and sign into Octoprint.
2.  Click the settings icon (wrench) at the top of the page.
3.  Select the 'Plugin Manager' link on the left side of the settings popup.
4.  Click on the 'Get More...' button towards the bottom of the Plugin Manager page.
5.  Paste the following link into the '... from URL' box and click 'Install':  https://github.com/FormerLurker/Octolapse/archive/master.zip
6.  After installation is complete, follow the prompts to restart Octoprint.

If you reinstall or upgrade Octolapse, make sure to refresh your browser (usually CTRL+F5) after Octoprint reboots to ensure that your cache is reset.

### Steps after installation
1.  Make sure to select or add the appropriate printer profile.  As of the time of this writing, only the Prusa Mk2S (with and without the multi material upgrade) has been tested.  Check your slicer settings and your printer's documentation for the appropriate values for your printer.  Note that non-cartesian printers are NOT yet supported, and printers with center origins or inverted axes have NOT been tested.
2.  Make sure your webcam is working by editing the default camera profile and clicking the 'Test Camera Snapshot' button.
3.  Unload any filament from your printer, and run a short print in 'Test Mode' to make sure things are working.  See 'Test Mode' below.

## Usage
Once Octolapse is enabled and configured, you're all set!  [Printing from the printer's internal SD card is not supported](https://github.com/FormerLurker/Octolapse/issues/18), so be sure you're printing a local file.  You can filter from the file browser in Octoprint by clicking the wrench icon and selecting 'Only show files stored locally'.

After print starts Octolapse will do its magic.  You'll notice that Octoprint will show that the printer pauses occasionally. This is normal and occurs when Octolapse takes a snapshot.

Once the print is completed or cancelled, Octolapse will inform you that your timelapse is rendering via the web client.  If synchronization is enabled, your video will be available within the default timelapse plugin, otherwise your timelapse will be in the Octolapse data foler.

### Test Mode
Test mode can be used to try out timelapse settings without printing anything.  Test mode must be activated BEFORE starting a print.  Changing this setting mid-print won't alter any current prints.

1.  Navigate to the Debug tab and select 'Test Mode'.  Note:  You shouldn't have to use any of the profiles marked 'Diagnostic' unless you suspect a bug.
2.  UNLOAD YOUR FILAMENT!  Even though I attempted to strip all extruder commands, there's a chance that I missed some cases.  Please let me know if you see any 'cold extrusion prevented' errors in the terminal window.  If you do, please send me your GCode!
3.  Select a local GCode file and click print.

Notes:  Pay attention to your printer temps during the test print.  Everything should remain cool!  If not, please let me know, send me the GCode, and I'll try to remedy the situation.  [See the known issues for details](https://github.com/FormerLurker/Octolapse/issues/12).


## Settings
To edit Octolapse settings, sign into Octoprint and click on the settings (wrench) icon at the top of the page.  Click on 'Octolapse Plugin' under 'Plugins' on the left-hand side.  You should now see the Octolapse setup screen.  You can disable or enable Octolapse by checking 'Enable Octolapse'.  You can also restore all of the default settings here by clicking the 'restore all default settings'.

You can add/edit/delete/copy profiles on any of the tabs.  You can set the current profile by clicking the star icon.  The current profile will be in bold with a star icon in front of it.

Octolapse comes with several useful presets that should accommodate typical use.

Important Notes:  Most settings changes will only affect the next print.  Active prints are only affected by the logging settings inside the debug profile and by the 'Apply Settings' button in the Camera Profile Add/Edit screen.  All other changes will take place during your next print, though while we're still in Alpha mode I don't suggest you do any massive settings changes during a print!

### Printer
Here you can configure retraction length, speed, axis speeds, home position, print volume, the printer snapshot command, as well as other printer/slicer related settings.  It is very important that the printer profile is correctly configured.

Notes:  Note that all axis speeds are in millimeters per minute, instead of the mm/s that most slicers use.  To convert from mm/s to mm/min, simply multiply mm/s by 60.

### Stabilization
Here you can control the position of the bed and extruder before each snapshot.  Positions can be fixed or relative.  Fixed coordinates are just like any absolute printer coordinates.  If your print bed is 200mmx200mm, coordinate 100,100 would represent the center of the bed.  When using relative coordinates, the center of the bed is at 50,50, and 0,0 is at the origin (home position).  100,100 would be the corner opposite the origin.

You can also provide a stabilization path.  In this case, each point in the path is used for each subsequent snapshot.  The points can be either fixed or bed-relative coordinates.  Once each coordinate is used once, the final coordinate will be used for each subsequent snapshot.  Selecting the ‘Loop’ option will cause the path to start over from the beginning after the end has been reached.  You can also invert the loop so that once it reaches the end, the path will continue in reverse.  Take a look at the ‘animated’ stabilizations for examples.

### Rendering
These profiles determine how your series of snapshots will be turned into a timelapse.  You can set the timelapse to have a fixed length (say 5 seconds) or use a constant FPS.  You can add pre or post-roll frames so that your timelapses don't start or stop abruptly.  The default output is MP4, which is required in order to (optionally) synchronize with the default timelapse plugin.  When synchronizing with the default plugin, your timelapses will appear in the native timelapse plugin tab after rendering is complete.  

### Camera
Here you can configure and fine-tune your camera.  Octolapse allows you to control the camera settings (if supported by your camera and streamer) before each print, giving you complete control of how your snapshots look.

### Debug

####Test Mode
If you would like to test a timelapse without actually printing anything, use the 'Test Mode' settings.  Test mode will only work if you select the option before starting a print.  This prevents the extruder from moving and suppresses any temperature setting commands so that you can quickly and easily make sure your stabilizations are working according to plan.

Even though I attempted to strip all extruder and temperature commands, there's a chance that I missed some cases. Please let me know if you see any 'cold extrusion prevented' errors in the terminal window or if either your bed, extruder, or enclosure heats up during a test print. If you do, please let me know and send me your GCode!

For safety's sake, even when using test mode DO NOT LEAVE YOUR PRINTER UNATTENDED!  This program is in alpha and hasn't been tested with all printers/slicers/custom GCode, so bad things could happen.

####Logging Settings
If you are having any issues you can check Octolapse's log.  You can find the log in the main settings page on the left-hand side under (Logs).  The log file is called plugin_octolapse.log.  The log file is useful to help me track down issues, so make sure you download a copy after any problems.

By default, Octolapse will log any errors that occur.  If you need more information to track down an issue you can turn on information logging within the Octolapse settings in the Debug tab.

You can change the logging settings or default debug profile at any time, and the logging settings will take effect immediately.  The only setting in debug that will NOT take effect until the next print is 'Test Mode'.

Please note that some of the options within the debug profile can cause the log file to grow quickly which might affect performance.  Only use information logging when necessary.

## History of Octolapse
I got the idea for Octolapse when I attempted to manually make a [stabilized timelapse](https://youtu.be/xZlP4vpAKNc) by hand editing my GCode files.  To accomplish this I used the excellent and simple [GCode System Commands](https://github.com/kantlivelong/OctoPrint-GCodesystemCommands) plugin.  The timelapse worked great, but it required a lot of effort which I didn't want to put in every time.  I received several requests for instructions on how to create a stabilized timelapse, so I decided to give plugin development a go.  I've never done one before (or programmed python or knockout or anything open source), but figured I could contribute something good to the community.  This is my "thank you" to all of the makers out there who have contributed your time and effort!

