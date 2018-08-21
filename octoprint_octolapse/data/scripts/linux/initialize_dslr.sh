#!/bin/sh
# Camera Pre-Render script
# Written by: Formerlurker@pm.me

# Put the arguments sent by Octolapse into variables for easy use
CAMERA_NAME=$1

gphoto2 --capture-image --set-config capturetarget=2
gphoto2 --delete-all-files --recurse
