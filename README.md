# Octolapse

<div style="text-align:center">
    <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Octolapse-Tab" title="Get more information about this feature from the Octolapse Wiki">
        <img src="https://raw.githubusercontent.com/wiki/FormerLurker/Octolapse/version/0.4/assets/images/tab/octolapse_tab_mini.png" alt="The Octolapse Tab" />
    </a><br/>
    <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Octolapse-Tab">
        The New and Improved Octolapse Tab
    </a>

</div>

***Octolapse is provided without warranties of any kind.  By installing Octolapse you agree to accept all liability for any damage caused directly or indirectly by Octolapse.  Use caution and never leave your printer unattended.***

## What Octolapse Does

Octolapse is designed to make stabilized timelapses of your prints with as little hassle as possible, and it's extremely configurable.  Now you can create a silky smooth timelapse without a custom camera mount, no GCode customizations required.

<figure style="text-align:center">
    <a href="https://www.youtube.com/watch?v=er0VCYen1MY" target="_blank">
        <img src="https://img.youtube.com/vi/er0VCYen1MY/maxresdefault.jpg" alt="Double Spiral Vase Timelapse Taken with Octolapse" title="Watch on Youtube"/>
    </a>
    <figcaption>
        <a href="https://www.thingiverse.com/thing:570288" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            A Timelapse of a Double Spiral Vase Made With Octolapse
        </a>
    </figcaption>
</figure>

Octolapse moves the print bed and extruder into position before taking each snapshot, giving you a crisp image in every frame.  Snapshots can be taken at each layer change, at specific height increments, after a period of time has elapsed, or when certain GCodes are detected.

**Important**:  *Octolapse requires OctoPrint v1.3.9 or higher and some features require OctoPrint v1.3.10rc1 or above.*  You can check your OctoPrint version by looking in the lower left hand corner of your OctoPrint server home page.

## Getting Started

