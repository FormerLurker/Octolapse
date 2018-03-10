---
layout: plugin
id: your plugin's identifier
title: Octolapse
description: Takes stabilized timelapses of your 3d prints.
author: Brad Hochgesang
license: [AGPL-3.0](https://github.com/FormerLurker/Octolapse/blob/master/LICENSE)
date: 2018-03-10
homepage: https://formerlurker.github.io/Octolapse/
source: https://github.com/FormerLurker/Octolapse/
archive: https://github.com/FormerLurker/Octolapse/archive/master.zip
tags:
- timelapse
screenshots:
- url: /assets/img/plugins/OctoLapse/tab.png
  alt: The octolapse main tab.
  caption: The main octolapse tab, including all four info panels.
featuredimage: /assets/img/plugins/OctoLapse/tab.png
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
Octolapse is a plugin for Octoprint, a well-known 3D print server.  It is designed to make stabilized timelapses of your prints, and it's extremely configurable.  Every effort has been made to maintain print quality when using Octolapse.

Octolapse monitors the GCode sent to your printer from Octoprint while printing locally, and takes snapshots either at height increments/layer changes, after a period of time has elapsed, when certain GCodes are detected, or a combination of the three.  Octolapse monitors the position of each axis and attempts to determine the extruder state in order to detect the optimal time to take a snapshot.  There are lots of settings to customize exactly when a snapshot should be taken and when they are not allowed.

Once it's time to take a snapshot, Octolapse inserts a series of GCode commands to move the bed and extruder to the proper position.  It will optionally ensure that the extruder is retracted in order to reduce stringing and oozing, and will lift if possible.  The snapshot position can be customized for each in a variety of ways, and can even be animated.

Once printing is finished, a timelapse is rendered according to your specifications.  Timelapses can be either fixed framerate, or fixed length.  Pre and post-roll frames can be added so that your timelapses don't start and end abruptly.  Renderings can be rotated, reversed, and more.  Multiple video formats are currently supported.  Your timelapse can optionally moved to the default timelapse plugin, making it easy and convenient to view, sort, and download your timelapses.  Currently Octolapse has no native file browser/viewer, so this is HIGHLY recommended.

Octolapse also allows you to define camera settings that can be applied at the start of a print.  This allows you to ensure consistent images by controlling things like focus, zoom, pan, and exposure, making your snapshots as crisp and clear as possible.  You can also use multiple cameras, though currently Octolapse only allows one camera to be used at a time.
