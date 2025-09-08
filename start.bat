@echo off
REM Modern sese-engine startup script for Windows

setlocal enabledelayedexpansion

REM Configuration
set PYTHONPATH=%PYTHONPATH%;%CD%\src
set SESE_STORAGE_PATH=%SESE_STORAGE_PATH%:".\\savedata"
set SESE_PORT=%SESE_PORT%:8080
set SESE_HOST=%SESE_HOST%:0.0.0.0

echo Starting sese-engine...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import fastapi, uvicorn, jieba, lxml, brotli" >nul 2>&1
if %errorlevel% neq 0 (
    echo Dependencies not found. Installing...
    pip install -e .
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies. Please run: pip install -e .
        pause
        exit /b 1
    )
)

REM Create necessary directories
echo Creating directories...
if not exist "%SESE_STORAGE_PATH%" mkdir "%SESE_STORAGE_PATH%"
if not exist ".\data" mkdir ".\data"
if not exist ".\logs" mkdir ".\logs"

REM Start components
echo Starting API server...
start "sese-engine API" cmd /k python -m src.api.main

echo Starting crawler...
start "sese-engine Crawler" cmd /k "echo Starting crawler... && :loop && python -m src.crawler.main && timeout /t 1 >nul && goto loop"

echo Starting indexer...
start "sese-engine Indexer" cmd /k "echo Starting indexer... && :loop && python -m src.indexer.main && timeout /t 1 >nul && goto loop"

echo Starting metrics...
start "sese-engine Metrics" cmd /k python -m src.metrics.main

echo.
echo sese-engine started successfully!
echo API server: http://%SESE_HOST%:%SESE_PORT%
echo.
echo Press any key to stop all components...
pause >nul

REM Stop all components
echo Stopping sese-engine...
taskkill /FI "WINDOWTITLE eq sese-engine*" /F >nul 2>&1
taskkill /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq sese-engine*" /F >nul 2>&1

echo sese-engine stopped.
pause