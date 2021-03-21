The Octolapse logger is module based, allowing you to log only the data you need.  Logfiles can get huge, and logging more than you need can make the log file hard to read.

Octolapse has many modules, and each has a different function.  Every module starts with ```octolapse.```, which has been omitted from the list below, where you will find a brief description of each module:

* **\_\_init\_\_** -  This is the core Octolapse module. It handles web requests, OctoPrint events, and client notifications.
* **camera** - This module includes functionality to test webcams and apply webcam image preferences (brightness, focus, etc).
* **gcode_commands** - This module contains information necessary to enable test mode, which strips extrusion and temperature related commands from the gcode stream, allowing you to test Octolapse settings without waiting for you bed to warm up, or wasting filament.
* **gcode_parser** - Part of the GcodePositionProcessor (c++ library) responsible for parsing gcode.  All gcode parsing in Octolapse uses this module.
* **gcode_position** - Part of the GcodePositionProcessor (c++ library) responsible for processing gcode and tracking your printer's current state, including position and extruders.
* **gcode_processor** - This module is a wrapper for Octolapse's custom parser/position processor (GcodePositionProcessor written in c++).
* **messenger_worker** - Sends rate limited push notifications to the client.
* **position** - This module has been mostly replaced by the GcodePositionProcessor (see gcode_processor above), but contains some functionality mostly to support the classic triggers (gcode, timer and layer) that has not yet been added to the c++ replacement.  Eventually this module will go away.  It currently implements custom trigger position restrictions, extruder trigger requirements, and some utility functions for sending position/state information to the client.
* **render** - This module is responsible for rendering snapshots into a video.
* **settings** - Contains all Octolapse configuration data definitions.  Is responsible for loading, saving and updating all settings, including default and client data.
* **settings_external** - Provides access to the octolapse profile repository, including import and update capability.  This module is used to import profiles from the profile settings pages and to perform updates when newer profiles are available.
* **migration** - Updates the settings for older versions of Octolapse right after installation, or when importing older settings into Octolapse.
* **settings_preprocessor** - Extracts slicer settings from gcode files to support the **Automatic Slicer Settings** option in your Octolapse printer profile.
* **snapshot** - Responsible for taking snapshots for webcams, external script cameras (DSLR), and gcode cameras (built into printer).  It also executes any before/after snapshot scripts in your camera profiles.
* **snapshot_plan** - Part of the GcodePositionProcessor (c++ library) responsible for creating snapshot plans for the **Smart** triggers.
* **stabilization_gcode** - Creates the gcode Octolapse uses to stabilize your extruder.  It is capable of reading snapshot plans produced by the stabilization preprocessor, or creating a snapshot plan from the current position.
* **stabilization_preprocessing** - Communicates with the GcodePositionProcessor in order to preprocess your gcode file when using any of the **Smart** triggers.  It provides updates to the UI showing the preprocessing progress, and returns a list of snapshot plans returned by the stabilization.  These plans are used to determine when Octolapse will take a snapshot.
* **timelapse** - This module is responsible for watching incoming and sent gcode commands, communicating with the printer, executing stabilizations, triggering snapshots, starting rendering, and a whole lot more.  Most modules in Octolapse are written to support this module.  It is the heart of the program (and a bit messy).  WARNING - Logging this module at the Debug or Verbose log level, though sometimes necessary, will create massive log files.
* **trigger** - Controls the three classic triggers - gcode, timer, and layer.  This module may be retired at some point.

