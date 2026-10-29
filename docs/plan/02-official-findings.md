# 02. What the Official Documentation Says

This file is the fact register. It exists because earlier assumptions came from stale search snippets and were corrected by official pages. Every API fact the design depends on is listed with an id, a source, a status tag, and its design consequence.

Authority order for any FL API fact:

1. The live interpreter on your machine and the Gate 0 API inventory probe.
2. The [Image-Line MIDI scripting manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm).
3. The [FL Studio API stubs reference pages](https://il-group.github.io/FL-Studio-API-Stubs/) for signatures and API version tags. The [stubs repository](https://github.com/IL-Group/FL-Studio-API-Stubs) now describes itself as unmaintained and points back to the manual.
4. Everything else is prior art and is never authority.

Tags: READ means opened and read for this plan. SEEN means only in search results. PROBE means it can only be settled on your machine at Gate 0.

## 1. Fact register

### 1.1 Controller scripting

| ID | Fact | Source | Tag | Design consequence |
| --- | --- | --- | --- | --- |
| FX-01 | Python inside FL cannot open files. Disk access is disabled in the embedded interpreter. | [Mixer tracks reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/mixer/tracks/) | READ | All data crosses into and out of FL by MIDI SysEx over virtual MIDI ports. FL-side code never touches disk. |
| FX-02 | A controller script lives at `Documents\Image-Line\FL Studio\Settings\Hardware\<name>\device_<name>.py`. Its first line names it. It is selected as the controller type in MIDI Settings. | [MIDI scripting manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm) | READ | The FL-side footprint is one controller script (generated) plus one piano roll script. Setup installs and verifies both. |
| FX-03 | The scripting modules are `playlist`, `channels`, `mixer`, `patterns`, `arrangement`, `ui`, `transport`, `device`, `plugins`, `general`, `launchMapPages`, `screen`. Events include `OnInit`, `OnMidiIn`, `OnIdle`, `OnRefresh`. | [MIDI scripting manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm) | READ | L1 ops are generated per module. The dispatcher runs work on `OnIdle` to avoid blocking FL. |
| FX-04 | A script output window shows prints and has Interpreter and Reload controls. | [MIDI scripting manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm) | READ | Setup instructs the user to keep it open during Gate 0. The inventory probe prints there as a fallback channel. |
| FX-05 | The embedded Python is based on roughly Python 3.9. Which standard library modules import inside FL is not documented in the pages read. | [FL MIDI scripting 101](https://flmidi-101.readthedocs.io/en/latest/scripting/fl_midi_api.html) | SEEN | PROBE: Gate 0 tests whether `json` imports in FL. If not, the bridge uses a compact delimited text body. |
| FX-06 | API version tags (for example "API v36") differ from FL Studio version numbers. | [Plugins reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/plugins/) | READ | Modules declare a minimum API version, not an FL version. Gate 0 records your live number. |

### 1.2 Plugins and parameters

| ID | Fact | Source | Tag | Design consequence |
| --- | --- | --- | --- | --- |
| FX-07 | The `plugins` module reads and writes parameters only. Nothing loads, inserts, removes, or reorders a plugin. | [Plugins reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/plugins/) | READ | Plugin loading is a GUI recipe in `desktop-control`. |
| FX-08 | Parameters are addressed by index. Values are floats from 0 to 1. A slot index of -1 addresses a channel rack plugin. | [Plugins reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/plugins/) | READ | `set_plugin_param_by_name` builds a name to index map at runtime and normalizes values. |
| FX-09 | A VST exposes 4096 parameters plus 128 CC slots and 16 aftertouch slots. Unused ones have empty names. | [Plugins reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/plugins/) | READ | `build_param_map` skips empty names and caches the result per plugin and version. |

### 1.3 Notes, patterns, and the piano roll

| ID | Fact | Source | Tag | Design consequence |
| --- | --- | --- | --- | --- |
| FX-10 | `channels.midiNoteOn` plays a live note and does not write a note into a pattern. A quick-quantize function exists. | [Channel notes reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/channels/notes/) | READ | Notes are written by a generated piano roll script or by importing a MIDI file. |
| FX-11 | Piano roll scripts are `.pyscript` files with a separate API (`flpianoroll`) that exists only inside piano roll scripts. The factory script folder holds a `Piano roll script reference.txt` that MAY be newer than the web page. | [Piano roll scripting](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll_scripting_api.htm) | READ | Gate 0 reads the reference file from your install and treats it as authority. |
| FX-12 | Whether a piano roll script can read an input file from disk is not stated in the pages read. | n/a | PROBE | Two note-writing routes are specified, and Gate 0 decides the primary. Route N1: generate a `.pyscript` whose body embeds the notes. Route N2: import a MIDI file through the GUI. |
| FX-13 | FL Studio 25.2.2 added mixer tracks as needed on MIDI import. FL Studio 2026 can open `.mid` files as scores. | [What's new in 25](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new_25.htm), [What's new in 26](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new.htm) | READ | MIDI import is a first-class route for bulk notes. |

### 1.4 Transport and mixer

| ID | Fact | Source | Tag | Design consequence |
| --- | --- | --- | --- | --- |
| FX-14 | `transport.start` toggles play and pause. Loop mode also toggles. | [Transport reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/transport/) | READ | Wrappers read state first and act only if needed (`ensure_playing`, `ensure_loop_mode`), so every call is idempotent. |
| FX-15 | Mixer track peaks are readable per track, with 1.0 equal to 0 dB. Route levels are settable (API v36). | [Mixer tracks reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/mixer/tracks/) | READ | Gain staging polls peaks inside FL. Peaks are not loudness, so final loudness comes only from rendered audio. |
| FX-16 | FL Studio 2026 added pattern length, swing, and clear-pattern scripting, plus undo flags and clone-pattern destinations. FL 25.2.4 added tempo, time base, and numerator setters. | [What's new in 26](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new.htm), [What's new in 25](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new_25.htm) | READ | Target 2026.1.7. Modules that need these declare the API level and refuse to run below it. |
| FX-17 | FL silently ignores some scripted writes. | [Postfader MCP listing](https://pypi.org/project/postfader-fl-studio-mcp/) (prior art) | READ | Every write is read back and reports `verified`. |

### 1.5 Capture and export

| ID | Fact | Source | Tag | Design consequence |
| --- | --- | --- | --- | --- |
| FX-18 | FL Studio renders from the command line: `FL.exe /R[filename] /E<formats> /F<folder> /O<outfolder> project.flp`. | [Export reference](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_save_export.htm) | READ | Primary capture route. No Export dialog and no GUI. Requires a saved project copy. |
| FX-19 | The Export dialog has a Split mixer tracks option that writes one WAV per mixer track. | [Export reference](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_save_export.htm) | READ | Stems come from a GUI recipe, or from Demucs on a full render. PROBE whether the CLI honors split settings. |
| FX-20 | The Audio Logger keeps Master audio in memory only and does not write to disk. | [Tools menu](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/menu_tools.htm) | READ | Not used for capture. |
| FX-21 | FL Studio has a built-in Extract Stems tool for audio clips (UI only). | [What's new in 25](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new_25.htm) | READ | MAY cross-check Demucs. Not scriptable. |
| FX-22 | FL Studio 2026 shipped July 7, 2026, with maintenance updates through 2026.1.7 on September 28, 2026. | [What's new in 26](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new.htm) | READ | Decision D-03: update to 2026.1.7 before Gate 0. |
| FX-23 | The executable name, where the rendered file lands, and whether the API can save a project are not stated in the pages read. | n/a | PROBE | Gate 0 probes: save-project route (API, hotkey GUI recipe, or manual), executable path, output location. |

## 2. Model and tool facts

| ID | Fact | Source | Tag | Design consequence |
| --- | --- | --- | --- | --- |
| M-01 | ACE-Step 1.5 is MIT licensed and needs Python 3.11 to 3.12. Its README lists a 12 to 16 GB tier using a 2B turbo or SFT model with a 0.6B or 1.7B language model. The 4B XL model needs offload or quantization at 12 GB. Cover and repaint tools exist. The 1.7B language model is rated medium at audio understanding and melody copying. | [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) | READ | Primary generator and reference-sketch tool. Melody preservation MUST NOT depend on it. Its own isolated environment. |
| M-02 | ACE-Step publishes a VST3 plugin repository. | [acestep.vst3](https://github.com/ace-step/acestep.vst3) | SEEN | A later option. Loading it would be a GUI recipe. |
| M-03 | Demucs separates stems (4 or 6). The `libretta` listing describes small weights. | [libretta on PyPI](https://pypi.org/project/libretta/) | SEEN | Stem separation adapter. Silent and leaky stems MUST be detected. |
| M-04 | Basic Pitch does polyphonic audio to MIDI with pitch bend. One Windows install note says to pin an older version when the default build fails. | [libretta on PyPI](https://pypi.org/project/libretta/), [AceForge](https://github.com/audiohacking/aceforge) | SEEN | Transcription adapter. Installer pins and verifies. Human review of melody MIDI. |
| M-05 | Music Flamingo (NVIDIA) is an 8B audio-language model. The model card lists Linux and A100/H100 as tested hardware, a non-commercial license, and a newer 2601 checkpoint. | [Music Flamingo](https://huggingface.co/nvidia/music-flamingo-hf) | READ | OPTIONAL critique model. Needs 4-bit quantization or offload at 12 to 16 GB. DSP-only critique is the fallback. |
| M-06 | The MCP Python SDK is the standard way to build the servers. | [MCP Python SDK docs](https://py.sdk.modelcontextprotocol.io/), [mcp on PyPI](https://pypi.org/project/mcp/) | SEEN | Servers use the official SDK. Version pinned at Gate 0. Re-check the current release when building. |
| M-07 | `pyloudnorm` implements ITU-R BS.1770 loudness metering in Python. | [pyloudnorm on PyPI](https://pypi.org/project/pyloudnorm/0.0.1) | SEEN | Candidate for integrated loudness. Gate 0 verifies against reference signals. A true peak measurement is written separately with oversampling. |
| M-08 | GUI-grounding models exist as open weights (UI-TARS, UGround, GUI-Actor, among others). | [UGround](https://github.com/OSU-NLP-Group/UGround), [GUI-Actor](https://microsoft.github.io/GUI-Actor/), [GUI grounding survey](https://www.perea.ai/research/gui-grounding-models-2026) | SEEN | Candidates for the `ground_gui_element` adapter. Chosen at Phase 0 by click accuracy on FL screenshots. |
| M-09 | Small agentic and coding models that fit in 16 GB at 4-bit exist and are ranked by several 2026 roundups. | [KDnuggets](https://www.kdnuggets.com/top-7-coding-models-you-can-run-locally-in-2026), [Morph best Ollama models](https://www.morphllm.com/best-ollama-models) | SEEN | Shortlist taken at Phase 0 and benchmarked on this project's own tool-call tasks. No model is fixed in this plan. |
| M-10 | Large SysEx messages are truncated or split at fixed sizes in some MIDI stacks (240, 256, and 4096 byte limits appear in reports). | [JUCE forum](https://forum.juce.com/t/sysex-midi-message-truncated-to-240-bytes/67818), [ALSA report](https://www.midimusicadventures.com/phpbb/viewtopic.php?p=18500) | SEEN | The bridge frames payloads at a conservative size and Gate 0 measures the real limit through loopMIDI and FL. |

## 3. Prior art, read as pitfalls only

| Project | What it taught | How it is used |
| --- | --- | --- |
| [rosasynthesiz/flstudio-mcp](https://github.com/rosasynthesiz/flstudio-mcp) | The scripting API cannot load plugins or audio files or render audio | Confirms the need for GUI recipes. Nothing reused. |
| [Postfader](https://pypi.org/project/postfader-fl-studio-mcp/) | Scripted writes can be silently ignored; verified writes; flag-gated writes; fake API for tests | Design ideas only. It is macOS only. Nothing reused. |
| [Flapi](https://github.com/MaddyGuthridge/Flapi) | Remote control of the FL API over MIDI exists, last release April 2024 per PyPI | Evidence the SysEx approach is viable. Not used. |

No code, schemas, or tool names from these projects enter this build.

## 4. Corrections the official pages forced

| Earlier assumption | What the official source showed | Change |
| --- | --- | --- |
| Capture would need GUI automation or audio loopback | The command-line render exists (FX-18) | CLI render is primary. Loopback is dropped. |
| The stubs package is the API authority | The stubs repo is marked unmaintained (FX-02 note) | Manual, live interpreter, and the inventory probe are authority. |
| FL 25.x is current | FL Studio 2026 is current (FX-22) | Target 2026.1.7. |
| Existing FL MCP could be a base | You decided on a clean-room build | Prior art only. |
| One Python environment for all models | ACE-Step pins Python 3.11 to 3.12 (M-01) | One isolated environment per stack. |
