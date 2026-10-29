# Installing the co-producer on Windows

One command installs everything: the program, its own Python, the packages, ffmpeg, loopMIDI and the MIDI settings, the models, and the
Claude Desktop registration. Nothing has to be installed by hand first, and no knowledge of Python, virtual environments, git or model
downloads is needed.

## What you need

- Windows 10 or 11, 64-bit, with an internet connection.
- FL Studio (any edition that runs Python controller scripts; built and tested with FL Studio 2026).
- About 35 GB free on the drive you install to (the models are most of it; see Options below for less, or another drive).
- An NVIDIA graphics card is strongly recommended. Without one the models run on the processor, which is much slower.
- Optional: Serum 2. With it, every remix gets Serum sounds generated to match the song; without it, the remix uses Sytrus.

## Install

1. Download `coproducer-<version>.zip` and save it in your Downloads folder.
2. Open PowerShell (Start menu, type PowerShell, press Enter) and paste this one line, with the version number of your zip:

   ```powershell
   Expand-Archive "$HOME\Downloads\coproducer-0.1.0.zip" "$HOME\Downloads\coproducer-0.1.0" -Force; & "$HOME\Downloads\coproducer-0.1.0\install.cmd"
   ```

   Or unzip it yourself (right-click, Extract All) and double-click `install.cmd` in the unzipped folder.
3. The installer shows what it will download and asks once before it starts. Windows asks for permission once more when loopMIDI
   installs (it adds a virtual MIDI driver): click Yes.
4. Near the end, if Claude Desktop is open, the installer asks you to quit it (right-click its icon next to the clock, then Quit;
   closing the window is not enough) and to leave it closed. It registers the servers the moment Desktop closes, then opens it again. When it says Done, ask a new
   chat "list the co-producer skills".

The whole install takes from 20 minutes to over an hour, almost all of it the model downloads. If it stops (a dropped connection, a full
disk), fix the cause and run the same command again: finished parts are kept.

## What it does

| Step | What | Where |
| --- | --- | --- |
| 1 | Checks Windows, disk space, FL Studio, Serum 2, Claude Desktop and the GPU, and shows the plan | |
| 2 | Copies the program | `C:\coproducer` (change with `-InstallDir`) |
| 3 | Downloads uv 0.11.22, checked against its pinned SHA-256 | `C:\coproducer\runtime\uv` |
| 4 | Downloads Python 3.11.3 and builds the program's environment from `requirements.lock` | `C:\coproducer\runtime\python`, `C:\coproducer\.venv` |
| 5 | Adds the `coproducer` command to your PATH (open a new PowerShell window to use it) | `%LOCALAPPDATA%\coproducer\bin` |
| 6 | Downloads ffmpeg 8.1.1, the full build (it has the rubberband filter the vocal chops use), checked against its SHA-256 | `C:\coproducer\runtime\ffmpeg` |
| 7 | Writes `config.toml`, installs the FL-side script, copies the template projects | FL's `Settings\Hardware\coproducer`, `C:\coproducer\sandbox\templates` |
| 8 | Installs loopMIDI 1.0.16.27 with winget, creates the ports `coproducer-in` and `coproducer-out`, and sets FL Studio's MIDI settings | registry (only while FL Studio is closed) |
| 9 | Installs the model environments and downloads their pinned weights | `C:\coproducer\models` (change with `-ModelsDir`) |
| 10 | Registers the servers with Claude Desktop while it is closed (it asks you to quit it, then opens it again), then starts each server the way Claude Desktop will, to check it | the config file Claude Desktop reads |
| 11 | Runs `coproducer doctor` and saves the log | `C:\coproducer\logs\install-<time>.log` |

It never closes, starts or changes an FL Studio that is open. FL Studio saves its MIDI settings when it closes, so if it is open the
installer asks you to close it first, or leaves that step for later (`coproducer setup-midi`).

## Options

Pass them after the command, for example `& "...\install.cmd" -Models none`:

