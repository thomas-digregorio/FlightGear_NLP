@echo off
REM Alternative FlightGear startup with different telnet format
echo Starting FlightGear with telnet (alternative format)...

cd /d "C:\Program Files\FlightGear\bin"

REM Try different telnet formats
REM Format 1: Standard
REM fgfs.exe --telnet=5500 --httpd=8080

REM Format 2: Socket format (some versions need this)
fgfs.exe --telnet=socket,bi,localhost,5500 --httpd=8080

pause

