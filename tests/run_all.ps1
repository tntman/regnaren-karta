# Runs all browser tests against docs/ (build first: py -3 tools/build.py)
# Windows version of run_all.sh. Needs:
#   py -3 -m pip install --user playwright numpy pillow scipy
#   py -3 -m playwright install chromium
# The tests run side by side (each has its own browser): 6 at a time, or
# $env:TEST_JOBS (1 = one after the other, like before).
# Only some: name them, e.g.  run_all.ps1 heatmap filter  (= test_*heatmap*.py, test_*filter*.py).
# Small changes: the area's tests + the ones that mention what changed; bigger ones (or Filip asks): ALL.
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'
# Playwright's own Chromium 115 fails to start on Filip's PC (side-by-side error),
# so use the installed Edge unless CHROMIUM is already set.
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not $env:CHROMIUM -and (Test-Path $edge)) { $env:CHROMIUM = $edge }
$jobs = 6; if ($env:TEST_JOBS) { $jobs = [int]$env:TEST_JOBS }
$port = 8899; if ($env:TEST_PORT) { $port = [int]$env:TEST_PORT }   # (TEST_PORT: another chat's tests can run at the same time -- fakefb.py follows it)
$env:TEST_PORT = "$port"
function PortUp { try { $c = [Net.Sockets.TcpClient]::new(); $c.Connect('127.0.0.1', $port); $c.Close(); $true } catch { $false } }
# py.exe (the launcher) starts python.exe as a child: stop the whole tree, or the server stays behind
function StopTree($id) { & taskkill /PID $id /T /F 2>&1 | Out-Null }
if (PortUp) { "Port $port var redan upptagen (en gammal testserver, eller en annan chatts tester - satt TEST_PORT) - stang den forst"; exit 1 }
$srv = Start-Process py -ArgumentList '-3', 'serve.py', "$port", '..\docs' `
    -WindowStyle Hidden -PassThru
$w = 0; while (-not (PortUp) -and $w -lt 100) { Start-Sleep -Milliseconds 100; $w++ }   # (up to 10 s; ~1,2 s normally)
if (-not (PortUp)) { 'Testservern startade inte'; StopTree $srv.Id; exit 1 }
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('ffmap_tests_' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory $tmp | Out-Null
$files = if ($args.Count) { $args | ForEach-Object { Get-ChildItem "test_*$_*.py" } } else { Get-ChildItem test_*.py }
$queue = [System.Collections.Queue]::new(); $files | Sort-Object Name -Unique | ForEach-Object { $queue.Enqueue($_.Name) }
if (-not $queue.Count) { 'Inga tester matchar: ' + ($args -join ' '); StopTree $srv.Id; exit 1 }
$running = @(); $done = @{}; $t0 = Get-Date
try {
    while ($queue.Count -or $running.Count) {
        while ($queue.Count -and $running.Count -lt $jobs) {
            $n = $queue.Dequeue()
            $p = Start-Process py -ArgumentList '-3', $n -NoNewWindow -PassThru `
                -RedirectStandardOutput (Join-Path $tmp "$n.out") -RedirectStandardError (Join-Path $tmp "$n.err")
            $running += [pscustomobject]@{ Name = $n; Proc = $p; T = Get-Date }
        }
        Start-Sleep -Milliseconds 300
        $still = @()
        foreach ($r in $running) { if ($r.Proc.HasExited) { $done[$r.Name] = ((Get-Date) - $r.T).TotalSeconds } else { $still += $r } }   # (seconds it took)
        $running = $still
    }
} finally {
    foreach ($r in $running) { StopTree $r.Proc.Id }
    StopTree $srv.Id
}
$fail = 0
foreach ($n in ($done.Keys | Sort-Object)) {
    $lines = @(Get-Content (Join-Path $tmp "$n.out") -Encoding UTF8 -ErrorAction SilentlyContinue) + @(Get-Content (Join-Path $tmp "$n.err") -Encoding UTF8 -ErrorAction SilentlyContinue)
    $out = ($lines | Where-Object { $_ -match '^\d+/\d+ passed' } | Select-Object -Last 1)
    if (-not $out) { $out = ($lines | Where-Object { $_ } | Select-Object -Last 1) }
    "{0,-24} {1,-14} {2,4:N0} s" -f $n, $out, $done[$n]
    if ($out -match '^(\d+)/(\d+) passed') { if ($Matches[1] -ne $Matches[2]) { $fail = 1 } } else { $fail = 1 }
    # failing checks, so you see what broke without running it again
    $lines | Where-Object { $_ -match '^FAIL ' } | ForEach-Object { '    ' + $_.Substring(0, [Math]::Min(160, $_.Length)) }
}
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
'({0:N0} s, {1} at a time)' -f ((Get-Date) - $t0).TotalSeconds, $jobs
if ($fail) { 'NAGOT TEST MISSLYCKADES' } elseif ($args.Count) { 'URVALET OK (' + $done.Count + ' filer) - hela sviten vid storre andringar' } else { 'ALLA TESTER OK' }
exit $fail
