@echo off
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║     🛰️  DisasterAI Backend Setup Script  🛰️                    ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install dependencies
echo 📦 Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt --quiet

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                    ✅ Setup Complete!                         ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
echo Next steps:
echo   1. Edit .env and add your GEMINI_API_KEY
echo   2. Run the server with: python run.py
echo   3. Visit http://localhost:8000/docs for API documentation
echo.

pause
