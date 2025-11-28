# Monitor Council Dataset Generation Progress
# Run this in a separate terminal while curriculum generation is running

param(
    [int]$RefreshSeconds = 10,
    [int]$TargetCount = 50
)

$datasetPath = "logs\golden_dataset.jsonl"

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host " COUNCIL DATASET GENERATION - LIVE MONITOR" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

$lastCount = 0
$startTime = Get-Date

while ($true) {
    Clear-Host
    
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host " COUNCIL GOLDEN DATASET - LIVE MONITOR" -ForegroundColor Cyan
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-Path $datasetPath) {
        $currentCount = (Get-Content $datasetPath | Measure-Object -Line).Lines
        $progress = [math]::Round(($currentCount / $TargetCount) * 100, 1)
        $newEntries = $currentCount - $lastCount
        
        # Time calculations
        $elapsed = (Get-Date) - $startTime
        $avgTimePerEntry = if ($currentCount -gt 0) { $elapsed.TotalSeconds / $currentCount } else { 0 }
        $remaining = ($TargetCount - $currentCount) * $avgTimePerEntry
        $eta = (Get-Date).AddSeconds($remaining)
        
        Write-Host "Progress:        " -NoNewline -ForegroundColor White
        Write-Host "$currentCount / $TargetCount entries" -ForegroundColor Yellow
        Write-Host "                 " -NoNewline
        Write-Host ("[" + ("=" * [math]::Floor($progress / 2)) + (" " * (50 - [math]::Floor($progress / 2))) + "]") -ForegroundColor Green
        Write-Host "                 $progress% complete`n" -ForegroundColor Gray
        
        Write-Host "New this cycle:  " -NoNewline -ForegroundColor White
        Write-Host "$newEntries entries" -ForegroundColor $(if ($newEntries -gt 0) { "Green" } else { "Gray" })
        
        Write-Host "Avg time/entry:  " -NoNewline -ForegroundColor White
        Write-Host "$([math]::Round($avgTimePerEntry, 1)) seconds" -ForegroundColor Cyan
        
        Write-Host "Time elapsed:    " -NoNewline -ForegroundColor White
        Write-Host "$($elapsed.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan
        
        if ($currentCount -lt $TargetCount) {
            Write-Host "ETA:             " -NoNewline -ForegroundColor White
            Write-Host "$($eta.ToString('HH:mm:ss'))" -ForegroundColor Yellow
        }
        else {
            Write-Host "`n" -NoNewline
            Write-Host "GENERATION COMPLETE!" -ForegroundColor Green
            Write-Host ""
            break
        }
        
        Write-Host ""
        Write-Host "Last Entry Preview:" -ForegroundColor White
        Write-Host "-" * 70 -ForegroundColor Gray
        
        $lastEntry = Get-Content $datasetPath -Tail 1 | ConvertFrom-Json
        $prompt = ($lastEntry.prompt | ConvertFrom-Json)
        $completion = ($lastEntry.completion | ConvertFrom-Json)
        
        Write-Host "Domain:   " -NoNewline -ForegroundColor Gray
        Write-Host $prompt.metadata.domain -ForegroundColor Cyan
        
        Write-Host "Status:   " -NoNewline -ForegroundColor Gray
        $statusColor = switch ($completion.status) {
            "PASS_RIGOR" { "Green" }
            "SALVAGEABLE" { "Yellow" }
            "VETOED" { "Red" }
            default { "White" }
        }
        Write-Host $completion.status -ForegroundColor $statusColor
        
        if ($completion.artifacts.trace.outputs.model_role) {
            Write-Host "Model:    " -NoNewline -ForegroundColor Gray
            Write-Host $completion.artifacts.trace.outputs.model_role -ForegroundColor Magenta
        }
        
        Write-Host "Coherence:" -NoNewline -ForegroundColor Gray
        Write-Host " $($completion.metrics.coherence)" -ForegroundColor Cyan
        
        $lastCount = $currentCount
        
    }
    else {
        Write-Host "Waiting for dataset file to be created..." -ForegroundColor Yellow
        Write-Host "Dataset path: $datasetPath" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Gray
    Write-Host "Refreshing in $RefreshSeconds seconds... (Ctrl+C to stop)" -ForegroundColor Gray
    
    Start-Sleep -Seconds $RefreshSeconds
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Audit: python scripts\audit_sft.py" -ForegroundColor White
Write-Host "  2. Train: python scripts\train_sft.py --model qwen3:8b-instruct" -ForegroundColor White
Write-Host ""
