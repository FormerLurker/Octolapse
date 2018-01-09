M107
M115 U3.0.12 ; tell printer latest fw version
; Start G-Code sequence START
T0
G21 ; set units to millimeters
G90 ; use absolute coordinates
M83 ; use relative distances for extrusion
G28 W ; Home Zxis (should be at 0,0,0 after this command)
G92 E0.0 ; Set extruder to position 0.0
G1 Z0.250 F7200.000 ; move z to .25
G1 E1.0; Feed, layer change now
G1 X100 Y100 ; move from 0,0 to 100,100
M114
G1 X100 Y150 ; move from 100,100 to 100,150
M114
G1 E1.0; Feed, no layer change
G91 ; switch to relative coordinates
G1 X-50 Y-50 ; move from 100,150 to 50,100
M114
G1 Z0.05 F7200.000 ; move z from .25 to .3
M114
G1 X50 Y50 ; move from 50,100 to 100,150
M114
G1 E1.0; Feed, layer change
G92 ; set position to 0,0 (100,150)
M114
G90 ; set to absolute mode
G1 X-50 Y-50 ; move from 0,0 (100,150) to -50,-50 (50,100)
M114
G1 Z0.2 F7200.000 ; move z from 0 (.3) to .2 (.5)
M114
G1 E1.0; Feed, layer change
M114
