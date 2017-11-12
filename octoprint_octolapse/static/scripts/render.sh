#!/bin/bash

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -fmp|--ffmpeg_path)
    FFMPEGPATH="$2"
    shift # past argument
    shift # past value
    ;;
    -d|--output_directory)
    OUTPUTDIRECTORY="$2"
    shift # past argument
    shift # past value
    ;;
	-n|--output_file_name)
    OUTPUTFILENAME="$2"
    shift # past argument
    shift # past value
    ;;
	--default)
    DEFAULT=YES
    shift # past argument
    ;;
    *)
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

echo FFMPEG PATH  = "${FFMPEGPATH}"
echo OUTPUT FILE DIRECTORY = "${OUTPUTFILEPATH}"
echo OUTPUT FILE NAME = "${OUTPUTFILENAME}"
echo DEFAULT         = "${DEFAULT}"


mkdir -p ${OUTPUTFILEPATH}
USERPARAM = ""
if [ -z "$USERNAME" ] && [ -z "$PASSWORD" ]; then
	USERPARAM = "$USERNAME:$PASSWORD"
	curl -u $USERPARAM -k $SNAPSHOTADDRESS > $OUTPUTFILEPATH/$OUTPUTFILENAME
else
	curl -k $SNAPSHOTADDRESS > $OUTPUTFILEPATH/$OUTPUTFILENAME

fi
