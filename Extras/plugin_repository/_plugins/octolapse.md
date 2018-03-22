---
layout: plugin

id: octolapse
title: Octolapse
description: Create a stabilized timelapse of your 3D prints.  Highly customizable, loads of presets, lots of fun.
author: Brad Hochgesang
license: AGPL-3.0
date: 2018-03-24

homepage: https://formerlurker.github.io/Octolapse/
source: https://github.com/FormerLurker/Octolapse/
archive: https://github.com/FormerLurker/Octolapse/archive/master.zip

tags:
- timelapse
 
featuredimage: /assets/img/plugins/octolapse/tab_mini.png

compatibility:

  octoprint:
  - 1.3.7

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
Octolapse is designed to make stabilized timelapses of your prints with as little hassle as possible, and it's extremely configurable.  Now you can create a silky smooth timelapse without a custom camera mount, no GCode customizations required.

Octolapse moves the print bed and extruder into position before taking each snapshot, giving you a crisp image in every frame.  Snapshots can be taken at each layer change, at specific height increments, after a period of time has elapsed, or when certain GCodes are detected.  You can even combine multiple methods in a single timelapse.

Octolapse is still in Beta but has been confirmed to work on several printers:

*  Genuine Prusa - Mk2, Mk2S, Mk2 w Multi Material, Mk3
*  Anet A8
*  CR-10 (Beta Profile)
*  I've heard reports that the Monoprice Maker Select v2/Wanhao Duplicator i3 also works but have yet to receive a profile for this printer.  [See this issue if you can help!](https://github.com/FormerLurker/Octolapse/issues/27)

Please note that some settings may need to be adjusted depending on your slicer settings.

[View the Octolapse Wiki on Github.](https://github.com/FormerLurker/Octolapse/wiki)

<div style="text-align:center">
    <br/>
    <div>
        <iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/er0VCYen1MY" frameborder="0" allow="encrypted-media" allowfullscreen></iframe>
    </div>
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

## More Octolapses
<div style="text-align:center">
    <div>
        <iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/dYbWfBCLNbI" frameborder="0" allow="encrypted-media" allowfullscreen></iframe>
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
        <iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/4kEHbRrp2Jk" frameborder="0" allow="encrypted-media" allowfullscreen></iframe>
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
        <iframe width="560" height="315" src="https://www.youtube-nocookie.com/embed/Ra5Jjq-nJfA" frameborder="0" allow="encrypted-media" allowfullscreen></iframe>
    </div>
    <div> 
        <a href="https://www.thingiverse.com/thing:763622" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            <i>The obligatory benchy</i>
        </a>
    </div>
    <br/>
</div>


Copyright (C) 2017  Brad Hochgesang - FormerLurker@protonmail.com
