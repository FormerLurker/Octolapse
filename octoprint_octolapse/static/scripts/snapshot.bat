
@echo off
:loop
IF NOT "%~0"=="" (
    IF "%0"=="--output_directory" (
        SET OUTPUTDIRECTORY=%1
		echo output directory %1
        SHIFT
    )
    IF "%0"=="--output_file_name" (
        SET OUTPUTFILENAME=%1
        SHIFT
    )
	IF "%0"=="--user_name" (
        SET USER_NAME_octolapse=%1
        SHIFT
    )
	IF "%0"=="--password" (
        SET PASSWORD=%1
        SHIFT
    )
	IF "%0"=="--snapshot_address" (
        SET SNAPSHOTADDRESS=%1
        SHIFT
    )
    SHIFT
    GOTO :loop
)

echo OUTPUT FILE DIRECTORY = %OUTPUTDIRECTORY%
echo OUTPUT FILE NAME = %OUTPUTFILENAME%
echo USER_NAME_octolapse = %USER_NAME_octolapse%
echo PASSWORD = %PASSWORD%
echo SNAPSHOTADDRESS = %SNAPSHOTADDRESS%
echo DEFAULT = %DEFAULT%

mkdir %OUTPUTDIRECTORY%
IF "%USER_NAME_octolapse%"=="" (
	bitsadmin /create snapshot
	bitsadmin /SetSecurityFlags snapshot 8
	bitsadmin /transfer snapshot %SNAPSHOTADDRESS% "%OUTPUTDIRECTORY%%OUTPUTFILENAME%"
	bitsadmin /complete snapshot
	goto commonexit
)
	bitsadmin /create snapshot
	bitsadmin /SetSecurityFlags snapshot 8
    bitsadmin /SetCredentials snapshot Server BASIC %USER_NAME_octolapse% %PASSWORD%
	bitsadmin /transfer snapshot %SNAPSHOTADDRESS% "%OUTPUTDIRECTORY%%OUTPUTFILENAME%"
	bitsadmin /complete snapshot



	
:commonexit





