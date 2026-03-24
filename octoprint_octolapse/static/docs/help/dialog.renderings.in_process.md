This dialog shows the progress of any renderings that are in the rendering queue.  Note that even if rendering is disabled, they will be added to the rendering queue so that a snapshot archive file (.zip) can be created.

### Where do I find the finished timelapses and saved snapshot files (.zip)?

All timelapse videos and saved snapshots can be found within the Octolapse tab by clicking the  **Videos and Images** button, which opens a popup window which will display all of your files.  Please note that snapshots are only saved if **Archive Snapshots After Rendering** is enabled, which can be found in your rendering profile under the **Files and Performance** section.

### What do the progress messages mean?

Timelapses will be rendered in the order they are sent, and go through following phases:

1. **Pending** - These timelapses have been queued, but have not yet started the rendering process.
2. **Script - Before** - If your camera has any **Before Render Scripts** configured, Octolapse will run these.  Unfortunately there is no way currently to report progress from these scripts, so Octolapse will not show a progress bar while in this phase.  I'm considering adding this capability in a future update, though it will require the script to send progress messages to the output screen.
3. **Preparing** - Before rendering starts, a few steps must be completed.  First, Octolapse will delete any existing temporary rendering files that might exist.  Next, the temporary rendering directory will be created.  Finally, all images with valid extensions will be copied to a temporary rendering directory and converted to JPEGs if they do not appear to be in JPEG format.  Copying the images does take extra disk space (as opposed to simply moving the images), but allows Octolapse to gracefully recover if there are any errors during any part of the rendering process.
4. **Adding Overlays** - If you have enabled text overlays within your rendering settings, they will be added during this phase.  This phase could take a while to complete depending on the resolution of your snapshots.
5. **Rename Images** - Octolapse must rename all image files so that they are sequential.  Images names may not be sequential at this point if there were any errors while acquiring snapshots.  This process should be very fast.
6. **Pre/Post Roll** - Depending on your rendering settings, pre-roll  and post roll frames may be made by copying the first and last images the appropriate number of times in order to achieve the specified pre/post-roll length.  This phase can take a while depending on the framerate and the size of your image files.  Please note that your images will need to be renamed once again if any pre-roll frames are added, but this usually doesn't take much time at all compared to copying the images.
7. **Rendering** - Thanks to a recent OctoPrint update, I was able to add a rendering progress indicator based on the code from a pull request!  This is usually the most time consuming phase, and can take quite a bit of time and CPU power to complete.  If Octoprint is running on multi-threaded hardware, you can reduce the rendering time by increasing the number of rendering threads within your rendering profile.  Check the **Rendering Thread Count** help within your rendering profile for details.
8. **Archiving** - Depending on your settings, an archive (.zip) file may be created.  This can take a while to complete, especially if there are a lot of high resolution images in your timelapse.  Note that the snapshots are the original images, unmodified by the rendering process, and will contain metadata and settings that can be used to re-create the rendering.
9. **Post Render Script** - If your camera has any **After Render Scripts** configured, Octolapse will run these.  Just like the **Script - Before** phase, there is no progress bar shown.
10. **Cleanup** - At this point all snapshots in the temporary directory are deleted along with the original timelapse images.  Progress is displayed during this phase.


