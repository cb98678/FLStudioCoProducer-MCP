# Coproducer

A local-first AI co-producer for FL Studio. It makes music, listens to it (render, measure, critique), restyles tracks while keeping the melody, mixes, gain stages and masters, and falls back to controlling the desktop when the FL API cannot do something. Everything runs on your machine. It is a clean-room build: nothing here is forked from or depends on any other FL Studio MCP.

Read `docs/HANDOFF.md` first if you are a new session (how to work, how to rebuild a remix), then `docs/ROADMAP.md` (what is missing and the build order) and `docs/STATUS.md`; `docs/FILE_MAP.md` lists every file and what it does. Stability and fragility results are in `docs/STRESS_REPORT.md`; every dependency and its pinned version is in `docs/DEPENDENCIES.md`. It says exactly what was tested here and what only your machine can prove (Gate 0).

## What is in the box

| Part | Where | What it is |
| --- | --- | --- |
| Four MCP servers | `src/coproducer/servers/` | `fl-bridge` (FL state, verified writes, run control), `studio-audio` (measurements), `studio-ml` (local models), `desktop-control` (GUI fallback) |
| Modules | `modules/` | 541 small tools (202 exposed to the agent; 320 are generated FL API ops), one function and one job each, with a manifest and tests. Checked by a linter (`coproducer lint`) |
| FL-side script | `fl_side/device_coproducer.py` | Generated. One controller script that runs inside FL Studio and answers over MIDI SysEx |
| Orchestrator | `src/coproducer/orchestrator/` | Plans as data, verifiers, a run ledger, phases P0 to P7, human questions |
| Model layer | `src/coproducer/models/`, `runners/`, `models/registry.toml` | GPU scheduler and one isolated environment per model |
| Skills | `skills/` | Seventeen skills that teach a local model how to use all of the above, each with eval prompts |
| Style packs | `styles/` | Genres as data: house, tech house, deep house, nu-disco, techno, dubstep, drum and bass, trap, hip-hop, and from the FL demo study afro house, afrobeats, reggaeton, trance, melodic techno, liquid drum and bass, future bass, UK drill, lo-fi, trip hop, pop dance, future house, big room, electro industrial and cinematic, each with the moods it serves (skill `genre-styles`) |
| Option bank and variety | `src/coproducer/data/options/`, `docs/DEMO_STUDY.md` | What the twenty FL demo songs do (forms, grooves, kits, bass lines, chords, arps, harmony, instruments, transitions, mix, vocals, automation) as options; each remix chooses its own and differs from the last ones (skill `creative-variety`) |
| Task cards | `cards/` | Work orders for a local coding model to write new modules, with a gated build loop |
| Data you fill | `targets/`, `genre_profiles/`, `specs/templates/`, `recipes/` | Templates with `FILL` blanks. The agent never invents these |
| Gate 0 probes | `probes/`, `coproducer probe ...` | The checks that need FL Studio and your hardware |

## Remix any song

```
python tools/remix_song.py NAME STYLE --song SONG.wav --title "the hook line"
```

One command runs the whole chain through the modules: stems (Mel-Band RoFormer vocals, Demucs), the bar grid (beat_this), words (Whisper),
melody, key vote, a song plan from the style pack, the editable FL project, the production recipe, a render (only while FL is closed), the
contrast loop, a club master to `targets/club_release.toml` and the evaluation panel, with a report and an MP3 in `sandbox\remix\NAME_STYLE`.
Reference tracks in `sandbox\references\STYLE` set the master's loudness and tonal balance and feed the similarity judge; `--finish`
re-masters an earlier run without rendering, and `--match-sounds` generates each synth part's Serum 2 sound to match the original
(`match_part_sound`; needs `coproducer install-models serum serummcp`). Steps one by one: skill `remix-from-stems`.

## Safety model

- The agent works only in a sandbox copy of your project. The original is hashed and never written.
- Autonomy levels: A0 read, A1 asks you first, A2 acts in the sandbox with a verifier, A3 touches a real project and is human only (`coproducer promote`).
- Every write is read back. `verified: false` means FL did not do what was asked.
- The GUI fallback is scoped to the FL window, has an action budget, and halts on any dialog it does not know.
- Emergency stop: run `coproducer halt --key` in its own window; Ctrl+Alt+F12 then stops every run and GUI action. `coproducer halt` does the same by hand and `coproducer halt --clear` lets runs start again.

## Install (Windows)

