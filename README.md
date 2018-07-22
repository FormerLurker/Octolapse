# Octolapse
<div align="center">
    <img src="https://raw.githubusercontent.com/FormerLurker/Octolapse/master/Extras/Wiki/assets/img/tab_mini.png" alt="Octolapse Tab"/>
    <div>
        <i>Create a stabilized timelapse of your 3D prints.  Highly customizable, loads of presets, lots of fun.</i>
    </div>
    <br/>
</div>

Octolapse is designed to make stabilized timelapses of your prints with as little hassle as possible, and it's extremely configurable.  Now you can create a silky smooth timelapse without a custom camera mount, no GCode customizations required.

Octolapse moves the print bed and extruder into position before taking each snapshot, giving you a crisp image in every frame.  Snapshots can be taken at each layer change, at specific height increments, after a period of time has elapsed, or when certain GCodes are detected.  You can even combine multiple methods in a single timelapse.

[Please support my work by becoming a patron.](https://www.patreon.com/bePatron?u=9588101)

**Important**:  *Octolapse requires OctoPrint v1.3.7 or higher.*  You can check your OctoPrint version by looking in the lower left hand corner of your OctoPrint server home page.

Octolapse is still in Beta but has been confirmed to work on several printers:

*  Genuine Prusa - Mk2, Mk2S, Mk2 w Multi Material, Mk3
*  Anet A8 - Beta - User Submitted
*  Anycube I3 Mega - Beta - User Submitted
*  CR-10 - Beta - User Submitted
*  Dagoma Neva - Beta - User Submitted
*  Irapid Black - Beta - User Submitted
*  Monoprice Maker Select v2/Wanhao Duplicator i3 - Beta - User Submitted - Requires OctoPrint 1.3.7rc3 or above

Please note that some settings may need to be adjusted depending on your slicer settings.

# Installation

[Read the installation instructions.](https://github.com/FormerLurker/Octolapse/wiki/Installation)

After installation, [checkout the project's wiki pages](https://github.com/FormerLurker/Octolapse/wiki).  It never hurts to know more about what you're doing!

# What Octolapse Does

<div align="center">
    <a href="https://youtu.be/er0VCYen1MY" title="Watch on youtube">
        <img src="https://img.youtube.com/vi/er0VCYen1MY/0.jpg" alt="A timelapse of a double spiral vase made with Octolapse"/>
    </a>
    <div>
        <a href="https://www.thingiverse.com/thing:570288" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
  <i>A timelapse of a double spiral vase made with Octolapse</i>
</a>
    </div>
    <br/>
</div>

**Octolapse is provided without warranties of any kind.  By installing Octolapse you agree to accept all liability for any damage caused directly or indirectly by Octolapse.**

Use caution and never leave your printer unattended.

## Octolapse was designed with print quality in mind
* **Continuous tracking** of the X,Y, and Z axes.  Octolapse knows where your extruder and bed will be at all times.
* **Extruder state detection** enables Octolapse to choose a good time take a snapshot, minimizing defects.
* Choose from dozens of existing **presets,** or use a **custom configuration** to maximize quality for your specific application.
* Customizable **Z-Hop and retract detection** to reduce stringing, maximizing quality.
* **Configurable stabilizations** allow you complete control of the X and Y position of each snapshot.  You can choose a position as close to or as far away from your part as you wish.
* **Minimal impact on print time and print quality.**  Octolapse normally takes between one and three seconds to take a snapshot.  It even reports exactly how much time it's using after each snapshot!
* Allow or prevent snapshots in certain areas with **snapshot position restrictions.**  This can be used to prevent snapshots over critical areas of your print or a delicate part.
* If you have a multi-material printer, you can even **restrict snapshots movements to your wipe tower**, virtually eliminating any quality considerations!
* Octolapse can **calculate intersections** between the printer path and any snapshot position restriction, allowing a snapshot even in the middle of an extrusion.
* **Stop the timelapse whenever you want!**  If things go awry, you can prevent Octolapse from taking any further snapshots for the rest of the print.  It will wait to render any snapshots that were already taken until after the print has finished.
* Use **test mode** to try out your timelapse settings without heating your bed or nozzle, turning on any fans, or extruding any filament.  This saves time and plastic.  It's also very useful for development and testing.
## Octolapse was also designed to make great timelapses
* **Synchronize your timelapses** with OctoPrint's built in plugin, keeping all of your videos in one place.
* Choose between **fixed frame rate** or **fixed length rendering.**  Octolapse will automatically adjust the frame rate to match any desired length.  You can even set a minimum or maximum acceptable frame rate.
* Add **pre or post roll frames** (not videos yet, sorry) to your snapshot preventing an abrupt start or finish.
* Choose from several output formats including **MP4, AVI, FLV, VOB, and MPEG.**  *More coming soon, suggestions welcome.*
* **Control the bitrate** of your video.
* **Flip and rotate** your videos.
## To make good timelapses, you need good snapshots
* Slow camera or low frame rate?  Octolapse allows you to **set a snapshot delay** before taking a snapshot to allow your camera enough time to get a clear image.
* **Control your camera settings** including: contrast, brightness, focus, white balance, pan, tilt, zoom, and much more.  You can apply your custom settings before each print.
* **Rotate, flip, and transpose your snapshots**

# Usage
[Learn how to start your first print here.](https://github.com/FormerLurker/Octolapse/wiki/Usage)  It's a good idea to read about the settings before using Octolapse.


## More Octolapses
<div align="center">
    <a href="https://youtu.be/uBeVbDJKHw0" title="Watch on youtube">
        <img src="https://img.youtube.com/vi/uBeVbDJKHw0/0.jpg" alt="User Created Compilation"/>
    </a>
    <div>
        <a href="https://www.youtube.com/channel/UCXRcs5H7Om8YbaNbaM5iOdg" alt="Link to WildRose builds channel" target="_blank">
            <i>A user generated compilation created by WildRose Builds</i>
        </a>
    </div>
    <br/>
</div>

<div align="center">
    <a href="https://youtu.be/dYbWfBCLNbI" title="Watch on youtube">
        <img src="https://img.youtube.com/vi/dYbWfBCLNbI/0.jpg" alt="The Milennium Falcon"/>
    </a>
    <div>
        <a href="https://www.thingiverse.com/thing:919475" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            <i>The Milennium Falcon</i>
        </a>
    </div>
    <br/>
</div>

<div align="center">
    <a href="https://youtu.be/4kEHbRrp2Jk" title="Watch on youtube">
        <img src="https://img.youtube.com/vi/4kEHbRrp2Jk/0.jpg" alt="The Moon - Animated X Axis"/>
    </a>
    <div>
        <a href="https://www.thingiverse.com/thing:2531838" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            <i>The Moon - Animated X Axis</i>
        </a>
    </div>
    <br/>
</div>

<div align="center">
    <a href="https://youtu.be/Ra5Jjq-nJfA" title="Watch on youtube">
        <img src="https://img.youtube.com/vi/Ra5Jjq-nJfA/0.jpg" alt="The obligatory benchy"/>
    </a>
    <div>
        <a href="https://www.thingiverse.com/thing:763622" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            <i>The obligatory benchy</i>
        </a>
    </div>
    <br/>
</div>

## History of Octolapse
I got the idea for Octolapse when I attempted to manually make a [stabilized timelapse](https://youtu.be/xZlP4vpAKNc) by hand editing my GCode files.  To accomplish this I used the excellent and simple [GCode System Commands](https://github.com/kantlivelong/OctoPrint-GCodesystemCommands) plugin.  The timelapse worked great, but it required a lot of effort which I didn't want to put in every time.  I received several requests for instructions on how to create a stabilized timelapse, so I decided to give plugin development a go.  I've never done one before (or programmed python or knockout or anything open source), but figured I could contribute something good to the community.  This is my "thank you" to all of the makers out there who have contributed your time and effort!


Copyright (C) 2017  Brad Hochgesang - FormerLurker@pm.me
