# Runs the .cmd files that Claude drops into C:\coproducer\sandbox\queue, one at a time, oldest name first.
# You start it and you stop it (Ctrl+C or close the window). Nothing outside that folder is ever executed.
# For job NAME.cmd it writes NAME.out.txt (stdout and stderr) and, when the job ends, NAME.exit.txt (the exit code).
# Start:  powershell -ExecutionPolicy Bypass -File C:\coproducer\tools\queue_runner.ps1
$root = 'C:\coproducer'
$queue = Join-Path $root 'sandbox\queue'
$done = Join-Path $queue 'done'
New-Item -ItemType Directory -Force -Path $queue, $done | Out-Null
Write-Host "Watching $queue  (Ctrl+C to stop)"
while ($true) {
    Get-ChildItem -Path $queue -Filter *.cmd -File | Sort-Object Name | ForEach-Object {
        $job = Join-Path $done $_.Name
        Move-Item -Path $_.FullName -Destination $job -Force
        $base = [IO.Path]::GetFileNameWithoutExtension($_.Name)
        $out = Join-Path $done ($base + '.out.txt')
        Write-Host ("{0}  running {1}" -f (Get-Date -Format HH:mm:ss), $_.Name)
        Push-Location $root
        cmd /c "`"$job`" > `"$out`" 2>&1"
        $code = $LASTEXITCODE
        Pop-Location
        Set-Content -Path (Join-Path $done ($base + '.exit.txt')) -Value $code
        Write-Host ("{0}  finished {1} exit {2}" -f (Get-Date -Format HH:mm:ss), $_.Name, $code)
    }
    Start-Sleep -Seconds 2
}
