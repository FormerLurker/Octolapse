#!/bin/sh
# Camera Pre-Render script
# Written by: Formerlurker@pm.me

# Put the arguments sent by Octolapse into variables for easy use
CAMERA_NAME=$1
SNAPSHOT_DIRECTORY=$2
SNAPSHOT_FILENAME_TEMPLATE=$3
SNAPSHOT_FULL_PATH_TEMPLATE=$4

# Check to see if the snapshot directory exists
if [ ! -d "${SNAPSHOT_DIRECTORY}" ];
then
  echo "Creating directory: ${SNAPSHOT_DIRECTORY}"
  mkdir -p "${SNAPSHOT_DIRECTORY}"
fi

# switch to the snapshot directory
cd "${SNAPSHOT_DIRECTORY}"

# download all of the images on the camera
gphoto2 --get-all-files --force-overwrite

# rename images according to the supplied file template
a=0
for i in *.JPG *.jpg *.JPEG *.jpeg; do
  new=$(printf "${SNAPSHOT_FILENAME_TEMPLATE}" "${a}")
  mv -- "${i}" "${new}"
  a=$((a+1))
done

