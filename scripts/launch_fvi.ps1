# FVI System PowerShell Launcher
# This script sets up and launches the Future Viability Index system

param(
    [switch]$Help,
    [int]$BackendPort = 8089,
    [int]$FrontendPort = 8502
)

if ($Help) {
    Write-Host @"
FVI System Launcher

USAGE:
    .\launch_fvi.ps1 [-BackendPort <port>] [-FrontendPort <port>] [-Help]

OPTIONS:
    -BackendPort    Port for the FastAPI backend (default: 8089)
    -FrontendPort   Port for the Streamlit frontend (default: 8502)
    -Help           Show this help message

EXAMPLES:
    .\launch_fvi.ps1                           # Use default ports
    .\launch_fvi.ps1 -BackendPort 8090         # Custom backend port
    .\launch_fvi.ps1 -FrontendPort 8503        # Custom frontend port
"@
    exit 0
}

# Clear screen and show header
Clear-Host
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "     FVI System - Future Viability Index Setup and Launcher" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Set working directory to script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[INFO] Starting FVI System setup..." -ForegroundColor Green
Write-Host "[INFO] Working directory: $(Get-Location)" -ForegroundColor Green
Write-Host ""

# Function to check if a command exists
function Test-Command($Command) {
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Check Python installation
Write-Host "[1/9] Checking Python..." -ForegroundColor Yellow
if (-not (Test-Command "python")) {
    Write-Host "[ERROR] Python not found! Please install Python 3.8+ from python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "[OK] $pythonVersion detected" -ForegroundColor Green
Write-Host ""

# Check Python version
$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $majorVersion = [int]$Matches[1]
    $minorVersion = [int]$Matches[2]
    if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 8)) {
        Write-Host "[ERROR] Python 3.8+ is required. Current version: $pythonVersion" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Install dependencies
Write-Host "[2/9] Installing dependencies..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip --quiet
    if (Test-Path "requirements.txt") {
        python -m pip install -r requirements.txt --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARNING] Some packages failed. Installing essentials..." -ForegroundColor Yellow
            python -m pip install streamlit fastapi uvicorn pandas numpy pyyaml python-dotenv requests --quiet
        }
    } else {
        Write-Host "[WARNING] requirements.txt not found. Installing essential packages..." -ForegroundColor Yellow
        python -m pip install streamlit fastapi uvicorn pandas numpy pyyaml python-dotenv requests --quiet
    }
    Write-Host "[OK] Dependencies ready" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to install dependencies: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Create directories
Write-Host "[3/9] Setting up directories..." -ForegroundColor Yellow
$directories = @("data", "logs", "vectorstore", "assets")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Name $dir | Out-Null
    }
}
Write-Host "[OK] Directories ready" -ForegroundColor Green
Write-Host ""

# Create config.yaml if missing
Write-Host "[4/9] Checking configuration..." -ForegroundColor Yellow
if (-not (Test-Path "config.yaml")) {
    Write-Host "[INFO] Creating default config.yaml..." -ForegroundColor Cyan
    $configContent = @"
# FVI System Configuration
persona_weights:
  analyst:
    infrastructure: 0.143
    necessity: 0.143
    resource: 0.143
    artificial_support: 0.143
    ecological: 0.143
    economic: 0.143
    emissions: 0.143
  investor:
    economic: 0.25
    artificial_support: 0.20
    emissions: 0.20
    infrastructure: 0.15
    resource: 0.10
    ecological: 0.05
    necessity: 0.05
  policy_maker:
    necessity: 0.20
    economic: 0.20
    emissions: 0.20
    infrastructure: 0.15
    ecological: 0.15
    artificial_support: 0.05
    resource: 0.05
  ngo:
    emissions: 0.25
    ecological: 0.25
    necessity: 0.20
    infrastructure: 0.10
    resource: 0.10
    artificial_support: 0.05
    economic: 0.05
  citizen:
    necessity: 0.25
    ecological: 0.20
    infrastructure: 0.20
    economic: 0.15
    emissions: 0.10
    artificial_support: 0.05
    resource: 0.05
data_dir: "data"
vectorstore_dir: "vectorstore"
"@
    $configContent | Out-File -FilePath "config.yaml" -Encoding UTF8
}
Write-Host "[OK] Configuration ready" -ForegroundColor Green
Write-Host ""

# Create .env if missing
Write-Host "[5/9] Setting up environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "[INFO] Creating .env file..." -ForegroundColor Cyan
    $envContent = @"
# FVI System Environment Variables
DEBUG=True
ENVIRONMENT=development
API_HOST=127.0.0.1
API_PORT=$BackendPort
FRONTEND_PORT=$FrontendPort

# Add your API keys below if using external LLM services
# OPENAI_API_KEY=your_openai_api_key_here
# GEMINI_API_KEY=your_gemini_api_key_here
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
}
Write-Host "[OK] Environment ready" -ForegroundColor Green
Write-Host ""

# Verify main files
Write-Host "[6/9] Verifying application files..." -ForegroundColor Yellow
if (-not (Test-Path "main.py")) {
    Write-Host "[ERROR] main.py not found! Please ensure you're in the correct directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
if (-not (Test-Path "backend\main.py")) {
    Write-Host "[ERROR] backend\main.py not found! Please ensure backend files are present." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Application files verified" -ForegroundColor Green
Write-Host ""

# Clean up existing processes
Write-Host "[7/9] Cleaning up existing processes..." -ForegroundColor Yellow
try {
    Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
} catch {
    # Ignore errors if no processes to kill
}
Write-Host "[OK] Cleanup completed" -ForegroundColor Green
Write-Host ""

# Start backend
Write-Host "[8/9] Starting backend API..." -ForegroundColor Yellow
try {
    $backendJob = Start-Job -ScriptBlock {
        param($BackendPort, $ScriptDir)
        Set-Location $ScriptDir
        Set-Location "backend"
        python main.py --port $BackendPort
    } -ArgumentList $BackendPort, $ScriptDir
    
    Start-Sleep -Seconds 3
    Write-Host "[OK] Backend starting on http://localhost:$BackendPort" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to start backend: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Start frontend
Write-Host "[9/9] Starting frontend UI..." -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "     FVI SYSTEM IS STARTING" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Opening FVI System in your browser..." -ForegroundColor Green
Write-Host "[INFO] Frontend URL: http://localhost:$FrontendPort" -ForegroundColor Green
Write-Host "[INFO] Backend API: http://localhost:$BackendPort" -ForegroundColor Green
Write-Host ""
Write-Host "Keep this window open while using the application." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the system." -ForegroundColor Yellow
Write-Host ""

try {
    # Start Streamlit
    python -m streamlit run main.py --server.port $FrontendPort --server.headless false
} catch {
    Write-Host "[ERROR] Failed to start frontend: $_" -ForegroundColor Red
} finally {
    # Cleanup when stopped
    Write-Host ""
    Write-Host "[INFO] Shutting down FVI System..." -ForegroundColor Yellow
    
    # Stop the backend job
    if ($backendJob) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job $backendJob -ErrorAction SilentlyContinue
    }
    
    # Kill any remaining Python processes
    Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
    
    Write-Host "[INFO] System stopped. Thank you for using FVI System!" -ForegroundColor Green
    Read-Host "Press Enter to exit"
}
