# scripts/train_tiny.ps1

Write-Host "Launching Tiny SFT Training Loop..." -ForegroundColor Cyan

# 1) Setup Environment
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
$env:PYTHONPATH = (Get-Location).Path

# Prefer project venv Python if available
$Py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python.exe" }

# 2) Define Paths
$ModelName = "sshleifer/tiny-gpt2"
$DatasetPath = "logs/golden_dataset.jsonl"
$OutputDir = "models/sft-tiny-demo"

# 3) Check for Dataset (create minimal JSONL if missing)
if (-not (Test-Path $DatasetPath)) {
    Write-Warning "Dataset '$DatasetPath' not found. Creating a dummy one for the test..."
    New-Item -ItemType Directory -Force -Path (Split-Path $DatasetPath) | Out-Null
    # Create two JSONL lines with required schema: {"prompt": ..., "completion": ...}
    # Build two JSONL lines via ConvertTo-Json for robust quoting
    $rec1 = @{ prompt = '{"metadata":{"domain":"logic"}}'; completion = '{"status":"PASS_RIGOR","rationale":"Dummy rationale A"}' }
    $rec2 = @{ prompt = '{"metadata":{"domain":"ethics"}}'; completion = '{"status":"PASS_RIGOR","rationale":"Dummy rationale B"}' }
    $rec1 | ConvertTo-Json -Compress | Out-File $DatasetPath -Encoding utf8
    $rec2 | ConvertTo-Json -Compress | Out-File $DatasetPath -Encoding utf8 -Append
}

# 4) Run Training
Write-Host "Starting Trainer on $ModelName..." -ForegroundColor Yellow
try {
    & $Py scripts/train_sft.py `
        --model_name $ModelName `
        --dataset $DatasetPath `
        --output-dir $OutputDir `
        --epochs 1 `
        --batch-size 2 `
        --max-samples 10 `
        --val-ratio 0.2 `
        --no-cuda `
        --max-length 128

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Training Complete! Artifacts in $OutputDir" -ForegroundColor Green
        if (Test-Path "$OutputDir/metrics.json") {
            Write-Host "Metrics:" -ForegroundColor Cyan
            Get-Content "$OutputDir/metrics.json"
        }
    }
    else {
        Write-Error "Training Failed with exit code $LASTEXITCODE"
    }
}
catch {
    Write-Error "Execution Error: $_"
}
