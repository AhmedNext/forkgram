@echo off
title SoundTouch 10 Pure Speech Variations
cd /d "%~dp0"
echo ========================================================
echo   SoundTouch Tuning Lab: 10 Pure Speech Variations
echo ========================================================
echo.

set "INPUT_FILE=%~1"

rem If no file was dragged onto the bat, auto-detect in folder
if "%INPUT_FILE%"=="" (
    if exist "voice.mp3" (
        set "INPUT_FILE=voice.mp3"
        echo [*] Detected voice.mp3 in this folder. Using it automatically!
    ) else (
        for %%f in (*.mp3) do (
            if /i not "%%f"=="test_sample.mp3" (
                set "INPUT_FILE=%%f"
            )
        )
    )
)

rem Fallback to test_sample if no user file found
if "%INPUT_FILE%"=="" (
    if exist "test_sample.mp3" (
        set "INPUT_FILE=test_sample.mp3"
        echo [*] No personal recording found. Running with test_sample.mp3 demo!
    ) else (
        echo Drag and drop your MP3 onto this file,
        echo or enter the file path below:
        echo.
        set /p "INPUT_FILE=Enter MP3 Path: "
    )
)

echo.
echo [*] Processing voice file: %INPUT_FILE%
echo.
python test_variations.py "%INPUT_FILE%"
echo.
echo ========================================================
echo Launching comparison player in your web browser...
echo ========================================================
start "" "%~dp0output\compare_player.html"
start "" "%~dp0output"
timeout /t 3 >nul

