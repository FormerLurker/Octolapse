No files were found within the imported zip archive.  Octolapse supports two different ways of importing zip archives:

1.  All files in the root of the archive.
2.  Files can be located within a JOB_GUID\CAMERA_GUID folder structure.  Here is an example of this structure:
```
dd46e35c-50ab-4f7a-a90d-4c69e59b2a4f\354def78-9eea-409a-ad23-ee966dfff4ba\{All Files Here}
```

The easiest way to resolve these errors is to put all of your images in a single folder, and zip them together.  Make sure your images have a ```.jpg``` extension.  Optionally you can include the following other settings file:
```
camera_info.json
camera_settings.json
rendering_settings.json
metadata.csv
timelapse_info.json
```
