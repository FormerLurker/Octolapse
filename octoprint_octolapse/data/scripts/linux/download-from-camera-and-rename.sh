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
gphoto2 --auto-detect --get-all-files --force-overwrite

# Count the number of images downloaded.  If we find 0, report an error.
a=0
for i in *.JPG *.jpg *.JPEG *.jpeg; do
  a=$((a+1))
done

# If no snapshots were found, report an error and exit.
if [ "$a" = "0" ]; then
    echo "No snapshot were found with extensions .JPG, .JPEG, .jpg or .jpeg. " 1>&2;
    exit 1;
fi

# rename images according to the supplied file template
a=0
for i in *.JPG *.jpg *.JPEG *.jpeg; do
  num_files=0
  num_files=$(ls -lq "${i}" 2>/dev/null | wc -l  )
  if [ "$num_files" != "0" ]; then
    new=$(printf "${SNAPSHOT_FILENAME_TEMPLATE}" "${a}")
    echo "Moving file ${i} to ${new}"
    mv -- "${i}" "${new}" 2>/dev/null
    a=$((a+1))
  fi
done
