# pyer.ps1 — 自動 dot-source 自己，讓啟動指令在當前作用域生效
if ($MyInvocation.InvocationName -ne '.') {
    Write-Host "[pyer] Loading function..." -ForegroundColor Cyan
    . $MyInvocation.MyCommand.Path
    return
}

# 定義 pyer 函式（供後續使用）
function pyer {
    Write-Host "[pyer] Launching GUI..." -ForegroundColor Cyan
    python "$PSScriptRoot\pyer_gui.py" powershell $args
    $next = Join-Path $PSScriptRoot "pyer_next.ps1"
    if (Test-Path $next) {
        Write-Host "[pyer] Found activation script, running..." -ForegroundColor Cyan
        Get-Content $next -Raw | Write-Host
        . $next
        Remove-Item $next
        Write-Host "[pyer] Virtual environment activated!" -ForegroundColor Green
    } else {
        Write-Host "[pyer] No activation script found" -ForegroundColor Yellow
    }
}

# 立即執行
pyer
