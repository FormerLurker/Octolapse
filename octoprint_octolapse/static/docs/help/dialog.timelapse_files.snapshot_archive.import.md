Octolapse supports importing a zip archive containing images.  These files can come from the download option within the **Saved Snapshot** tab, or you can create them yourself.  Currently, Octolapse only supports images with a ```jpg``` extension.  After you import the archive, Octolapse will add it to the **Saved Snapshots** tab within the **Videos and Images** dialog.  From there you can download, delete, or add the archive to the list of unfinished renderings.

Archive file generation can be enabled in two ways:

1.  If rendering is disabled, an archive will always be produced.
2.  If rendering is enabled, Octolapse will produce an archive if the **Archive Snapshots After Rendering** setting is enabled within your rendering settings.  It is disabled by default, since it takes a lot of space.

Octolapse supports two kinds of file structures:

1.  Everything in the root of the zip archive.  This means all images are located right inside of the archive, and are not in any subfolders.  All subfolders will be ignored.
2.  All images contained within a **job** and **camera** folder.  These folders have a special naming scheme that mimics how Octolapse stores timelapse images within the temporary folder.  Both the Job and Camera folder are GUIDs.  The following would be a valid job/camera folder structure:  ```48bb64c2-e878-4b1b-87b8-a06d1b4fc181\354def78-9eea-409a-ad23-ee966dfff4ba```.

Octolapse will also search for various settings files, and will include settings if you choose to render the snapshots within the archive.  These settings files are as follows:
1.  timelapse_info.json - This file contains information about the print file name, the start and end time of the print, and the GUID of the original print job.  This file must be located within the root, or within the job folder.
2.  camera_info.json - This file contains information about the total number of snapshots attempts, failures and successes.  This file must be located within the root, or within the camera folder.
3.  metadata.csv - This file contains information about the snapshot image file name, the snapshot number, and the time the snapshot was taken.  This is used for adding text overlays to the rendered video.  This file must be located within the root, or within the camera folder.
4.  camera_settings.json - This is the settings file for the camera profile that was used to take the snapshots.  Camera settings can affect what scripts run during rendering, and the final rendered video name if the {CAMERANAME} token is used in the rendering **Filename Template**.  This file must be located within the root, or within the camera folder.
5.  rendering_settings.json - This is the settings file for the rendering profile that was used to take the snapshots.  This file will be used to create the rendering if you choose to render a timelapse from the archive.  This file must be located within the root, or within the camera folder.

Note:  You can change the camera and rendering settings before you render any videos from a snapshot archive file.
