python "$PSScriptRoot\pyer_gui.py" $args
$next = Join-Path $PSScriptRoot "pyer_next.ps1"
if (Test-Path $next) {
    Write-Host "" -ForegroundColor Green
    Write-Host "=== Pyer Auto-Activation ===" -ForegroundColor Green
    Get-Content $next -Raw | Write-Host
    Write-Host "=== Copy the above command ===" -ForegroundColor Green
    Remove-Item $next
}
