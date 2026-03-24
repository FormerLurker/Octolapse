

There are several smart layer types that are available:

#### Fastest 
Gets the closest position.  **This WILL leave very noticeable defects on your print when using this mode.**  However, it can be VERY useful if you are printing an ooze shield, or want to stabilize on top of a wipe tower.  The key is to adjust the stabilization point so that Octolapse always triggers on an unimportant piece.

**Not recommended for vase mode**
#### Compatibility
Attempts to return a high quality position if possible (see position rankings below).  If it cannot, it will return the next best position available, **including extrusions**, to ensure that a snapshot is taken on every layer.  Use this trigger if you're concerned with quality, but you want Octolapse to trigger on every layer no matter what.  This mode is also more likely to work with some lesser tested slicers and slicer settings.  This mode WILL take a snapshot while extruding if it has found no alternative and is more likely to leave artifacts than the high quality or smap to print types.
**Not recommended for vase mode**
#### High Quality
Gets the best quality position available.  This includes any slicer comment based gcode features.

**THIS MODE WILL NOT WORK WITH VASE MODE!**  

Snapshots will be skipped if no quality positions can be found.  If you are using this mode and notice fewer snapshots than you expect, try compatibility mode instead if you don't care about reduced quality.  If you have retraction disabled this mode will probably not take any snapshots at all.  If you use vase mode, you will only get a few snapshots at the beginning and possible a few snapshots at the end of the print.

#### Snap to Print

Prevents the extruder from leaving the print during stabilization, reducing travel movements to 0.  This is a great option for improving print quality and reducing the amount of time Octolapse adds to your print.  However, your timelapse will likely be a little jerky depending on the shape of your printed part.

**For the highest quality prints , reduce your camera delay to 0.**

**Not recommended for DSLR cameras or with long camera delays!**

**Works with vase mode**, but you will probably see a seam where snapshots were taken.  This can be reduced somewhat by decreasing the time it takes to acquire a snapshot.

### Position Rankings by Quality

Octoalpse ranks positions by both position and feature type.  Exactly how it does this depends on the exact smart layer trigger type and options.

#### Feature Type

In general, the smart layer trigger will choose positions with a known feature type over those without.  However, this depends on the smart layer trigger type.

Most slicers include some comments within the gcode file that indicates what type of feature is being printed.  This information is not always complete, but is often useful for choosing when to take a snapshot with the least impact on print quality.  

These are used with the **Compatibility**, **High Quality**, and **Snap to Print**.

Note that features are only detected in the **Snap to Print** trigger when the **High Quality Mode** option is enabled.

Each slicer has slightly different capabilities.  Cura and Simplify 3D add gcode comment sections to their sliced gcode files by default.  

Slic3r, Slic3r PE, and PrusaSlicer do not output comments by default.  It is **highly recommended** that you enable this by going into ```Print Settings```->```Output Options```->```Output Options``` and enabling ```Verbose G-Code``` by checking the box next to the setting.  This will increase file-size somewhat, but has the potential 

There are the following features that can be detected by Octolapse, in order of quality (highest quality to lowest):

* Prime Pillar - This is usually a waste piece, so it's totally safe to take snapshots when printing a prime pillar.  Supported by Simplify3D, Slic3r PE and Prusa Slicer (Pusa slicers supported when printing with an MMU only as far as I know.)
* Infill - This is generally the best place to take a snapshot.  Works on all supported slicers.
* Ooze Shield - This is printed to protect a print from ooze.  I think this is a good place to take a snapshot, but have not tested it yet.
* Solid Infill - This is usually on the inside of a print, or on the top surface.  An OK place to take a snapshot.  Not yet supported for Prusa slicers.
* Gap Fill - Another OK place to take a snapshot, but we're starting to get iffy.  Only supported by Simplify 3d.
* Skirt - This would be considered a high quality place to take a snapshot, and it is, but having it higher causes problems with snap-to-print.
* Inner Perimeters - Not a great place to take a snapshot, but much better than exterior perimeters.  Prusa slicers do not distinguish from internal and external perimeters.

Some features types are ignored
* Unknown Perimeters -  Slic3r doesn't differentiate between internal and external perimeters, so all are considered to be external.
* External Perimeters - The worst place to take snapshots!  Octolapse tries to avoid taking snapshots over these features if at all possible.
* Bridge - Prusa Slicers will note when a move is a bridge.  Octolapse will avoid taking snapshots over these positions if possible.


#### Position Type
Here is how Octolapse ranks positions (from best to worst) when choosing a point to start taking a snapshot:

* Fastest Extrusion - If a layer has more than one print speed, the extrusions with the fastest speed are considered the best place to take snapshots.  This isn't always true, especially if the slicer's minimum layer time is being enforced by slowing down priting speeds, but true more often than it is not.  Usually this is the best time to take a snapshot.  Note that for layers with only one extrusion speed, this position will not exist.
* Lifted and Retracted Travel Move - Usually a good time to take a snapshot.  Your printer is fully lifted, fully retracted, and is traveling.
* Lifting and Retracted Travel Move - Your printer is fully retracted, and is traveling while lifting at the same time.
* Retracted Travel Move - Your printer is rully retracted and traveling.
* Retracted and Lifted - Your printer is fully retracted and fully lifted.
* Retracted and Lifting - Your printer is fully retracted, and is lifting.
* Retracted - Your printer has just completed a retraction.  This can be a good time to take a snapshot.  Most of the smart trigger types will return a position without looking for a closer one at this point.  Only the 'fastest', and sometimes the 'fast' option will keep searching for a closer position if a higher quality position was already found.
* Lifted Travel - Your printer is lifted fully, and traveling.
* Lifting Travel - Your printer is lifting and traveling at the same time (Cura does this I believe)
* Travel - Your printer is traveling.
* Lifted - Your printer is fully lifted (according to the z-hop distance setting in your slicer).
* Lifting - Your printer is raising the Z axis.  Though not a great place to take a snapshot, it's better than while extruding.
* Extruding - Your printer is extruding.  This is usually the worst time to take a snapshot.
* Unknown - Octolapse doesn't know, or doesn't care what type of position this is.  Snapshots are never taken from unknown positions

If you believe there are other scenarios that need to be handled, or that the order of any of the items above is incorrect, please let me know.  This is a work in progress, and I believe there will be lots of tweaks in the future.

