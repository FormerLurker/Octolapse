#!/bin/sh
# Camera Pre-Render script
# Written by: Formerlurker@pm.me

# Put the arguments sent by Octolapse into variables for easy use
CAMERA_NAME=$1
# Set camera to save images to flash memory
gphoto2 --capture-image --set-config capturetarget=2
# DELETE ALL FILES ON THE CAMERA, SO BACKUP YOUR FAMILY PHOTOS FIRST!
gphoto2 --delete-all-files --recurse
