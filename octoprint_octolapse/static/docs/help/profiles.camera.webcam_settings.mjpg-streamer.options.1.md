In theory this should control the quality of the final jpeg image in percent, with higher values yielding a better image, and lower values yielding a smaller image (less bandwidth).  However, I have not been able to tell if this setting is doing anything at all, at least on the two cameras I've tested (Logitech C920 and Raspberry Pi Camera Module V2).

If you are using a Raspberry Pi Camera Module V2, see 'Video Bitrate' setting, which really does seem to improve the camera stream quality.  It will also increase the bandwidth required, so use caution when adjusting that setting.
