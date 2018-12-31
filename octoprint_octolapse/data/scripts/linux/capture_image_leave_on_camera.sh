#!/bin/sh
# Camera Capture Script - Leave on Camera, Don't download
# Requires a camera initialization script with the following command:  gphoto2 --capture-image --set-config capturetarget=2
# Written by: Formerlurker@pm.me
# Put the arguments sent by Octolapse into variables for easy use
SNAPSHOT_NUMBER=$1
DELAY_SECONDS=$2
DATA_DIRECTORY=$3
SNAPSHOT_DIRECTORY=$4
SNAPSHOT_FILENAME=$5
SNAPSHOT_FULL_PATH=$6

# trigger the camera and exit immediately
gphoto2 --trigger-capture


