python "$PSScriptRoot\pyer_gui.py" $args
$next = Join-Path $PSScriptRoot "pyer_next.ps1"
if (Test-Path $next) {
    . $next
    Remove-Item $next
}
