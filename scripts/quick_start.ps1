#!/usr/bin/env pwsh

# FVI System Quick Start Script
# This script automatically sets up and starts the FVI system

Write-Host "🚀 FVI System Quick Start" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Check if Python is installed
Write-Host "📋 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.11+ and try again." -ForegroundColor Red
    exit 1
}

# Navigate to project directory
Set-Location $PSScriptRoot\..
$projectDir = Get-Location

Write-Host "📁 Project directory: $projectDir" -ForegroundColor Cyan

# Check if virtual environment exists
if (Test-Path ".venv") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Install/update dependencies
Write-Host "📥 Installing/updating dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

# Check if installation was successful
Write-Host "🔍 Verifying installation..." -ForegroundColor Yellow
try {
    python -c "import streamlit, fastapi, pandas, numpy, faiss; print('✅ All packages verified!')"
    Write-Host "✅ All dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Some packages failed to install. Please check the error messages above." -ForegroundColor Red
    exit 1
}

# Start the application
Write-Host "`n🎯 Starting FVI System..." -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "📡 Backend will start on: http://localhost:8089" -ForegroundColor Cyan
Write-Host "🌐 Frontend will open at: http://localhost:8502" -ForegroundColor Cyan
Write-Host "`n🔄 Starting services (this may take a moment)..." -ForegroundColor Yellow

# Start backend in a new terminal
Write-Host "🚀 Starting backend API..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectDir'; .venv\Scripts\Activate.ps1; Write-Host '🔧 Backend API Server' -ForegroundColor Green; python backend\main.py --port 8089"

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend in another new terminal
Write-Host "🚀 Starting frontend interface..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectDir'; .venv\Scripts\Activate.ps1; Write-Host '🌐 Frontend Interface' -ForegroundColor Blue; streamlit run main.py --server.port 8502 --server.headless false"

# Wait for services to fully start
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Try to open browser
Write-Host "🌐 Opening browser..." -ForegroundColor Yellow
try {
    Start-Process "http://localhost:8502"
} catch {
    Write-Host "⚠️  Could not open browser automatically. Please visit: http://localhost:8502" -ForegroundColor Yellow
}

Write-Host "`n✅ FVI System is now running!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "🌐 Frontend: http://localhost:8502" -ForegroundColor Cyan
Write-Host "🔧 API Docs: http://localhost:8089/docs" -ForegroundColor Cyan
Write-Host "`n📋 To stop the system:" -ForegroundColor Yellow
Write-Host "   - Close the terminal windows" -ForegroundColor Gray
Write-Host "   - Or press Ctrl+C in each terminal" -ForegroundColor Gray
Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
