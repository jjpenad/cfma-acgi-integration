@echo off
REM Background Export Runner - Batch File Version
REM Usage: run_export_background.bat [script_name] [csv_file] [output_file]

setlocal enabledelayedexpansion

REM Check arguments
if "%~1"=="" (
    echo Usage: run_export_background.bat [script_name] [csv_file] [output_file]
    echo Example: run_export_background.bat export_event_registrations.py contacts_export.csv
    exit /b 1
)

if "%~2"=="" (
    echo Usage: run_export_background.bat [script_name] [csv_file] [output_file]
    echo Example: run_export_background.bat export_event_registrations.py contacts_export.csv
    exit /b 1
)

set SCRIPT_NAME=%~1
set CSV_FILE=%~2
set OUTPUT_FILE=%~3
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOG_FILE=%SCRIPT_NAME%_background_%TIMESTAMP%.log

REM Change to script directory
cd /d "%~dp0"

REM Check if script exists
if not exist "%SCRIPT_NAME%" (
    echo Error: Script '%SCRIPT_NAME%' not found!
    exit /b 1
)

REM Check if CSV file exists
if not exist "%CSV_FILE%" (
    echo Error: CSV file '%CSV_FILE%' not found!
    exit /b 1
)

echo Starting %SCRIPT_NAME% in background...
echo Command: python %SCRIPT_NAME% %CSV_FILE% %OUTPUT_FILE%
echo Log file: %LOG_FILE%
echo Started at: %date% %time%
echo ------------------------------------------------------------

REM Build command
set CMD=python %SCRIPT_NAME% %CSV_FILE%
if not "%OUTPUT_FILE%"=="" (
    set CMD=%CMD% --output %OUTPUT_FILE%
)

REM Run in background with logging
start /B %CMD% > %LOG_FILE% 2>&1

echo Process started in background!
echo Check progress with: type %LOG_FILE%
echo Follow log with: Get-Content %LOG_FILE% -Wait
echo Check if running with: tasklist ^| findstr python
echo.
echo Log file: %LOG_FILE%
echo Output file: %OUTPUT_FILE%

endlocal
