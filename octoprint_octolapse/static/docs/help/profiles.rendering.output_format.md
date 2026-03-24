Choose the output video format.  Several are available, including mp4, gif, mpeg,

### Important Notes for High Resolution Videos

The H.264 codec will most likely fail to encode or fail to play if you try to render a video with a resolution higher than 4096x2048.  H.265 supports higher resolution of up to 8192×4320.  Also, both of these formats require a large amount of memory to encode, so it's possible that you **will run out of memory** when using either format to encode a very high resolution video.

### H.265
This format is BETA, so use at your own risk.  My tests have yielded mixed results.  I was able to produce very high quality 4K video with this format at a CBR of 28, but playback only works on a small number of players.  At a lower CBR, of 5, the resulting file was huge and did not play back properly.
