#!/bin/sh
# Camera Initialization Script
# Sets the capture target to the SD card
# Written by: Formerlurker@pm.me

# Put the arguments sent by Octolapse into variables for easy use
CAMERA_NAME=$1
# Set camera to save images to flash memory
gphoto2 --set-config capturetarget=2
# DELETE ALL FILES ON THE CAMERA, SO BACKUP YOUR FAMILY PHOTOS FIRST!
gphoto2 --delete-all-files --recurse
