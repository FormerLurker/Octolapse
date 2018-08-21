#!/bin/sh
# Put the arguments sent by Octolapse into variables for easy use
SNAPSHOT_NUMBER=$1
DELAY_SECONDS=$2
DATA_DIRECTORY=$3
SNAPSHOT_DIRECTORY=$4
SNAPSHOT_FILENAME=$5
SNAPSHOT_FULL_PATH=$6

# If this command fails with a permissions error, you may need to comment it out and use the sudo version below
gphoto2 --trigger-capture

# if sudo is required uncomment this line and comment out the previous one
# echo "PUT_YOUR_PASSWORD_HERE" | sudo -S gphoto2 --trigger-capture

