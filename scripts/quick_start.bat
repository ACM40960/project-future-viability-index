@echo off
echo.
echo ==========================================
echo   FVI System - Quick Start (Windows)
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.11+ and try again.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Navigate to project directory
cd /d "%~dp0\.."

REM Check if virtual environment exists
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment found
)

echo.
echo 🔄 Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo 📥 Installing/updating dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

echo.
echo 🔍 Verifying installation...
python -c "import streamlit, fastapi, pandas, numpy; print('✅ All packages verified!')" 2>nul
if errorlevel 1 (
    echo ❌ Some packages failed to install. Please check for errors.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   🎯 Starting FVI System...
echo ==========================================
echo 📡 Backend: http://localhost:8089
echo 🌐 Frontend: http://localhost:8502
echo.

REM Start backend in new window
echo 🚀 Starting backend API...
start "FVI Backend API" cmd /k "cd /d "%CD%" && .venv\Scripts\activate.bat && echo 🔧 Backend API Server && python backend\main.py --port 8089"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo 🚀 Starting frontend interface...
start "FVI Frontend" cmd /k "cd /d "%CD%" && .venv\Scripts\activate.bat && echo 🌐 Frontend Interface && streamlit run main.py --server.port 8502"

REM Wait for services to start
echo ⏳ Waiting for services to start...
timeout /t 5 /nobreak >nul

REM Try to open browser
echo 🌐 Opening browser...
start http://localhost:8502

echo.
echo ✅ FVI System is now running!
echo ==========================================
echo 🌐 Frontend: http://localhost:8502
echo 🔧 API Docs: http://localhost:8089/docs
echo.
echo 📋 To stop the system:
echo    - Close the command windows
echo    - Or press Ctrl+C in each window
echo.
pause
