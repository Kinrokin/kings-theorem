# King's Theorem - Quick Launch Script
# Run this after setting OPENROUTER_API_KEY

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host " KING'S THEOREM v53 - COUNCIL EDITION" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host ""

# Check Python environment
Write-Host "[1/5] Checking Python environment..." -ForegroundColor Yellow
$pythonCmd = ".\.venv\Scripts\python.exe"

if (!(Test-Path $pythonCmd)) {
    Write-Host "  ERROR: Virtual environment not found at .venv" -ForegroundColor Red
    Write-Host "  Run: python -m venv .venv" -ForegroundColor Gray
    exit 1
}

Write-Host "  Python: " -NoNewline
& $pythonCmd --version
Write-Host ""

# Check API key
Write-Host "[2/5] Checking OpenRouter API key..." -ForegroundColor Yellow

if (!$env:OPENROUTER_API_KEY) {
    Write-Host "  WARNING: OPENROUTER_API_KEY not set" -ForegroundColor Yellow
    Write-Host "  Council Router will not work without it." -ForegroundColor Gray
    Write-Host ""
    Write-Host "  To set (PowerShell):" -ForegroundColor Cyan
    Write-Host '    $env:OPENROUTER_API_KEY = "your-key-here"' -ForegroundColor Gray
    Write-Host ""
    $continue = Read-Host "  Continue anyway? (y/N)"
    if ($continue -ne "y") {
        exit 0
    }
}
else {
    $keyPreview = $env:OPENROUTER_API_KEY.Substring(0, [Math]::Min(10, $env:OPENROUTER_API_KEY.Length))
    Write-Host "  API Key: $keyPreview..." -ForegroundColor Green
}
Write-Host ""

# Check Ollama
Write-Host "[3/5] Checking Ollama status..." -ForegroundColor Yellow

try {
    $ollamaCheck = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "  Ollama: Online" -ForegroundColor Green
    
    # Check for Qwen models
    $models = ($ollamaCheck.Content | ConvertFrom-Json).models
    $hasQwen2 = $models | Where-Object { $_.name -like "*qwen2*" }
    $hasQwen3 = $models | Where-Object { $_.name -like "*qwen3*" }
    
    if ($hasQwen3) {
        Write-Host "  Model: Qwen 3 8B installed" -ForegroundColor Green
    }
    elseif ($hasQwen2) {
        Write-Host "  Model: Qwen 2.5 installed (consider upgrading to Qwen 3)" -ForegroundColor Yellow
    }
    else {
        Write-Host "  WARNING: No Qwen models found" -ForegroundColor Yellow
        Write-Host "  Run: ollama pull qwen3:8b" -ForegroundColor Gray
    }
    
}
catch {
    Write-Host "  Ollama: Offline or not running" -ForegroundColor Red
    Write-Host "  Start: docker-compose up -d (or 'ollama serve')" -ForegroundColor Gray
}
Write-Host ""

# Prompt for action
Write-Host "[4/5] What would you like to do?" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Quick Council Demo (test all 4 specialist roles)" -ForegroundColor Cyan
Write-Host "  2. Launch Control Tower UI with chat interface" -ForegroundColor Cyan
Write-Host "  3. Generate Council-powered curriculum (10 steps)" -ForegroundColor Cyan
Write-Host "  4. Verify Qwen 3 8B installation" -ForegroundColor Cyan
Write-Host "  5. Exit" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "  Enter choice (1-5)"

Write-Host ""
Write-Host "[5/5] Executing..." -ForegroundColor Yellow
Write-Host ""

switch ($choice) {
    "1" {
        Write-Host "Running Council quick demo..." -ForegroundColor Green
        Write-Host ""
        & $pythonCmd scripts\demo_council.py --mode quick
    }
    
    "2" {
        Write-Host "Launching Control Tower on http://localhost:8080..." -ForegroundColor Green
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
        Write-Host ""
        & $pythonCmd scripts\control_tower.py
    }
    
    "3" {
        Write-Host "Generating Council-powered curriculum (10 steps)..." -ForegroundColor Green
        Write-Host "This will take 5-10 minutes depending on OpenRouter speed" -ForegroundColor Gray
        Write-Host ""
        & $pythonCmd scripts\run_curriculum.py --use-council --steps 10
        
        Write-Host ""
        Write-Host "Done! Check logs/golden_dataset.jsonl" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next: Audit the data" -ForegroundColor Cyan
        Write-Host "  python scripts\audit_sft.py" -ForegroundColor Gray
    }
    
    "4" {
        Write-Host "Verifying Qwen 3 8B installation..." -ForegroundColor Green
        Write-Host ""
        & $pythonCmd scripts\verify_qwen3.py
    }
    
    "5" {
        Write-Host "Exiting..." -ForegroundColor Gray
        exit 0
    }
    
    default {
        Write-Host "  Invalid choice. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host " Complete! See docs/UPGRADE_SUMMARY_2025-11-28.md for full guide" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
