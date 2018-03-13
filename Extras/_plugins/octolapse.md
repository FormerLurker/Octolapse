---
layout: plugin

id: octolapse
title: Octolapse
description: Create a stabilized timelapse of your 3d prints.  Highly customizable, loads of presets, lots of fun.
author: Brad Hochgesang
license: AGPL-3.0
date: 2018-03-10

homepage: https://formerlurker.github.io/Octolapse/
source: https://github.com/FormerLurker/Octolapse/
archive: https://github.com/FormerLurker/Octolapse/archive/NoPause.zip

tags:
- timelapse
 
featuredimage: /assets/img/plugins/octolapse/tab.png

compatibility:

  octoprint:
  - 1.3.6

  os:
  - linux
  - windows
  - macos
  - freebsd
---

# Octolapse
Octolapse is designed to make stabilized timelapses of your prints with as little hassle as possible, and it's extremely configurable.  Now you can create a silky smooth timelapse without a custom camera mount.  No gcode customization required.

Octolapse moves the print bed and extruder into position before taking each snapshot, giving you a crisp image in every frame.  Snapshots can be taken at each layer change, at specific height increments, after a period of time has elapsed, or when certain GCodes are detected.  You can even combine multiple methods in a single timelapse.

Octolapse is still in Beta, but has been confirmed to work on several printers:

*  Genuine Prusa - Mk2, Mk2S, Mk2 w Multi Material, Mk3
*  Anet A8
*  CR-10 (Beta Profile)

Please note that some settings may need to be adjusted depending on your slicer settings.   

**Octolapse is provided without warranties of any kind.  By installing Octolapse you agree to accept all liability for any damage caused directly or indirectly by Octolapse.**  

Use caution and never leave your printer unattended.

## Octolapse was designed with print quality in mind
* Continuous tracking of the X,Y and Z axes.  Octolapse knows where your extruder and bed are at all times.
* Extruder state detection enables Octolapse choose a good time to time to take a snapshot, minimizing defects.  Use existing presets, or use a custom configuration to maximize quality for your specific application.
* Optional Z-Hop and retract detection to reduce stringing, maximizing quality.
* Configurable stabilizations allow you complete control of the X and Y position of each snapshot.  You can choose a position as close to or as far away from your part as you wish.
* Minimal impact on print time and print quality.  Octolapse only takes a second or two to take a snapshot.  It even reports exactly how much time it's using after each snapshot!
* Allow or prevent snapshots in certain areas.  This can be used to prevent snapshots over a critical area of your print or a delicate part.  If you have a multi-material printer, you can even restrict snapshots to your wipe tower, virtually eliminating any quality considerations!
* Stop the timelapse whenever you want!  If things go awry, you can prevent Octolapse from taking any further snapshots for the rest of the print.  It will even render any snapshots after the print has finished!
* Use test mode to try out your timelapse settings without heating your bed or nozzle, turning on any fans, or extruding any filament. 
## Octolapse was also designed to make great timelapses
* Choose a traditional fixed frame rate timelapse, or try out our fixed length timelapses!  Octolapse will adjust the framerate to match any desired length.  You can even set a minimum or maximum acceptable frame rate for fixed-length renderings.
* Add pre or post roll frames (not videos yet, sorry) to your snapshot preventing an abrupt start or finish.
* Choose from several output formats including MP4, AVI, FLV, VOB and MPEG.  More coming soon.
* Control the bitrate of your video.
* Synchronize your timelapses with OctoPrint's built in plugin, keeping all of your videos in one place!
## To make good timelapses you need good snapshots
* Slow camera or low framerate?  Octolapse allows you to set a delay beofre taking a snapshot to allow your camera enough time to get a clear image.
* If you have a compatible camera you can control contrast, brightness, focus, white balance, pan, tilt, zoom, and much more.  You can apply your custom settings before each print.
# Tab
You can navigate to the Octolapse tab by either clicking on the drop down menu in OctoPrint, or by clicking the 'Octolapse' link in the nav bar.
<details>
	<summary>click to see the tab</summary>
	<img src="/assets/img/plugins/octolapse/tab.jpg" alt="Octolapse Tab"/>
</details>
# Settings
Octolapse has lots of settings, but there are lots of presets to help you get started quickly.  Most settings are organized into profiles, which can be created, updated, removed or copied.  You can see which profiles are active within the main tab so you always know which profiles you are using. 
## Main Settings
The main settings tab allows you to do the following:

* Enable/disable Octolapse
* Enable/disable the nav bar control
* Adjust the timelapse preview display on the tab
* Show or hide various information panels that can be useful for debugging or testing
<details>
	<summary>click to see the main settings</summary>
	<img src="/assets/img/plugins/octolapse/settings_main.jpg" alt="Main Settings"/>
</details>
## Stabilization Profiles
The stabilizations tell Octolapse where to move the bed and extruder for a snapshot.  You can pick fixed or bed-relative coordinates.  You can also provide a list of coordinates to animate each axis, or disable stabilization entirely for an axis.
<details>
<summary>click to see the stabilization settings</summary>
<img src="/assets/img/plugins/octolapse/settings_stabilizations.jpg" alt="Main Settings"/>
</details>
## Snapshot Profiles
<details>
	<summary>click to see the snapshot settings</summary>
	<img src="/assets/img/plugins/octolapse/settings_snapshots.jpg" alt="Snapshot Settings"/>
</details>
## Rendering Profiles
<details>
	<summary>click to see the rendering settings</summary>
	<img src="/assets/img/plugins/octolapse/settings_rendering.jpg" alt="Rendering Settings"/>
</details>
## Camera Profiles
<details>
	<summary>click to see the camera settings</summary>
	<img src="/assets/img/plugins/octolapse/settings_camera.jpg" alt="Camera Settings"/>
</details>
## Debug Profiles
<details>
	<summary>click to see the debug settings</summary>
	<img src="/assets/img/plugins/octolapse/settings_debug.jpg" alt="Debug Settings"/>
</details>

