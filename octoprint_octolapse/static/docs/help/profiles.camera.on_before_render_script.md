This script is executed before rendering begins for this camera. This script runs with no timeout, so make sure it returns, else your rendering will never complete.  It will only run if rendering is enabled, and will run even if there are no snapshots at the proper location to generate a timelapse.  I used this script to download all images from my DSLR in order to reduce the amount of time it took to take snapshots (reduced it by more than half) for high res images.  It could be used to apply custom image filters, and a whole lot more.  Please let me know what you are using this for!

The *Test* button will run this script with the **Snapshot Timeout**, but during a live print there is no timeout.  This is to prevent scripts from running for an unusual amount of time when testing.

Parameters:

* Camera Name - The name of the camera profile used to generate the images
* Snapshot Directory - The path to the current camera's snapshot folder for the current print job.  This directory may not exist, so be sure to create it before using the path!
* Snapshot File Name Template - A template that can be used to format the filenames so that ffmpeg can turn them into a timelapse.
* Snapshot Full Path Template - Combines the snapshot directory and the file name template.

Here is a bash script that I used to move and rename all of the images that I downloaded from my DSLR in order to render a timelapse from them:
```
a=0
for i in *.JPG *.jpg *.JPEG *.jpeg; do
  new=$(printf "${SNAPSHOT_FILENAME_TEMPLATE}" "${a}")
  mv -- "${i}" "${new}"
  a=$((a+1))
done
```
I plan to add this to the DSLR guide soon.
