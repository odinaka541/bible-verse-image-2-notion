@echo off
REM youversion to notion sync - windows setup script

echo ==================================================
echo YouVersion to Notion Sync Setup
echo ==================================================
echo.

REM check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

echo Python found!
python --version

REM create virtual environment
echo.
echo Setting up virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM install dependencies
echo.
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM create .env file if it doesnt exist
if not exist .env (
    echo.
    echo Creating .env file...
    copy .env.template .env
    echo WARNING: Please edit .env and add your Notion credentials!
    echo          NOTION_TOKEN and NOTION_PAGE_ID are required.
) else (
    echo.
    echo .env file already exists
)

echo.
echo ==================================================
echo Setup Complete!
echo ==================================================
echo.
echo Next steps:
echo 1. Edit .env file with your Notion credentials
echo 2. Run: python test_sync.py (to test)
echo 3. Run: python youversion_sync_enhanced.py (for real sync)
echo 4. Set up automation (see README.md)
echo.
echo Need help? Check README.md for detailed instructions.
echo.

pause
