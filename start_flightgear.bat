@echo off
REM FlightGear Startup Script for Windows
REM This script attempts to find and start FlightGear with telnet enabled

echo Searching for FlightGear...

REM Common installation paths
set FG_PATHS[0]=C:\Program Files\FlightGear\bin\fgfs.exe
set FG_PATHS[1]=C:\Program Files (x86)\FlightGear\bin\fgfs.exe
set FG_PATHS[2]=C:\FlightGear\bin\fgfs.exe

REM Try to find FlightGear
set FOUND=0

REM Check each path
if exist "C:\Program Files\FlightGear\bin\fgfs.exe" (
    echo Found FlightGear at: C:\Program Files\FlightGear\bin\fgfs.exe
    echo Starting FlightGear with HTTP interface and autostart...
    cd /d "C:\Program Files\FlightGear\bin"
    start "" fgfs.exe --httpd=8080 --aircraft=c172p --autostart
    set FOUND=1
    goto :found
)

if exist "C:\Program Files (x86)\FlightGear\bin\fgfs.exe" (
    echo Found FlightGear at: C:\Program Files (x86)\FlightGear\bin\fgfs.exe
    echo Starting FlightGear with HTTP interface and autostart...
    cd /d "C:\Program Files (x86)\FlightGear\bin"
    start "" fgfs.exe --httpd=8080 --aircraft=c172p --autostart
    set FOUND=1
    goto :found
)

if exist "C:\FlightGear\bin\fgfs.exe" (
    echo Found FlightGear at: C:\FlightGear\bin\fgfs.exe
    echo Starting FlightGear with HTTP interface and autostart...
    cd /d "C:\FlightGear\bin"
    start "" fgfs.exe --httpd=8080 --aircraft=c172p --autostart
    set FOUND=1
    goto :found
)

if %FOUND%==0 (
    echo.
    echo ERROR: FlightGear not found in common locations.
    echo.
    echo Please either:
    echo 1. Install FlightGear from https://www.flightgear.org/download/
    echo 2. Or edit this script and add the path to your FlightGear installation
    echo.
    echo You can also start FlightGear manually with:
    echo "C:\Path\To\FlightGear\bin\fgfs.exe" --telnet=5500 --httpd=8080
    pause
    exit /b 1
)

:found
echo.
echo FlightGear should now be starting...
echo Once it's loaded, you can run: python main.py
echo.
pause

