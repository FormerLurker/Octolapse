Determines the rendering file name. You can use the following replacement tokens:
 
 * {FAILEDFLAG}
 * {FAILEDSTATE}
 * {FAILEDSEPARATOR}
 * {PRINTSTATE}
 * {GCODEFILENAME}
 * {DATETIMESTAMP}
 * {PRINTENDTIME}
 * {PRINTENDTIMESTAMP}
 * {PRINTSTARTTIME}
 * {PRINTSTARTTIMESTAMP}
 * {SNAPSHOTCOUNT}
 * {FPS}
 * {CAMERANAME}
 
 The default template `{FAILEDFLAG}{FAILEDSEPARATOR}{GCODEFILENAME}_{PRINTENDTIME}` might render something like this for a failed print:
 
```
 FAILED_PLA_Benchy_Octolapse_20190603151733.mp4
```
 Or this for a successful print:
```
 PLA_Benchy_Octolapse_20190603151733.mp4
```
