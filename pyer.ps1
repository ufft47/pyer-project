# pyer function (auto-activation when dot-sourced)
function pyer {
    python "$PSScriptRoot\pyer_gui.py" powershell $args
    $next = Join-Path $PSScriptRoot "pyer_next.ps1"
    if (Test-Path $next) {
        . $next
        Remove-Item $next
        Write-Host "Virtual environment activated!" -ForegroundColor Green
    }
}

# 直接執行時：開 GUI + 輸出啟動指令
python "$PSScriptRoot\pyer_gui.py" powershell $args
$next = Join-Path $PSScriptRoot "pyer_next.ps1"
if (Test-Path $next) {
    Write-Host "`n=== Pyer Auto-Activation ===" -ForegroundColor Green
    Get-Content $next -Raw | Write-Host
    Write-Host "=== Copy & paste the above command ===" -ForegroundColor Green
    Remove-Item $next
}