One command does all of it: the program, its own Python and packages, ffmpeg, loopMIDI with the MIDI ports and FL Studio's MIDI settings,
the models, and the Claude Desktop registration. Nothing has to be installed first. Save the release zip in Downloads, open PowerShell and
run (with your zip's version number):

```powershell
Expand-Archive "$HOME\Downloads\coproducer-0.1.0.zip" "$HOME\Downloads\coproducer-0.1.0" -Force; & "$HOME\Downloads\coproducer-0.1.0\install.cmd"
```

or unzip it and double-click `install.cmd`. If Claude Desktop is open it asks you to quit it near the end (it rewrites its config file
while it runs), registers the servers, and opens it again; then ask a new chat to "list the co-producer skills". Options (`-Models none|standard|full`, `-InstallDir`, `-ModelsDir`, `-NoDesktop`, `-NoMidi`, `-Yes`), what
each step does and every pin with its source: `docs/INSTALL.md`. Run it again to repair or upgrade; your sandbox, models and
`config.toml` are kept. `python tools/make_release.py` builds the zip from a working tree (it leaves out everything of this machine).

By hand, for development (Python 3.11, `uv`, `git`):

```
git clone <this repo> C:\coproducer
cd C:\coproducer
uv venv --python 3.11.3 .venv
coproducer install-host     # every package pinned from requirements.lock (uses uv); or pip install -e .[midi,gui,dev]
coproducer setup
coproducer setup-midi       # loopMIDI ports and FL's MIDI settings in the registry (FL closed)
coproducer doctor
coproducer deps             # checks this machine against the dependency lock
```

Production rule: build editable first (drums as sampler channels plus patterns, synths and bass as plugin channels plus piano-roll notes, audio clips only with a reason). It is in `docs/PRODUCTION_POLICY.md` and the `editable-first` skill; the file patching format is in `docs/FLP_FORMAT.md`.

Every dependency, why it is needed and its pinned version is in `docs/DEPENDENCIES.md`. The lock is `src/coproducer/data/deps.lock.json` plus `requirements.lock`; `coproducer deps --freeze` rewrites both from a machine where everything works.

`coproducer setup` writes `config.toml`, copies the FL-side script into FL's Hardware folder, and prints the two click paths (loopMIDI ports, then MIDI Settings in FL). Then follow `docs/GATE0.md` step by step. Local model choice and VRAM budget: `docs/LOCAL_MODELS.md`.

Models are installed one environment each, because their requirements conflict (the installer runs this for you):

```
coproducer install-models --dry-run
coproducer install-models demucs sep mir critique basicpitch
coproducer install-models acestep --with-optional     # generation, with ACE-Step's checkpoints
```

Set `[gpu] torch_index` in `config.toml` first if you want a CUDA build of PyTorch (pick the index on the [PyTorch install page](https://pytorch.org/get-started/locally/)).

## Connect a model to the servers

`mcp.example.json` shows the four servers for any MCP client. Each takes `--home` (this folder) and `--run` (a run id). All four share one run folder, so the plan, phase and ledger are common. Tools are limited to the current phase; the agent asks for others with `request_tool`.

### Add the servers to Claude Desktop

```
coproducer install-desktop --dry-run     # show what would change
coproducer install-desktop               # fl-bridge, studio-audio, studio-ml
coproducer install-desktop --with-serum  # also the Serum 2 preset server (serum-mcp, cloned in sandbox\third_party\serum-mcp)
coproducer install-desktop --with-desktop-control   # also the server that clicks in the FL window
coproducer install-desktop --claude-code # also write the same servers to .mcp.json here, for Claude Code
coproducer install-desktop --remove      # take the coproducer entries out again
coproducer install-models serum          # Serum 2 played headless, to hear generated sounds without FL (docs/SERUM_MCP.md)
```

**In a new chat**, the first call is `list_skills` (on `coproducer-fl-bridge`): a Claude Desktop chat has no copy of this folder's skills, so the server serves them read only, with `read_skill` for one skill, reference, doc or style pack. Start with `co-producer-protocol`, then the skill for the task (`remix-from-stems` for a remix, with its `references/creative-brief.md`). The fl-bridge server's own instructions say the same.

`coproducer setup` offers the same step at the end (`--desktop` says yes, `--no-desktop` skips the question). `--with-serum` registers the third-party [serum-mcp](https://github.com/Celian-mrc/serum-mcp) as `coproducer-serum` (`uv run --frozen --directory <clone> serum-mcp`, Serum's preset, table and sample folders as its environment; `--serum-presets`, `--sample-bank` and `--uv` override), so `--remove` takes it out with the rest. The command edits `claude_desktop_config.json` (Windows: the Microsoft Store build reads its own copy in `%LOCALAPPDATA%\Packages\Claude_<id>\LocalCache\Roaming\Claude`, and the command writes that one when it exists, else `%APPDATA%\Claude`; macOS `~/Library/Application Support/Claude`; `--config PATH` overrides), keeps your other servers and keys, writes a timestamped `.bak` first, and refuses a file that is not valid JSON. Entries are named `coproducer-fl-bridge` and so on, run `python -m coproducer serve ...` with the interpreter that ran the command and an absolute `--home`, so no PATH setup is needed. After it runs, fully quit Claude Desktop (tray icon, not just the window) and start it again; the servers appear under Settings > Developer, and their logs are in `%LOCALAPPDATA%\Claude\logs\mcp-server-NAME.log`; `coproducer check-servers` starts each one the way Claude Desktop will. `desktop-control` is off by default because it moves the mouse and keyboard (autonomy ceiling A2, halt key honoured). Format and restart behaviour: [MCP docs, connect local servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers). A one-click `.mcpb` bundle was not chosen because the servers need compiled Python packages that do not bundle portably ([MCPB](https://github.com/modelcontextprotocol/mcpb)).

For the local brain, set `[llm] endpoint` in `config.toml` to any OpenAI-compatible server. That endpoint is also what builds new modules from task cards.

## Commands

| Command | What it does |
| --- | --- |
| `coproducer doctor` | Checks Python, packages, lint, FL script, MIDI ports and settings, GPU, model environments, Claude Desktop registration |
| `coproducer check-servers` | Starts each registered server the way Claude Desktop will and lists its tools |
| `coproducer setup-midi` | Writes the loopMIDI ports and FL Studio's MIDI device settings (only while FL is closed) |
| `coproducer remix SONG ...` | The remix pipeline (`tools/remix_song.py`) |
| `coproducer setup` | Folders, `config.toml`, FL-side script, click paths |
| `coproducer install-models [names]` | Creates model environments with `uv` and records them |
| `coproducer install-host` | Builds the host venv from `requirements.lock` with `uv` (pinned) |
| `coproducer deps [--freeze] [--docs]` | Checks the machine against the dependency lock; `--freeze` writes it, `--docs` regenerates `docs/DEPENDENCIES.md` |
| `coproducer lint` | Lints every module against the rules LM-001 to LM-015 |
| `coproducer gen` | Regenerates the FL-side script, the API inventory and the skill catalogs |
| `coproducer new-project NAME --mode restyle --source X.flp` | Creates the spec sheet in `specs/` |
| `coproducer run PLAN.json` / `resume RUN` | Runs a plan against FL, asking you in the terminal (or `--unattended`) |
| `coproducer promote RESULT DEST` | You, copying a sandbox result over a real file, with a backup |
| `coproducer calibrate ANCHOR...` | Records click anchors for GUI recipes |
| `coproducer probe ...` | Gate 0 probes: `install-fl`, `report`, `ping`, `throughput`, `render`, `desktop`, `models`, `vibe`, `eq`, `polish`, `numbering`, and `stress` (read-only abuse of the live bridge; `--only desktop` adds the window-state tests) |
| `python tools/spec_match.py RENDER REF BAR_MAP` | Bar-matched third-octave comparison of a render with a reference remix |
| `python tools/vocal_clean.py OUT_DIR FILE...` / `python tools/vocal_patch.py IN.flp OUT.flp ...` | Clean vocal source files (high-pass, noise reduction, tone, de-ess, compress, saturate) and point the project's vocal clips at them, trimming lead-ins and snapping off-grid clips to the sixteenth grid |
| `python tools/flp_tool.py ...` | Offline editable-first patching of a sandbox FLP: `info`, `kit`, `set-sample`, `enable`, `clone`, `add-drums`, `add-notes` (see `docs/FLP_FORMAT.md`) |
| `python tools/build_techhouse.py BASE.flp DTP.flp AUDIODIR OUT.flp` | Build the tech-house remix project from the stems and the audio made by `tools/techhouse_audio.py` (full recipe in `docs/HANDOFF.md`) |
| `python tools/gen_file_map.py` | Rewrite `docs/FILE_MAP.md` from every file's docstring (a test fails when it is stale) |
| `python tools/fuzz_all.py` | Fuzzes every module with hostile arguments on the fake FL and writes a JSON report (see `docs/STRESS_REPORT.md`) |
| `coproducer check-cards` / `build-card CARD...` | Validate task cards; have the local LLM write modules and gate them |

## Develop

```
pytest tests modules   # about 700 tests; takes several minutes
coproducer lint        # must print "lint clean"
```

Modules are authored as bundle files with `tools/unbundle.py`. A new module is one folder under `modules/<layer>/<name>/` with `<name>.py`, `module.toml`, `test_<name>.py`. The rules are in `skills/module-authoring/references/catalog/rules.md`.

## Sources checked on 2026-10-18

- [FL Studio MIDI scripting manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm) and [piano roll scripting](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll_scripting_api.htm)
- [FL Studio API stubs](https://il-group.github.io/FL-Studio-API-Stubs/) (the L1 ops and the piano roll `Note` and `score` calls come from these)
- [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) and its [inference guide](https://github.com/ACE-Step/ACE-Step-1.5/blob/main/docs/en/INFERENCE.md)
- [Demucs](https://github.com/adefossez/demucs), [Basic Pitch](https://github.com/spotify/basic-pitch), [Music Flamingo](https://huggingface.co/nvidia/music-flamingo-hf)
