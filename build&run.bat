@echo off
setlocal
SET "PROJECT_NAME=smx_sound_creator"

ECHO =======================================
ECHO  STEP 1: SETTING UP VIRTUAL ENVIRONMENT
ECHO =======================================
ECHO.

IF NOT EXIST "venv" (
    ECHO Virtual environment not found. Creating it now...
    python -m venv venv
    IF ERRORLEVEL 1 (
        ECHO #############################################################
        ECHO #  ERROR: FAILED to create virtual environment.             #
        ECHO #  Make sure Python 3 is installed and added to your PATH.  #
        ECHO #############################################################
        ECHO.
        pause
        exit /b 1
    )
)

ECHO Activating environment and installing required packages...
CALL "venv\Scripts\activate.bat"
pip install -r requirements.txt --quiet
IF ERRORLEVEL 1 (
    ECHO #############################################################
    ECHO #  ERROR: FAILED to install packages from requirements.txt  #
    ECHO #############################################################
    ECHO.
    pause
    exit /b 1
)
ECHO Packages are installed and up to date.
ECHO.

ECHO =======================================
ECHO  STEP 2: CLEANING & BUILDING
ECHO =======================================
ECHO.
ECHO Cleaning up previous builds...
IF EXIST "dist" rmdir /s /q "dist"
IF EXIST "build" rmdir /s /q "build"
taskkill /F /IM %PROJECT_NAME%.exe 2>nul
ECHO.

ECHO Building %PROJECT_NAME%...
venv\Scripts\python.exe -m PyInstaller --noconfirm %PROJECT_NAME%.spec
IF ERRORLEVEL 1 GOTO build_failed

ECHO.
ECHO =======================================
ECHO  STEP 3: LAUNCHING APPLICATION
ECHO =======================================
ECHO.

del "dist\%PROJECT_NAME%.exe"
start "" "dist\%PROJECT_NAME%\%PROJECT_NAME%.exe"
exit /b 0

:build_failed
ECHO #############################################################
ECHO #                   BUILD FAILED!                           #
ECHO #  An error occurred during the PyInstaller build process.  #
ECHO #  Please review the messages above.                        #
ECHO #############################################################
ECHO.
pause
exit /b 1