| Option | Meaning |
| --- | --- |
| `-InstallDir D:\coproducer` | Install somewhere else. |
| `-Models none` | No models now (about 3 GB in all); run the installer again later to add them. The default, `standard`, is every model the remix pipeline uses (Demucs, the RoFormer vocal separator, beat and pitch tracking, Whisper, Basic Pitch, and the Serum ones when Serum 2 is installed), about 30 GB. |
| `-Models full` | Also ACE-Step (generation from a prompt, with its checkpoints), the Music Flamingo critic (about 16 GB) and MuQ-MuLan reference similarity: about 65 GB in all. |
| `-ModelsDir D:\cp-models` | Keep the model environments and weights on another drive. |
| `-NoDesktop` | Do not touch Claude Desktop. |
| `-NoMidi` | Do not install loopMIDI or change MIDI settings. |
| `-Yes` | Do not ask anything (for a second run, or unattended). |

## Upgrading and repairing

Run the installer of the new version the same way. It copies the new program over the old one and keeps `config.toml`, the sandbox (your
projects and renders), the models and the downloads. Running it again on the same version repairs whatever is missing.

## Checking an install

Open a new PowerShell window:

```powershell
coproducer doctor          # every check with PASS, WARN or FAIL and the fix for each
coproducer check-servers   # starts each server the way Claude Desktop does and lists its tools
```

## Claude Desktop notes

- Claude Desktop from the Microsoft Store does not read `%APPDATA%\Claude\claude_desktop_config.json`. It reads its own copy inside its
  package folder, `%LOCALAPPDATA%\Packages\Claude_<id>\LocalCache\Roaming\Claude\claude_desktop_config.json`. The installer (and
  `coproducer install-desktop`) writes the file the installed Claude Desktop really reads, keeps every other server in it, backs it up
  first, and removes old co-producer entries from the file Claude Desktop ignores. This was the reason the servers did not load on
  rtxclub before 2026-10-26.
- Claude Desktop reads the file only when it starts, and while it runs it keeps the file in memory and writes all of it back whenever
  one of its own settings changes (its preferences live in the same file). Servers added while it runs are therefore lost at its next
  settings change: on rtxclub two such writes (23:08 and 03:44 on 2026-10-26) removed them before Desktop was ever restarted. So the
  servers are written only while Claude Desktop is closed: `coproducer install-desktop` refuses while it runs, `--wait` waits for you to
  quit it, and `--restart` opens it again afterwards (the installer uses both). A Desktop reopened before the write finished (on rtxclub
  it was reopened 3 seconds after quitting and read the file one second too early) is noticed by its start time and waited out again.
- The skills come from the servers themselves (the `list_skills` tool), so nothing has to be uploaded in Claude Desktop's settings.

## Removing it

Delete `C:\coproducer` (and the `-ModelsDir` folder if you used one) and `%LOCALAPPDATA%\coproducer`, then remove
`%LOCALAPPDATA%\coproducer\bin` from your PATH and the `coproducer-*` entries from Claude Desktop's config
(`coproducer install-desktop --remove` does that last part before you delete the folder). loopMIDI is removed from Windows Settings, Apps.

## Pins and sources

| Item | Pin | Source |
| --- | --- | --- |
| uv | 0.11.22, `uv-x86_64-pc-windows-msvc.zip`, SHA-256 `b56939ba...` | https://github.com/astral-sh/uv/releases/tag/0.11.22, install options https://docs.astral.sh/uv/reference/installer/ |
| Python | 3.11.3 (uv's managed build) | `src/coproducer/data/deps.lock.json` |
| ffmpeg | 8.1.1 full build, SHA-256 `49b28c5f...` | https://github.com/GyanD/codexffmpeg/releases/tag/8.1.1 (the builds winget's `Gyan.FFmpeg` installs) |
| loopMIDI | 1.0.16.27, winget `TobiasErichsen.loopMIDI` | https://www.tobias-erichsen.de/software/loopmidi.html |
| Host packages | `requirements.lock` | `docs/DEPENDENCIES.md` |
| Model environments | `src/coproducer/cli/stacks.py`, `models/locks/*.txt` | `docs/DEPENDENCIES.md` |
| ACE-Step checkpoints (`-Models full` only) | not pinned: ACE-Step's own `acestep-download` takes no revision | https://github.com/ace-step/ACE-Step-1.5 |

The full hashes are in `install.ps1`; `tests/test_installer.py` checks them against the dependency lock.
