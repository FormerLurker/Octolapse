#!/bin/sh
# Camera Post-Render Script - Move Snapshots to Target Folder
# Written by: Formerlurker@pm.me

# 1.  This script should be created within the '/home/pi/scripts/'
#     folder on your pi and called move_snapshots_to_target.sh.
#     You can use the following command to create the file
#     sudo nano move_snapshots_to_target.sh
# 2.  Copy and paste this script into nano via a single right click.
# 3.  ** IMPORTANT - Change the TARGET_SNAPSHOT_DIRECTORY below
TARGET_SNAPSHOT_DIRECTORY="/home/pi/snapshot_target_folder"
# 4.  Save the file via ctrl+o and exit via ctrl+x
# 5.  Add execute permissions to the file via:
#     sudo chmod +x /home/pi/scripts/move_snapshots_to_target.sh
# 6.  In your Octolapse camera profile add the following to the 'After Render Script':
#     /home/pi/scripts/move_snapshots_to_target.sh
# 7.  Enjoy!

# Put the arguments sent by Octolapse into variables for easy use
CAMERA_NAME=$1
SNAPSHOT_DIRECTORY=$2
SNAPSHOT_FILENAME_TEMPLATE=$3
SNAPSHOT_FULL_PATH_TEMPLATE=$4
TIMELAPSE_OUTPUT_DIRECTORY=$5
TIMELAPSE_OUTPUT_FILENAME=$6
TIMELAPSE_EXTENSION=$7
TIMELAPSE_FULL_PATH=$8
SYNCHRONIZATION_DIRECTORY=$9
SYNCHRONIZATION_FULL_PATH=$10
# -------------------------------------------------------

# Create the directory if it doesn't exist
if [ ! -d "${TARGET_SNAPSHOT_DIRECTORY}" ];
then
  echo "Creating directory: ${TARGET_SNAPSHOT_DIRECTORY}"
  mkdir -p "${TARGET_SNAPSHOT_DIRECTORY}"
fi
# -------------------------------------------------------

# switch to the snapshot directory
cd "${SNAPSHOT_DIRECTORY}"
# -------------------------------------------------------

# Copy all images in the snapshot_directory to the target directory
for snapshot in *.JPG *.jpg *.JPEG *.jpeg; do
  new="$TARGET_SNAPSHOT_DIRECTORY/${snapshot##*/}"
  cp -- "${snapshot}" "${new}"
done
# -------------------------------------------------------
