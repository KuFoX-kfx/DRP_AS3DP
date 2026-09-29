@echo off
REM Packages src\drp into dist\DRP_AS3DP-python.zip
REM
REM Usage:
REM   build\build.bat

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT_DIR=%%~fI"
set "SRC_DIR=%ROOT_DIR%\src\drp"
set "DIST_DIR=%ROOT_DIR%\dist"

set "ZIP_NAME=DRP_AS3DP-python.zip"

if not exist "%SRC_DIR%" (
    echo error: source folder not found at %SRC_DIR%
    exit /b 1
)

echo Building DRP_AS3DP-python...

if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
mkdir "%DIST_DIR%\staging"

xcopy "%SRC_DIR%" "%DIST_DIR%\staging\drp\" /e /i /q >nul

REM The author's own settings must never ship: a release zip is unpacked
REM on top of an existing install, so everyone would silently inherit the
REM author's language and intervals. The paths are inside staging\drp,
REM where xcopy put them.
del /q "%DIST_DIR%\staging\drp\settings.json" >nul 2>&1
del /q "%DIST_DIR%\staging\drp\settings.json.bak" >nul 2>&1

REM Strip caches / bytecode that shouldn't ship.
for /d /r "%DIST_DIR%\staging" %%D in (__pycache__) do (
    if exist "%%D" rmdir /s /q "%%D"
)
del /s /q "%DIST_DIR%\staging\*.pyc" >nul 2>&1

REM Zip via PowerShell's Compress-Archive - no extra tooling required
REM on Windows 10+.
powershell -NoProfile -Command ^
    "Compress-Archive -Path '%DIST_DIR%\staging\drp' -DestinationPath '%DIST_DIR%\%ZIP_NAME%' -Force"

rmdir /s /q "%DIST_DIR%\staging"

echo Done: dist\%ZIP_NAME%
echo Extract '%ZIP_NAME%' directly into your Painter python\plugins folder.

endlocal
