@echo off
title SoundTouch 10 Variations Lab
cd /d "%~dp0"
echo ========================================================
echo   SoundTouch Tuning Lab: 10 Variations Generator
echo ========================================================
echo.
if "%~1"=="" (
    echo Drag and drop an MP3 onto this batch file,
    echo or enter the full path to your MP3 file below:
    echo.
    set /p "INPUT_FILE=Enter MP3 Path: "
) else (
    set "INPUT_FILE=%~1"
)

python test_variations.py "%INPUT_FILE%"
echo.
echo ========================================================
echo Press any key to open the output folder and player...
echo ========================================================
pause >nul
start "" "%~dp0output\compare_player.html"
start "" "%~dp0output"
