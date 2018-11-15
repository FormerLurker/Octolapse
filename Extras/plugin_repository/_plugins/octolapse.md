---
layout: plugin

id: octolapse
title: Octolapse
description: Create a stabilized timelapse of your 3D prints.  Highly customizable, loads of presets, lots of fun.  Requires OctoPrint 1.3.9 or higher.
author: Brad Hochgesang
license: AGPL-3.0
date: 2018-11-15

homepage: https://formerlurker.github.io/Octolapse/
source: https://github.com/FormerLurker/Octolapse/
archive: https://github.com/FormerLurker/Octolapse/archive/v0.3.4.zip

tags:
- timelapse

featuredimage: /assets/img/plugins/octolapse/tab_mini.png

compatibility:

  octoprint:
  - 1.3.9

  os:
  - linux
  - windows
  - macos
  - freebsd
---


# Octolapse

<div style="text-align:center">
    <img src="/assets/img/plugins/octolapse/tab_mini.png" alt="Octolapse Tab"/>
    <div>
        <i>The Octolapse Tab</i>
    </div>
    <br/>
</div>

***Octolapse is provided without warranties of any kind.  By installing Octolapse you agree to accept all liability for any damage caused directly or indirectly by Octolapse.  Use caution and never leave your printer unattended.***

Octolapse is designed to make stabilized timelapses of your prints with as little hassle as possible, and it's extremely configurable.  Now you can create a silky smooth timelapse without a custom camera mount, no GCode customizations required.

Octolapse moves the print bed and extruder into position before taking each snapshot, giving you a crisp image in every frame.  Snapshots can be taken at each layer change, at specific height increments, after a period of time has elapsed, or when certain GCodes are detected.

