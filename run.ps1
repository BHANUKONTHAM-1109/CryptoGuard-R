# CryptoGuard-R - Startup Script for Windows PowerShell
# Run from project root: .\run.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Activate virtual environment if exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
} elseif (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
}

# Load .env if exists
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

# Run FastAPI with uvicorn
Set-Location backend
$AppHost = if ($env:HOST) { $env:HOST } else { "0.0.0.0" }
$Port = if ($env:PORT) { $env:PORT } else { "8000" }
uvicorn app.main:app --host $Host --port $Port --reload
