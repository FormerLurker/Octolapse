set SNAPSHOT_NUMBER=%1
set DELAY_SECONDS=%2
set DATA_DIRECTORY=%3
set SNAPSHOT_DIRECTORY=%4
set SNAPSHOT_FILENAME=%5
set SNAPSHOT_FULL_PATH=%6
if not exist %SNAPSHOT_DIRECTORY% mkdir %SNAPSHOT_DIRECTORY%

"C:\Program Files (x86)\digiCamControl\CameraControlCmd.exe" /filename %SNAPSHOT_FULL_PATH% /capture
rem see if the file exists, if not throw an error.
if not exist %SNAPSHOT_FULL_PATH% (
	echo The file was not created! 1>&2
	EXIT /B 1
)
EXIT /B 0
