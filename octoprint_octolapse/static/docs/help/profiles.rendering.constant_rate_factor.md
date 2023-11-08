CRF (Constant Rate Factor) scales the video quality and compression, and ranges from 0 to 51.  A value of 0 yields lossless encoding (highest possible quality), but produces a huge file.  A value of 51 would result in the smallest file size with the lowest quality.  The default value of 28.  A good rule of thumb is that decreasing the CRF by 6 will approximately double the file size, while increasing it by 6 will cut the file size roughly in half.

Currently this setting is only supported for H265, a High Efficiency Video Coding (HVEC) format since manually specifying the bitrate for single pass encoding is not recommended.


