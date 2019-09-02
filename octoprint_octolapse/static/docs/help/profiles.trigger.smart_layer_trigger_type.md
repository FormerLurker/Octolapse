

There are several smart layer types that are available:

#### Fastest 
Gets the closest position.  **This WILL leave very noticeable defects on your print when using this mode.**  However, it can be VERY useful if you are printing an ooze shield, or want to stabilize on top of a wipe tower.  The key is to adjust the stabilization point so that Octolapse always triggers on an unimportant piece.

**Not recommended for vase mode**
#### Compatibility
Attempts to return a high quality position if possible (see position rankings below).  If it cannot, it will return the next best position available, **including extrusions**, to ensure that a snapshot is taken on every layer.  Use this trigger if you're concerned with quality, but you want Octolapse to trigger on every layer no matter what.  This mode is also more likely to work with some lesser tested slicers and slicer settings.  This mode WILL take a snapshot while extruding if it has found no alternative and is more likely to leave artifacts than the high quality or smap to print types.
**Not recommended for vase mode**
#### Best Quality
Gets the best quality position available.  This includes any slicer comment based gcode features.  

**THIS MODE WILL NOT WORK WITH VASE MODE!**  

Snapshots will be skipped no quality positions can be found.  If you are using this mode and notice fewer snapshots than you expect, try compatibility mode instead if you don't care about reduced quality.  If you have retraction disabled this mode will probably not take any snapshots at all.  If you use vase mode, you will only get a few snapshots at the beginning and possible a few snapshots at the end of the print.

#### Snap to Print

Prevents the extruder from leaving the print during stabilization, reducing travel movements to 0.  This is a great option for improving print quality and reducing the amount of time Octolapse adds to your print.  However, your timelapse will likely be a little jerky depending on the shape of your printed part.

**For the highest quality prints , reduce your camera delay to 0.**

**Not recommended for DSLR cameras or with long camera delays!**

**Works with vase mode**, but you will probably see a seam where snapshots were taken.  This can be reduced somewhat by decreasing the time it takes to acquire a snapshot.

### Position Rankings by Quality

Here is how Octolapse ranks positions (from best to worst) when choosing a point to start taking a snapshot:

* lifted_retracted_travel - The best time to take a snapshot.  Your printer is fully lifted, fully retracted, and is traveling.
* lifting_retracted_travel - Your printer is fully retracted, and is traveling while lifting at the same time.
* retracted_travel - Your printer is rully retracted and traveling.
* retracted_lifted - Your printer is fully retracted and fully lifted.
* retracted_lifting - Your printer is fully retracted, and is lifting.
* retraction - Your printer has just completed a retraction.  This can be a good time to take a snapshot.  Most of the smart trigger types will return a position without looking for a closer one at this point.  Only the 'fastest', and sometimes the 'fast' option will keep searching for a closer position if a higher quality position was already found.
* lifted_travel - Your printer is lifted fully, and traveling.
* lifting_travel - Your printer is lifting and traveling at the same time (Cura does this I believe)
* travel - Your printer is traveling.
* lifted - Your printer is fully lifted (according to the z-hop distance setting in your slicer).
* lifting - Your printer is raising the Z axis.  Though not a great place to take a snapshot, it's better than while extruding.
* extrusion - Your printer is extruding.  This is usually the worst time to take a snapshot.
* unknown - Octolapse doesn't know, or doesn't care what type of position this is.  Snapshots are never taken from unknown positions

If you believe there are other scenarios that need to be handled, or that the order of any of the items above is incorrect, please let me know.  This is a work in progress, and I believe there will be lots of tweaks in the future.
