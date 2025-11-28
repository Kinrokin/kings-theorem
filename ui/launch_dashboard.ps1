#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launch Ouroboros Dashboard - Full Stack
.DESCRIPTION
    Starts both FastAPI backend (port 8000) and React frontend (port 5173).
    Opens browser to dashboard automatically.
.EXAMPLE
    .\ui\launch_dashboard.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "🐍 OUROBOROS DASHBOARD - FULL STACK LAUNCHER" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if in repo root
if (-not (Test-Path "ui\frontend\package.json")) {
    Write-Host "❌ Error: Must run from repository root (kings-theorem-v53)" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Node.js not found. Install from: https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python not found. Install Python 3.10+" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location "ui\frontend"

if (-not (Test-Path "node_modules")) {
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ npm install failed" -ForegroundColor Red
        Set-Location "..\..\"
        exit 1
    }
}

Set-Location "..\..\"

Write-Host "✅ Frontend dependencies ready" -ForegroundColor Green
Write-Host ""

# Start backend in background
Write-Host "🚀 Starting FastAPI backend (port 8000)..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    uvicorn ui.api.server:app --reload --port 8000
}

Start-Sleep -Seconds 3

# Check if backend started
$backendRunning = $false
try {
    $null = Invoke-WebRequest -Uri "http://localhost:8000/api/tribunal_report" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    $backendRunning = $true
}
catch {
    # Expected if no data yet, but confirms server is up
    if ($_.Exception.Response.StatusCode -eq 404) {
        $backendRunning = $true
    }
}

if ($backendRunning) {
    Write-Host "✅ Backend running at http://localhost:8000" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Backend may still be starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎨 Starting React frontend (port 5173)..." -ForegroundColor Yellow
Set-Location "ui\frontend"

# Start frontend in background
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    Set-Location "ui\frontend"
    npm run dev
}

Start-Sleep -Seconds 5

Write-Host "✅ Frontend running at http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "🌐 DASHBOARD READY!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Dashboard:    http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers" -ForegroundColor Yellow
Write-Host ""

# Open browser
Start-Process "http://localhost:5173"

# Wait for user interrupt
try {
    Wait-Job -Job $backendJob, $frontendJob
}
finally {
    Write-Host ""
    Write-Host "🛑 Shutting down servers..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob, $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Shutdown complete" -ForegroundColor Green
}