[Please support my work by becoming a patron.](https://www.patreon.com/bePatron?u=9588101)

**Important**:  *Octolapse requires OctoPrint v1.3.9 or higher and some features require OctoPrint v1.3.10rc1 or above.*  You can check your OctoPrint version by looking in the lower left hand corner of your OctoPrint server home page.

# Recent Changes
If you are upgrading from [v0.3.1](https://github.com/FormerLurker/Octolapse/releases/tag/v0.3.1), please read the [v0.3.4 release notes](https://github.com/FormerLurker/Octolapse/releases/tag/v0.3.4), a lot has changed.  If you've had trouble running Octolapse in the past, you just might want to try it again!

# What Octolapse Does

<div style="text-align:center">
    <br/>
    <div>
        {% include youtube.html vid="er0VCYen1MY" %}
    </div>
    <div>
        <a href="https://www.thingiverse.com/thing:570288" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            <i>A timelapse of a double spiral vase made with Octolapse</i>
        </a>
    </div>
    <br/>
</div>
## Octolapse was designed with print quality in mind
* **Continuous tracking** of the X,Y, and Z axes.  Octolapse knows where your extruder and bed will be at all times.
* **Extruder state detection** enables Octolapse to choose a good time take a snapshot, minimizing defects.
* Choose from dozens of existing **presets,** or use a **custom configuration** to maximize quality for your specific application.
* Customizable **Z-Hop and retract detection** to reduce stringing, maximizing quality.
* **Configurable stabilizations** allow you complete control of the X and Y position of each snapshot.  You can choose a position as close to or as far away from your part as you wish.
* **Minimal impact on print time and print quality.**  Octolapse normally takes between one and three seconds to take a snapshot.  It even reports exactly how much time it's using after each snapshot!
* Use **High Quality Mode** to prevent snapshots over exterior perimeters using the new fully customizable **Feature Detection**.
* Allow or prevent snapshots in certain areas with **snapshot position restrictions.**  This can be used to prevent snapshots over critical areas of your print or a delicate part.
* If you have a multi-material printer, you can even **restrict snapshots movements to your wipe tower**, virtually eliminating any quality considerations!
* Octolapse can **calculate intersections** between the printer path and any snapshot position restriction, allowing a snapshot even in the middle of an extrusion.
* **Stop the timelapse whenever you want!**  If things go awry, you can prevent Octolapse from taking any further snapshots for the rest of the print.  It will wait to render any snapshots that were already taken until after the print has finished.
* Use **test mode** to try out your timelapse settings without heating your bed or nozzle, turning on any fans, or extruding any filament.  This saves time and plastic.  It's also very useful for development and testing.
## Octolapse was also designed to make great timelapses
* **Synchronize your timelapses** with OctoPrint's built in plugin, keeping all of your videos in one place.
* Choose between **fixed frame rate** or **fixed length rendering.**  Octolapse will automatically adjust the frame rate to match any desired length.  You can even set a minimum or maximum acceptable frame rate.
* Add **pre or post roll frames** (not videos yet, sorry) to your snapshot preventing an abrupt start or finish.
* Choose from several output formats including **MP4 (libxvid and H.264), AVI, FLV, VOB, GIF, and MPEG.**  *More coming soon, suggestions welcome.*  _Note: *OctoPrint 1.3.10 is required to synchronize some formats with the built-in timelapse plugin.*_
* **Control the bitrate** of your video.
* Add a **Custom Watermark** to your video.
* Add **Text Overlays** to your video using replacement tokens.  Control the position, color, font and more!
* Control the number of **rendering threads** to reduce rendering time.
## To make good timelapses, you need good snapshots
* Slow camera or low frame rate?  Octolapse allows you to **set a snapshot delay** before taking a snapshot to allow your camera enough time to get a clear image.
* **Control your camera settings** when using [mjegstreamer](https://sourceforge.net/projects/mjpg-streamer/) including: contrast, brightness, focus, white balance, pan, tilt, zoom, and much more.  You can apply your custom settings before each print.
* **Rotate, flip, and transpose your snapshots**
* Use custom camera scripts to **trigger a DSLR**, post-process images, configure your camera, turn lighting on and off, control **GPIO**, or practically anything you can think of!  Five script types are available.
* Use **Multiple cameras** to create multiple timelapses.
* Send gcode to your printer when it's time to take a snapshot via the new **Gcode Camera Type**.  Supports for the **M240** gcode!
## Simplified Setup and Better Compatibility
* Select your **slicer type** to simplify printer setup by making the setting names and units match your slicer!  Cura, Simplify 3d and Slic3r PE are fully supported.
* Enhanced and **simplified error reporting** and informational panels.
* All settings include links to the **Octolapse Wiki**, so you can get to the documentation quickly if you have questions.
* Octolapse now works with **Themeify**.

# Installation

[Read the installation instructions.](https://github.com/FormerLurker/Octolapse/wiki/Installation)

After installation, [checkout the project's wiki pages](https://github.com/FormerLurker/Octolapse/wiki).  It never hurts to know more about what you're doing!

# Usage
[Learn how to start your first print here.](https://github.com/FormerLurker/Octolapse/wiki/Usage)  It's a good idea to read about the settings before using Octolapse.  I also recommend you [watch this brief tutorial](https://youtu.be/sDyg9lMqMG8), which explains how to configure your printer profile for use with the new **High Quality** snapshot profile.

# Known Printer Support

Octolapse is still in Beta but has been confirmed to work on several printers:

*  Genuine Prusa - Mk2, Mk2S, Mk2 w Multi Material, Mk3
*  Anet A8 - Beta - User Submitted
*  Anycube I3 Mega - Beta - User Submitted
*  CR-10 - Beta - User Submitted
*  Dagoma Neva - Beta - User Submitted
*  Irapid Black - Beta - User Submitted
*  Monoprice Maker Select v2/Wanhao Duplicator i3 - Beta - User Submitted - Requires OctoPrint 1.3.7rc3 or above

Please note that some settings may need to be adjusted depending on your slicer settings.

## More Octolapses
<div style="text-align:center">
    <div>
        {% include youtube.html vid="uBeVbDJKHw0" %}
    </div>
    <div>
        <a href="https://www.youtube.com/channel/UCXRcs5H7Om8YbaNbaM5iOdg" alt="Link to WildRose builds channel" target="_blank">
            <i>A user generated compilation created by WildRose Builds.  Support this channel and please subscribe!</i>
        </a>
    </div>
    <br/>
</div>

<div style="text-align:center">
    <div>
        {% include youtube.html vid="dYbWfBCLNbI" %}
    </div>
    <div>
        <a href="https://www.thingiverse.com/thing:919475" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            <i>The Milennium Falcon</i>
        </a>
    </div>
    <br/>
</div>

<div style="text-align:center">
    <div>
        {% include youtube.html vid="4kEHbRrp2Jk" %}
    </div>
    <div>
        <a href="https://www.thingiverse.com/thing:2531838" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            <i>The Moon - Animated X Axis</i>
        </a>
    </div>
    <br/>
</div>
<div style="text-align:center">
    <div>
        {% include youtube.html vid="Ra5Jjq-nJfA" %}
    </div>
    <div>
        <a href="https://www.thingiverse.com/thing:763622" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            <i>The obligatory benchy</i>
        </a>
    </div>
    <br/>
</div>

## History of Octolapse
I got the idea for Octolapse when I attempted to manually make a [stabilized timelapse](https://youtu.be/xZlP4vpAKNc) by hand editing my GCode files.  To accomplish this I used the excellent and simple [GCode System Commands](https://github.com/kantlivelong/OctoPrint-GCodesystemCommands) plugin.  The timelapse worked great, but it required a lot of effort which I didn't want to put in every time.  I received several requests for instructions on how to create a stabilized timelapse, so I decided to give plugin development a go.  I've never done one before (or programmed python or knockout or anything open source), but figured I could contribute something good to the community.  This is my "thank you" to all of the makers out there who have contributed your time and effort!

## Report Problems
If you think you have found a bug in Octolapse, please create an issue on the official github.com page [here](https://github.com/FormerLurker/Octolapse/issues/new).  In order to have your issue handled properly and quickly, please completely

## License
View the [Octolapse license](https://github.com/FormerLurker/Octolapse/blob/master/LICENSE).

<hr/>

_Copyright (C) 2017  Brad Hochgesang - FormerLurker@pm.me_
