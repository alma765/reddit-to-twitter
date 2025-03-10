@echo off
REM Setup script for Reddit to Twitter Video Reposter (Windows)

echo Setting up Reddit to Twitter Video Reposter...

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is required but not installed.
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to create virtual environment.
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment.
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install dependencies.
    exit /b 1
)

REM Create config.json if it doesn't exist
if not exist config.json (
    echo Creating config.json from template...
    copy config.json.template config.json
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to create config.json.
        exit /b 1
    )
    echo Please edit config.json with your Reddit and Twitter API credentials.
)

REM Create downloads directory
echo Creating downloads directory...
if not exist downloads mkdir downloads

echo.
echo Setup completed successfully!
echo.
echo Next steps:
echo 1. Edit config.json with your Reddit and Twitter API credentials
echo 2. Run the script with: python reddit_to_twitter.py
echo.
echo For more information, see README.md