This is called after rendering is completed successfully (not on error), but before any prepossessed images are deleted and before the rendered timelapse is optionally moved into the OctoPrint timelapse folder.  This has not been tested too much because I haven't had a use for it yet.  It was requested by a user who wanted to move completed timelapses to another server after rendering.

The *Test* button will run this script with the **Snapshot Timeout**, but during a live print there is no timeout.  This is to prevent scripts from running for an unusual amount of time when testing.

Parameters:

* Camera Name - The name of the camera profile used to generate the images
* Snapshot Directory - The path to the current camera's snapshot folder for the current print job.  This directory may not exist, so be sure to create it before using the path!
* Snapshot File Name Template - A template that can be used to format the filenames so that ffmpeg can turn them into a timelapse.
* Snapshot Full Path Template - Combines the snapshot directory and the file name template.
* Timelapse Output Directory - The directory containing the final rendered timelapse.
* Timelapse Output Filename - The final timelapse file name without extension
* Timelapse Extension - The output extension of the rendered timelapse.
* Timelapse Full Path - The current location of any rendered timelapse.

