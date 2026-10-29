<#
.SYNOPSIS
    Installs the co-producer for FL Studio on Windows with one command.

.DESCRIPTION
    Run it from the unzipped release folder (install.cmd does this for you):

        powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1

    It does every step a person would otherwise do by hand, and can be run again at any time (to repair or upgrade; your projects,
    models and settings are kept):

      1. Checks the machine (Windows 64-bit, disk space, FL Studio, Serum 2, Claude Desktop, NVIDIA GPU) and shows what it will download.
      2. Copies the program to the install folder (default C:\coproducer).
      3. Downloads its own copy of uv (the Python package tool), checked against a pinned SHA-256.
      4. Downloads Python 3.11 with uv and builds the program's environment from the pinned package list (requirements.lock).
      5. Puts a "coproducer" command on your PATH (open a new PowerShell window to use it).
      6. Downloads ffmpeg (the full build, which has the rubberband filter), checked against a pinned SHA-256.
      7. Writes config.toml, copies the FL-side script into FL Studio's Hardware folder, and the template projects into the sandbox.
      8. Installs loopMIDI with winget (Windows asks for permission once) and sets up the two MIDI ports and FL Studio's MIDI settings.
      9. Installs the model environments and downloads their weights (the biggest step; skip with -Models none).
     10. Registers the servers with Claude Desktop (in the config file Claude Desktop really reads), then starts each one to check it.

    Nothing here closes, starts or changes an open FL Studio. If FL Studio is open, the MIDI settings step waits until it is closed (or is
    left for later with the command it prints).

.PARAMETER InstallDir
    Where the program goes. Default C:\coproducer.

.PARAMETER Models
    none, standard (default: every model the remix pipeline uses, about 30 GB) or full (also ACE-Step generation with its checkpoints,
    the Music Flamingo critic and MuQ-MuLan reference similarity, about 65 GB).

.PARAMETER ModelsDir
    Put the model environments and weights in another folder or drive (for example D:\coproducer-models).

.PARAMETER NoDesktop
    Do not register with Claude Desktop.

.PARAMETER NoMidi
    Do not install loopMIDI or change MIDI settings.

.PARAMETER Yes
    Do not ask before downloading; answer yes to every question.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Models none -InstallDir D:\coproducer