Be sure to [read the getting started guide](https://github.com/FormerLurker/Octolapse/wiki/V0.4---Getting-Started) on the [Octolapse Wiki](https://github.com/FormerLurker/Octolapse/wiki).  This will save you a lot of hassle, and allow you to unlock some of the best features of Octolapse.

<figure style="text-align:center">
    <a href="https://www.youtube.com/watch?v=41wmVbZvcUI" target="_blank">
        <img src="https://img.youtube.com/vi/41wmVbZvcUI/maxresdefault.jpg" alt="View the Getting Started Guide Companion Video on Youtube" title="Watch on Youtube"/>
    </a>
    <figcaption>
        <a href="https://www.youtube.com/watch?v=41wmVbZvcUI" target="_blank">
            View the Getting Started Guide Companion Video
        </a>
    </figcaption>
</figure>

## Recent Changes

A **lot** has changed since the last release (v0.3.4).  Over **18** months of development and over 600 commits went into this newest version.  If you've had trouble installing or running Octolapse in the past, you just might want to try it again!

I have been focusing on 3 items for V0.4:

1. **Print Quality** - This is my #**1** concern, and a ton of effort has gone into  reducing artifacts.
2. **Print Time** - Lots of folks have complained about the print time impact of Octolapse, and this is a totally legitimate concern.  This has been handled by adding new *Smart* triggers that minimize travel distance.  In fact, the new *Smart - Snap To Print* trigger *completely eliminates* travel moves from the stabilization!
3. **Simplify Setup** - Octolapse prior to V0.4 was much more difficult to configure, especially for beginners.  Incorrect setup leads to poor print quality as well as extreme frustration.  This sad situation has been improved (but not completely solved) in several ways, including automatic slicer settings extraction and profile import/export/update functionality.

## Highlights of V0.4

### Python 3 and Octoprint 1.4.0 Support

Octolapse now runs on the newest versions of Python, and is still backwards compatible with Python 2.7.  Additionally, Octolapse also runs on the newest version of OctoPrint.

### Automatic Slicer Settings Detection

Octolapse can now extract all the required slicer settings directly from your GCode file.  You no longer need to copy your slicer settings into Octolapse before every print.  This is my favorite new feature!

<figure style="text-align:center">
    <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Automatic-Slicer-Configuration" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
        <img src="https://raw.githubusercontent.com/wiki/FormerLurker/Octolapse/version/0.4/assets/images/settings/profiles/printer/slicer_type_automatic.png" alt="Automatic Slicer Settings Configuration"/>
    </a>
    <figcaption>
        <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Automatic-Slicer-Configuration" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
            Automatic Slicer Settings Configuration
        </a>
    </figcaption>
</figure>


### Smart Triggers

The new smart triggers read your entire gcode file before starting a print, giving them a lot more information to make better decisions.  They automatically detect print features and prefer to take snapshots over infill, wipe towers, or interior perimeters, and avoid taking snapshots (where possible) over exterior perimeters.  They also try to start snapshots as close to the stabilization point as possible, reducing travel.  This all adds up to improvements in quality and a reduction in print time.  Plus, you will get to see a preview of your timelapse **before** your print starts.  Octolapse will inform you of potential problems *and* will help you to fix them.  If you don't like what you see, you can cancel the print and change your settings, which will save you time and effort.

<figure style="text-align:center">
    <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Getting-Started#snapshot-plan-preview" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
        <img src="https://raw.githubusercontent.com/wiki/FormerLurker/Octolapse/version/0.4/assets/images/tab/snapshot_plan_preview.png" alt="Smart Trigger Snapshot Plan Preview"/>
    </a>
    <figcaption>
        <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Getting-Started#snapshot-plan-preview" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
            Smart Trigger Snapshot Plan Preview
        </a>
    </figcaption>
</figure>


### Improved Interface

Thanks to the UX advice of [Derek73](https://github.com/derek73), the Octolapse tab has been greatly improved.  The highlights include:  a larger snapshot preview, shortcuts to the Octolapse settings pages, video and image file browsers, rendering progress, unfinished rendering recovery, new and improved informational panels, and a more intuitive design.

<figure style="text-align:center">
    <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Octolapse-Tab" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
        <img src="https://raw.githubusercontent.com/wiki/FormerLurker/Octolapse/version/0.4/assets/images/tab/octolapse_tab.png" alt="Improved UX"/>
    </a>
    <figcaption>
        <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Octolapse-Tab" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
            Improved UX
        </a>
    </figcaption>
</figure>

### Import/Export/Download and Automatically Update Settings

Octolapse now has its own [profile repository](https://github.com/FormerLurker/Octolapse-Profiles)!  Access a library of pre-configured profiles, download, customize and share your settings with the world!  You can export and import individual profiles, or all of your Octolapse settings.  If newer settings are available from the repository, Octolapse will notify you, and can automatically update any of the pre-configured profiles.

<figure style="text-align:center">
    <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Profiles#importing-profiles-from-the-octolapse-profile-repository" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
        <img src="https://raw.githubusercontent.com/wiki/FormerLurker/Octolapse/version/0.4/assets/images/settings/profiles/printer/import_a_profile_model.png" alt="Import Profiles from the Repository"/>
    </a>
    <figcaption>
        <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Profiles#importing-profiles-from-the-octolapse-profile-repository" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
            Import Profiles from the Repository
        </a>
    </figcaption>
</figure>

### Enhanced Rendering Capabilities

Now you can see detailed rendering progress, and retry or alter renderings that never finished.  Added beta support for the H.265 codec (most Raspberry PIs don't have the memory for this though).  Added new rendering overlay tokens, text outlining, and added a default font for simplified setup.

<figure style="text-align:center">
    <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Getting-Started#rendering" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
        <img src="https://raw.githubusercontent.com/wiki/FormerLurker/Octolapse/version/0.4/assets/images/tab/rendering_progress_popup.png" alt="Renderings In Process"/>
    </a>
    <figcaption>
        <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Getting-Started#rendering" title="Get more information about this feature from the Octolapse Wiki">
            Renderings In Process
        </a>
    </figcaption>
</figure>

### Browse Videos and Image Archives

I've finally added native file browsers to Octolapse!  Now you can download, sort, or delete timelapses, all without leaving the Octolapse tab.  If you enable the new **archive images** feature, you can also download snapshot images, or re-render them using different settings.  I've even added the ability to upload images into Octolapse!

<figure style="text-align:center">
    <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Getting-Started#download-and-view-your-timelapse" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
        <img src="https://raw.githubusercontent.com/wiki/FormerLurker/Octolapse/version/0.4/assets/images/tab/videos_and_images_popup.png" alt="Videos and Images Browser"/>
    </a>
    <figcaption>
        <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Getting-Started#download-and-view-your-timelapse" alt="Videos and Images Browser" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
            Videos and Images Browser
        </a>
    </figcaption>
</figure>

### Better Camera Controls

Octolapse already included the ability to control camera settings, like focus, exposure and white balance.  In the new version, Octolapse detects your camera's capabilities and renders a control page dynamically.  Octolapse even has enhanced custom control pages for some cameras (like the Raspberry Pi cameras and many Logitech models).  You can now watch your image change in real time as you adjust the settings.  You can even stabilize your extruder to make adjusting focus a snap!  **Requires mjpg-streamer.  Not compatible with [*Octoprint Anywhere*](https://plugins.octoprint.org/plugins/anywhere/) or [*The Spaghetti Detective*](https://plugins.octoprint.org/plugins/thespaghettidetective/)**.

<figure style="text-align:center">
    <a href="https://github.com/FormerLurker/octolapse/wiki/V0.4---Enabling-Camera-Controls" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
        <img src="https://github.com/FormerLurker/octolapse/wiki/version/0.4/assets/images/settings/custom_image_preferences/custom_image_preferences_logitech_c920.png" alt="Custom Image Controls"/>
    </a>
    <figcaption>
        <a href="https://github.com/FormerLurker/octolapse/wiki/V0.4---Enabling-Camera-Controls" title="Get more information about this feature from the Octolapse Wiki" target="_blank">
            Custom Image Controls
        </a>
    </figcaption>
</figure>

### Integrated Help System

Octolapse now provides documentation for every single setting, and it's all built-in.  Get your questions answered quickly by clicking on the help links (blue question marks).  Many error popups now also have a help button explaining what the problem is and how to fix it.  I've also added [versioneer](https://github.com/warner/python-versioneer), including a link within the Octolapse tab that points directly to the release notes or commit specific to the version you have installed.

<figure style="text-align:center">
  <img src="https://github.com/FormerLurker/octolapse/wiki/version/0.4/assets/images/tab/get_help.png" alt="Help With Common Print Start Issues" title="Get Help for Common Print Start Issues"/>
  <figcaption>Help for Common Print Start Issues</figcaption>
</figure>

<figure style="text-align:center">
  <img src="https://github.com/FormerLurker/octolapse/wiki/version/0.4/assets/images/tab/snapshot_plan_preview_qualtiy_warning_get_help.png" alt="Automatic Detection of Print Quality Issues, With Help" title="Automatic Detection of Print Quality Issues, With Help"/>
  <figcaption>Automatic Detection of Print Quality Issues, With Help</figcaption>
</figure>

<figure style="text-align:center">
  <img src="https://github.com/FormerLurker/octolapse/wiki/version/0.4/assets/images/tab/test_mode_snapshot_plan_get_help.png"  alt="Integrated Help Links in the Octolapse Tab" title="Integrated Help Links in the Octolapse Tab"/>
  <img src="https://github.com/FormerLurker/octolapse/wiki/version/0.4/assets/images/settings/profiles/printer/get_help.png" alt="Integrated Help Links Within the Octolapse Profiles" title="Integrated Help Links Within the Octolapse Profiles"/>
  <figcaption>Integrated Help Links</figcaption>
</figure>

### Improved Camera Scripts and Tests

Before and After snapshot gcode scripts allow you to run custom gcode before and/or after every snapshot.  A new *After Print Ends* script is now available.  All bash/bat scripts now have test buttons, making it much easier to test your custom scripts.

<figure style="text-align:center">
  <img src="https://raw.githubusercontent.com/wiki/FormerLurker/Octolapse/version/0.4/assets/images/settings/profiles/camera/custom_camera_scripts.png" alt="Additional Camera Scripts and Tests" title="Additional Camera Scripts and Tests"/>
  <figcaption>Additional Camera Scripts and Tests</figcaption>
</figure>

### New @OCTOLAPSE Commands

Now you can use gcode to tell Octolapse when to take snapshots.  Prevent Octolapse from taking snapshots within your start/end gcode with the new ```@OCTOLAPSE STOP-SNAPSHOTS``` and ```@OCTOLAPSE START-SNAPSHOTS``` commands.  You can also use the new ```@OCTOLAPSE TAKE-SNAPSHOT``` command to trigger a snapshot when using one of the GCode triggers.

### Alpha Support for Multi-Material/Multi-Extruder printers

Octolapse now supports per-extruder/material slicer settings and offsets.  It's even compatible with the *Automatic Slicer Settings Detection* feature.  This is an *Alpha* feature, so it is probably a bit rough since I don't actually own a multi-extruder printer.

### Better Logging

I've added a custom module based logging system that should help with debugging.  You can also clear and download logs right from your *Logging* profile.  Exceptions are now logged automatically.  This enhancement is really for me, but I though I'd mention it here.

### More Efficient Parsing and Processing

In order to make the new *Smart* triggers as fast as possible, and to reduce the CPU load, I've created a new GCode parser and position processor entirely in C++.  This has increased performance by several orders of magnitude, especially when using the new *Smart* triggers.

### Faster Snapshots

Octolapse now captures snapshots more quickly, and performs all image manipulations on a background thread.  This reduces print time and improves quality.

###  G2/G3 (Arc) Support
Octolapse now supports Arc commands.  Now you can use the [Arc Welder](https://github.com/FormerLurker/ArcWelderPlugin) plugin with Octolapse.

## Support Octolapse Development

Please consider supporting my work by becoming a [patron](https://www.patreon.com/join/FormerLurker), a [Github Sponsor](https://github.com/sponsors/FormerLurker), or by sending me beer money via [PayPal](https://paypal.me/formerlurker).  Almost all of the donations go towards offsetting the cost of development, which are substantial. Plus it always makes my day!  If you cannot afford to leave a tip or just don't want to, that is fine too! Octolapse is [free and open source](https://raw.githubusercontent.com/FormerLurker/Octolapse/master/LICENSE) after all.

## More Octolapses

<figure style="text-align:center">
    <a href="https://www.youtube.com/watch?v=uBeVbDJKHw0" target="_blank" title="Watch on Youtube">
        <img src="https://img.youtube.com/vi/uBeVbDJKHw0/maxresdefault.jpg" alt="A user generated compilation created by WildRose Builds"/>
    </a>
    <figcaption>
        <a href="https://www.youtube.com/watch?v=uBeVbDJKHw0" title="Watch on Youtube" target="_blank">
            A user generated compilation created by WildRose Builds.  Support this channel and please subscribe!
        </a>
    </figcaption>
</figure>

<figure style="text-align:center">
    <a href="https://www.youtube.com/watch?v=dYbWfBCLNbI" target="_blank" title="Watch on Youtube">
        <img src="https://img.youtube.com/vi/dYbWfBCLNbI/maxresdefault.jpg" alt="A timelapse of The The 'Fillenium Malcon'"/>
    </a>
    <figcaption>
        <a href="https://www.thingiverse.com/thing:919475" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            The 'Fillenium Malcon'
        </a>
    </figcaption>
</figure>

<figure style="text-align:center">
    <a href="https://www.youtube.com/watch?v=4kEHbRrp2Jk" target="_blank" title="Watch on Youtube">
        <img src="https://img.youtube.com/vi/4kEHbRrp2Jk/maxresdefault.jpg" alt="A timelapse of The Moon"/>
    </a>
    <figcaption>
        <a href="https://www.thingiverse.com/thing:2531838" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            The Moon - Animated Stabilization
        </a>
    </figcaption>
</figure>

<figure style="text-align:center">
    <a href="https://www.youtube.com/watch?v=Ra5Jjq-nJfA" target="_blank" title="Watch on Youtube">
        <img src="https://img.youtube.com/vi/Ra5Jjq-nJfA/maxresdefault.jpg" alt="A Timelapse of Benchy"/>
    </a>
    <figcaption>
        <a href="https://www.thingiverse.com/thing:763622" alt="Link to the model from this video" title="view model on thingiverse" target="_blank">
            The Obligatory Benchy
        </a>
    </figcaption>
</figure>

## History of Octolapse

I got the idea for Octolapse when I attempted to manually make a [stabilized timelapse](https://youtu.be/xZlP4vpAKNc) by hand editing my GCode files.  To accomplish this I used the excellent and simple [GCode System Commands](https://github.com/kantlivelong/OctoPrint-GCodesystemCommands) plugin.  The timelapse worked great, but it required a lot of effort which I didn't want to put in every time.  I received several requests for instructions on how to create a stabilized timelapse, so I decided to give plugin development a go.  At the time I had never before written any OctoPrint plugins (or programmed python or knockout or anything open source), but figured I could contribute something good to the community.

on Jan 20, 2018 I released the first alpha version of Octolapse, and on March 24, 2018 I relased the plugin on the [OctoPrint Plugin Repository](https://plugins.octoprint.org).  Octolapse grew up pretty quickly, and on November 15th 2018 I released V0.3.4.  Over a year and a half and 640+ commits later I finally completed V0.4.0, which is a major rewrite of the software and includes all of the features discussed above.  It took a long time to get here.

Octolapse is my "thank you" to all of the makers out there who have contributed your time and effort to this hobby.  I hope that Octolapse can spread information about the 3D printing hobby by bringing in a few new users.

## Report Problems and Suggest Improvements

If you think you have found a bug in Octolapse, please [see this guide for reporting issues](https://github.com/FormerLurker/Octolapse/wiki/V0.4---Reporting-An-Issue).  Maybe you have an idea for a cool new feature?  Find out how to let me know about your idea [here](https://github.com/FormerLurker/Octolapse/wiki/V0.4---Request-A-New-Feature).

# License

View the [Octolapse license](https://github.com/FormerLurker/Octolapse/blob/master/LICENSE).

<hr/>

_Copyright (C) 2020  Brad Hochgesang - FormerLurker@pm.me_
