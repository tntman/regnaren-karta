# Runs all browser tests against docs/ (build first: py -3 tools/build.py)
# Windows version of run_all.sh. Needs:
#   py -3 -m pip install --user playwright numpy pillow
#   py -3 -m playwright install chromium
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
# Playwright's own Chromium 115 fails to start on Filip's PC (side-by-side error),
# so use the installed Edge unless CHROMIUM is already set.
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not $env:CHROMIUM -and (Test-Path $edge)) { $env:CHROMIUM = $edge }
$srv = Start-Process py -ArgumentList '-3', '-m', 'http.server', '8899', '--directory', '..\docs' `
    -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 1
$fail = 0
try {
    foreach ($t in Get-ChildItem test_*.py | Sort-Object Name) {
        $out = (& py -3 $t.Name 2>&1 | ForEach-Object { "$_" } | Select-Object -Last 1)
        "{0,-24} {1}" -f $t.Name, $out
        if ($out -match '^(\d+)/(\d+) passed') {
            if ($Matches[1] -ne $Matches[2]) { $fail = 1 }
        } else { $fail = 1 }
    }
} finally {
    Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue
}
if ($fail) { 'NAGOT TEST MISSLYCKADES' } else { 'ALLA TESTER OK' }
exit $fail