#>
[CmdletBinding()]
param(
    [string]$InstallDir = "C:\coproducer",
    [ValidateSet("none", "standard", "full")][string]$Models = "standard",
    [string]$ModelsDir = "",
    [switch]$NoDesktop,
    [switch]$NoMidi,
    [switch]$Yes
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"          # Windows PowerShell 5.1 downloads many times slower with the progress bar drawn
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

# ---- Pins (checked by tests/test_installer.py against src/coproducer/data/deps.lock.json) ----------------------------------------
$UvVersion = "0.11.22"
$UvUrl = "https://github.com/astral-sh/uv/releases/download/0.11.22/uv-x86_64-pc-windows-msvc.zip"
$UvSha256 = "b56939bac92d29996d351647f7c6f15b31cc69cf952d06d136de3e1e62eb64d1"
$FfmpegVersion = "8.1.1"
$FfmpegUrl = "https://github.com/GyanD/codexffmpeg/releases/download/8.1.1/ffmpeg-8.1.1-full_build.zip"
$FfmpegSha256 = "49b28c5f16addd40239a66949973458769b7056fb7752c30ac0d53389d09a552"
$HostPython = "3.11.3"
$LoopMidiId = "TobiasErichsen.loopMIDI"
$LoopMidiVersion = "1.0.16.27"
$LoopMidiExe = "${env:ProgramFiles(x86)}\Tobias Erichsen\loopMIDI\loopMIDI.exe"
$ClaudeDesktopId = "Anthropic.Claude"
$TorchIndex = "https://download.pytorch.org/whl/cu128"
# Every model the registry does not mark optional, plus sep (the remix pipeline's vocal separation; Demucs alone is only its fallback).
$StandardStacks = @("demucs", "sep", "mir", "critique", "basicpitch")
$FullOnlyStacks = @("acestep")                    # generation from a prompt, with its checkpoints
$SerumStacks = @("serum", "serummcp")

# ---- Output and logging ------------------------------------------------------------------------------------------------------------
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $env:TEMP ("coproducer-install-" + $Stamp + ".log")
$script:StepNo = 0
$script:Warnings = New-Object System.Collections.ArrayList

function Write-Log([string]$Text) {
    try { Add-Content -LiteralPath $LogFile -Value $Text -Encoding UTF8 } catch { }
}

function Say([string]$Text, [string]$Color = "Gray") {
    Write-Host $Text -ForegroundColor $Color
    Write-Log $Text
}

function Step([string]$Title) {
    $script:StepNo++
    Say ""
    Say ("[" + $script:StepNo + "] " + $Title) "Cyan"
}

function Warn([string]$Text) {
    [void]$script:Warnings.Add($Text)
    Say ("    WARNING: " + $Text) "Yellow"
}

function Stop-Install([string]$Text) {
    Say ""
    Say ("STOPPED: " + $Text) "Red"
    Say ("The full log is at " + $LogFile) "Red"
    Say "Fix the problem above, then run the installer again: it picks up where it left off." "Red"
    exit 1
}

function Invoke-Tool([string]$Exe, [string[]]$Arguments, [switch]$Quiet, [switch]$NoThrow) {
    # Runs a program, shows and logs its output line by line, and stops the install when it fails. With -NoThrow it returns the exit
    # code instead (and only then returns anything, so a plain call prints nothing extra).
    Write-Log ("> " + $Exe + " " + ($Arguments -join " "))
    if (-not (Test-Path -LiteralPath $Exe)) { Stop-Install ("missing program: " + $Exe) }
    $code = $null
    $tail = New-Object System.Collections.Generic.Queue[string]
    $old = $ErrorActionPreference
    $ErrorActionPreference = "Continue"           # a program writing progress to stderr is not an error; its exit code decides
    try {
        # The empty pipeline in front closes the program's input, so nothing can sit waiting for a key press that never comes
        # (an unattended run, or a run from the queue, has nobody at the keyboard).
        @() | & $Exe @Arguments 2>&1 | ForEach-Object {
            $line = "$_"
            Write-Log $line
            $tail.Enqueue($line)
            if ($tail.Count -gt 15) { [void]$tail.Dequeue() }
            if (-not $Quiet) { Write-Host ("    " + $line) -ForegroundColor DarkGray }
        }
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $old
    }
    if ($null -eq $code) { $code = 0 }
    if ($code -ne 0 -and $Quiet) { foreach ($l in $tail) { Write-Host ("    " + $l) -ForegroundColor DarkGray } }
    if ($NoThrow) { return $code }
    if ($code -ne 0) { Stop-Install ((Split-Path $Exe -Leaf) + " " + ($Arguments -join " ") + " failed with exit code " + $code) }
}

function Get-Output([string]$Exe, [string[]]$Arguments) {
    # A program's standard output as one string, or "" when it cannot run. Used for version checks.
    $old = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { return ((@() | & $Exe @Arguments 2>$null) -join "`n") } catch { return "" } finally { $ErrorActionPreference = $old }
}

function Get-Download([string]$Url, [string]$Dest, [string]$Sha256) {
    # Downloads to Dest.part, checks the pinned SHA-256, then renames. A file already there with the right hash is kept.
    if ((Test-Path -LiteralPath $Dest) -and ((Get-FileHash -LiteralPath $Dest -Algorithm SHA256).Hash -eq $Sha256.ToUpper())) {
        Say ("    already downloaded: " + (Split-Path $Dest -Leaf))
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $Dest -Parent) | Out-Null
    $part = $Dest + ".part"
    Say ("    downloading " + $Url)
    $curl = Join-Path $env:SystemRoot "System32\curl.exe"
    $ok = $false
    for ($try = 1; $try -le 3 -and -not $ok; $try++) {
        try {
            if (Test-Path -LiteralPath $curl) {
                $code = Invoke-Tool $curl @("-L", "--fail", "--silent", "--show-error", "--retry", "3", "--retry-delay", "5", "-o", $part, $Url) -Quiet -NoThrow
                if ($code -ne 0) { throw ("curl exit code " + $code) }
            } else {
                Invoke-WebRequest -Uri $Url -OutFile $part -UseBasicParsing
            }
            $ok = $true
        } catch {
            Say ("    download attempt " + $try + " failed: " + $_.Exception.Message) "Yellow"
            Start-Sleep -Seconds (5 * $try)
        }
    }
    if (-not $ok) { Stop-Install ("could not download " + $Url + " (check the internet connection)") }
    $got = (Get-FileHash -LiteralPath $part -Algorithm SHA256).Hash
    if ($got -ne $Sha256.ToUpper()) {
        Remove-Item -LiteralPath $part -Force -ErrorAction SilentlyContinue
        Stop-Install ("the download of " + $Url + " does not match its pinned SHA-256 (got " + $got + ")")
    }
    Move-Item -LiteralPath $part -Destination $Dest -Force
}

function Add-UserPath([string]$Dir) {
    # Adds Dir to the user's PATH in the registry, keeping the other entries exactly as they are (%VARIABLES% stay unexpanded).
    $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Environment", $true)
    try {
        $old = [string]$key.GetValue("Path", "", [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $parts = @($old -split ";" | Where-Object { $_ })
        if ($parts -notcontains $Dir) {
            $key.SetValue("Path", ((@($parts) + $Dir) -join ";"), [Microsoft.Win32.RegistryValueKind]::ExpandString)
            return $true
        }
        return $false
    } finally {
        $key.Close()
    }
}

function Test-FlRunning {
    return [bool](Get-Process -Name "FL64", "FL" -ErrorAction SilentlyContinue)
}

function Get-FreeGB([string]$Path) {
    $qualifier = Split-Path -Qualifier $Path
    $disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter ("DeviceID='" + $qualifier + "'") -ErrorAction SilentlyContinue
    if ($null -eq $disk) { return -1 }
    return [math]::Round($disk.FreeSpace / 1GB, 1)
}

function Ask([string]$Question) {
    if ($Yes) { return $true }
    $answer = Read-Host ($Question + " [Y/n]")
    return ($answer -eq "" -or $answer -match "^(y|yes)$")
}

# ---- 0. Where we are ---------------------------------------------------------------------------------------------------------------
$Source = $PSScriptRoot
if (-not $Source) { $Source = Split-Path -Parent $MyInvocation.MyCommand.Path }
Say "Co-producer for FL Studio: installer" "White"
Say ("log: " + $LogFile)
if (-not (Test-Path -LiteralPath (Join-Path $Source "pyproject.toml")) -or -not (Test-Path -LiteralPath (Join-Path $Source "src\coproducer"))) {
    Stop-Install ("install.ps1 must be run from the unzipped release folder (no pyproject.toml or src\coproducer next to it in " + $Source + ")")
}
$InstallDir = [IO.Path]::GetFullPath($InstallDir)
$Runtime = Join-Path $InstallDir "runtime"     # uv, Python and ffmpeg the installer downloads (the repo's own tools folder holds scripts)
$UvExe = Join-Path $Runtime "uv\uv.exe"
$Py = Join-Path $InstallDir ".venv\Scripts\python.exe"

# ---- 1. Check the machine ----------------------------------------------------------------------------------------------------------
Step "Checking this computer"
if (-not [Environment]::Is64BitOperatingSystem) { Stop-Install "a 64-bit Windows is needed" }
$os = [Environment]::OSVersion.Version
if ($os.Major -lt 10) { Stop-Install "Windows 10 or 11 is needed" }
Say ("    Windows " + $os + ", PowerShell " + $PSVersionTable.PSVersion)

# Newest release first, by the year in the folder name ("FL Studio 21BETA" is 2021 and a beta, so "FL Studio 2026" comes before it).
$flYear = { $m = [regex]::Match($_.Directory.Name, "\d{2,4}"); $y = 0; if ($m.Success) { $y = [int]$m.Value; if ($y -lt 100) { $y += 2000 } }; $y }
$flExe = @(Get-ChildItem -Path @("$env:ProgramFiles\Image-Line", "${env:ProgramFiles(x86)}\Image-Line") -Filter "FL64.exe" -Recurse -Depth 1 -ErrorAction SilentlyContinue |
    Sort-Object -Property @{ Expression = $flYear; Descending = $true }, @{ Expression = { $_.Directory.Name -notmatch "beta" }; Descending = $true })
if ($flExe.Count -gt 0) { Say ("    FL Studio: " + $flExe[0].FullName) } else { Warn "FL Studio was not found under Program Files. Install FL Studio, then run this installer again." }

$serumVst = Join-Path $env:CommonProgramFiles "VST3\Serum2.vst3"
$hasSerum = Test-Path -LiteralPath $serumVst
if ($hasSerum) { Say ("    Serum 2: " + $serumVst) } else { Say "    Serum 2: not installed (the remix uses Sytrus sounds instead; install Serum 2 and run this again to add generated Serum sounds)" }

$claudeStore = $null
try { $claudeStore = Get-AppxPackage -Name "Claude" -ErrorAction SilentlyContinue } catch { }
$claudeExe = Join-Path $env:LOCALAPPDATA "AnthropicClaude\claude.exe"
$hasClaude = ($null -ne $claudeStore) -or (Test-Path -LiteralPath $claudeExe)
if ($hasClaude) { Say "    Claude Desktop: installed" } else { Say "    Claude Desktop: not installed (it will be installed with winget)" }

$winget = Get-Command winget.exe -ErrorAction SilentlyContinue
if ($null -eq $winget) { Warn "winget (App Installer) is not available: loopMIDI and Claude Desktop must be installed by hand (links at the end)." }

$gpu = $null
$smi = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
if ($null -ne $smi) { $gpu = ((Get-Output $smi.Source @("--query-gpu=name,driver_version,memory.total", "--format=csv,noheader")) -split "`n")[0].Trim() }
if ($gpu) { Say ("    NVIDIA GPU: " + $gpu) } else { Warn "no NVIDIA GPU found: the models run on the CPU, which is much slower." }

$hasLoopMidi = Test-Path -LiteralPath $LoopMidiExe

# ---- 2. Plan -----------------------------------------------------------------------------------------------------------------------
$stacks = @()
if ($Models -ne "none") { $stacks += $StandardStacks }
if ($Models -eq "full") { $stacks += $FullOnlyStacks }
if ($hasSerum -and $Models -ne "none") { $stacks += $SerumStacks }
$modelsGB = 0
if ($Models -eq "standard") { $modelsGB = 30 }
if ($Models -eq "full") { $modelsGB = 65 }
$needGB = 3 + $modelsGB
if ($ModelsDir) { $ModelsDir = [IO.Path]::GetFullPath($ModelsDir) }
$free = Get-FreeGB $InstallDir
Say ""
Say "This will:" "White"
Say ("  - install to " + $InstallDir + "  (upgrades keep your sandbox, models and config.toml)")
Say ("  - download uv " + $UvVersion + " (24 MB), Python " + $HostPython + " (30 MB) and the program's packages (about 300 MB)")
if (-not (Get-Command ffmpeg.exe -ErrorAction SilentlyContinue)) { Say ("  - download ffmpeg " + $FfmpegVersion + " full build (250 MB)") }
if (-not $NoMidi -and -not $hasLoopMidi) { Say ("  - install loopMIDI " + $LoopMidiVersion + " (Windows asks for permission)") }
if (-not $NoDesktop -and -not $hasClaude) { Say "  - install Claude Desktop" }
if ($stacks.Count -gt 0) {
    $where = $InstallDir
    if ($ModelsDir) { $where = $ModelsDir }
    Say ("  - install the models " + ($stacks -join ", ") + " in " + $where + ": about " + $modelsGB + " GB, the longest step (an hour or more on a slow line)")
} else {
    Say "  - no models (run the installer again with -Models standard to add them)"
}
if (-not $NoDesktop) { Say "  - register the co-producer servers with Claude Desktop (your other servers are kept, the old file is backed up)" }
if ($free -ge 0) { Say ("  disk: " + $free + " GB free on " + (Split-Path -Qualifier $InstallDir) + ", about " + $needGB + " GB needed") }
if ($free -ge 0 -and $free -lt $needGB -and -not $ModelsDir) {
    Stop-Install ("not enough free disk space: " + $free + " GB free, about " + $needGB + " GB needed. Free some space, or use -ModelsDir on another drive, or -Models none.")
}
if ($ModelsDir) {
    $mfree = Get-FreeGB $ModelsDir
    if ($mfree -ge 0 -and $mfree -lt $modelsGB) { Stop-Install ("not enough free disk space for the models on " + (Split-Path -Qualifier $ModelsDir) + ": " + $mfree + " GB free, about " + $modelsGB + " GB needed") }
}
if (-not (Ask "Go ahead?")) { Say "Nothing was changed."; exit 0 }

# ---- 3. Copy the program -----------------------------------------------------------------------------------------------------------
Step ("Copying the program to " + $InstallDir)
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$same = ([IO.Path]::GetFullPath($Source).TrimEnd("\") -eq $InstallDir.TrimEnd("\"))
if ($same) {
    Say "    running from the install folder itself: nothing to copy"
} else {
    foreach ($rel in @("docs\DEPENDENCIES.md", "requirements.lock", "src\coproducer\data\deps.lock.json")) {
        $f = Join-Path $InstallDir $rel
        if (Test-Path -LiteralPath $f) { Set-ItemProperty -LiteralPath $f -Name IsReadOnly -Value $false }
    }
    # Files unzipped from a download carry the "came from the internet" mark; clear it on the unzipped copy (a few thousand files)
    # before copying, not afterwards on the install folder, which on an upgrade also holds the models (hundreds of thousands of files).
    Get-ChildItem -LiteralPath $Source -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue
    # Never copied from the source: machine-specific or user data. Never removed from the target: robocopy runs without /PURGE.
    $xd = @(".venv", ".git", "__pycache__", ".pytest_cache", ".ruff_cache") + @("sandbox", "runs", "logs", "dist", "runtime", "models\envs", "models\weights", "models\acestep" | ForEach-Object { Join-Path $Source $_ })
    $rcArgs = @($Source, $InstallDir, "/E", "/R:2", "/W:2", "/NFL", "/NDL", "/NJH", "/NP", "/XF", (Join-Path $Source "config.toml"), "*.pyc", "/XD") + $xd
    $old = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    & robocopy.exe @rcArgs | ForEach-Object { Write-Log "$_" }
    $rc = $LASTEXITCODE
    $ErrorActionPreference = $old
    if ($rc -ge 8) { Stop-Install ("copying the files failed (robocopy exit code " + $rc + "); see the log") }
    Say "    copied"
}

# ---- 4. uv ------------------------------------------------------------------------------------------------------------------------
Step ("uv " + $UvVersion)
$haveUv = $false
if (Test-Path -LiteralPath $UvExe) {
    $v = Get-Output $UvExe @("--version")
    $haveUv = ($v -like ("uv " + $UvVersion + "*"))
}
if ($haveUv) {
    Say ("    already installed: " + $UvExe)
} else {
    $zip = Join-Path $Runtime "downloads\uv-$UvVersion-x86_64-pc-windows-msvc.zip"
    Get-Download $UvUrl $zip $UvSha256
    $dest = Join-Path $Runtime "uv"
    if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
    Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force
    $found = Get-ChildItem -LiteralPath $dest -Recurse -Filter "uv.exe" | Select-Object -First 1
    if ($null -eq $found) { Stop-Install "the uv archive holds no uv.exe" }
    if ($found.DirectoryName -ne $dest) { Get-ChildItem -LiteralPath $found.DirectoryName | Move-Item -Destination $dest -Force }
    Say ("    installed: " + $UvExe)
}
$env:Path = (Join-Path $Runtime "uv") + ";" + (Join-Path $Runtime "ffmpeg\bin") + ";" + $env:Path
$env:UV_PYTHON_INSTALL_DIR = Join-Path $Runtime "python"     # uv's Pythons live inside the install, so removing the folder removes everything
$env:UV_MANAGED_PYTHON = "1"                                # always uv's own Python builds, never whatever else is on the machine
$env:COPRODUCER_HOME = $InstallDir
$env:PYTHONUNBUFFERED = "1"                                 # the program's lines show as they come, not when it ends

# ---- 5. Python and the program's environment ---------------------------------------------------------------------------------------
Step ("Python " + $HostPython + " and the program's packages")
Invoke-Tool $UvExe @("python", "install", $HostPython)
Invoke-Tool $UvExe @("venv", "--allow-existing", "--python", $HostPython, (Join-Path $InstallDir ".venv"))
Invoke-Tool $UvExe @("pip", "install", "--python", $Py, "-r", (Join-Path $InstallDir "requirements.lock"))
Invoke-Tool $UvExe @("pip", "install", "--python", $Py, "--no-deps", "-e", $InstallDir)
Invoke-Tool $Py @("-c", "import coproducer, mcp, numpy, mido; print('coproducer imports')")

# ---- 6. The coproducer command -----------------------------------------------------------------------------------------------------
Step "The coproducer command"
$bin = Join-Path $env:LOCALAPPDATA "coproducer\bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null
# Each line in parentheses: in PowerShell the comma binds tighter than +, so "a" + $x + "b", "c" would split into separate lines
# (the first build of this installer wrote a shim that started a bare Python prompt and hung, 2026-10-27).
$shim = @(
    "@echo off",
    ("rem Written by the co-producer installer. Runs the co-producer from " + $InstallDir + "."),
    ("set ""COPRODUCER_HOME=" + $InstallDir + """"),
    ("set ""UV_PYTHON_INSTALL_DIR=" + (Join-Path $Runtime "python") + """"),
    ("set ""PATH=" + (Join-Path $Runtime "uv") + ";" + (Join-Path $Runtime "ffmpeg\bin") + ";%PATH%"""),
    ("""" + $Py + """ -m coproducer %*")
)
if ($shim.Count -ne 6) { Stop-Install "internal error: the coproducer command file did not come out as six lines" }
Set-Content -LiteralPath (Join-Path $bin "coproducer.cmd") -Value $shim -Encoding ASCII
$added = Add-UserPath $bin
[Environment]::SetEnvironmentVariable("COPRODUCER_HOME", $InstallDir, "User")     # this .NET call also tells Windows the environment changed
$env:Path = $bin + ";" + $env:Path
if ($added) { Say ("    added " + $bin + " to your PATH: open a NEW PowerShell window to use the coproducer command") } else { Say ("    " + (Join-Path $bin "coproducer.cmd")) }
$Cop = Join-Path $bin "coproducer.cmd"

# ---- 7. ffmpeg ---------------------------------------------------------------------------------------------------------------------
Step ("ffmpeg " + $FfmpegVersion)
$ffDir = Join-Path $Runtime "ffmpeg"
$ffExe = Join-Path $ffDir "bin\ffmpeg.exe"
if (Test-Path -LiteralPath $ffExe) {
    Say ("    already installed: " + $ffExe)
} else {
    $zip = Join-Path $Runtime "downloads\ffmpeg-$FfmpegVersion-full_build.zip"
    Get-Download $FfmpegUrl $zip $FfmpegSha256
    $tmp = Join-Path $Runtime "ffmpeg.part"
    if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
    Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
    $inner = Get-ChildItem -LiteralPath $tmp -Directory | Select-Object -First 1
    if ($null -eq $inner -or -not (Test-Path -LiteralPath (Join-Path $inner.FullName "bin\ffmpeg.exe"))) { Stop-Install "the ffmpeg archive holds no bin\ffmpeg.exe" }
    if (Test-Path -LiteralPath $ffDir) { Remove-Item -LiteralPath $ffDir -Recurse -Force }
    Move-Item -LiteralPath $inner.FullName -Destination $ffDir
    Remove-Item -LiteralPath $tmp -Recurse -Force
    Remove-Item -LiteralPath $zip -Force                 # 250 MB that is not needed once unpacked
    Say ("    installed: " + $ffExe)
}
$filters = Get-Output $ffExe @("-hide_banner", "-filters")
if ($filters -notmatch "rubberband") { Warn "this ffmpeg has no rubberband filter: vocal time-stretching will not work" }

# ---- 8. Settings, FL-side script, templates ----------------------------------------------------------------------------------------
Step "Settings, the FL-side script and the template projects"
$docs = [Environment]::GetFolderPath("MyDocuments")
# The FL executable is found by setup itself (it ranks release folders by year, so "FL Studio 21BETA" does not beat "FL Studio 2026").
# "--torch-index=" with nothing after it is the CPU build: Windows PowerShell drops an empty argument, so it is written as one word.
$setupArgs = @("setup", "--no-desktop", "--data-dir", (Join-Path $docs "Image-Line\FL Studio"))
if ($gpu) { $setupArgs += ("--torch-index=" + $TorchIndex) } else { $setupArgs += "--torch-index=" }
if ($ModelsDir) { $setupArgs += @("--models-dir", $ModelsDir) }
Invoke-Tool $Cop $setupArgs -Quiet
Say "    config.toml, FL-side script and templates are in place"

# ---- 9. MIDI ---------------------------------------------------------------------------------------------------------------------
if ($NoMidi) {
    Step "MIDI (skipped: -NoMidi)"
} else {
    Step "loopMIDI and FL Studio's MIDI settings"
    if (-not (Test-Path -LiteralPath $LoopMidiExe)) {
        if ($null -ne $winget) {
            Say "    installing loopMIDI (Windows asks for permission: click Yes)"
            [void](Invoke-Tool $winget.Source @("install", "--id", $LoopMidiId, "-e", "--version", $LoopMidiVersion, "--accept-package-agreements", "--accept-source-agreements", "--silent", "--disable-interactivity") -NoThrow)
        }
        if (-not (Test-Path -LiteralPath $LoopMidiExe)) { Warn "loopMIDI is not installed: get it from https://www.tobias-erichsen.de/software/loopmidi.html, then run  coproducer setup-midi" }
    }
    if (Test-Path -LiteralPath $LoopMidiExe) {
        if (Test-FlRunning) {
            Say "    FL Studio is open. It saves its MIDI settings when it closes, so they can only be set while it is closed." "Yellow"
            if (-not $Yes) {
                [void](Read-Host "    Save your work, close FL Studio, then press Enter (or just press Enter to do this later)")
            }
        }
        if (Test-FlRunning) {
            Warn "FL Studio is still open: close it later and run  coproducer setup-midi"
        } else {
            $code = Invoke-Tool $Cop @("setup-midi") -NoThrow
            if ($code -ne 0) { Warn "the MIDI settings were not written (see above); close FL Studio and run  coproducer setup-midi" }
        }
    }
}

# ---- 10. Models ------------------------------------------------------------------------------------------------------------------
if ($stacks.Count -eq 0) {
    Step "Models (skipped)"
} else {
    Step ("Models: " + ($stacks -join ", ") + " (the long step; it can be stopped and run again, finished parts are kept)")
    $modelArgs = @("install-models") + $stacks
    if ($Models -eq "full") { $modelArgs += "--with-optional" }
    $code = Invoke-Tool $Cop $modelArgs -NoThrow
    if ($code -ne 0) { Warn ("a model install failed (see the log); run the installer again, or  coproducer install-models " + ($stacks -join " ")) }
}

# ---- 11. Claude Desktop ----------------------------------------------------------------------------------------------------------
if ($NoDesktop) {
    Step "Claude Desktop (skipped: -NoDesktop)"
} else {
    Step "Claude Desktop"
    if (-not $hasClaude -and $null -ne $winget) {
        Say "    installing Claude Desktop"
        [void](Invoke-Tool $winget.Source @("install", "--id", $ClaudeDesktopId, "-e", "--accept-package-agreements", "--accept-source-agreements", "--silent", "--disable-interactivity") -NoThrow)
    }
    $deskArgs = @("install-desktop")
    $presets = Join-Path $docs "Xfer\Serum 2 Presets\Presets\User"
    if ($hasSerum -and (Test-Path -LiteralPath (Join-Path $InstallDir "sandbox\third_party\serum-mcp\.venv"))) {
        if (Test-Path -LiteralPath $presets) { $deskArgs += @("--with-serum", "--serum-presets", $presets) }
        else { Warn "Serum 2 has no user preset folder yet: open Serum 2 once, then run  coproducer install-desktop --with-serum" }
    }
    # Claude Desktop rewrites its config file from memory while it runs, so the servers are only written while it is closed: if it is
    # open, the command asks you to quit it, waits, writes, and starts it again.
    $deskArgs += @("--wait", "--restart")
    $running = @(Get-Process -Name "claude" -ErrorAction SilentlyContinue | Where-Object { $_.Path -and ($_.Path -like "*\WindowsApps\Claude_*" -or $_.Path -like "*\AnthropicClaude\*") })
    if ($running.Count -gt 0) {
        Say "    Claude Desktop is open. It has to be closed for a moment so it reads the new servers when it starts:" "Yellow"
        Say "    right-click its icon by the clock and choose Quit, then leave it closed. The installer opens it again a moment later." "Yellow"
    }
    $code = Invoke-Tool $Cop $deskArgs -NoThrow
    if ($code -eq 3 -or $code -eq 4) {
        Warn "Claude Desktop was not closed, so the servers were not registered yet: quit it, then run  coproducer install-desktop --wait --restart"
    } elseif ($code -ne 0) {
        Stop-Install "registering the servers with Claude Desktop failed (the lines above say why)"
    } else {
        Say "    checking that each server starts the way Claude Desktop starts it"
        $code = Invoke-Tool $Cop @("check-servers") -NoThrow
        if ($code -ne 0) { Warn "a server did not start (see above and the log)" }
    }
}

# ---- 12. Check everything ----------------------------------------------------------------------------------------------------------
Step "Final check"
[void](Invoke-Tool $Cop @("doctor") -NoThrow)
try {
    New-Item -ItemType Directory -Force -Path (Join-Path $InstallDir "logs") | Out-Null
    Copy-Item -LiteralPath $LogFile -Destination (Join-Path $InstallDir ("logs\install-" + $Stamp + ".log")) -Force
} catch { }

Say ""
if ($script:Warnings.Count -eq 0) { Say "Done." "Green" } else {
    Say ("Done, with " + $script:Warnings.Count + " thing(s) to look at:") "Yellow"
    foreach ($w in $script:Warnings) { Say ("  - " + $w) "Yellow" }
}
Say ""
Say "Next:" "White"
if (-not $NoDesktop) {
    Say "  1. Claude Desktop has been started with the co-producer servers (if it is not open, open it)."
    Say "  2. In a new chat, ask: ""list the co-producer skills"". The answer should come from the coproducer servers."
}
Say "  3. Open FL Studio. In Options > MIDI settings, coproducer-in should show the Coproducer script (the installer set this)."
Say "  4. Any time: open a new PowerShell window and run  coproducer doctor"
Say ("Log: " + (Join-Path $InstallDir ("logs\install-" + $Stamp + ".log")))
exit 0
