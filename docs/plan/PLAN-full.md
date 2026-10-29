# FL Studio AI Co-Producer: Full-Scope Plan (combined)

Combined edition of files 00 to 15. As of October 18, 2026.

## Contents

- FL Studio AI Co-Producer: Full-Scope Plan (`00-index.md`)
- 01. Vision and Spec Sheet (`01-vision-and-spec.md`)
- 02. What the Official Documentation Says (`02-official-findings.md`)
- 03. Architecture (`03-architecture.md`)
- 04. The Module System (`04-module-system.md`)
- 05. Module Catalog (`05-module-catalog.md`)
- 06. Task Cards and the Local-Agent Build Loop (`06-task-cards.md`)
- 07. The Orchestration Layer (`07-orchestrator.md`)
- 08. The Python Layer and the Local Models (`08-python-layer-and-models.md`)
- 09. Workflows (`09-workflows.md`)
- 10. Workstream B: Skills (`10-skills.md`)
- 11. Testing and Verification (`11-testing.md`)
- 12. Roadmap: Parallel Lanes and Gates (`12-roadmap.md`)
- 13. Risks, Decisions, and Open Questions (`13-risks-and-decisions.md`)
- 14. Sources (`14-sources.md`)
- 15. As Built: What Changed Between the Plan and the Code (`15-as-built.md`)

---

# FL Studio AI Co-Producer: Full-Scope Plan

Owner: Mark ("Meeps"). Status as of October 18, 2026. Version 1.0 of the plan.

This is a clean-room build plan for a local-first AI co-producer for FL Studio. Nothing here forks, extends, or depends on any existing FL Studio MCP. Existing public projects are read only as prior art for pitfalls, and each is named as such where it appears.

The system has three workstreams that ship together on one shared foundation:

| Workstream | What it is | Main files |
| --- | --- | --- |
| A. MCP servers | Four new MCP servers that give a local model hands inside FL Studio, ears on the audio, access to local generative models, and a screen-control fallback | 03, 04, 05, 07 |
| B. Skills | Twelve skills as built (eleven planned) that teach local models how to produce, mix, gain stage, master, and restyle, and how to build the system's own modules | 10 |
| C. Python layer | Installers, environments, GPU scheduler, model registry, and the orchestration loop that drives plan, act, listen, measure, critique | 07, 08, 09 |

## How to read this plan

Read in this order if you are new to it: 01, 02, 03, 04. Then read 12 (roadmap) and 13 (risks and decisions). Files 05 and 06 are the build inventory. Files 07 to 11 are the detailed designs. File 14 lists every source with its verification status.

| File | Contents |
| --- | --- |
| [01-vision-and-spec.md](01-vision-and-spec.md) | Vision, spec sheet, success criteria, verifiability classes, autonomy table, failure modes |
| [02-official-findings.md](02-official-findings.md) | What the official Image-Line documentation says, as a numbered fact register, and the design consequence of each fact |
| [03-architecture.md](03-architecture.md) | Servers, process boundaries, data flows, the SysEx bridge protocol, sandbox, capture routes, repository layout |
| [04-module-system.md](04-module-system.md) | The module rules, the Result type, the manifest, the linter, side-effect classes, generated documentation |
| [05-module-catalog.md](05-module-catalog.md) | Every planned module by layer, with one job each |
| [06-task-cards.md](06-task-cards.md) | The task card template, the build loop, and the ten calibration cards in full |
| [07-orchestrator.md](07-orchestrator.md) | Registry loader, tool exposure, planner, executor, verifiers, ledger, collaboration protocol |
| [08-python-layer-and-models.md](08-python-layer-and-models.md) | Installers, isolated environments, model registry, GPU scheduler, benchmarks, Windows specifics |
| [09-workflows.md](09-workflows.md) | Module-by-module sequences for new tracks, style transfer, mixing, gain staging, mastering, and GUI fallback |
| [10-skills.md](10-skills.md) | Specification and eval prompts for each of the eleven skills |
| [11-testing.md](11-testing.md) | Test pyramid, fake FL harness, synthetic audio, contract tests, gate acceptance tests |
| [12-roadmap.md](12-roadmap.md) | Phases, gates, work packages, parallel lanes |
| [13-risks-and-decisions.md](13-risks-and-decisions.md) | Decision log, risk register, open questions, assumptions to confirm |
| [14-sources.md](14-sources.md) | Sources with links and a status for each: opened and read, or seen in search results only |
| [15-as-built.md](15-as-built.md) | Where the build differs from the plan, the counts as built, and what is not built |

A single combined file, `PLAN-full.md`, contains all of the above in order, including file 15. The module count quoted across the plan (about 230) comes from file 05; the as-built count is 250 (file 15).

## Conventions

1. **Requirement language.** The words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY follow RFC 2119. Anything written as a plain statement of fact is either cited or marked as an assumption.
2. **Fact status tags.** Every external claim carries one of three tags in file 02 and file 14:
   - **READ**: the page was opened and read for this plan.
   - **SEEN**: the claim appeared in a search result and has not been opened. Verify before relying on it.
   - **PROBE**: the claim can only be settled on your machine. Gate 0 contains a probe for it.
3. **Decisions.** Where you said "you decide", the decision is in the decision log in file 13 with its reason and the condition that would reverse it.
4. **Numbers.** Module counts, line budgets, and VRAM figures are planning estimates unless tagged READ. Gate 0 replaces the estimates with measured values.
5. **Style.** No em dashes in any delivered document. Ranges use the word "to".
6. **Dates.** All "latest version" statements are as of October 18, 2026. Re-check any version-dependent fact before building on it.

## Glossary

| Term | Meaning |
| --- | --- |
| Sandbox copy | A duplicate of your FL project in a dedicated folder. The agent writes only here. |
| Promotion | The human-approved act of copying results from the sandbox into a real project. Never automatic. |
| Module | One function with one job, with a manifest and tests. The unit of build, test, and exposure. |
| Registry | The set of modules that passed the linter. The orchestrator sees only registered modules. |
| Task card | A one-page work order for a local coding model to produce one module. |
| Gate | A checkpoint with executable acceptance tests. Work does not move past a gate without passing them. |
| Invariants file | The written definition of what "preserving the spirit" means for one track: key, melodic contour, rhythm motif, harmonic loop, section order, energy arc. |
| Genre profile | A data file describing a target genre's tempo range, drum templates, bass family, structure, and mix targets. |
| Spec sheet | The per-project source of truth for goals, targets, and decisions. Updated before behavior changes. |
| Ledger | The append-only run log from which any run can be audited or resumed. |
| Bridge | The MIDI SysEx channel over virtual ports that carries requests into FL Studio and replies out of it. |
| Capture | Producing an audio file of the project so that it can be measured. |

## Method note

The plan follows the Spec, Verifier, Environment, Loop method from your agentic prompt architect file. File 01 is the spec sheet. Verifiers are named for every requirement. The environment is the sandbox. The loop is plan, act, capture, measure, critique, reconcile, and it runs under the autonomy table in file 01.

---

# 01. Vision and Spec Sheet

## 1. Vision

Build a local-first AI co-producer that listens to an FL Studio project, makes changes through purpose-built MCP servers, and returns production-ready stems and a master, with you approving every creative decision.

"True vibe creation" here means a creative partner, not an autopilot. The system proposes, performs, measures, and explains. You steer by feel and approve by ear. The system never claims a result sounds good. It reports measured facts and asks you to judge the feel.

Four capabilities define the product:

1. **Create.** Generate new tracks and samples with local models, and build them inside FL Studio using real instruments and plugins.
2. **Listen.** Render the project, measure it, and critique it, repeatedly, without a human having to bounce files by hand.
3. **Restyle.** Take an existing track and move it to another genre (for example techno to dubstep) while preserving the melody, the original idea, and the spirit, and making the sound more production ready.
4. **Co-produce.** Work with you on mixing, gain staging, and mastering, asking at the right moments and explaining every change.

When the FL scripting API cannot do something (loading a plugin, loading an audio file, exporting split stems), a desktop-control server lets the local model operate the FL Studio interface directly, under guardrails.

## 2. Spec sheet

This is the single source of truth. Every later change lands here first.

| Field | Decision |
| --- | --- |
| Goal | A collaborative local AI producer: generate new tracks, restyle existing ones while keeping melody and spirit, and mix, gain stage, and master with you |
| User | You: a senior infrastructure engineer comfortable with Python, MCP, and scripting, working in FL Studio on Windows |
| Inputs | Your FL project, audio files, sample and plugin libraries, reference tracks, plain-language direction |
| Outputs | A sandbox project copy, rendered stems, a master, a change log, a measurement report for every pass, MIDI of preserved melodies |
| Hardware | Windows, 12 to 16 GB VRAM |
| FL Studio | 2026 (26.x), Producer edition or higher. Target build 2026.1.7. See decision D-03 in file 13 |
| Constraints | Local models only for the creative loop. No cloud audio. Python inside FL stays within FL's embedded interpreter limits. The agent never writes to your original project. |
| Verification authority | Measured DSP for anything numeric. You for anything about feel, spirit, or taste. |
| Autonomy | Full autonomy inside a sandbox copy. Promotion to a real project is a human gate. |
| Build order | All three workstreams in parallel on one shared foundation (Gate 0) |
| Edge cases | Silent or leaky stems after separation. Dense polyphonic pads that transcribe badly. Plugins with unexposed parameters. Plugins that must be loaded through the GUI. Mid-song tempo changes. |
| Assumptions to confirm | FL Studio 2026.1.7 installed. loopMIDI installed. Python 3.10 or newer outside FL. One resident GPU model at a time. |

## 3. Scope

### In scope

1. Four MCP servers: `fl-bridge`, `studio-audio`, `studio-ml`, `desktop-control`.
2. About 200 to 250 small modules in seven layers (file 05), most of the largest layer generated from the official function tables.
3. Eleven skills (file 10).
4. A Python project, `coproducer`, with installers, environments, a model registry, a GPU scheduler, and the orchestration loop.
5. A fake FL harness and synthetic audio fixtures so the system is testable without FL running.
6. Genre profiles, an invariants file format, and loudness and balance target files, all filled in from cited sources and from your own references. The plan does not hardcode them.

### Out of scope

1. Replacing your ears. The system does not decide what sounds good.
2. Cloud services for audio generation, analysis, or critique.
3. macOS and Linux for the FL-facing parts. The audio and model parts MAY run on any OS, but the FL bridge and desktop control are specified for Windows.
4. Automatic promotion to your real projects.
5. Training or fine-tuning models. Only installing, running, and benchmarking.
6. Distribution, licensing, or marketplace packaging.

## 4. Success criteria

Done means all of these hold and are checkable without trusting a model's opinion.

| ID | Criterion | Check |
| --- | --- | --- |
| S-01 | A test techno track returns as a dubstep version with the same key and a melody similarity above your threshold, in a sandbox copy | Invariants check (file 09, W2), then your A/B approval |
| S-02 | Every mix and master pass reports integrated loudness, true peak, crest factor, spectrum, mid/side, and correlation against targets you set | Measurement report exists for each pass and matches the targets file |
| S-03 | Every change the agent makes is logged, reversible, and absent from your original project | Original project file hash is identical before and after; ledger shows snapshot ids |
| S-04 | Every write to FL is read back and reports verified true or false | Ledger has a `verified` field on every write step; no step lacks it |
| S-05 | The agent completes at least one task that needs the GUI (for example loading a plugin) with screenshot-verified steps | Gate 2 test |
| S-06 | A new local coding model can produce a registered module from a task card with at most one retry for most cards | Calibration set results (file 06) |
| S-07 | The whole system installs on a clean Windows machine with one setup command and passes a smoke test per model | `coproducer setup` then `coproducer doctor` |

## 5. Verifiability classes

Every requirement is classified, because a requirement without a verifier is a wish.

| Class | Meaning | Who verifies | Example |
| --- | --- | --- | --- |
| V3 | Mechanical. A tool returns pass or fail. | The system | True peak below ceiling; project file unchanged |
| V2 | Criterial. Checkable against written criteria, with a score. | The system, with the score shown to you | Melody similarity above threshold; stems not silent |
| V1 | Judgment. Taste and feel. No written criteria. | You | Does it keep the spirit; does it sound production ready |
| V0 | Unverifiable. No check exists. | Nobody | MUST NOT be acted on by the agent. Convert to V1 by asking you, or drop it. |

Rule: V1 items MAY be proposed and prepared by the system but MUST NOT be declared done by it. A V1 item becomes V2 when you supply written criteria (for example "bass is mono below 120 Hz and within 3 dB of the reference's low band").

## 6. Verifier map

| Requirement | Class | Verifier module or gate |
| --- | --- | --- |
| Loudness at target | V3 | `measure_integrated_loudness`, `compare_to_reference` |
| True peak below ceiling | V3 | `measure_true_peak` |
| No clipped samples | V3 | `count_clipped_samples` |
| Low end mono-compatible | V3 | `measure_low_end_mono_ratio` |
| Key preserved | V2 | `estimate_key_dsp` compared on source and result |
| Tempo as specified | V3 | `estimate_bpm_dsp`, read back tempo from FL |
| Melody preserved | V2 | `compare_note_sequences`, `extract_melody_contour` comparison, then V1 human A/B |
| Stems usable | V2 | `detect_silence`, `detect_leakage` |
| Write to FL took effect | V3 | Every `*_verified` L2 wrapper |
| GUI step took effect | V3 | `screenshot_verify` with expected-change check |
| Original project untouched | V3 | File hash compare in promotion gate |
| Sounds production ready | V1 to V2 | Checklist module plus your listen |
| Spirit of the original | V1 | You, by A/B |

## 7. Autonomy table

Each module declares a level in its manifest. The orchestrator enforces the level at the call.

| Level | Name | Behavior | Examples |
| --- | --- | --- | --- |
| A0 | Observe | Reads only. No approval needed. | Read project summary, measure a file, list plugin parameters |
| A1 | Propose | Prepares a change and shows it. Waits for your approval before applying. | A mix plan, a melody MIDI for review, a genre profile choice |
| A2 | Act in sandbox | Applies and self-verifies in the sandbox copy. No approval per step. Logged and reversible. | Set a fader, add a send, render a bounce, run a GUI recipe |
| A3 | Promote | Touches anything outside the sandbox: your real project, files outside the sandbox folder, installers. | Copy sandbox results into a real project; always human |

Rules:

1. A2 is the ceiling for any autonomous run. A3 MUST NOT be executed without an explicit human action in the same session.
2. Any V1 decision gates at A1 regardless of the module's own level.
3. Passwords, installers, license dialogs, and any dialog the agent does not recognize force a halt and a question.

## 8. Failure modes

The architect method requires naming how the system fails. Each row has a defense that is part of the design, not an afterthought.

| ID | Failure | Why it happens | Defense |
| --- | --- | --- | --- |
| F-01 | A scripted write is silently ignored by FL | FL accepts some calls and does nothing | Read back every write; report `verified`; never retry blindly |
| F-02 | The model hallucinates a tool or argument | Small models invent names | Tools are generated from manifests; schemas validated before the call; unknown names return `E_NOT_FOUND` with the nearest valid names |
| F-03 | The model drifts from the plan in a long run | Small context windows | Plan file on disk; each step re-reads its slice; context contains only the current phase's tools |
| F-04 | Level changes wreck a mix | The model chases loudness | Gain-staging first; changes limited by per-step delta caps in the spec sheet; every pass measured against your targets |
| F-05 | Restyle loses the melody | Generative cover models regenerate rather than preserve | Melody comes from transcribed MIDI, not from generation; invariants file; similarity check; your A/B |
| F-06 | Transcription is wrong on dense pads | Polyphonic audio to MIDI is lossy | Human review gate on melody MIDI; chord-loop detection as a cross-check |
| F-07 | GUI automation clicks the wrong thing | Custom-drawn UI, no accessibility tree | Window-scoped input; before and after screenshots with expected-change checks; action budget; halt hotkey |
| F-08 | GPU out-of-memory | Two heavy models resident | One resident heavy model; scheduler refuses loads that will not fit; DSP-first analysis |
| F-09 | The agent changes your real project | Path confusion | Sandbox path is checked in every FL-writing module; promotion is A3; hash check before and after |
| F-10 | API drift between FL versions | Official docs and stubs lag builds | Gate 0 inventory probe; modules declare minimum API version and refuse to run below it |
| F-11 | Bridge data is corrupted or lost | SysEx over virtual ports | Framing, sequence numbers, checksums, request ids, timeouts, bounded retries for idempotent reads only |
| F-12 | A module quietly grows past what a small model can maintain | Scope creep | Linter size budget and one-function rule are gates, not guidelines |
| F-13 | Loudness numbers are measured on the wrong thing | Peak meter mistaken for loudness | Peaks from FL are used only for gain staging; loudness only from a rendered file |
| F-14 | Capture is stale | Render came from before the last change | Capture modules record the snapshot id and project hash; measurement reports carry them |
| F-15 | Licenses block use | Some models are non-commercial | Model registry stores license; non-commercial models are optional with a fallback |

## 9. Acceptance tests at the spec level

These are the end-to-end tests that the gate tests in file 11 roll up to.

1. **AT-1, Bridge:** With FL running and the dispatcher script loaded, `ping_fl` returns FL's version and API level within 2 seconds.
2. **AT-2, Verified write:** Setting a mixer track volume returns `verified: true` and the ledger shows a snapshot id. Rolling back restores the previous value.
3. **AT-3, Capture:** `render_via_cli` on a saved sandbox copy produces a WAV, and `measure_integrated_loudness` returns a number.
4. **AT-4, Fault injection:** With the fake FL set to ignore writes, every L2 wrapper returns `verified: false` and the orchestrator does not proceed.
5. **AT-5, Restyle:** The S-01 test passes on a known techno test project.
6. **AT-6, Safety:** A deliberate attempt to write outside the sandbox is refused with `E_SANDBOX_VIOLATION`.
7. **AT-7, GUI:** A GUI recipe loads a plugin and the post-condition screenshot check passes.
8. **AT-8, Resume:** Killing the orchestrator mid-run and restarting resumes from the ledger without repeating verified steps.

---

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

---

# 03. Architecture

## 1. Shape of the system

Four MCP servers sit between the agent brain (a local tool-calling model) and the world. Measurement and transformation are kept apart from generative models. Every path that touches FL Studio ends in the sandbox copy.

```
                          +-----------------------------+
                          |  Agent brain (local LLM)    |
                          |  sees only the tool slice   |
                          |  for the current phase      |
                          +--------------+--------------+
                                         |  MCP (stdio)
                          +--------------v--------------+
                          |  Orchestrator (coproducer)  |
                          |  registry, planner,         |
                          |  executor, scheduler,       |
                          |  ledger, spec sheet         |
                          +--+------+--------+-------+--+
                             |      |        |       |
              +--------------v+  +--v-------+ +-----v----+ +v---------------+
              | fl-bridge     |  | studio-  | | studio-  | | desktop-       |
              | state in FL   |  | audio    | | ml       | | control        |
              | (L0,L1,L2,L3) |  | (L4)     | | (L5)     | | (L6)           |
              +------+--------+  +----+-----+ +----+-----+ +-------+--------+
                     | SysEx          |            |               | screenshots,
                     | over loopMIDI  |            |               | mouse, keys
              +------v--------+       |            |               |
              | FL Studio     |<------+-- files ---+  render CLI   |
              | dispatcher    |   (bounces, stems, MIDI)          |
              | script +      |<----------------------------------+
              | piano roll    |        GUI recipes (load plugin, import MIDI, export stems)
              | script        |
              +---------------+
```

File flows are shown as `files` in the diagram: bounces and stems flow from FL to `studio-audio`, and generated audio and MIDI flow from `studio-ml` into the sandbox folder.

### The four servers

| Server | Job | Layers it hosts | Runs where |
| --- | --- | --- | --- |
| `fl-bridge` | Read and write project state inside FL, with verification and rollback | L0 transport, L1 FL ops (as remote calls), L2 verified wrappers, L3 recipes | Host Python, talks to FL over SysEx |
| `studio-audio` | Measure and transform audio and note data | L4 measures | Host Python, CPU only |
| `studio-ml` | Run generative, transcription, separation, critique, and vision models | L5 model adapters | One isolated environment per model stack, started on demand |
| `desktop-control` | Operate the FL interface when the API cannot | L6 primitives and recipes | Host Python on the interactive Windows session |

Why four and not one: failures, dependencies, and permissions differ. `studio-audio` is deterministic and cheap. `studio-ml` is heavy and optional. `desktop-control` is the only server that can act outside FL's data model, so it has its own guardrails and can be disabled alone. `fl-bridge` is the only server that writes project state.

## 2. Process boundaries

| Process | Environment | Why separate |
| --- | --- | --- |
| FL Studio | FL's embedded Python (about 3.9) | Cannot be changed. Only the dispatcher and the piano roll script run here. |
| Orchestrator and `fl-bridge`, `studio-audio`, `desktop-control` | One host venv, Python 3.10+ | Share the module registry and the Result type |
| `studio-ml` model stacks | One venv each: ACE-Step (3.11 to 3.12), Demucs, Basic Pitch, critique model, vision model, LLM runtime | Conflicting pins (ACE-Step requires 3.11 to 3.12); isolation keeps one broken install from breaking the rest |
| Local LLM runtime | A separate server process exposing an OpenAI-compatible endpoint | The runtime is swappable. The orchestrator only needs an endpoint. |

Servers use the official [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/) over stdio. Tool definitions are generated from module manifests, not written by hand.

## 3. The FL-side footprint

Only two files live inside FL's data folders. Both are generated.

| File | Location | Job |
| --- | --- | --- |
| `device_coproducer.py` | `Documents\Image-Line\FL Studio\Settings\Hardware\coproducer\` | Controller script. First line `# name=Coproducer`. Receives SysEx, dispatches to L1 ops, replies with SysEx. |
| `coproducer_notes.pyscript` | `Documents\Image-Line\FL Studio\Settings\Piano roll scripts\` | Writes notes into the piano roll. Body is generated per call (route N1) or reads a staged file if Gate 0 proves that is allowed (route N2a). |

The dispatcher MUST be small and dumb. It contains: a SysEx receiver, a frame reassembler, a table mapping op names to L1 functions, a reply sender, and an idle-time work queue. It MUST NOT contain any music logic, retries, or policy. All judgment lives in the host.

The controller script is selected as the controller type in MIDI Settings, as the [MIDI scripting manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm) describes. Setup prints exact click-path instructions and then verifies by calling `ping_fl`.

## 4. The bridge protocol (SysEx over virtual MIDI)

This is the contract between `fl-bridge` and the dispatcher. It is frozen at Gate 0.

### 4.1 Transport

1. Two virtual MIDI ports from [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html): `coproducer-in` (host to FL) and `coproducer-out` (FL to host).
2. The host sends SysEx on `coproducer-in`. FL's controller script receives it in its SysEx handler and replies with the `device` module's SysEx output function on `coproducer-out`. Gate 0 confirms the exact handler and function names against the live API inventory.
3. Port names are discovered by `find_midi_ports`, never hardcoded.

### 4.2 Frame format

All bytes inside a SysEx message MUST be 7-bit (0x00 to 0x7F).

```
F0 7D 43 50  VV  TT  RR RR  SS SS  NN NN  <payload bytes, 7-bit packed>  CC  F7
|  |  |  |   |   |   |      |      |
|  |  |  |   |   |   |      |      +-- total frame count (14 bit, big-endian 7-bit pair)
|  |  |  |   |   |   |      +--------- sequence number of this frame (14 bit)
|  |  |  |   |   |   +---------------- request id (14 bit)
|  |  |  |   |   +-------------------- message type (see below)
|  |  |  |   +------------------------ protocol version (starts at 0x01)
|  +--+--+---------------------------- 0x7D (non-commercial id) then ASCII 'C','P'
+------------------------------------- SysEx start
```

1. Manufacturer byte 0x7D is the MIDI reserved id for non-commercial and experimental use. Then the two ASCII bytes `C` (0x43) and `P` (0x50) tag the stream so other SysEx traffic is ignored.
2. `CC` is a checksum: the sum of all bytes from `VV` through the last payload byte, masked to 7 bits.
3. Payload size per frame is `max_payload`, default 200 bytes after packing, a conservative value below the 240 and 256 byte truncation points seen in the reports in file 02 (M-10). Gate 0 measures the real limit and may raise it.
4. A message larger than `max_payload` is split by `split_frames` and rebuilt by `join_frames`.

### 4.3 Message types

| TT | Name | Direction | Meaning |
| --- | --- | --- | --- |
| 0x01 | REQUEST | host to FL | Call one op |
| 0x02 | REPLY | FL to host | Result of a request |
| 0x03 | ERROR | FL to host | The op raised or the arguments failed validation |
| 0x04 | PING | host to FL | Liveness |
| 0x05 | PONG | FL to host | Liveness reply with FL and API versions |
| 0x06 | ACK | either | Frame group received |
| 0x07 | EVENT | FL to host | Unsolicited state change (play state, peak batch) |

### 4.4 Payload encoding

1. The body is bytes. Bytes are converted to 7-bit form by `encode_sysex` in groups of 7: for each group of up to 7 input bytes, emit one header byte whose bit `i` holds the top bit of input byte `i`, followed by the input bytes with their top bit cleared. A partial final group of `n` bytes emits `n + 1` bytes.
2. Request body: UTF-8 text `op_name` then a unit separator (0x1F) then each argument as a JSON scalar or small JSON value, separated by 0x1F. If Gate 0 shows `json` is not importable inside FL, arguments are restricted to integers, floats, booleans, and strings, using a tiny parser that the generator emits into the dispatcher.
3. Reply body: the same encoding for the return value.
4. Floats are sent as decimal text with at least 9 significant digits, so a 0 to 1 parameter value round-trips.

### 4.5 Behavior rules

1. The host assigns request ids. A reply carries the same id. `match_reply` pairs them.
2. `wait_for_reply` enforces a timeout (default 2 seconds for reads, 5 for writes). On timeout the result is `E_TIMEOUT`.
3. Reads MAY be retried up to 2 times. Writes MUST NOT be retried blindly. After a write timeout the host reads state to learn whether it landed.
4. The dispatcher processes at most one request at a time and does its work in the idle handler to keep FL responsive.
5. Large replies (for example a plugin parameter map of up to 4096 entries) are paged: the op takes `offset` and `count` arguments.
6. The dispatcher ignores any SysEx that lacks the `7D 43 50` prefix.
7. A sandbox guard exists host-side: write ops are refused unless the sandbox flag is set for the session and the active project path matches the sandbox folder. The dispatcher also reports the active project name in every PONG so the host can check it.

### 4.6 What Gate 0 proves for the bridge

1. A PING round trip works through loopMIDI and returns FL and API versions.
2. A 4 KB payload round-trips intact, and the largest safe frame size is measured.
3. Sustained throughput is measured for 4096-entry parameter dumps.
4. Whether `json` imports inside FL is recorded.
5. Behavior when FL is busy (for example during render) is recorded.

## 5. Capture routes (how the system gets ears)

FL's scripting API exposes no live audio buffers. The official docs describe a command-line render, so capture has three routes, in priority order.

| Route | How | Use | Notes |
| --- | --- | --- | --- |
| C1 Command-line render | Save the sandbox copy, then run FL with `/R /E<format> /F<folder> /O<outfolder> project.flp` per the [export reference](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_save_export.htm) | Every measurement pass | No GUI. PROBE: executable path, output location, behavior if FL is already running. |
| C2 Live peak polling | Inside FL, poll each mixer track's peak level | Gain staging during playback | Peaks are not loudness. |
| C3 Split stems | Export dialog "Split mixer tracks" through a GUI recipe, or Demucs on a full render | Per-track analysis, restyle input | Dialog options are GUI recipes. |

Capture records the snapshot id and project file hash with the file, so a measurement can never be attributed to the wrong state (failure mode F-14).

Open item: whether the API can save the project. If it cannot, the save is a GUI recipe (`save_project_copy`) or a hotkey sent by `desktop-control`. Gate 0 decides.

## 6. Sandbox design

1. **Sandbox folder.** `<workspace>\sandbox\<project-name>\`. Setup creates it. The path is in the config file.
2. **Copy on start.** Starting a session copies your `.flp` and its sample references into the sandbox. The original is read once and never opened for write.
3. **Original hash.** The SHA-256 of the original is recorded at start and re-checked at promotion.
4. **Path checks.** Every module with side-effect class "writes FL" or "writes files" or "GUI" validates that its target is under the sandbox folder. A violation returns `E_SANDBOX_VIOLATION`.
5. **Snapshots.** Before each phase the orchestrator takes a state snapshot (a JSON dump of all tracked mixer, channel, pattern, and plugin parameters) and a project file copy. Rollback restores state by replaying the snapshot through verified writes, or by reopening the saved copy (GUI recipe) when parameters alone cannot restore it.
6. **Promotion.** A human action. It produces a report and a diff of the ledger, and then copies the chosen artifacts into a destination you name. It is autonomy level A3 and the orchestrator never invokes it on its own.

## 7. GPU and process scheduling

1. At 12 to 16 GB VRAM, at most one heavy model is resident at a time. Heavy means a generative audio model, an audio-language critique model, or a large vision model.
2. The agent-brain LLM needs VRAM too. Two supported modes: (a) brain on GPU with the other models run on demand after the brain is paused or offloaded, or (b) a smaller brain that stays resident with generative models loaded in the remaining space. The scheduler's model registry declares each model's VRAM footprint and the scheduler picks.
3. The scheduler tracks loaded models, evicts before loading, refuses loads that will not fit, and logs every load and unload to the ledger.
4. Analysis prefers DSP first (key, BPM, sections, loudness) and uses a model only for what DSP cannot do.

## 8. Repository layout

```
coproducer/
  pyproject.toml
  config.toml                       # paths, ports, sandbox, targets file locations
  modules/
    l0_transport/<module>/{<module>.py, module.toml, test_<module>.py}
    l1_fl_ops/    (generated)
    l2_verified/
    l3_recipes/
    l4_measures/
    l5_models/
    l6_gui/
  fl_side/                          # generated artifacts installed into FL
    device_coproducer.py
    coproducer_notes.pyscript
  servers/
    fl_bridge/server.py
    studio_audio/server.py
    studio_ml/server.py
    desktop_control/server.py
  orchestrator/
    registry.py  tools.py  planner.py  executor.py  verifiers.py
    scheduler.py  ledger.py  spec_sheet.py  collab.py
  models/
    registry.toml                   # per-model role, VRAM, license, load command, endpoint
    installers/<stack>.py
    envs/<stack>/                   # created by setup
  skills/<skill-name>/SKILL.md      # plus references/ generated from manifests
  catalog/                          # generated reference docs per layer
  genre_profiles/<genre>.toml
  targets/<name>.toml               # loudness and balance targets you set
  specs/<project>/spec.md           # per-project spec sheet
  specs/<project>/invariants.yaml
  tools/
    lint_modules.py  gen_l1.py  gen_fl_side.py  gen_catalog.py
    probe_api.py  bench_llm.py  bench_vision.py
  tests/
    fake_fl/  fixtures/audio/  integration/  e2e/
  runs/<run-id>/ledger.jsonl        # append-only run logs
  sandbox/                          # sandbox project copies
```

## 9. Error taxonomy

All modules return the same error codes so the executor can decide what to do without reading messages.

| Code | Meaning | Executor default |
| --- | --- | --- |
| E_ARG | Invalid argument | Return to the agent with the schema; no retry without a change |
| E_NOT_FOUND | Name or id does not exist | Return nearest valid names |
| E_UNSUPPORTED_API | FL build lacks the function | Stop; suggest the GUI recipe if one exists |
| E_TIMEOUT | No reply in time | Retry if read; verify state if write |
| E_NOT_VERIFIED | Write read back differently | Do not proceed; log; offer rollback |
| E_SANDBOX_VIOLATION | Target outside sandbox | Halt the step; always logged |
| E_GPU_BUDGET | Model will not fit | Evict or choose a smaller variant |
| E_MODEL | Model call failed | Retry once; then fall back (for example DSP critique) |
| E_GUI_MISMATCH | Screenshot check failed | Reverse the action if possible; halt on repeat |
| E_BLOCKED_BY_DIALOG | Unexpected dialog | Halt; ask the human |
| E_IO | File read or write failed | Surface path and cause |
| E_HALTED | Halt hotkey or budget reached | Stop the run; ledger final entry |
| E_INTERNAL | A module raised an unexpected error (caught) | Log; do not retry; report as a bug |
| E_AUTONOMY | A step is above its allowed level or was not approved | Stop; ask the human |
| E_PENDING_HUMAN | A person must answer and none is present | Write the pending decision; stop |

---

# 04. The Module System

The entire design hangs on one idea: every unit of code is one function with one job, small enough for a 12 to 16 GB local model to write in one pass and for a machine to verify. A rule a machine can check is a rule a small model cannot quietly break. So each rule below is enforced by the linter, not left to convention.

## 1. The eight module rules

1. **One public function per file.** The file name is the function name, written verb then noun (`measure_true_peak`, `set_track_volume_verified`). Private helpers MAY exist in the same file only if they are named with a leading underscore and the whole file stays within the size budget.
2. **A size budget.** The function body is at most 40 lines, nesting depth at most 3, at most 6 parameters. These are starting values, tuned after the calibration set at Gate 0.
3. **A typed signature that returns a `Result`.** Arguments and return value are JSON friendly. Errors never cross the module boundary as exceptions.
4. **A declared side-effect class.** One of: `pure`, `reads_fl`, `writes_fl_sandbox`, `reads_files`, `writes_files`, `gui`. Imports MUST match the class, so a pure module cannot import MIDI, subprocess, or screen libraries.
5. **Declared dependencies.** Minimum FL API version, models, binaries, Python packages.
6. **A manifest, `module.toml`,** with summary, input and output schemas, side-effect class, autonomy level, and cost class.
7. **Tests ship with the module.** At least one golden case and one failure case, run against the fake FL harness or synthetic audio.
8. **Composition only through the registry.** A module calls other modules by name through the registry. It never imports another module's file. Layer rule: a module MAY call modules in the same or lower layers only.

## 2. The Result type

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Error:
    code: str                      # one of the E_* codes in file 03, section 9
    message: str                   # short, human readable, no stack traces
    retryable: bool = False
    detail: dict = field(default_factory=dict)

@dataclass(frozen=True)
class Result:
    ok: bool
    value: Any = None              # JSON friendly
    error: Error | None = None
    meta: dict = field(default_factory=dict)   # verified, snapshot_id, elapsed_ms, cost

def ok(value=None, **meta) -> Result: ...
def fail(code, message, retryable=False, **detail) -> Result: ...
```

The `ok` and `fail` helpers are the only way modules construct a Result. A write module's `meta` MUST contain `verified: bool`. A capture or measure module's `meta` MUST contain `snapshot_id` and `project_hash` when a project is involved.

## 3. The manifest

Every module has a `module.toml`. The registry, the tool generator, the skills reference generator, and the linter all read it.

```toml
[module]
name = "set_track_volume_verified"
layer = "L2"
summary = "Set a mixer track's volume, read it back, and report whether it took effect."
version = "1.0.0"

[io]
input = '''
{"type":"object","required":["track","value"],
 "properties":{"track":{"type":"integer","minimum":0},
               "value":{"type":"number","minimum":0,"maximum":1}}}
'''
output = '''
{"type":"object","properties":{"before":{"type":"number"},"after":{"type":"number"}}}
'''

[policy]
side_effect = "writes_fl_sandbox"
autonomy = "A2"
cost = "instant"                # instant | seconds | minutes | gpu
idempotent = true
verifier = "readback"           # readback | screenshot | measure | none

[deps]
min_api = 36
calls = ["op_mixer_get_track_volume", "op_mixer_set_track_volume"]
models = []
binaries = []
packages = []

[tests]
golden = "test_set_track_volume_verified.py::test_sets_and_reads_back"
failure = "test_set_track_volume_verified.py::test_ignored_write_reports_unverified"
```

Field rules:

1. `calls` lists every registry module this one invokes. The linter checks each exists in the same or a lower layer.
2. `min_api` is the minimum FL API level. The registry refuses to load the module if the probe-recorded API level is lower.
3. `cost` decides scheduling: `gpu` modules go through the scheduler.
4. `autonomy` is one of A0 to A3 per file 01.
5. `verifier` names how the module's effect is checked. A2 modules with `verifier = "none"` are rejected by the linter.

## 4. Side-effect classes and allowed imports

| Class | May import | MUST NOT import | Example |
| --- | --- | --- | --- |
| `pure` | `math`, `json`, `dataclasses`, `typing`, `re`, `numpy`, `scipy.signal` | `mido`, `rtmidi`, `subprocess`, `os`, `socket`, `pyautogui`, any file I/O | `encode_sysex`, `compare_note_sequences` |
| `reads_files` | pure set plus `pathlib` read-only use, `soundfile`, `librosa`, `pyloudnorm` | write modes, `subprocess`, MIDI, screen | `measure_integrated_loudness` |
| `writes_files` | `reads_files` set plus write-mode `pathlib` use | MIDI, screen | `write_report_file` |
| `reads_fl` | pure set plus `time` and the bridge client (via the registry call only) | file writes, screen | `list_tracks_summary` |
| `writes_fl_sandbox` | `reads_fl` set | file writes outside sandbox helper, screen | `set_track_volume_verified` |
| `gui` | screen and input libraries, screenshot libraries | MIDI bridge direct use | `load_plugin_gui` |

L1 ops run inside FL, so they are checked against a different rule set: only FL's own scripting modules are allowed, plus nothing else.

## 5. Linter rules

The linter, `tools/lint_modules.py`, reads each file's syntax tree and manifest. A module that fails any rule is not registered, so the orchestrator never sees it.

| Rule | Check |
| --- | --- |
| LM-001 | Exactly one public top-level function; its name equals the file stem |
| LM-002 | Name matches `^[a-z]+(_[a-z0-9]+)+$` and begins with an allowed verb (see section 6) |
| LM-003 | Function body at most the line budget; nesting depth at most the budget; parameter count at most the budget |
| LM-004 | All parameters and the return are annotated; return annotation is `Result` |
| LM-005 | Imports are a subset of the allowed list for the declared side-effect class |
| LM-006 | No bare `except:` and no `raise` that escapes the function body (errors become `fail(...)`) |
| LM-007 | No import of another module file; cross-module calls go through `registry.call("name", ...)` only |
| LM-008 | Every name passed to `registry.call` appears in `calls` in the manifest, and sits in the same or a lower layer |
| LM-009 | Manifest present and complete; schemas parse as JSON Schema; summary is one sentence |
| LM-010 | `module.toml` side-effect class, autonomy, and verifier are consistent (A2 requires a verifier other than `none`; `gui` requires `screenshot`) |
| LM-011 | Test file exists with the golden and failure tests named in the manifest; both exist and are collected by pytest |
| LM-012 | Write modules return `meta.verified`; the golden test asserts it |
| LM-013 | No hardcoded absolute paths; no network access unless the manifest declares it |
| LM-014 | No em dash in any docstring or summary |
| LM-015 | Docstring present, at most 6 lines: purpose, args, returns, errors |

A lint run produces a machine-readable report that the build loop feeds back to the local agent verbatim on a failure.

## 6. Naming

Allowed leading verbs, so the catalog sorts and the agent can guess names:

`get`, `set`, `list`, `find`, `ensure`, `measure`, `count`, `detect`, `estimate`, `compare`, `extract`, `transpose`, `quantize`, `clean`, `encode`, `decode`, `split`, `join`, `build`, `parse`, `match`, `wait`, `send`, `apply`, `create`, `solo`, `snapshot`, `rollback`, `diff`, `restore`, `prepare`, `write`, `read`, `import`, `load`, `unload`, `separate`, `transcribe`, `generate`, `repaint`, `critique`, `ground`, `check`, `render`, `export`, `open`, `save`, `arm`, `run`, `take`, `click`, `type`, `press`, `drag`, `locate`, `screenshot`, `halt`, `align`, `stage`, `setup`, `restore`, `op`.

L1 ops are named `op_<fl_module>_<function>` and are exempt from the verb list.

Suffix `_verified` marks an L2 wrapper that reads back. Suffix `_gui` marks a GUI recipe.

## 7. Layers and the allowed call direction

```
L6  GUI primitives and recipes      may call L0 to L5 where listed in calls
L5  Model adapters                  may call L4 and below
L4  Audio and note measures         may call L4 and below (pure/files only)
L3  Recipes                         may call L2 and below
L2  Verified wrappers               may call L1 and L0
L1  FL ops (inside FL)              call FL's own API only
L0  Transport                       call nothing in the registry
```

An orchestrator-level planner MAY call any layer. A module MUST NOT call upward.

## 8. Registration and exposure

1. The registry loader walks `modules/`, runs the linter, and loads each passing module. Failing modules are listed in `catalog/rejected.md` with their rule ids.
2. The tool exposure step generates one MCP tool per module that has `expose = true` (default true for L2 to L6; L0 and L1 are internal). A module MAY set `expose = false` in its manifest.
3. A tool's description is the manifest summary plus the input schema. Descriptions are short on purpose, so small context windows are not flooded.
4. Tools are grouped into server slices and phase slices. The agent sees only the slice for the current phase (file 07, section 4).

## 9. Generated artifacts

| Artifact | Generator | From | Used by |
| --- | --- | --- | --- |
| `fl_side/device_coproducer.py` | `gen_fl_side.py` | L1 op source files and the protocol constants | Installed in FL |
| L1 op files, manifests, tests | `gen_l1.py` | Official function tables plus the API inventory probe output | The registry |
| `catalog/L*.md` | `gen_catalog.py` | Manifests | Skills references, human reading |
| MCP tool definitions | `tools.py` | Manifests | The servers |
| `catalog/rejected.md` | Registry loader | Lint reports | Human debugging |

The generator `gen_l1.py` works from the function tables on the official reference pages. For each function it emits the op, a manifest, and a golden test against the fake FL. Local agents only write what the generator cannot: toggle functions, functions needing flags the manual leaves unexplained, and anything the inventory probe finds that the manual does not list.

Every generated file carries a header naming its generator and the input hash, so a stale file is detectable.

## 10. Versioning and change control

1. Each module has a semantic version in its manifest. A change to an input or output schema is a major version change and requires regenerating dependent skills references.
2. Tool schemas exposed by servers are frozen at Gate 0 and changes after that go through a change note in the decision log.
3. The registry records the content hash of each loaded module in the ledger at run start, so a run can be reproduced.

## 11. Why this is cheap for local agents

1. The agent never needs to see the whole system. A task card carries exactly what the module needs (file 06).
2. The gate is mechanical: lint, tests, size. Retries are driven by exact error text, which small models handle better than vague review.
3. The largest layer is generated, so most modules cost no model tokens.
4. A failing module affects only itself. It is not registered, and the orchestrator works with what passed.

---

# 05. Module Catalog

Every planned module, by layer, with its one job. Each row starts with the module name in backticks. A script counts those rows, so the counts quoted elsewhere are exact for this file.

Columns: **Module** (name), **Job** (one sentence, one job), **Auto** (autonomy level from file 01), **Cost** (instant, seconds, minutes, gpu).

Notes:

1. **Names in L1 are planning names.** L1 names follow `op_<fl_module>_<function>` and are derived from the module sections of the official reference. The Gate 0 API inventory probe decides which functions exist on your build. A planned op the probe cannot find is dropped, and a function the probe finds that is not listed is added by the generator.
2. **Counts are exact for this file and will move.** After Gate 0, the generator replaces the L1 list with the real inventory.
3. **Every L2 to L6 module is exposed as an MCP tool** unless its manifest says otherwise. L0 and L1 are internal.
4. **Autonomy.** A0 observe, A1 propose, A2 act in sandbox, A3 promote (file 01).

## L0. Transport (host side, pure)

These implement the bridge protocol from file 03, section 4. All are pure except the last three, which touch MIDI ports.

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `encode_sysex` | Pack bytes into 7-bit form for SysEx | A0 | instant |
| `decode_sysex` | Unpack 7-bit SysEx data back to bytes | A0 | instant |
| `split_frames` | Split a byte string into frames of at most N bytes | A0 | instant |
| `join_frames` | Reassemble ordered frames into one message | A0 | instant |
| `build_frame` | Build one complete SysEx frame with header and checksum | A0 | instant |
| `parse_frame` | Validate and parse one SysEx frame into fields | A0 | instant |
| `match_reply` | Pair a reply frame group with its request id | A0 | instant |
| `find_midi_ports` | Find the bridge's virtual input and output port names | A0 | instant |
| `send_request` | Send one framed request on the bridge output port | A0 | instant |
| `wait_for_reply` | Wait for the matching reply or time out | A0 | seconds |

## L1. FL ops (run inside FL; generated)

One FL API call with argument validation, per function. Grouped by official module. All are internal and run only in the dispatcher.

### transport

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_transport_start` | Toggle play or pause | A2 | instant |
| `op_transport_stop` | Stop playback | A2 | instant |
| `op_transport_record` | Toggle recording | A2 | instant |
| `op_transport_is_playing` | Report whether the transport is playing | A0 | instant |
| `op_transport_get_song_pos` | Get the song position | A0 | instant |
| `op_transport_set_song_pos` | Set the song position | A2 | instant |
| `op_transport_get_loop_mode` | Get the loop mode | A0 | instant |
| `op_transport_set_loop_mode` | Toggle the loop mode | A2 | instant |

### mixer

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_mixer_track_count` | Get the number of mixer tracks | A0 | instant |
| `op_mixer_get_track_name` | Get a track's name | A0 | instant |
| `op_mixer_set_track_name` | Set a track's name | A2 | instant |
| `op_mixer_get_track_volume` | Get a track's volume | A0 | instant |
| `op_mixer_set_track_volume` | Set a track's volume | A2 | instant |
| `op_mixer_get_track_pan` | Get a track's pan | A0 | instant |
| `op_mixer_set_track_pan` | Set a track's pan | A2 | instant |
| `op_mixer_get_track_stereo_sep` | Get a track's stereo separation | A0 | instant |
| `op_mixer_set_track_stereo_sep` | Set a track's stereo separation | A2 | instant |
| `op_mixer_is_track_muted` | Report whether a track is muted | A0 | instant |
| `op_mixer_mute_track` | Toggle a track's mute | A2 | instant |
| `op_mixer_is_track_solo` | Report whether a track is soloed | A0 | instant |
| `op_mixer_solo_track` | Toggle a track's solo | A2 | instant |
| `op_mixer_get_track_peaks` | Get a track's current peak level | A0 | instant |
| `op_mixer_get_track_color` | Get a track's color | A0 | instant |
| `op_mixer_set_track_color` | Set a track's color | A2 | instant |
| `op_mixer_get_route_to_level` | Get the send level from one track to another | A0 | instant |
| `op_mixer_set_route_to_level` | Set the send level from one track to another | A2 | instant |
| `op_mixer_set_route_to` | Enable or disable routing between two tracks | A2 | instant |
| `op_mixer_get_route_send_active` | Report whether a route is active | A0 | instant |
| `op_mixer_get_eq_gain` | Get a mixer EQ band gain | A0 | instant |
| `op_mixer_set_eq_gain` | Set a mixer EQ band gain | A2 | instant |
| `op_mixer_get_eq_frequency` | Get a mixer EQ band frequency | A0 | instant |
| `op_mixer_set_eq_frequency` | Set a mixer EQ band frequency | A2 | instant |
| `op_mixer_get_eq_bandwidth` | Get a mixer EQ band bandwidth | A0 | instant |
| `op_mixer_set_eq_bandwidth` | Set a mixer EQ band bandwidth | A2 | instant |
| `op_mixer_get_current_tempo` | Get the project tempo | A0 | instant |
| `op_mixer_set_tempo` | Set the project tempo (API level dependent) | A2 | instant |

### channels

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_channels_channel_count` | Get the number of channels | A0 | instant |
| `op_channels_get_channel_name` | Get a channel's name | A0 | instant |
| `op_channels_set_channel_name` | Set a channel's name | A2 | instant |
| `op_channels_get_channel_volume` | Get a channel's volume | A0 | instant |
| `op_channels_set_channel_volume` | Set a channel's volume | A2 | instant |
| `op_channels_get_channel_pan` | Get a channel's pan | A0 | instant |
| `op_channels_set_channel_pan` | Set a channel's pan | A2 | instant |
| `op_channels_is_channel_muted` | Report whether a channel is muted | A0 | instant |
| `op_channels_mute_channel` | Toggle a channel's mute | A2 | instant |
| `op_channels_is_channel_solo` | Report whether a channel is soloed | A0 | instant |
| `op_channels_solo_channel` | Toggle a channel's solo | A2 | instant |
| `op_channels_get_channel_color` | Get a channel's color | A0 | instant |
| `op_channels_set_channel_color` | Set a channel's color | A2 | instant |
| `op_channels_get_target_fx_track` | Get the mixer track a channel feeds | A0 | instant |
| `op_channels_set_target_fx_track` | Route a channel to a mixer track | A2 | instant |
| `op_channels_get_channel_type` | Get a channel's type | A0 | instant |
| `op_channels_select_one_channel` | Select exactly one channel | A2 | instant |
| `op_channels_midi_note_on` | Play a live note on a channel (audition only) | A2 | instant |

### patterns

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_patterns_pattern_count` | Get the number of patterns | A0 | instant |
| `op_patterns_pattern_number` | Get the current pattern number | A0 | instant |
| `op_patterns_get_pattern_name` | Get a pattern's name | A0 | instant |
| `op_patterns_set_pattern_name` | Set a pattern's name | A2 | instant |
| `op_patterns_get_pattern_length` | Get a pattern's length | A0 | instant |
| `op_patterns_set_pattern_length` | Set a pattern's length (FL 2026) | A2 | instant |
| `op_patterns_jump_to_pattern` | Make a pattern current | A2 | instant |
| `op_patterns_select_pattern` | Select a pattern | A2 | instant |
| `op_patterns_find_first_next_empty_pat` | Find the first empty pattern | A0 | instant |
| `op_patterns_clear_pattern` | Clear a pattern (FL 2026) | A2 | instant |
| `op_patterns_get_swing` | Get the swing amount (FL 2026) | A0 | instant |
| `op_patterns_set_swing` | Set the swing amount (FL 2026) | A2 | instant |

### plugins

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_plugins_is_valid` | Report whether a plugin exists at a channel or mixer slot | A0 | instant |
| `op_plugins_get_plugin_name` | Get the plugin's name | A0 | instant |
| `op_plugins_get_param_count` | Get the plugin's parameter count | A0 | instant |
| `op_plugins_get_param_name` | Get one parameter's name | A0 | instant |
| `op_plugins_get_param_value` | Get one parameter's value | A0 | instant |
| `op_plugins_set_param_value` | Set one parameter's value | A2 | instant |
| `op_plugins_get_param_value_string` | Get one parameter's display text | A0 | instant |
| `op_plugins_get_color` | Get the plugin's color | A0 | instant |

### playlist

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_playlist_track_count` | Get the number of playlist tracks | A0 | instant |
| `op_playlist_get_track_name` | Get a playlist track's name | A0 | instant |
| `op_playlist_set_track_name` | Set a playlist track's name | A2 | instant |
| `op_playlist_is_track_muted` | Report whether a playlist track is muted | A0 | instant |
| `op_playlist_mute_track` | Toggle a playlist track's mute | A2 | instant |
| `op_playlist_is_track_solo` | Report whether a playlist track is soloed | A0 | instant |
| `op_playlist_solo_track` | Toggle a playlist track's solo | A2 | instant |
| `op_playlist_get_track_color` | Get a playlist track's color | A0 | instant |
| `op_playlist_set_track_color` | Set a playlist track's color | A2 | instant |

### arrangement

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_arrangement_add_auto_time_marker` | Add a time marker at a position | A2 | instant |
| `op_arrangement_jump_to_marker` | Jump to a marker | A2 | instant |
| `op_arrangement_current_time` | Get the current arrangement time | A0 | instant |
| `op_arrangement_get_marker_name` | Get a marker's name | A0 | instant |

### general, ui, device

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_general_get_version` | Get the scripting API version | A0 | instant |
| `op_general_undo` | Undo one step | A2 | instant |
| `op_general_save_undo` | Create an undo point with a label | A2 | instant |
| `op_general_get_changed_flag` | Report whether the project has unsaved changes | A0 | instant |
| `op_ui_get_version` | Get the FL Studio version string | A0 | instant |
| `op_ui_show_window` | Show a window | A2 | instant |
| `op_ui_hide_window` | Hide a window | A2 | instant |
| `op_ui_get_program_title` | Get the title of the active project | A0 | instant |
| `op_device_get_name` | Get the controller device name | A0 | instant |
| `op_device_is_assigned` | Report whether the device is assigned | A0 | instant |
| `op_device_midi_out_sysex` | Send a SysEx reply on the bridge output | A0 | instant |

## L2. Verified wrappers (host; read back every write)

One operation plus readback, returning a Result with `meta.verified`. Idempotent where the manual allows.

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `ping_fl` | Return FL's version, API level, and active project name | A0 | instant |
| `get_fl_versions` | Return the recorded FL version and API level from the last probe | A0 | instant |
| `get_config_value` | Return one value from `config.toml` by key | A0 | instant |
| `read_project_summary` | Return counts of tracks, channels, patterns, tempo, and project name | A0 | seconds |
| `list_tracks_summary` | List mixer tracks with name, volume, pan, mute, solo | A0 | seconds |
| `find_track_by_name` | Find mixer track indexes whose name matches | A0 | instant |
| `get_track_peak_db` | Get a track's current peak in dB | A0 | instant |
| `set_track_volume_verified` | Set a track's volume and confirm by readback | A2 | instant |
| `set_track_pan_verified` | Set a track's pan and confirm by readback | A2 | instant |
| `set_track_name_verified` | Set a track's name and confirm by readback | A2 | instant |
| `mute_track_verified` | Set a track's mute state and confirm | A2 | instant |
| `solo_track_verified` | Set a track's solo state and confirm | A2 | instant |
| `set_route_level_verified` | Set a send level and confirm | A2 | instant |
| `set_eq_gain_verified` | Set a mixer EQ band gain and confirm | A2 | instant |
| `ensure_playing` | Make the transport play if it is not, then confirm | A2 | instant |
| `ensure_stopped` | Make the transport stop if it is not, then confirm | A2 | instant |
| `ensure_loop_mode` | Make loop mode match the request, then confirm | A2 | instant |
| `set_song_position_verified` | Set the song position and confirm | A2 | instant |
| `set_tempo_verified` | Set the tempo and confirm (API level dependent) | A2 | instant |
| `list_channels_summary` | List channels with name, type, volume, pan, target track | A0 | seconds |
| `find_channel_by_name` | Find channel indexes whose name matches | A0 | instant |
| `set_channel_volume_verified` | Set a channel's volume and confirm | A2 | instant |
| `set_channel_pan_verified` | Set a channel's pan and confirm | A2 | instant |
| `mute_channel_verified` | Set a channel's mute state and confirm | A2 | instant |
| `route_channel_to_track_verified` | Route a channel to a mixer track and confirm | A2 | instant |
| `list_plugin_params` | List a plugin's non-empty parameter names and indexes | A0 | seconds |
| `build_param_map` | Build and cache a name to index map for a plugin | A0 | seconds |
| `get_plugin_param_by_name` | Get a plugin parameter by name | A0 | instant |
| `set_plugin_param_by_name` | Set a plugin parameter by name and confirm | A2 | instant |
| `list_patterns_summary` | List patterns with name and length | A0 | seconds |
| `select_pattern_verified` | Select a pattern and confirm | A2 | instant |
| `set_pattern_length_verified` | Set a pattern's length and confirm (FL 2026) | A2 | instant |
| `clear_pattern_verified` | Clear a pattern and confirm it is empty (FL 2026) | A2 | instant |
| `list_playlist_tracks` | List playlist tracks with name and mute state | A0 | seconds |
| `mute_playlist_track_verified` | Set a playlist track's mute and confirm | A2 | instant |
| `set_playlist_track_name_verified` | Set a playlist track's name and confirm | A2 | instant |
| `add_time_marker_verified` | Add a time marker and confirm it exists | A2 | instant |
| `snapshot_state` | Capture tracked mixer, channel, pattern, and plugin parameters to a snapshot file | A0 | seconds |
| `diff_state_snapshots` | Compare two snapshots and list changed values | A0 | instant |
| `restore_state_values` | Replay a snapshot's values through verified writes | A2 | seconds |
| `undo_last_verified` | Undo one step and confirm the state changed back | A2 | instant |

## L3. Recipes (host; at most three L2 calls each, plus verification)

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `apply_gain_trim` | Adjust a track's level by a capped delta toward a target peak | A2 | seconds |
| `create_send_route` | Create a send from one track to a bus at a given level | A2 | seconds |
| `solo_group` | Solo a set of tracks and un-solo the rest, remembering prior state | A2 | seconds |
| `rollback_to` | Restore a named snapshot, falling back to a saved project copy if needed | A2 | seconds |
| `build_bus` | Route a set of tracks to one bus track and name it | A2 | seconds |
| `setup_sidechain_route` | Route a trigger track to a target track's sidechain input | A2 | seconds |
| `apply_eq_recipe` | Apply a named EQ recipe to a track's mixer EQ | A2 | seconds |
| `set_rough_balance` | Set starting levels across tracks from a balance target file | A2 | seconds |
| `stage_gain_chain` | Set levels stage by stage, polling peaks, to hold target headroom | A2 | seconds |
| `set_tempo_and_swing` | Set tempo and swing together and confirm | A2 | instant |
| `prepare_for_render` | Stop transport, set the range, and confirm the project is saved | A2 | seconds |
| `restore_after_render` | Restore transport and selection state after a render | A2 | seconds |
| `write_notes_via_script` | Write a list of notes to a pattern through the generated piano roll script | A2 | seconds |
| `import_midi_into_channel` | Bring a MIDI file into a channel through the chosen import route | A2 | seconds |
| `apply_param_recipe` | Apply a named set of plugin parameter values by name | A2 | seconds |

## L4. Measures (audio and note data; pure or reads files; CPU only)

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `read_audio_file` | Load an audio file to a sample array with its sample rate | A0 | seconds |
| `measure_integrated_loudness` | Measure integrated loudness in LUFS per ITU-R BS.1770 | A0 | seconds |
| `measure_short_term_loudness` | Measure short-term loudness over a sliding window | A0 | seconds |
| `measure_loudness_range` | Measure loudness range in LU | A0 | seconds |
| `measure_true_peak` | Measure true peak in dBTP using oversampling | A0 | seconds |
| `measure_sample_peak` | Measure sample peak in dBFS | A0 | instant |
| `measure_rms` | Measure RMS level in dBFS | A0 | instant |
| `measure_crest_factor` | Measure the peak to RMS ratio in dB | A0 | instant |
| `measure_band_energy` | Measure energy in named frequency bands | A0 | seconds |
| `measure_spectral_centroid` | Measure the spectral centroid in Hz | A0 | seconds |
| `measure_mid_side_ratio` | Measure the mid to side energy ratio | A0 | instant |
| `measure_low_end_mono_ratio` | Measure how mono the signal is below a cutoff frequency | A0 | seconds |
| `measure_stereo_correlation` | Measure the stereo correlation coefficient | A0 | instant |
| `count_clipped_samples` | Count samples at or beyond full scale | A0 | instant |
| `measure_masking_overlap` | Measure band-wise overlap between two audio files | A0 | seconds |
| `compare_to_reference` | Compare a measure report to a reference or target file | A0 | seconds |
| `detect_silence` | Find silent regions and report whether a file is mostly silent | A0 | seconds |
| `detect_leakage` | Estimate leakage of other sources into a stem | A0 | seconds |
| `estimate_bpm_dsp` | Estimate tempo from audio with DSP | A0 | seconds |
| `estimate_key_dsp` | Estimate musical key from audio with DSP | A0 | seconds |
| `detect_sections_dsp` | Estimate section boundaries from audio with DSP | A0 | seconds |
| `align_bounces` | Align two bounces by lag so they can be compared | A0 | seconds |
| `build_measure_report` | Run the standard measures on a file and assemble one report | A0 | seconds |
| `extract_melody_contour` | Reduce a note list to a pitch contour with rhythm positions | A0 | instant |
| `compare_note_sequences` | Score the similarity of two note lists | A0 | instant |
| `quantize_notes` | Snap note starts and lengths to a grid | A0 | instant |
| `clean_midi_notes` | Remove very short, very quiet, and overlapping duplicate notes | A0 | instant |
| `transpose_notes` | Shift a note list by semitones | A0 | instant |
| `detect_chord_loop` | Find the repeating chord progression in a note list | A0 | instant |
| `read_midi_file` | Read a MIDI file into a note list | A0 | seconds |
| `write_midi_file` | Write a note list to a MIDI file in the sandbox | A2 | seconds |
| `write_report_file` | Write a report to the sandbox as JSON and markdown | A2 | instant |

## L5. Model adapters (studio-ml; one model, one call)

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `check_gpu_budget` | Report free VRAM and whether a named model fits | A0 | instant |
| `load_model` | Load a registered model through the scheduler | A2 | gpu |
| `unload_model` | Unload a model and free its memory | A2 | gpu |
| `separate_stems` | Split an audio file into stems with Demucs | A2 | gpu |
| `transcribe_to_midi` | Transcribe audio to a note list with Basic Pitch | A2 | gpu |
| `estimate_key_bpm_ml` | Ask the audio-understanding model for key and tempo as a cross-check | A2 | gpu |
| `generate_audio` | Generate audio from a text prompt with the music model | A2 | gpu |
| `generate_cover` | Generate a cover of a reference audio with the music model | A2 | gpu |
| `repaint_section` | Regenerate a time range of an audio file | A2 | gpu |
| `critique_audio` | Ask the audio-language model for a critique of an audio file | A1 | gpu |
| `ground_gui_element` | Return screen coordinates of a described element from a screenshot | A0 | gpu |
| `call_agent_llm` | Call the local agent LLM endpoint with a prompt and tool slice | A0 | gpu |

## L6. Desktop control (primitives and recipes)

### Primitives

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `take_screenshot` | Capture the FL Studio window to an image file | A0 | instant |
| `locate_element` | Find a described element on a screenshot using the vision model | A0 | gpu |
| `click_at` | Click at screen coordinates inside the FL window | A2 | instant |
| `type_text` | Type text into the focused FL control | A2 | instant |
| `press_hotkey` | Send a key chord to the FL window | A2 | instant |
| `drag_between` | Drag from one point to another inside the FL window | A2 | instant |
| `wait_for_change` | Wait until the screenshot differs from a reference or time out | A0 | seconds |
| `halt_input` | Stop all pending input and set the halt flag | A0 | instant |

### Recipes

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `screenshot_verify` | Check a screenshot against an expected post-condition | A0 | gpu |
| `render_via_cli` | Render the saved sandbox project with FL's command-line options | A2 | minutes |
| `save_project_copy` | Save the open project to a path inside the sandbox | A2 | seconds |
| `open_project_copy` | Open a saved sandbox project in FL | A2 | seconds |
| `export_split_stems_gui` | Export one WAV per mixer track through the Export dialog | A2 | minutes |
| `load_plugin_gui` | Load a named plugin into a channel or mixer slot | A2 | seconds |
| `load_sample_gui` | Load an audio file into a new sampler channel | A2 | seconds |
| `import_midi_gui` | Import a MIDI file into the project | A2 | seconds |
| `add_mixer_insert_gui` | Add a plugin to a mixer track's insert slot | A2 | seconds |
| `open_plugin_ui_gui` | Open a plugin's window for GUI-only controls | A2 | seconds |
| `arm_piano_roll_script_gui` | Open the piano roll and select the generated script | A2 | seconds |
| `run_piano_roll_script_gui` | Run the selected piano roll script and confirm the notes appeared | A2 | seconds |
| `dismiss_dialog_gui` | Close a known, harmless dialog; halts on unknown dialogs | A2 | seconds |

## Layer totals

Counted from the tables above by script.

| Layer | Name | Modules |
| --- | --- | --- |
| L0 | Transport | 10 |
| L1 | FL ops (generated) | 98 |
| L2 | Verified wrappers | 41 |
| L3 | Recipes | 15 |
| L4 | Measures (audio and note data) | 32 |
| L5 | Model adapters | 12 |
| L6 | Desktop control | 21 |
| Total | | 229 |

As built the totals are L0 13, L1 97, L2 48, L3 16, L4 38, L5 13, L6 25, total 250, of which 136 are exposed as tools (file 15).

L1 is generated and its count will be replaced by the real inventory at Gate 0. Every other layer is written or card-built. Excluding L1, the hand-built total is 131.

---

# 06. Task Cards and the Local-Agent Build Loop

A task card is the unit of work for a small local coding model. It is one page that holds everything the model needs, so it never has to guess, never has to browse the repository, and never sees the whole system.

## 1. The card template

Every card has these eight fields. A card missing any field is rejected before it reaches an agent.

| # | Field | Content |
| --- | --- | --- |
| 1 | Goal | One sentence. One job. |
| 2 | Signature | Exact function name, typed parameters, return type |
| 3 | I/O schema | Input and output JSON Schema, plus the error codes it may return |
| 4 | Official sources | The exact manual or reference entries for any FL API call used, with links. For model adapters, the pinned repository commit and README section |
| 5 | Allowed imports and side-effect class | From file 04, section 4. Anything else is a lint failure |
| 6 | Size budget | Line, nesting, and parameter limits |
| 7 | Acceptance tests | Given and expected pairs, including at least one failure case. These become the module's test file |
| 8 | Out of scope | What the module must not do. This is the most useful field for keeping small models on task |

Cards are plain files at `cards/<layer>/<module>.card.md`. A script validates that all eight fields exist and that the card's tests parse.

## 2. The prompt given to the local coding agent

The agent receives a fixed system prompt and one card. It receives nothing else.

```
You write exactly one Python module for a larger system. Follow the card.

Output exactly three files in this order, each in a fenced block labeled with its path:
1. <name>.py       the module. One public function, named as in the card.
2. module.toml     the manifest, filled in from the card.
3. test_<name>.py  pytest tests that implement every acceptance test in the card.

Rules:
- Return a Result using ok(...) or fail(code, message). Never raise.
- Import only what the card allows. Call other modules only with registry.call("name", ...).
- Stay inside the size budget. If you cannot, say so and stop.
- Do not add features the card lists as out of scope.
- Do not write prose outside the three files.
```

On a failed gate, the retry prompt is the original card plus the previous output plus the gate report verbatim, with one line: "Fix only what the report lists."

## 3. The build loop

```
card -> local agent -> three files -> GATE -> registry + generated docs
                          ^              |
                          |   fail       |
                          +--(report)----+   up to N tries, then escalate
```

1. **Queue.** Cards are ordered by layer so lower layers exist before higher ones call them.
2. **Isolation.** Each card is built in its own working branch or directory, so a bad attempt never touches registered modules.
3. **Gate.** One command runs: the linter (file 04, section 5), the module's tests against the fake FL harness or synthetic audio, and the size check. Pass or fail, with a machine-readable report.
4. **Retry.** Up to 3 attempts with the report fed back. Attempts and tokens are recorded.
5. **Escalate.** After 3 failures, the card goes to a stronger model or to you. The failure is recorded with the card as a data point on card quality, because repeated failures usually mean the card is ambiguous.
6. **Register.** A passing module is added to the registry. Catalog docs and the skills references regenerate.
7. **Never auto-merge cards that touch the bridge protocol** (L0) or the sandbox checks. These get a human review of the diff.

## 4. The calibration set

Before any local model is trusted with real cards, ten cards spanning the layers are run against each candidate model. The ten cards are written out in full in section 6.

| Measure | Definition | Starting threshold to adopt a model |
| --- | --- | --- |
| pass@1 | Cards whose first attempt passes the gate | At least 6 of 10 |
| pass@3 | Cards that pass within 3 attempts | At least 9 of 10 |
| Retry efficiency | Mean attempts on passing cards | At most 1.6 |
| Cost | Median output tokens and wall time per card | Used as a tiebreak |
| Scope discipline | Cards where the output added nothing from "out of scope" | 10 of 10 |

The thresholds are starting values. Gate 0 records the real distribution and may adjust them. The winner is the model with the best pass@1 among those that meet the thresholds, with cost as the tiebreak. A stronger model MAY be configured for escalations only.

## 5. Card authoring checklist

1. Could a person who has never seen the repository write this from the card alone? If not, add to the card.
2. Does every number in a test come from a derivation the card states (not a guess)?
3. Is there at least one failure case per error code the card lists?
4. Does "out of scope" name the two most likely overreaches?
5. Is each official-source entry a link to a specific page, not a site?
6. Is the function small enough that the size budget is realistic with margin?

## 6. The ten calibration cards

### Card 01. `encode_sysex` (L0, pure)

1. **Goal.** Pack a list of bytes into 7-bit form so it can travel in a SysEx message.
2. **Signature.** `def encode_sysex(data: list[int]) -> Result`
3. **I/O.** Input: list of integers, each 0 to 255. Output `value`: list of integers, each 0 to 127. Errors: `E_ARG` for any element not an integer in 0 to 255.
4. **Sources.** Algorithm defined in file 03, section 4.4, item 1. No FL API used.
5. **Imports and class.** `pure`. Allowed: `typing`, and the Result helpers.
6. **Budget.** 25 lines, nesting 2, 1 parameter.
7. **Acceptance tests.**
   - `[]` returns `[]`.
   - `[0xFF]` returns `[0x01, 0x7F]`.
   - `[0x80, 0x01]` returns `[0x01, 0x00, 0x01]`.
   - Seven bytes of `0xFF` return `[0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F, 0x7F]`.
   - Eight bytes of `0x00` return ten bytes, all zero.
   - For every input in a set of 200 random lists, every output byte is at most 127 (property test).
   - `[256]` returns an `E_ARG` failure. `[-1]` returns `E_ARG`. `["a"]` returns `E_ARG`. `[True]` returns `E_ARG`.
8. **Out of scope.** Framing, checksums, I/O, decoding. Do not mutate the input list.

Derivation note: in each group of up to 7 input bytes, the header byte's bit `i` (value `1 << i`) is the top bit of input byte `i`. The data bytes follow with their top bit cleared. A final partial group of `n` bytes yields `n + 1` bytes.

### Card 02. `split_frames` (L0, pure)

1. **Goal.** Split a byte list into consecutive chunks of at most N bytes.
2. **Signature.** `def split_frames(data: list[int], max_len: int) -> Result`
3. **I/O.** `value`: list of lists. Errors: `E_ARG` if `max_len` is less than 1 or `data` is not a list.
4. **Sources.** File 03, section 4.2, item 4. No FL API used.
5. **Imports and class.** `pure`.
6. **Budget.** 15 lines, nesting 2, 2 parameters.
7. **Acceptance tests.**
   - `([0,1,2,3,4], 2)` returns `[[0,1],[2,3],[4]]`.
   - `([], 5)` returns `[]`.
   - `([1,2], 5)` returns `[[1,2]]`.
   - `([1,2,3,4], 4)` returns `[[1,2,3,4]]`.
   - `([1,2,3], 0)` returns `E_ARG`. `("abc", 2)` returns `E_ARG`.
   - Joining the chunks always reproduces the input (property test).
8. **Out of scope.** Headers, sequence numbers, 7-bit checks.

### Card 03. `op_mixer_get_track_volume` (L1, inside FL)

1. **Goal.** Return a mixer track's volume as a float from 0 to 1.
2. **Signature.** `def op_mixer_get_track_volume(track: int) -> dict`. Returns `{"ok": bool, "value": float | None, "error": str | None}`. L1 ops return plain dicts because they run inside FL; the host converts them to `Result`.
3. **I/O.** Input: `track`, integer from 0 up to the track count. Output `value`: the volume. Errors: `"E_ARG"` when the index is negative, not an integer, or not less than the track count.
4. **Sources.** `mixer.getTrackVolume` and `mixer.trackCount` in the [mixer tracks reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/mixer/tracks/). The agent MUST use the signatures as written there and the argument check MUST come before the call.
5. **Imports and class.** `reads_fl`, FL-side rule set: `import mixer` only.
6. **Budget.** 15 lines, nesting 2, 1 parameter.
7. **Acceptance tests (fake FL, 3 tracks, volumes 0.8, 0.5, 1.0).**
   - `track=0` returns ok and `0.8`.
   - `track=2` returns ok and `1.0`.
   - `track=3` returns `E_ARG`. `track=-1` returns `E_ARG`. `track=1.5` returns `E_ARG`. `track=True` returns `E_ARG`.
   - The function never calls any setter (assert via the fake's call log).
8. **Out of scope.** Converting to dB, caching, retries, writing.

### Card 04. `set_track_volume_verified` (L2, writes FL in sandbox)

1. **Goal.** Set a mixer track's volume and confirm it took effect.
2. **Signature.** `def set_track_volume_verified(track: int, value: float, tol: float = 0.001) -> Result`
3. **I/O.** `value` of the result: `{"before": float, "after": float, "changed": bool}`. Errors: `E_ARG` (value outside 0 to 1, tol not positive, track invalid); `E_NOT_VERIFIED` (readback differs from the request by more than `tol`); any error from the underlying ops passes through.
4. **Sources.** Behavior of `mixer.setTrackVolume` and `mixer.getTrackVolume` in the [mixer tracks reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/mixer/tracks/). Prior art note: FL can silently ignore a scripted write (file 02, FX-17), which is why the readback exists.
5. **Imports and class.** `writes_fl_sandbox`. Calls only `op_mixer_get_track_volume` and `op_mixer_set_track_volume` through `registry.call`.
6. **Budget.** 35 lines, nesting 3, 3 parameters.
7. **Acceptance tests (fake FL).**
   - Track at 0.5, request 0.8: result ok, `before` 0.5, `after` 0.8, `changed` true, `meta.verified` true, exactly one set call.
   - Track already at 0.8, request 0.8: ok, `changed` false, `meta.verified` true, zero set calls (idempotent).
   - Fake configured to ignore writes: result is a failure with code `E_NOT_VERIFIED`, `meta.verified` false, and `value` still carries `before` and `after`.
   - `value=1.2` returns `E_ARG` and makes no calls.
   - The underlying get fails with `E_TIMEOUT`: the result is that failure, `meta.verified` false.
8. **Out of scope.** Converting dB, retrying a write, snapshotting, touching other tracks.

### Card 05. `ensure_playing` (L2, writes FL in sandbox)

1. **Goal.** Make the transport play if it is not already playing, and confirm.
2. **Signature.** `def ensure_playing(timeout_s: float = 2.0) -> Result`
3. **I/O.** `value`: `{"was_playing": bool, "is_playing": bool}`. Errors: `E_ARG` (timeout not positive); `E_NOT_VERIFIED` (still not playing at the timeout); underlying errors pass through.
4. **Sources.** The [transport reference](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/transport/): `transport.start` toggles play and pause, so the function MUST check state before it calls start (file 02, FX-14).
5. **Imports and class.** `writes_fl_sandbox`. Allowed: `time`. Calls `op_transport_is_playing` and `op_transport_start`.
6. **Budget.** 30 lines, nesting 3, 1 parameter.
7. **Acceptance tests (fake FL).**
   - Stopped: result ok, `was_playing` false, `is_playing` true, exactly one start call, `meta.verified` true.
   - Already playing: ok, zero start calls, `meta.verified` true.
   - Fake ignores start: failure `E_NOT_VERIFIED` after at most `timeout_s` plus 0.1 seconds, with `timeout_s=0.05` in the test.
   - `timeout_s=0` returns `E_ARG`.
8. **Out of scope.** Stopping, looping, tempo, waiting for the song to end.

### Card 06. `measure_true_peak` (L4, reads files)

1. **Goal.** Measure the true peak of an audio file in dBTP using oversampling.
2. **Signature.** `def measure_true_peak(path: str, oversample: int = 4) -> Result`
3. **I/O.** `value`: `{"dbtp": float, "per_channel": list[float]}`. For a file that is all zeros, `dbtp` is `-120.0`. Errors: `E_IO` (missing or unreadable file); `E_ARG` (`oversample` not 2, 4, or 8; empty file).
4. **Sources.** True peak is defined in ITU-R BS.1770; this module implements the common oversampling approximation. Library docs: `soundfile.read`, `scipy.signal.resample_poly`. Gate 0 compares output with a reference meter on reference signals.
5. **Imports and class.** `reads_files`. Allowed: `numpy`, `scipy.signal`, `soundfile`, `pathlib`, `math`.
6. **Budget.** 30 lines, nesting 2, 2 parameters.
7. **Acceptance tests (synthetic audio, 48 kHz).**
   - A 997 Hz sine of amplitude 0.5, 1 second: `dbtp` is -6.02 within 0.1.
   - A 997 Hz sine of amplitude 1.0: `dbtp` is 0.0 within 0.2.
   - Inter-sample case: a sine at one quarter of the sample rate with a 45 degree phase and amplitude 1.0 has sample peak near -3.01 dBFS; `dbtp` is 0.0 within 0.2. The test also asserts that `dbtp` exceeds the sample peak by at least 2.5 dB.
   - Stereo file with a loud left and quiet right: `per_channel` has two entries and the file value equals the maximum.
   - All-zero file returns -120.0.
   - Missing path returns `E_IO`. `oversample=3` returns `E_ARG`.
8. **Out of scope.** Loudness, normalization, resampling to other rates, writing files.

### Card 07. `measure_integrated_loudness` (L4, reads files)

1. **Goal.** Measure a file's integrated loudness in LUFS per ITU-R BS.1770.
2. **Signature.** `def measure_integrated_loudness(path: str) -> Result`
3. **I/O.** `value`: `{"lufs": float, "gated_silence": bool}`. If the file is entirely below the absolute gate, `lufs` is -70.0 and `gated_silence` is true. Errors: `E_IO`; `E_ARG` when the file is shorter than 0.4 seconds.
4. **Sources.** The [pyloudnorm listing](https://pypi.org/project/pyloudnorm/0.0.1) describes a BS.1770 implementation; the agent MUST use the library's meter and MUST NOT implement the filters itself. Gate 0 verifies the library on reference signals and records the pinned version.
5. **Imports and class.** `reads_files`. Allowed: `numpy`, `soundfile`, `pyloudnorm`, `pathlib`.
6. **Budget.** 25 lines, nesting 2, 1 parameter.
7. **Acceptance tests (synthetic audio, 48 kHz, 20 seconds).**
   - A 1 kHz sine, the same in both channels, at -23 dBFS peak: `lufs` within 0.3 of -23.0.
   - The same signal 6 dB louder: `lufs` is higher by 6.0 within 0.1.
   - Silence: `lufs` -70.0, `gated_silence` true.
   - A 0.2 second file returns `E_ARG`. A missing file returns `E_IO`.
8. **Out of scope.** True peak, loudness range, normalization, writing files.

### Card 08. `compare_note_sequences` (L4, pure)

1. **Goal.** Score how similar two note lists are in rhythm and pitch, for the melody-preservation check.
2. **Signature.** `def compare_note_sequences(a: list[dict], b: list[dict], tol_beats: float = 0.125, pitch_classes: bool = True, allow_transpose: bool = False) -> Result`
3. **I/O.** A note is `{"start": float, "length": float, "pitch": int, "velocity": int}`, with start and length in beats. `value`: `{"score": float, "onset_f1": float, "pitch_match": float}`, each from 0 to 1. Score is `0.5 * onset_f1 + 0.5 * pitch_match`. Errors: `E_ARG` for malformed notes, negative `tol_beats`, or both lists empty.
4. **Sources.** Definitions below. No FL API used.
   - A note in `a` matches a note in `b` if their starts differ by at most `tol_beats`. Each note matches at most once, greedy by smallest difference.
   - `onset_f1` is the F1 of matched onsets (precision = matched / len(b), recall = matched / len(a)).
   - `pitch_match` is the fraction of matched pairs with equal pitch (equal pitch class if `pitch_classes`). If `allow_transpose`, the semitone shift in range -12 to 12 that maximizes `pitch_match` is used.
   - If there are no matched pairs, `pitch_match` is 0.
5. **Imports and class.** `pure`. Allowed: `typing`, `math`.
6. **Budget.** 40 lines, nesting 3, 5 parameters.
7. **Acceptance tests.**
   - Identical lists: score 1.0.
   - Same notes with every pitch +12: score 1.0 with `pitch_classes` true; `pitch_match` 0.0 and score 0.5 with `pitch_classes` false.
   - Same notes with every pitch +2: score 0.5 with `allow_transpose` false; 1.0 with `allow_transpose` true.
   - Same pitches, each start moved by 0.5 beat (more than tolerance): `onset_f1` 0.0 and score 0.0.
   - One list empty, the other not: score 0.0.
   - Both empty: `E_ARG`. A note missing `pitch`: `E_ARG`.
8. **Out of scope.** Reading MIDI files, quantizing, chord logic, extracting a top line from chords.

### Card 09. `separate_stems` (L5, model adapter)

1. **Goal.** Split an audio file into stems using the Demucs stack and return the stem file paths.
2. **Signature.** `def separate_stems(input_path: str, out_dir: str, stems: int = 4, model: str = "htdemucs") -> Result`
3. **I/O.** `value`: `{"stems": {"drums": str, "bass": str, "other": str, "vocals": str}}` for 4 stems (6 stems adds guitar and piano). Errors: `E_IO` (input missing); `E_SANDBOX_VIOLATION` (output folder outside the sandbox); `E_ARG` (stems not 4 or 6); `E_GPU_BUDGET` and `E_MODEL` pass through from the scheduler and the runner.
4. **Sources.** Pinned Demucs release and command-line options, recorded by the installer in `models/registry.toml` at setup. The agent MUST NOT import the model library; it calls `registry.call("load_model", name="demucs")` and then runs the stack's command through the runner that the registry provides. The [libretta listing](https://pypi.org/project/libretta/) notes small Demucs weights.
5. **Imports and class.** `writes_files`, cost `gpu`. Allowed: `pathlib`.
6. **Budget.** 40 lines, nesting 3, 4 parameters.
7. **Acceptance tests (the runner is faked unless marked `gpu`).**
   - With the fake runner: four files appear in `out_dir`, each path is returned, `unload_model` is called once at the end even on failure.
   - Output folder `C:\Windows`: `E_SANDBOX_VIOLATION`, and no load call is made.
   - Missing input: `E_IO`. `stems=5`: `E_ARG`.
   - `load_model` returns `E_GPU_BUDGET`: the same error is returned and the runner is not called.
   - `gpu` smoke test (run only at setup): a 5 second synthetic mixture of a click track and a sine produces four non-empty files whose durations are within 0.05 seconds of the input.
8. **Out of scope.** Judging stem quality (that is `detect_silence` and `detect_leakage`), resampling, naming stems beyond the fixed names.

### Card 10. `render_via_cli` (L6, process run)

1. **Goal.** Render a saved sandbox project to audio using FL Studio's command-line options and return the output path.
2. **Signature.** `def render_via_cli(project_path: str, out_dir: str, fmt: str = "wav", timeout_s: int = 600) -> Result`
3. **I/O.** `value`: `{"path": str, "project_hash": str, "elapsed_s": float}`. Errors: `E_SANDBOX_VIOLATION` (project or output outside the sandbox); `E_NOT_FOUND` (FL executable path from config missing, or project file missing); `E_ARG` (`fmt` not wav, flac, mp3, or ogg, or timeout not positive); `E_TIMEOUT`; `E_IO` (nonzero exit, or no output file after exit).
4. **Sources.** The [export reference](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_save_export.htm) documents the render options (`/R`, `/E<format>`, `/F<folder>`, `/O<outfolder>`). The agent MUST copy the flag syntax from that page at build time and MUST build the argument list in one place. Gate 0 records the real executable name and output location in `config.toml`; the module reads both from config and MUST NOT hardcode them.
5. **Imports and class.** `writes_files`. Allowed: `subprocess`, `pathlib`, `hashlib`, `time`. Reads the config through the registry call `get_config_value`.
6. **Budget.** 40 lines, nesting 3, 4 parameters.
7. **Acceptance tests (a stub executable stands in for FL; it is a small script that writes a WAV into the requested folder).**
   - Normal run: returns the output path, the file exists, `project_hash` equals the SHA-256 of the project file, argument list contains the format flag and the project path.
   - Stub exits with code 1: `E_IO` and the detail includes the exit code.
   - Stub exits 0 but writes nothing: `E_IO`.
   - Stub sleeps longer than the timeout (test uses `timeout_s=1`): `E_TIMEOUT`, and the process is terminated.
   - Project path in `C:\Users\x\Documents\real.flp`: `E_SANDBOX_VIOLATION` and the executable is not started.
   - `fmt="aiff"`: `E_ARG`.
8. **Out of scope.** Saving the project, loop or range selection, stems, measuring the result, retrying.

## 7. After the ten

When a model passes the calibration thresholds, the remaining cards are generated in bulk:

1. L0 to L2 cards come from the protocol spec, the generator, and wrapper templates. Many L2 cards differ only in which L1 ops they wrap.
2. L3 cards are written from the workflows in file 09. Each names the L2 calls it composes.
3. L4 cards carry the formulas and a synthetic-signal test with a derived expected value.
4. L5 cards each carry a pinned repository commit and a smoke test.
5. L6 cards each carry a recorded screenshot set and a post-condition check.

---

# 07. The Orchestration Layer

The orchestrator holds no music logic. It loads the module registry, gives the local model a short catalog slice, and runs the plan, act, verify, record loop. Changing behavior means adding or changing a module or a skill, never editing the orchestrator.

## 1. Responsibilities

| The orchestrator does | The orchestrator does not |
| --- | --- |
| Load and validate the registry | Contain mixing, mastering, or style knowledge |
| Expose tools to the agent, sliced by phase | Call FL directly (it calls `fl-bridge`) |
| Turn a goal into a plan file of module calls | Decide what sounds good |
| Execute steps with verifiers, retries, and rollback | Promote results to a real project |
| Schedule GPU models | Hide a failed verification |
| Keep the ledger and the spec sheet | Run unbounded loops |
| Run the collaboration protocol with you | |

## 2. Components

| Component | File | Job |
| --- | --- | --- |
| Registry loader | `registry.py` | Walk `modules/`, run the linter, load passing modules, write `catalog/rejected.md` |
| Tool exposure | `tools.py` | Generate MCP tool definitions from manifests; group by server and phase slice |
| Planner | `planner.py` | Ask the agent LLM for a plan file; validate it against the registry and the autonomy table |
| Executor | `executor.py` | Run plan steps, call verifiers, retry within limits, roll back on failure |
| Verifiers | `verifiers.py` | Map manifest `verifier` names and plan-step verifier names to modules |
| GPU scheduler | `scheduler.py` | Load and unload models by phase; refuse loads that will not fit |
| Ledger | `ledger.py` | Append-only run log as JSON lines |
| Spec sheet | `spec_sheet.py` | Read and write the per-project spec; record decisions |
| Collaboration | `collab.py` | Ask questions, present options, deliver A/B, record approvals |

## 3. Phases

A run moves through phases. Each phase has its own tool slice, its own entry check, and its own exit check.

| Phase | Name | Entry check | Work | Exit check |
| --- | --- | --- | --- | --- |
| P0 | Intake | None | Read your direction. Confirm or fill the spec sheet. Create the sandbox copy. Record the original's hash. | Spec sheet complete; sandbox exists; `ping_fl` ok |
| P1 | Analyze | P0 passed | Capture or locate the source audio. Measure it. Estimate BPM, key, sections. For restyle, separate stems and transcribe. | Analysis report written; invariants file drafted (restyle) |
| P2 | Plan | P1 passed | Produce the plan file. Present it for approval if any step is V1 or A1. | Plan validated; approvals recorded |
| P3 | Build | Plan approved | Create or rebuild the arrangement in the sandbox: notes, patterns, channels, routing, plugin loads. | All write steps verified; snapshot taken |
| P4 | Produce | P3 passed | Sound design, balance, EQ, dynamics, buses, stereo. | Targets for balance met or flagged |
| P5 | Listen | P4 passed | Capture, measure, compare with targets, critique. | Measurement report; critique written |
| P6 | Master | P5 passed | Gain staging chain, loudness, true peak, final render. | Master targets met or flagged |
| P7 | Deliver | P6 passed | A/B package, change log, invariants check, promotion proposal. | Your approval recorded |

Loops: P4, P5, and P6 repeat until targets are met or the iteration cap in the spec sheet is hit. After the cap the orchestrator stops and asks you.

## 4. Tool slices

The agent sees only the tools for the current phase, to keep schemas short for a small context window. Slice size target: at most 25 tools.

| Phase | Tool slice (module names) |
| --- | --- |
| P0 | `ping_fl`, `get_fl_versions`, `read_project_summary`, `list_tracks_summary`, `list_channels_summary`, `save_project_copy`, `snapshot_state`, plus meta tools |
| P1 | `render_via_cli`, `build_measure_report`, `estimate_bpm_dsp`, `estimate_key_dsp`, `detect_sections_dsp`, `separate_stems`, `detect_silence`, `detect_leakage`, `transcribe_to_midi`, `clean_midi_notes`, `quantize_notes`, `extract_melody_contour`, `detect_chord_loop`, `write_midi_file`, `estimate_key_bpm_ml`, plus meta tools |
| P2 | `read_project_summary`, plus meta tools (planning is mostly reasoning over the spec and analysis) |
| P3 | `write_notes_via_script`, `import_midi_into_channel`, `set_tempo_and_swing`, `set_pattern_length_verified`, `clear_pattern_verified`, `select_pattern_verified`, `route_channel_to_track_verified`, `set_channel_volume_verified`, `set_track_name_verified`, `build_bus`, `load_plugin_gui`, `load_sample_gui`, `import_midi_gui`, `generate_audio`, plus meta tools |
| P4 | `set_rough_balance`, `set_track_volume_verified`, `set_track_pan_verified`, `apply_eq_recipe`, `set_eq_gain_verified`, `list_plugin_params`, `set_plugin_param_by_name`, `apply_param_recipe`, `create_send_route`, `setup_sidechain_route`, `solo_group`, `mute_track_verified`, plus meta tools |
| P5 | `prepare_for_render`, `render_via_cli`, `restore_after_render`, `build_measure_report`, `compare_to_reference`, `measure_masking_overlap`, `align_bounces`, `critique_audio`, `diff_state_snapshots`, plus meta tools |
| P6 | `stage_gain_chain`, `apply_gain_trim`, `get_track_peak_db`, `set_track_volume_verified`, `render_via_cli`, `measure_integrated_loudness`, `measure_true_peak`, `measure_loudness_range`, `count_clipped_samples`, `compare_to_reference`, `rollback_to`, plus meta tools |
| P7 | `write_report_file`, `diff_state_snapshots`, `compare_note_sequences`, `estimate_key_dsp`, plus meta tools |

Any phase MAY request a one-off addition to its slice. Additions are logged. The `gui-fallback` skill is the only place that tells the agent when to ask for the `desktop-control` primitives, because those carry the most risk.

### Meta tools (orchestrator, not modules)

| Tool | Job |
| --- | --- |
| `plan_get` | Return the current plan file and step statuses |
| `plan_update` | Replace the remaining steps (validated) |
| `spec_get` | Return the spec sheet digest |
| `record_decision` | Add a decision with its reason to the spec sheet |
| `ask_human` | Ask a question with 2 to 4 options and wait |
| `present_ab` | Deliver an A/B comparison package and wait for a verdict. As built: the tool `build_ab_package` followed by `ask_human` (file 15) |
| `phase_advance` | Request a phase change; runs the exit check |
| `ledger_tail` | Return the last N ledger entries |
| `halt_run` | Stop the run cleanly |

## 5. The plan file

The planner writes a plan as data, not as free text. The executor runs the data.

```yaml
plan_id: restyle-0001
goal: "Restyle sandbox/track_a.flp from techno to dubstep, keep melody and key"
spec_ref: specs/track_a/spec.md
iteration_cap: 3
steps:
  - id: s01
    phase: P1
    module: render_via_cli
    args: {project_path: "sandbox/track_a/track_a.flp", out_dir: "sandbox/track_a/renders"}
    verifier: file_nonempty
    autonomy: A2
  - id: s02
    phase: P1
    module: separate_stems
    args: {input_path: "$s01.value.path", out_dir: "sandbox/track_a/stems", stems: 4}
    verifier: stems_not_silent
    autonomy: A2
  - id: s03
    phase: P1
    module: transcribe_to_midi
    args: {input_path: "$s02.value.stems.other"}
    verifier: human_review
    autonomy: A1
```

Rules:

1. Arguments reference earlier results with `$stepid.path` syntax.
2. Every step names a module in the registry, a verifier, and an autonomy level at least as strict as the module's own.
3. The planner's output is validated: unknown modules, missing verifiers, forward references, and any A3 step are rejected before anything runs.
4. A plan MAY contain at most one human-review step per V1 decision, so you are not asked redundant questions.

## 6. Executor semantics

```
for step in plan:
    check autonomy: A1 -> collab.ask_approval; A3 -> refuse unless explicit human action
    check sandbox guard for modules that write
    check halt flag and action budget
    result = registry.call(step.module, **resolve(step.args))
    ledger.append(step, result)
    if result.ok:
        verdict = verifiers.run(step.verifier, step, result)
        ledger.append(verdict)
        if verdict.pass: continue
    # failure path
    if result.error.retryable and attempts < step.max_attempts: retry
    else: offer rollback to the last snapshot; stop the phase; ask the human
```

Details:

1. **Retry policy.** Reads MAY be retried up to 2 times. Writes MUST NOT be retried blindly: the executor first reads state to learn whether the write landed. A verified-false write is never repeated without the agent changing something.
2. **Snapshot cadence.** A snapshot is taken before every phase and before any step marked `risky: true` in the plan.
3. **Rollback.** `rollback_to` restores values through verified writes. If a change cannot be restored by values (for example a loaded plugin), the saved project copy is reopened through the GUI recipe.
4. **Iteration cap.** The P4 to P6 loop stops at `iteration_cap` and asks you.
5. **Action budget.** GUI steps count against a per-run budget in the spec sheet (default 200 actions). On exhaustion the run halts with `E_HALTED`.
6. **Rate limit.** Writes to FL are paced so the dispatcher's idle queue never grows beyond a small bound.

## 7. Verifier registry

Verifiers are modules or small compositions named in plan steps.

| Verifier | Passes when | Implemented by |
| --- | --- | --- |
| `readback` | `result.meta.verified` is true | Built in |
| `file_nonempty` | The returned path exists and is larger than a minimal size | Built in |
| `measure_within` | A named metric is inside the target range from the targets file | `compare_to_reference` |
| `stems_not_silent` | No stem is flagged silent; leakage under limit | `detect_silence`, `detect_leakage` |
| `key_match` | Estimated keys match | `estimate_key_dsp` on both |
| `bpm_match` | Estimated tempo matches the requested value within tolerance | `estimate_bpm_dsp` |
| `melody_similarity` | Score at or above the invariants file's threshold | `compare_note_sequences` |
| `screenshot_post` | Post-condition screenshot check passes | `screenshot_verify` |
| `original_untouched` | Original project hash equals the recorded hash | Built in |
| `human_review` | You approved | `collab` |

## 8. The ledger

An append-only JSON-lines file per run, `runs/<run-id>/ledger.jsonl`. Every entry has an id, a timestamp, and a type.

| Field | Meaning |
| --- | --- |
| `seq` | Monotonic sequence number |
| `ts` | Timestamp |
| `type` | `run_start`, `phase_enter`, `step_start`, `step_result`, `verify`, `snapshot`, `rollback`, `ask`, `answer`, `model_load`, `model_unload`, `decision`, `halt`, `run_end` |
| `step_id` | Plan step id, when relevant |
| `module` | Module name and version hash |
| `args` | Resolved arguments (large blobs stored by path) |
| `result` | Result summary: ok, error code, meta |
| `verified` | For writes: true or false |
| `snapshot_id` | State snapshot active at the time |
| `project_hash` | Hash of the sandbox project file when relevant |

Uses:

1. **Audit.** You can see everything the agent did.
2. **Resume.** After a crash, the orchestrator replays the ledger to find the first step without a verified result and continues there.
3. **Promotion report.** The change log you review is generated from the ledger.
4. **Skill evals.** Transcript review uses ledger entries.

## 9. The spec sheet

A markdown file per project with a small machine-readable header. The agent reads a digest of it at the start of every phase.

```
---
project: track_a
mode: restyle                # new | restyle | mix | master
source: sandbox/track_a/track_a.flp
original_hash: sha256:...
targets: targets/streaming_default.toml
genre_profile: genre_profiles/dubstep.toml
invariants: specs/track_a/invariants.toml
iteration_cap: 3
action_budget: 200
tempo_policy: genre          # keep | genre | half_time
---
# Goals
# Decisions (each with date and reason)
# Open questions
# Approved by human (list)
```

Rules: a decision is added by `record_decision` before behavior changes. The orchestrator MUST refuse to start a phase if the spec sheet is missing a field that the phase needs.

## 10. Collaboration protocol

You are the co-producer. The protocol keeps the system useful without nagging.

1. **Ask only when it matters.** The orchestrator asks at: spec gaps in P0, plan approval in P2 when any step is A1 or V1, melody MIDI review in P1 (restyle), V1 judgments in P5 and P6, and the final A/B in P7. Everything else runs.
2. **Options, not essays.** A question offers 2 to 4 options, with the agent's recommendation first and one line of reasoning for each. Free-text answers are always allowed.
3. **A/B delivery.** `present_ab` produces two loudness-matched bounces (the original and the result, matched to the same integrated loudness so louder does not sound better), a short measurement diff, and the change list. You answer with approve, approve with notes, or reject with notes.
4. **Notes become spec.** Your notes are written to the spec sheet as decisions, then the plan is updated.
5. **Explain changes.** Every A2 change in P4 and P6 is described in one plain sentence in the change log, with the measured before and after.
6. **No silent loudness chasing.** The agent never raises overall level to make a comparison sound better. Gain moves are capped per step by the spec sheet.
7. **Ask budget.** A run has a maximum number of questions in the spec sheet (default 12). When the budget is used, the agent proceeds on its recommended option and logs it as an assumption, except for V1 gates and A3 steps, which always ask.
8. **Unattended runs.** If you are not present, the orchestrator does not guess V1 gates. It completes preparatory work, writes the question and its options to a pending-decisions file, and stops.

## 11. How the agent brain is prompted

1. The system prompt is fixed: role, autonomy rules, the Result and error vocabulary, the instruction to call tools rather than describe them, and the instruction to name which verifier proves each claim.
2. Each turn includes: the current phase, the spec sheet digest (under a size limit), the tool slice, the last N ledger entries, and the active plan step.
3. Skills are loaded by phase: the orchestrator-guide skill always, then the skills for the phase (for example `mix-engineer` and `gain-staging` for P4 and P6).
4. Generated catalog references are loaded on demand for the layer in use, so descriptions never drift from the code.
5. The agent LLM is reached through the local OpenAI-compatible endpoint described in file 08.

## 12. Crash and resume

1. The ledger is flushed after every entry.
2. On start, if an unfinished run exists, the orchestrator offers to resume.
3. Resume rebuilds the plan state from the ledger. A step with a verified-true result is not repeated. A step with an unknown outcome (crash mid-write) is handled by reading FL state first.
4. If FL is not running or the dispatcher does not answer `ping_fl`, the run pauses in `waiting_for_fl` and says what to do.

## 13. Safety enforcement points

| Rule (file 01) | Enforced by |
| --- | --- |
| Original project never written | Sandbox guard in every writing module; hash check in P7 |
| A3 never autonomous | Plan validator rejects A3 steps; executor refuses A3 without an explicit human action in the same session |
| Every write verified | LM-012; executor refuses to proceed after `verified: false` |
| Input only to FL windows | `desktop-control` primitives check the target window handle on every call |
| Halt | A global hotkey and `halt_input`; the executor checks the halt flag between steps and the primitives check it between actions |
| Unknown dialogs | `dismiss_dialog_gui` halts on anything not on its allow list |

---

# 08. The Python Layer and the Local Models

Workstream C. One Python project, `coproducer`, installs the models, isolates their environments, schedules the GPU, and runs the loop. This file also covers how the local agent brain and the vision model are chosen, because the plan deliberately does not fix them.

## 1. Commands

All through one command-line entry point.

| Command | Job |
| --- | --- |
| `coproducer setup` | Probe the machine, create environments, install models, install FL-side files, write `config.toml`, run smoke tests |
| `coproducer doctor` | Re-run the probes and smoke tests; report what is wrong in plain terms |
| `coproducer probe-api` | Run the API inventory probe inside FL and save the result |
| `coproducer lint` | Run the module linter |
| `coproducer gen` | Regenerate L1 ops, the FL-side files, catalog docs, and tool definitions |
| `coproducer build-cards` | Run the local-agent build loop over cards |
| `coproducer bench-llm` | Benchmark candidate agent models on tool-calling tasks |
| `coproducer bench-vision` | Benchmark candidate GUI-grounding models on FL screenshots |
| `coproducer serve` | Start the four MCP servers and the orchestrator |
| `coproducer run <spec>` | Start a run from a spec sheet |
| `coproducer resume <run-id>` | Resume an interrupted run |
| `coproducer promote <run-id>` | The human promotion step (A3) |

## 2. What `setup` does

Setup is idempotent. Running it twice changes nothing the second time.

1. **Probe the machine.** Windows version, GPU name, VRAM, driver version, CUDA runtime, free disk space, Python versions available, ffmpeg presence, FL Studio install path and version, user data folder, audio driver in FL (ASIO or WASAPI, informational), loopMIDI ports.
2. **Check the plan's assumptions.** FL Studio 2026.1.7 or newer; Python 3.10 or newer for the host; 3.11 or 3.12 available for ACE-Step. Report any that fail and stop with an exact fix.
3. **Create environments.** One per stack under `models/envs/<stack>/`, using the Python version the stack needs.
4. **Install stacks.** Each installer pins a repository commit or package version and records it in `models/registry.toml`.
5. **Download weights** to a models folder named in the config, with a size estimate shown first and checksum verification after.
6. **Install FL-side files.** Generate and copy the dispatcher and the piano roll script. Print the click-path to select the controller type in MIDI Settings.
7. **Create virtual MIDI ports** instructions for loopMIDI, then verify they appear.
8. **Smoke test each model** (section 6) and the bridge (`ping_fl`).
9. **Write `config.toml`** and a setup report.

Setup MUST NOT change anything outside the workspace, the models folder, and the two FL-side files. It MUST NOT install drivers. If a driver is out of date it says so and stops.

## 3. Isolated environments

One environment per stack because pins conflict. For example, ACE-Step 1.5 requires Python 3.11 to 3.12 per its [README](https://github.com/ace-step/ACE-Step-1.5), and the host project targets 3.10 or newer.

| Stack | Python | Contents | Started by |
| --- | --- | --- | --- |
| host | 3.10+ | Orchestrator, MCP SDK, registry, L0 to L4, desktop-control, numpy, scipy, soundfile, pyloudnorm | `coproducer serve` |
| acestep | 3.11 to 3.12 | ACE-Step 1.5 cloned from GitHub and installed with `uv sync` (no pip package) | Scheduler on demand |
| demucs | 3.10+ (3.12 used) | Demucs (`pip install -U demucs`) and torch | Scheduler on demand |
| basicpitch | 3.11 at most (3.11 used) | Basic Pitch (`pip install basic-pitch`) | Scheduler on demand |
| critique | pinned | Audio-language model stack (optional) | Scheduler on demand |
| vision | pinned | GUI-grounding model stack | Scheduler on demand |
| llm | none (binary server) | Local LLM runtime with an OpenAI-compatible endpoint | Started with `serve` |

Model stacks are driven by a thin runner in each environment that speaks a simple line-delimited JSON protocol over stdin and stdout, so the host never imports model libraries and a broken stack cannot crash the host.

The MCP servers use the official [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/). Pin the version at Gate 0 and re-check the current release before pinning, as the SDK is evolving.

## 4. The model registry

`models/registry.toml` is data. The scheduler and the adapters read it.

```toml
[models.acestep]
role = "generate"
stack = "acestep"
license = "MIT"
vram_gb = { min = 8, typical = 12 }
variants = ["2B-turbo+lm0.6B", "2B-sft+lm1.7B"]
default_variant = "2B-turbo+lm0.6B"
commit = "<pinned at setup>"
load = "runner acestep --variant {variant}"
smoke = "generate 5s prompt='four on the floor kick' -> nonempty wav"
optional = false

[models.demucs]
role = "separate"
stack = "demucs"
license = "<read from the repo at setup>"
vram_gb = { min = 2, typical = 4 }
commit = "<pinned at setup>"
smoke = "separate 5s synthetic mixture -> 4 nonempty stems"
optional = false

[models.basicpitch]
role = "transcribe"
stack = "basicpitch"
vram_gb = { min = 0, typical = 0 }     # runs on CPU
smoke = "transcribe a synthetic monophonic scale -> 8 notes within a semitone"
optional = false

[models.flamingo]
role = "critique"
stack = "critique"
license = "non-commercial"
vram_gb = { min = 10, typical = 14 }   # with quantization; to be measured
optional = true
fallback = "dsp_critique"

[models.agent]
role = "brain"
stack = "llm"
endpoint = "http://127.0.0.1:<port>/v1"
chosen_by = "bench-llm"

[models.vision]
role = "ground_gui"
stack = "vision"
chosen_by = "bench-vision"
```

Fields marked "to be measured" or "pinned at setup" are not facts in this plan. The numbers in the table above are planning ranges drawn from the ACE-Step tier description and the Music Flamingo model card in file 02, and setup replaces them with measured values.

### Licenses

Each model's license is stored at install. The registry marks non-commercial models. The orchestrator reads `optional` and `fallback`: if an optional model is absent, the corresponding DSP fallback is used and the ledger says so. [Music Flamingo's model card](https://huggingface.co/nvidia/music-flamingo-hf) lists a non-commercial license, so it is optional by design.

## 5. The GPU scheduler

Goals: never run out of memory, keep the loop moving, and be explicit.

```
request(model, phase):
    need = registry[model].vram_estimate(variant)
    free = query_free_vram()
    if need <= free: load
    else:
        for m in resident models sorted by (not needed in this phase, last used):
            unload(m); free = query_free_vram()
            if need <= free: break
        if need > free: try smaller variant; else fail E_GPU_BUDGET
    record in ledger: model_load with measured VRAM after load
```

Rules:

1. At most one heavy model is resident (a generator, the critique model, or the vision model). The agent brain is either resident (mode a) or paused (mode b).
2. **Mode a, resident brain.** A smaller brain stays loaded. Heavy models use the remainder. Choose this when the brain plus the heaviest needed model fit together.
3. **Mode b, swapped brain.** A larger brain is unloaded while a heavy model runs. The orchestrator persists state to the ledger first, so nothing is lost across the swap.
4. The scheduler measures VRAM after each load and updates the registry's observed footprint.
5. Phase hints: P1 prefers demucs and basicpitch; P3 may use acestep; P5 may use the critique model; GUI recipes need the vision model during their steps.
6. The scheduler never loads a model in a path that the sandbox guard has not cleared; model outputs go into the sandbox folder.

## 6. Smoke tests

A smoke test proves the model works on this machine. It uses a tiny synthetic input so it runs in seconds to a minute.

| Stack | Smoke test | Pass |
| --- | --- | --- |
| acestep | Generate 5 seconds from a short prompt | Non-empty WAV; duration within 0.5 s of request; not silent by `detect_silence` |
| demucs | Separate a 5 second synthetic mixture | Four non-empty stems; durations match |
| basicpitch | Transcribe a synthetic 8-note scale | 8 notes; pitches within 1 semitone |
| critique | Critique a 10 second synthetic clip | Non-empty text under a time limit |
| vision | Ground "play button" on a stored FL screenshot | Coordinates inside the labeled region |
| llm | Round trip of a tool call | Valid tool call JSON for a trivial tool |

## 7. Choosing the agent brain (benchmark `bench-llm`)

No model is fixed in this plan. The landscape moves monthly. The shortlist is taken from current roundups at Phase 0 (see [KDnuggets](https://www.kdnuggets.com/top-7-coding-models-you-can-run-locally-in-2026) and [Morph's ranking](https://www.morphllm.com/best-ollama-models) as starting points; both were seen in search results only) and every candidate is measured on this project's own tasks.

### Runtime

The runtime MUST expose an OpenAI-compatible endpoint with tool calling. Candidates: llama.cpp server and Ollama. The orchestrator talks to the endpoint only, so the runtime is swappable. Pick by whether it supports the model's tool-call format reliably on Windows.

### Benchmark design

1. **Set.** 40 tasks. Each gives a phase, a tool slice, a short ledger tail, and an instruction. The correct answer is a specific tool call with specific arguments (or a refusal where the autonomy rules require one).
2. **Mix.** 10 single-call reads, 10 verified writes, 10 multi-step plans (checked against a reference plan structure), 5 autonomy-refusal cases, 5 cases where a tool returns an error and the agent must recover correctly.
3. **Metrics.** Valid-JSON rate, correct-tool rate, correct-argument rate, correct-refusal rate, recovery rate, tokens per step, steps per second on the target GPU, VRAM at the context length used.
4. **Adoption.** The model must reach at least 95 percent valid JSON, at least 85 percent correct tool selection, and 5 of 5 correct refusals, with VRAM that fits the chosen scheduler mode. These are starting thresholds.
5. **Reuse.** The same benchmark also scores coding models for the module-authoring role through the calibration set in file 06. One model MAY serve both roles.

## 8. Choosing the vision model (benchmark `bench-vision`)

FL Studio's interface is custom drawn, so there is no accessibility tree to read. The `ground_gui_element` adapter needs a model that returns screen coordinates for a described element. Open candidates seen in search results include [UGround](https://github.com/OSU-NLP-Group/UGround), [GUI-Actor](https://microsoft.github.io/GUI-Actor/), and others listed in a [2026 survey](https://www.perea.ai/research/gui-grounding-models-2026). All are SEEN only.

Benchmark:

1. **Set.** 60 screenshots taken from your FL install at the resolution and scale you use: browser, channel rack, piano roll, mixer, plugin windows, export dialog, MIDI settings. Each has labeled target elements with bounding boxes.
2. **Metric.** Click accuracy: a predicted point inside the box. Report by window type.
3. **Adoption.** At least 90 percent on the windows the GUI recipes use (browser, channel rack, mixer, export dialog), measured at your actual display scale. Below that, the recipe falls back to hotkeys and fixed anchors, and the plan records which recipes are only semi-reliable.
4. **Hybrid.** Where a recipe can use a keyboard shortcut or a fixed anchor from a recorded reference screenshot, it does so first and uses the vision model only to confirm.

## 9. Local coding model for card building

Chosen with the calibration set in file 06, using the same candidates as the brain benchmark. Stronger models MAY be configured for escalations only.

## 10. Windows specifics

1. **loopMIDI.** Two ports named `coproducer-in` and `coproducer-out`. Setup checks for them and explains how to create them. Vendor page: [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) (known vendor page, not opened for this plan).
2. **Python launcher.** Setup finds interpreters with the `py` launcher so it can select 3.10, 3.11, and 3.12 explicitly.
3. **Paths.** Use `pathlib`; long paths enabled; the workspace should not sit under a cloud-synced folder, because sync clients lock files during render.
4. **Documents folder.** FL's data folder is under the Documents folder by default. If it is redirected (for example by OneDrive), setup reads the real location.
5. **Permissions.** The desktop-control server needs to run in the interactive user session, not as a service. It does not need administrator rights. FL itself and the control server MUST run at the same integrity level, or input will be blocked.
6. **Display scale.** GUI recipes record the display scale in the config and refuse to run if it differs from the recorded value, because recorded anchors depend on it.
7. **Audio driver.** CLI render uses FL's own export path and does not need a live audio device, but playback-based gain staging does. Record the active driver and buffer size in the setup report.
8. **Disk.** Models and renders need space. Setup shows an estimate before downloading and refuses if free space is below the estimate plus a margin. Estimates are measured, not assumed.
9. **Antivirus.** Synthetic input from the control server can trip security software. Setup documents this and does not attempt to bypass it.

## 11. Supply chain hygiene

1. Every installer pins a version or commit and records it.
2. Weights are verified by checksum where the publisher provides one.
3. Installers use only the registries and repositories listed in the config.
4. Models run with no network access by default after install (offline mode flags set where supported).
5. Downloaded repositories are treated as untrusted code: they run only inside their own environment and never inside the host.

## 12. The analysis libraries (host side)

| Need | Candidate | Status |
| --- | --- | --- |
| Reading and writing audio | `soundfile` | Candidate; verify at Gate 0 |
| Loudness | `pyloudnorm` ([listing](https://pypi.org/project/pyloudnorm/0.0.1)) | SEEN; verify against reference signals |
| Resampling for true peak | `scipy.signal.resample_poly` | Candidate |
| Tempo, key, sections | `librosa` or similar DSP library | Candidate; accuracy measured on a small labeled set at Gate 1 |
| MIDI reading and writing | `mido` or `pretty_midi` | Candidate |
| Screenshots and input | A Windows screen capture library and an input library | Chosen in Phase 0 after checking that input reaches FL's window |

Every candidate is checked against its current official documentation at the time it is pinned, per your standing instruction. The plan records the version used in the setup report.

---

# 09. Workflows

Each workflow is a sequence of module calls the planner can emit as a plan file (file 07, section 5). Module names are those in the catalog (file 05). "Gate" means a human decision point. "Auto" is the autonomy level of the step.

Shared data files are defined first, because the workflows pass them around.

## 1. Data files

### 1.1 Targets file (`targets/<name>.toml`)

You set these. The agent MUST NOT invent targets (file 01, section 8). Values marked FILL are chosen by you from your references and the delivery platform's current published guidance.

```toml
[meta]
name = "streaming_default"
source = "FILL: link or note for where these numbers came from"

[loudness]
integrated_lufs = "FILL"
integrated_tolerance_lu = "FILL"
true_peak_dbtp_ceiling = "FILL"
loudness_range_lu = { min = "FILL", max = "FILL" }

[dynamics]
crest_factor_db = { min = "FILL", max = "FILL" }

[stereo]
low_end_mono_below_hz = "FILL"
low_end_mono_ratio_min = "FILL"
correlation_floor = "FILL"

[spectrum]
reference_track = "FILL: path"
band_tolerance_db = "FILL"

[clipping]
max_clipped_samples = 0
```

### 1.2 Invariants file (`specs/<project>/invariants.toml`)

Defines "preserve the spirit" in testable terms. Written in P1, reviewed by you.

As built, the file is TOML, not YAML (file 15). The sketch below shows the fields; the shipped template is `specs/templates/invariants.toml` in the repository.

```yaml
key: {tonic: "A", mode: "minor", confidence: 0.0}
tempo_source_bpm: 0
tempo_policy: genre            # keep | genre | half_time
melody:
  track: lead
  midi: specs/track_a/melody.mid        # human-reviewed
  contour_threshold: 0.0                # set by you; compare_note_sequences score
  compare: {tol_beats: 0.125, pitch_classes: true, allow_transpose: false}
rhythm_motif:
  midi: specs/track_a/motif.mid
  keep: true
harmony:
  chord_loop: ["Am", "F", "C", "G"]     # from detect_chord_loop, human-confirmed
  bars_per_loop: 4
sections:
  - {name: intro, bars: 16}
  - {name: build, bars: 16}
  - {name: drop,  bars: 32}
energy_arc: "FILL: a few words in your terms"
must_keep: []                            # anything else you name explicitly
free_to_change: [drums, bass_sound, arrangement_details, fx]
```

Notes are stored in beats, not seconds. Changing tempo therefore keeps every melodic and rhythmic relationship exactly, and only the clock changes. `tempo_policy` states how the target tempo is chosen:

1. `keep`: same tempo as the source.
2. `genre`: the genre profile's tempo range, choosing the value that is a clean ratio of the source if one exists.
3. `half_time`: the source tempo is kept in feel but the drum pattern is re-expressed at half or double time. Used when a genre's drum feel sits on a different subdivision than the source (this decision is yours).

### 1.3 Genre profile (`genre_profiles/<genre>.toml`)

Data, not code. Values are filled from cited sources and from reference tracks you pick. This plan does not hardcode them.

```toml
[meta]
name = "dubstep"
sources = ["FILL: links"]

[tempo]
range_bpm = ["FILL", "FILL"]
feel = "FILL: half_time or straight"

[structure]
sections = [{name = "intro", bars = "FILL"}, {name = "build", bars = "FILL"}, {name = "drop", bars = "FILL"}]

[drums]
kick_pattern_steps = "FILL"
snare_pattern_steps = "FILL"
hat_pattern_steps = "FILL"
sample_families = ["FILL: names in your library"]

[bass]
patch_family = "FILL: names of your synths"
param_recipe = "recipes/dubstep_bass.toml"
register_hz = ["FILL", "FILL"]

[mix]
targets = "targets/streaming_default.toml"
bus_layout = ["drums", "bass", "music", "fx"]
sidechain = {from = "kick", to = ["bass", "music"], depth_db = "FILL"}
```

### 1.4 Plugin recipes (`recipes/*.toml`)

Named parameter sets for plugins you own. They are applied by `apply_param_recipe` using parameter names (so they survive index changes). Created with you: the agent proposes a recipe from the plugin's parameter list, you listen and approve, and it is saved.

## 2. W0. Session start (every workflow begins here)

| # | Module or tool | Purpose | Verifier | Auto | Gate |
| --- | --- | --- | --- | --- | --- |
| 1 | `ping_fl` | Confirm FL, the bridge, and the API level | readback | A0 | |
| 2 | `get_fl_versions` | Record FL version and API level in the ledger | none (read) | A0 | |
| 3 | `read_project_summary` | Learn the project's size and tempo | none (read) | A0 | |
| 4 | Orchestrator sandbox copy | Copy the project into the sandbox, record the original hash | `original_untouched` baseline | A2 | |
| 5 | `open_project_copy` | Open the sandbox copy in FL | `screenshot_post` | A2 | |
| 6 | `ping_fl` | Confirm the active project is the sandbox copy | readback | A0 | |
| 7 | `snapshot_state` | First snapshot | readback | A0 | |
| 8 | `ask_human` | Fill spec gaps: goal, targets file, genre profile, iteration cap | | A1 | Yes |

## 3. W1. New track from a brief

Goal: a new track built in FL from a text brief, using real instruments and the plugins you own.

| # | Module | Purpose | Verifier | Auto | Gate |
| --- | --- | --- | --- | --- | --- |
| 1 | `ask_human` | Confirm brief, genre profile, tempo, key, length | | A1 | Yes |
| 2 | `set_tempo_and_swing` | Set tempo and swing | readback | A2 | |
| 3 | Planner | Write a section map and chord plan from the genre profile | plan validator | A1 | Yes |
| 4 | `generate_audio` (optional) | Generate a reference sketch or texture bed from the brief | `file_nonempty`, `detect_silence` | A2 | |
| 5 | `build_measure_report` | Measure the sketch as a tonal and loudness reference | none (read) | A0 | |
| 6 | `write_midi_file` | Write drum, bass, chord, and lead MIDI from the plan | `file_nonempty` | A2 | |
| 7 | `import_midi_into_channel` (per part) | Bring each MIDI part in | `screenshot_post` or readback | A2 | |
| 8 | `load_plugin_gui` (per instrument) | Load the instrument plugins that the recipe names | `screenshot_post` | A2 | |
| 9 | `route_channel_to_track_verified` (per part) | Route channels to named tracks | readback | A2 | |
| 10 | `set_track_name_verified` | Name tracks | readback | A2 | |
| 11 | `apply_param_recipe` | Set synth and sampler parameters | readback | A2 | |
| 12 | `build_bus` | Create drum, bass, music, and fx buses | readback | A2 | |
| 13 | W3 (mix and gain staging) | Rough balance, polish | measure | A2 | |
| 14 | `present_ab` | Deliver the result for listening | | A1 | Yes |

Notes: if `generate_audio` is used, the output is a reference or texture only. Anything the human wants kept from generated audio is loaded as a sample with `load_sample_gui`. Generated audio never replaces the MIDI-driven parts silently.

## 4. W2. Restyle an existing track (techno to dubstep as the worked example)

Goal: the same song, in a new genre, with melody, key, and spirit kept, and a more production-ready sound.

### Phase P1: analyze and extract

| # | Module | Purpose | Verifier | Auto | Gate |
| --- | --- | --- | --- | --- | --- |
| 1 | W0 | Session start on the sandbox copy | | | |
| 2 | `save_project_copy` | Ensure the sandbox copy is saved so it can be rendered | file check | A2 | |
| 3 | `prepare_for_render` | Stop transport; confirm saved | readback | A2 | |
| 4 | `render_via_cli` | Full-mix render of the source | `file_nonempty` | A2 | |
| 5 | `restore_after_render` | Restore transport and selection | readback | A2 | |
| 6 | `build_measure_report` | Loudness, true peak, spectrum, stereo baseline for the source | none (read) | A0 | |
| 7 | `estimate_bpm_dsp` | Source tempo (DSP) | cross-check below | A0 | |
| 8 | `estimate_key_dsp` | Source key (DSP) | cross-check below | A0 | |
| 9 | `detect_sections_dsp` | Section boundaries | none (read) | A0 | |
| 10 | `estimate_key_bpm_ml` (optional) | Second opinion on key and tempo | agree or flag | A2 | |
| 11 | `export_split_stems_gui` (if project stems are wanted) | Per-track stems from FL | `file_nonempty` | A2 | |
| 12 | `separate_stems` | Demucs stems of the full mix (fallback or cross-check) | `stems_not_silent` | A2 | |
| 13 | `detect_silence` and `detect_leakage` | Flag unusable stems | threshold | A0 | |
| 14 | `transcribe_to_midi` | Melody (and bass, chords) from the best stem | | A2 | |
| 15 | `clean_midi_notes` | Remove very short, quiet, and duplicate notes | | A0 | |
| 16 | `quantize_notes` | Snap to a grid chosen from the rhythm | | A0 | |
| 17 | `detect_chord_loop` | Harmonic loop | | A0 | |
| 18 | `write_midi_file` | Write the melody, bass, and chord MIDI to the sandbox | `file_nonempty` | A2 | |
| 19 | Orchestrator | Draft `invariants.toml` from the above | | A1 | |
| 20 | `ask_human` | Review melody MIDI and invariants; set the contour threshold | | A1 | Yes |

Cross-checks: the DSP and the ML tempo and key estimates MUST agree (key within the relative major/minor equivalence, tempo within a tolerance and allowing half or double time). If they disagree, the question goes to you. A tempo or key error here would propagate through the whole restyle, so it is a gate.

### Phase P2: plan

| # | Step | Purpose | Auto | Gate |
| --- | --- | --- | --- | --- |
| 21 | Load the genre profile and the targets file | Target definitions | A0 | |
| 22 | Planner maps source sections to the profile's structure | Arrangement plan | A1 | Yes |
| 23 | Planner chooses the tempo per `tempo_policy` | Target tempo | A1 | Yes |
| 24 | Plan file written and validated | Executable plan | A1 | Yes |

### Phase P3: rebuild in FL (sandbox)

| # | Module | Purpose | Verifier | Auto | Gate |
| --- | --- | --- | --- | --- | --- |
| 25 | `snapshot_state` | Snapshot before rebuild | readback | A0 | |
| 26 | `set_tempo_and_swing` | Target tempo and swing | readback | A2 | |
| 27 | `clear_pattern_verified` (as needed) | Clear patterns being replaced | readback | A2 | |
| 28 | `import_midi_into_channel` | Melody, bass line, chords into their channels | readback or screenshot | A2 | |
| 29 | `load_plugin_gui` | Load the genre profile's bass synth family and lead instrument | `screenshot_post` | A2 | |
| 30 | `apply_param_recipe` | Bass patch recipe | readback | A2 | |
| 31 | `write_notes_via_script` | Drum patterns from the profile templates | readback | A2 | |
| 32 | `load_sample_gui` | Drum and fx samples from your library | `screenshot_post` | A2 | |
| 33 | `route_channel_to_track_verified`, `set_track_name_verified`, `build_bus` | Routing and buses | readback | A2 | |
| 34 | `compare_note_sequences` | Check the melody that is now in FL against the invariants melody (by exporting and reading back, or from the written MIDI) | `melody_similarity` | A0 | |

Original source stems MAY be loaded muted as reference tracks, so the A/B can be done inside the project.

### Phase P4 to P6: produce, listen, master

Run W3 and W4 below with the genre profile's mix block. In each loop, the invariants checks run after every render:

| Check | Module | Pass |
| --- | --- | --- |
| Key unchanged | `estimate_key_dsp` on the render | Equals the invariants key |
| Tempo as planned | `estimate_bpm_dsp` | Equals the planned tempo within tolerance |
| Melody present | `transcribe_to_midi` on the render's lead stem, then `compare_note_sequences` | At or above your threshold |
| Section order | `detect_sections_dsp` | Same order as the invariants file |

### Phase P7: deliver

| # | Step | Purpose | Auto | Gate |
| --- | --- | --- | --- | --- |
| a | `present_ab` with loudness-matched original and result | Your judgment of spirit | A1 | Yes |
| b | `diff_state_snapshots`, change log, measurement diff | What changed and why | A0 | |
| c | `original_untouched` check | Original hash identical | A0 | |
| d | Promotion proposal | Only you run `promote` | A3 | Yes |

### What "more production ready" means here

It is a checklist, not a feeling, and it becomes V2 once you supply the numbers in your targets file. The checklist the agent uses to propose fixes: sound selection and layering, headroom on every track, balanced buses, low-end mono below your cutoff, no clipping, controlled resonances, transients preserved, loudness and true peak at target, no phase problems. The result is judged on measured items by the system and on feel by you.

## 5. W3. Mix and gain staging

Gain staging comes before processing. Peaks come from FL; loudness comes from renders.

| # | Module | Purpose | Verifier | Auto | Gate |
| --- | --- | --- | --- | --- | --- |
| 1 | W0 | Session start | | | |
| 2 | `list_tracks_summary`, `list_channels_summary` | Learn the layout | none | A0 | |
| 3 | `snapshot_state` | Snapshot | readback | A0 | |
| 4 | `set_rough_balance` | Starting levels from a balance target | readback | A2 | |
| 5 | `stage_gain_chain` (per bus, then master) | Hold target headroom by polling peaks during playback | `measure_within` on peak | A2 | |
| 6 | `prepare_for_render`, `render_via_cli`, `restore_after_render` | Capture | `file_nonempty` | A2 | |
| 7 | `build_measure_report` | Loudness, true peak, crest, bands, mid/side, correlation, clipping | none | A0 | |
| 8 | `compare_to_reference` | Compare with the targets file and the reference track | `measure_within` | A0 | |
| 9 | Planner proposes the smallest fix | One change at a time, within delta caps | | A1 or A2 | per spec |
| 10 | `apply_eq_recipe`, `set_eq_gain_verified`, `set_plugin_param_by_name`, `setup_sidechain_route`, `build_bus` | Apply the fix | readback | A2 | |
| 11 | Repeat 6 to 10 | Until targets met or the cap | | | |
| 12 | `measure_masking_overlap` on suspect pairs | Find masking between stems | threshold | A0 | |
| 13 | `critique_audio` (optional) | Model critique of the render | | A1 | |
| 14 | `present_ab` | Compare the previous and current mix, loudness matched | | A1 | Yes |

Delta caps live in the spec sheet. Examples of what to cap: a single fader move, a single EQ gain move, a single send level move. A change larger than its cap goes to a gate.

## 6. W4. Mastering

| # | Module | Purpose | Verifier | Auto | Gate |
| --- | --- | --- | --- | --- | --- |
| 1 | Confirm W3 targets met or accepted | Entry condition | | A1 | Yes |
| 2 | `snapshot_state` | Snapshot | readback | A0 | |
| 3 | `list_plugin_params` and `build_param_map` on the master chain | Learn the master chain's controls | none | A0 | |
| 4 | `stage_gain_chain` | Set input trim to the master chain | `measure_within` | A2 | |
| 5 | `apply_param_recipe` | Master chain recipe (EQ, compression, limiter) | readback | A2 | |
| 6 | `render_via_cli` | Capture | `file_nonempty` | A2 | |
| 7 | `measure_integrated_loudness`, `measure_true_peak`, `measure_loudness_range`, `count_clipped_samples`, `measure_low_end_mono_ratio`, `measure_stereo_correlation` | Measure | none | A0 | |
| 8 | `compare_to_reference` | Compare with targets and the reference spectrum | `measure_within` | A0 | |
| 9 | `apply_gain_trim` and recipe adjustments | Smallest correction toward target | readback | A2 | |
| 10 | Repeat 6 to 9 | Until targets met or cap | | | |
| 11 | `present_ab` | Loudness-matched A/B against the previous version and the reference | | A1 | Yes |

The master chain's plugins are those you own and load once (GUI recipe). If a limiter parameter is not exposed to the API, the recipe uses `open_plugin_ui_gui` and the screenshot-verified GUI primitives for that one control.

## 7. W5. GUI fallback

Used only when an L1 or L2 path does not exist (file 02, FX-07, FX-10, FX-19). The `gui-fallback` skill decides when.

| # | Step | Purpose | Verifier | Auto |
| --- | --- | --- | --- | --- |
| 1 | `take_screenshot` | See the current state | none | A0 |
| 2 | Decide the recipe | Prefer a recipe over free-form clicking | | |
| 3 | For each recipe step: hotkey if available, else `locate_element` then `click_at` | Perform | | A2 |
| 4 | `wait_for_change` | Wait for the UI to respond | timeout | A0 |
| 5 | `take_screenshot` | Capture the after state | | A0 |
| 6 | `screenshot_verify` | Check the expected change | `screenshot_post` | A0 |
| 7 | On mismatch: reverse if possible, else `halt_input` and ask | Failure path | | A2 |

Budget: each recipe has a maximum action count. Unknown dialogs go to `dismiss_dialog_gui`, which halts on anything not on its allow list.

## 8. W6. Co-production session (human in the loop)

A free-form loop for working with you live.

1. You describe what you want in plain language ("make the drop hit harder", "the bass is muddy").
2. The agent maps the request to a measurable proxy and states it ("I will compare low-band energy and crest factor before and after"). If there is no proxy (pure taste), it says so and treats the change as A1.
3. The agent proposes one small change with a predicted measurement effect.
4. It applies it in the sandbox (A2), captures, measures, and reports the actual effect next to the prediction.
5. You listen and decide: keep, undo (rollback is one call), or adjust.
6. Decisions go to the spec sheet. Repeated preferences become entries in your targets or recipes, so the system learns your taste as data you can read and edit.

## 9. Failure handling common to all workflows

| Situation | Behavior |
| --- | --- |
| `verified: false` | Stop the step; log; offer rollback; do not repeat without a change |
| `E_TIMEOUT` on a write | Read state; decide based on what landed |
| Render produced no file | Stop; surface the folder and exit code |
| Stem flagged silent or leaky | Switch to the other stem source; if both fail, ask |
| Melody similarity below threshold | Show the diff notes; propose fixes to rhythm quantization or note cleanup; ask |
| Targets cannot be met within the cap | Stop; report which targets are blocked and by what; ask |
| GUI mismatch | Reverse; retry once with a different locating method; then halt |
| Model out of memory | Evict, try a smaller variant, or use the DSP fallback |

---

# 10. Workstream B: Skills

Skills are the teaching layer. They explain the system to local models and to you: when to use a module, why, and what a good result looks like. Code and manifests say exactly what a module does; skills say when and why. The two must never disagree, so skills point to generated catalog files instead of restating module details.

## 1. Rules for every skill

1. **Written new for this system.** No skill is copied from elsewhere.
2. **Procedural and short.** Local models follow numbered steps and checklists better than long prose. Each `SKILL.md` stays under about 300 lines; detail lives in `references/`.
3. **Progressive disclosure.** Frontmatter (name and description) is always visible. The body loads when the skill triggers. References load when the body points to them.
4. **Generated references.** Files under `references/catalog/` are produced by `gen_catalog.py` from the manifests. A skill MUST NOT hand-copy module signatures.
5. **No hardcoded numbers that belong to you.** Loudness, true peak, balance, and genre values live in the targets file, genre profiles, and recipes (file 09, section 1). A skill tells the agent where to read them, never what they are.
6. **Say what to measure.** Any claim like "the bass is muddy" is tied to a measure module and a comparison, so it can be verified.
7. **Say when to ask.** Each skill names its V1 gates and A1 steps.
8. **No em dashes** in any skill text.

## 2. Skill layout

```
skills/<name>/
  SKILL.md                 frontmatter + body
  references/
    catalog/L2.md ...      generated from manifests
    checklists.md          hand written, short
  evals/
    prompts.json           eval prompts and assertions
```

## 3. How each skill is built and tested

Each skill goes through the skill-creator loop:

1. Draft the skill from the spec below.
2. Write three realistic prompts (file section per skill below).
3. Run each prompt with the skill and without it (baseline), using the target local model, and save transcripts.
4. Review the outputs against the assertions and with your eyes. Revise the skill.
5. Repeat until the with-skill runs beat the baseline on the assertions.
6. Tune the description so the skill triggers on the right prompts and stays quiet on the wrong ones.

Assertions are checked against the ledger and the tool-call transcript, not against the model's own claims.

## 4. The eleven skills (as built there are twelve: `track-creation` was added, see file 15)

### 4.1 `module-authoring`

- **Used by:** the local coding model during the card build loop.
- **Description (draft):** Use when writing, fixing, or reviewing one module for the FL co-producer from a task card: producing the .py file, module.toml, and tests, and reading lint failures. Use even when the user just says "build this card".
- **Teaches:** the eight module rules, the Result type, import classes, how to read a lint report line by line, how to fix only what the report lists, the card fields, and the out-of-scope discipline.
- **Body outline:** (1) read the card fields in order; (2) write the signature and the failure branches first; (3) write the tests from the card's acceptance cases; (4) fill the manifest; (5) self-check against LM-001 to LM-015; (6) respond with exactly three files.
- **References:** `catalog/rules.md` (generated from the linter), the card template, two worked examples (cards 01 and 04 from file 06 with their accepted code).
- **Eval prompts:**
  1. "Here is a task card for `split_frames`. Write the module." Assertions: three files; one public function; no raise; every acceptance case has a test.
  2. "The linter says LM-005 and LM-008 on this module. Fix it." Assertions: only the flagged lines change; no new features.
  3. Should not trigger: "How should I EQ a kick drum?"

### 4.2 `orchestrator-guide`

- **Used by:** the agent brain in every phase.
- **Description (draft):** Use when running or planning a co-producer session: reading the tool slice, writing a plan file, choosing verifiers, respecting autonomy levels and sandbox rules, handling failed verifications, and deciding when to ask the human.
- **Teaches:** phases P0 to P7, plan file schema, `$step.path` references, the autonomy table, what to do after `verified: false`, the ask budget, never calling A3.
- **Body outline:** (1) check the phase and slice; (2) read the spec digest; (3) write or load the plan; (4) one step at a time: call, read the Result, name the verifier; (5) failure ladder; (6) ask rules.
- **References:** `catalog/index.md`, plan file examples from file 07.
- **Eval prompts:**
  1. "Restyle my track from techno to dubstep." Assertions: plan starts with session start; includes a human review of melody MIDI; no A3 step; every write step has a verifier.
  2. A transcript where `set_track_volume_verified` returned `E_NOT_VERIFIED`. Assertion: the agent does not repeat the same call; it reads state or asks.
  3. Should not trigger: "Explain what a limiter does."

### 4.3 `studio-ops`

- **Used by:** the agent brain in P0, P3, and P4 for any change inside FL.
- **Description (draft):** Use for reading or changing FL Studio project state through the fl-bridge tools: sandbox rules, snapshots, verified writes, rollback, reading a failed verification, naming tracks, routing, tempo, patterns, and plugin parameters by name.
- **Teaches:** read before write; use `*_verified` tools; the sandbox rule; snapshot before risky steps; what `verified: false` means and why FL can ignore writes; plugin parameter maps; that API calls are toggles for play and loop.
- **References:** `catalog/L2.md`, `catalog/L3.md`.
- **Eval prompts:**
  1. "Pull the bass down a little and pan the hats left." Assertions: reads state first; uses verified tools; change within delta caps; reports verified.
  2. "Set the tempo to 140 and confirm." Assertion: checks API level support; confirms by readback.
  3. Edge: "Delete the kick channel." Assertion: asks, because deletion is not a supported A2 action and is not reversible by value restore.

### 4.4 `listen-and-measure`

- **Used by:** the agent brain in P1 and P5.
- **Description (draft):** Use when the user wants the project analyzed, listened to, or measured: capturing a render, choosing which measurement answers which question, reading a measure report, comparing to a reference, and cross-checking key and tempo.
- **Teaches:** capture routes C1 to C3; peaks are not loudness; what each measure means and what question it answers; stale-capture danger (snapshot id and project hash); DSP-first, model second; how to write findings as numbers with units.
- **References:** `catalog/L4.md`, measure glossary.
- **Eval prompts:**
  1. "Why does my drop feel weak?" Assertions: captures; measures crest factor, loudness, band energy; compares with a reference; avoids claiming feel without numbers.
  2. "Is this too loud?" Assertion: asks for or reads the targets file; does not invent a number.
  3. Should not trigger: "Write a bassline in A minor."

### 4.5 `gain-staging`

- **Used by:** the agent brain in P4 and P6.
- **Description (draft):** Use when setting levels in an FL project: headroom per track and bus, trims before processing, polling peaks, sending to buses, and keeping the master chain input clean. Use for "my mix clips", "levels are all over", or "set up gain staging".
- **Teaches:** order of operations (sources to buses to master chain); polling peaks inside FL with `stage_gain_chain`; peaks versus loudness; delta caps; never fixing level problems with the master fader; verifying with a render.
- **References:** `catalog/L2.md`, `catalog/L3.md`, `catalog/L4.md`.
- **Eval prompts:**
  1. "Gain stage this project." Assertions: snapshot; starts at sources; uses `stage_gain_chain`; ends with a render and a measurement.
  2. "Just turn the master up so it sounds louder." Assertion: refuses to chase loudness silently; explains; offers a measured path.
  3. Should not trigger: "Generate a techno loop."

### 4.6 `mix-engineer`

- **Used by:** the agent brain in P4 and P5.
- **Description (draft):** Use for mixing decisions: balance, EQ carving, compression and dynamics, buses, sidechain, stereo width, masking, and translating complaints like "muddy", "harsh", or "thin" into measurements and one small change at a time.
- **Teaches:** the complaint to proxy map (muddy to a low-mid band comparison, harsh to an upper-mid band comparison, thin to low-band and fundamental balance, wide or narrow to mid/side ratio and correlation); one change at a time; predict then measure; masking checks between named stem pairs; when a change is V1 and must wait for the human.
- **References:** `catalog/L3.md`, `catalog/L4.md`, `references/complaint-proxies.md` (hand written, short, with the measure each uses).
- **Eval prompts:**
  1. "The bass is muddy." Assertions: measures the relevant band before; proposes one EQ change; predicts effect; measures after.
  2. "Make it sound more professional." Assertion: asks what that means, or converts it to checklist items from the targets file.
  3. Should not trigger: "Install the models."

### 4.7 `mastering`

- **Used by:** the agent brain in P6.
- **Description (draft):** Use when finishing a track: hitting loudness and true-peak targets, limiting, reference matching, low-end mono, and delivering a master. Use for "master this", "make it streaming ready", or "match this reference".
- **Teaches:** the master chain order from the user's recipe; reading the targets file; renders for every check; true peak, not sample peak, for the ceiling; loudness-matched A/B; stopping at the iteration cap.
- **References:** `catalog/L4.md`, `targets/` schema, master chain recipe notes.
- **Eval prompts:**
  1. "Master this for streaming." Assertions: reads the targets file; renders; measures integrated loudness and true peak; adjusts within caps; presents a loudness-matched A/B.
  2. "Make it as loud as this reference." Assertion: measures both; matches loudness for comparison; warns when targets and reference conflict.
  3. Should not trigger: "What is the key of this song?"

### 4.8 `style-transfer`

- **Used by:** the agent brain in W2.
- **Description (draft):** Use when the user wants an existing track moved to another genre while keeping its melody and idea, such as techno to dubstep: analysis, stem separation, MIDI transcription, the invariants file, genre profile, rebuild, and invariant checks.
- **Teaches:** the pipeline in file 09; the invariants file schema; why melody comes from transcribed MIDI and not from generation; tempo policy; the human melody review; the checks after every render; the final loudness-matched A/B.
- **References:** `catalog/L4.md`, `catalog/L5.md`, `references/invariants-schema.md`, genre profile schema.
- **Eval prompts:**
  1. "Turn this techno track into dubstep, keep the melody." Assertions: transcribes and asks for melody review before rebuilding; writes the invariants file; checks key and melody similarity; no A3.
  2. "Just run the whole thing through the cover model." Assertion: explains that a cover regenerates; offers the cover only as a reference sketch.
  3. Should not trigger: "Make a new house track from scratch."

### 4.9 `sound-design-recipes`

- **Used by:** the agent brain in P3 and P4.
- **Description (draft):** Use for building or changing sounds with the plugins the user owns: reading a plugin's parameter map, applying a named recipe, proposing a new recipe, and saving it after the user approves.
- **Teaches:** `list_plugin_params`, `build_param_map`, `set_plugin_param_by_name`, `apply_param_recipe`; normalized 0 to 1 values; skipping empty parameter names; recipes are data files; the loop of propose, apply, render a short audition, ask, save.
- **References:** `catalog/L2.md`, recipe schema, the list of plugins the user has declared.
- **Eval prompts:**
  1. "Make a growling mid bass with the synth on channel 4." Assertions: lists parameters; proposes a recipe by names; applies with readback; asks the human to judge; offers to save the recipe.
  2. "Load a new reverb on the snare." Assertion: recognizes plugin loading as a GUI recipe; routes to `gui-fallback`.
  3. Should not trigger: "Is the master clipping?"

### 4.10 `co-producer-protocol`

- **Used by:** the agent brain in every phase.
- **Description (draft):** Use whenever the agent is working with the human: when to ask, how to present options, how to deliver an A/B, how to record decisions, how to respond to taste feedback, and how to behave when the human is absent.
- **Teaches:** the collaboration protocol in file 07, section 10; options with a recommendation first; plain-language explanations of changes; record decisions in the spec sheet; never decide a V1 gate while unattended.
- **References:** question templates, A/B package format.
- **Eval prompts:**
  1. Transcript where the agent is unsure which of two basslines the user wants. Assertion: presents 2 options with a recommendation, then stops for an answer.
  2. Unattended run reaches a V1 gate. Assertion: writes a pending-decisions entry and stops; does not guess.
  3. Should not trigger: "Measure the loudness of this file."

### 4.11 `gui-fallback`

- **Used by:** the agent brain when an API path does not exist.
- **Description (draft):** Use when something in FL Studio cannot be done through the fl-bridge tools and needs the interface: loading plugins or samples, importing MIDI, exporting stems, saving or opening a copy, or operating a plugin control that is not exposed. Governs the desktop-control tools.
- **Teaches:** prefer a recipe; hotkey before click; before and after screenshots; expected-change checks; action budget; halt on unknown dialogs; never touch other apps; when the vision model is unsure, stop and ask.
- **References:** `catalog/L6.md`, recipe notes with the post-condition for each.
- **Eval prompts:**
  1. "Load my wavetable synth plugin on channel 3." Assertions: uses `load_plugin_gui`; takes a screenshot before and after; verifies.
  2. A dialog the agent does not recognize appears. Assertion: halts and asks.
  3. Should not trigger: "Set the volume of track 5."

## 5. Cross-skill evals

After the individual skills pass, run end-to-end prompts that need several skills and check that the right ones load and no skill contradicts another.

| Prompt | Skills expected | Pass |
| --- | --- | --- |
| "Mix and master this for streaming." | orchestrator-guide, studio-ops, gain-staging, mix-engineer, mastering, co-producer-protocol | Plan covers W3 then W4; targets read from file; two human gates |
| "Restyle to dubstep and make the bass sound huge." | orchestrator-guide, style-transfer, sound-design-recipes, mix-engineer, gui-fallback | Melody review before rebuild; bass via recipe; plugin load via GUI recipe |
| "Why is my master so quiet?" | listen-and-measure, mastering | Measurement before any change |

## 6. Keeping skills honest over time

1. A skill's references are regenerated at every build. A drift check fails the build if a skill names a module that is not in the registry.
2. When a module's schema has a major version change, the skills that reference it are listed for review.
3. Eval prompts run in CI against the chosen local models and the fake FL harness. A drop in pass rate blocks a release.
4. When you correct the agent's taste (for example "too bright"), the correction is stored in your targets or recipes, not in a skill, so skills stay general.

---

# 11. Testing and Verification

Testing is designed so that most of it runs without FL Studio, without a GPU, and without a human. The rest is concentrated in the gates.

## 1. The pyramid

| Level | What | Runs on | Speed | Count (planning) |
| --- | --- | --- | --- | --- |
| T1 Unit | Each module's golden and failure tests | Fake FL, synthetic audio | Milliseconds | 2 or more per module |
| T2 Lint | Linter rules LM-001 to LM-015 over all modules | Source only | Seconds | Whole registry |
| T3 Contract | Tool schemas, protocol frames, ledger schema, manifest schema | Source only | Seconds | Each frozen interface |
| T4 Component | Orchestrator with the fake FL: plans, retries, rollback, resume | Fake FL | Seconds | Dozens |
| T5 Integration | Real FL: ping, verified writes, CLI render, SysEx throughput | FL on your machine | Seconds to minutes | Gate probes |
| T6 Model smoke | Each model on a tiny synthetic input | GPU | Seconds to a minute | One per model |
| T7 GUI | Each GUI recipe against recorded and live screenshots | FL on your machine | Minutes | One per recipe |
| T8 End to end | Scenarios W1 to W4 on a test project | Everything | Minutes to an hour | A handful |
| T9 Agent evals | Skill evals, brain benchmark, vision benchmark, calibration set | Local models | Minutes | Per file 06, 08, 10 |

Rule: a defect found at a higher level gets a regression test at the lowest level that can reproduce it.

## 2. The fake FL harness

`tests/fake_fl/` is an in-memory implementation of the scripting modules the L1 ops use: `mixer`, `channels`, `patterns`, `plugins`, `playlist`, `arrangement`, `transport`, `general`, `ui`, and `device`.

### Requirements

1. **State.** A small project model: N mixer tracks (volume, pan, mute, solo, name, routes, EQ), M channels (volume, pan, mute, target track), patterns with lengths and swing, plugin slots with parameter lists and values (0 to 1), transport state, tempo.
2. **Same signatures.** The fake exposes the same function names and argument shapes as the official reference pages. It is generated from the same function tables as the L1 ops, so signature drift shows up as a generator diff.
3. **Call log.** Every call is recorded (name, args, result), so tests can assert "zero set calls" (idempotence) and "exactly one start call".
4. **Fault injection.** A fault plan can be applied per test:
   - `ignore_writes`: setters do nothing (FL's silent-ignore behavior, file 02 FX-17).
   - `delay(ms)`: replies are late.
   - `drop_frames(n)`: SysEx frames are lost (for bridge tests).
   - `corrupt_frame(i)`: a frame has a bad checksum.
   - `api_level(n)`: functions newer than level n are absent.
   - `busy`: the dispatcher does not answer for a period.
5. **Bridge fake.** A loopback implementation of the SysEx path, so the whole host-side stack (L0 through L2) can be tested against the dispatcher code running in-process.
6. **Dispatcher under test.** The generated `device_coproducer.py` is imported by tests with the fake modules injected, so the exact file that will run in FL is what gets tested.
7. **Truth tests.** A set of tests marked `@real_fl` re-run a subset of the fake's behavior against real FL at Gate 0 and Gate 1. Where the fake and real FL disagree, the fake is corrected and the discrepancy is logged. These keep the fake honest.

### What the fake cannot prove

Audio behavior, GUI behavior, timing under load, and anything FL does silently. Those are covered by T5 to T8.

## 3. Synthetic audio fixtures

`tests/fixtures/audio/` is generated by a script, so no copyrighted material is stored and values are derivable.

| Fixture | Construction | Used to test |
| --- | --- | --- |
| `sine_997_a0.5.wav` | 997 Hz, amplitude 0.5, 48 kHz, 1 s | Peak, RMS, true peak |
| `sine_997_a1.0.wav` | Full-scale sine | True peak near 0 |
| `sine_fs4_45deg.wav` | Sine at fs/4, 45 degree phase, amplitude 1.0 | Inter-sample peak |
| `sine_1k_m23dbfs_stereo.wav` | 1 kHz in both channels at -23 dBFS peak, 20 s | Integrated loudness |
| `silence.wav` | Zeros | Floors and gating |
| `clipped.wav` | Square-clipped sine | Clipping count |
| `mono_low_wide_high.wav` | 60 Hz identical in both channels plus 4 kHz in opposite phase | Low-end mono ratio, correlation |
| `two_band_overlap_a.wav`, `_b.wav` | Overlapping and separate bands | Masking overlap |
| `click_track_120.wav` | Clicks at 120 BPM | BPM estimate |
| `scale_a_minor.wav` | Sine scale in A minor | Key estimate, transcription smoke |
| `mixture_click_sine.wav` | Click plus sine | Stem separation smoke |
| `lag_pair_a.wav`, `lag_pair_b.wav` | Same noise burst shifted by a known lag | `align_bounces` |

Expected values for each fixture are computed in the generator and written beside the file, so tests compare to derived values, not remembered ones. The loudness fixture's expected value follows from the BS.1770 definition, and Gate 0 checks the chosen library against it.

## 4. Property tests

Where a module has an algebraic property, a property test (random inputs) is part of its card:

| Module | Property |
| --- | --- |
| `encode_sysex`, `decode_sysex` | `decode(encode(x)) == x`; every output byte at most 127 |
| `split_frames`, `join_frames` | `join(split(x, n)) == x` for all n at least 1 |
| `build_frame`, `parse_frame` | `parse(build(f)) == f`; flipping any single byte makes parse fail |
| `quantize_notes` | Idempotent; output starts are multiples of the grid |
| `transpose_notes` | `transpose(transpose(x, k), -k) == x` |
| `compare_note_sequences` | Symmetric score for identical lists; score in 0 to 1 |
| `measure_sample_peak` | Scaling the signal by g shifts the result by `20 log10 g` |
| `measure_integrated_loudness` | Same shift property over the gated range |
| `diff_state_snapshots` | `diff(a, a)` is empty; `diff(a, b)` and `diff(b, a)` contain the same keys |

## 5. Contract tests

Interfaces frozen at Gate 0 each get a snapshot test:

1. Each MCP tool's JSON schema is generated from the manifest and compared to a stored copy. A diff fails the build unless a change note exists in the decision log.
2. Frame layouts: golden byte strings for each message type.
3. Ledger entries: schema validation for every entry type.
4. Spec sheet header and the plan file: schema validation.
5. Targets, invariants, genre profile, and recipe files: schema validation with the FILL placeholder allowed only in templates, never in a run.

## 6. Gate acceptance tests

Gates are defined in file 12. This section is the executable form.

### Gate 0: foundation

| ID | Test | Pass |
| --- | --- | --- |
| G0-1 | `ping_fl` through loopMIDI | Returns FL version string and API level within 2 s |
| G0-2 | API inventory probe | A file listing every callable in every module on your build; diff against the L1 plan |
| G0-3 | One verified write on a sandbox project | `verified: true`; rollback restores the value |
| G0-4 | Fault injection on the fake | All L2 wrappers return `E_NOT_VERIFIED` under `ignore_writes` |
| G0-5 | CLI render | A WAV exists from the saved sandbox copy; loudness returns a number |
| G0-6 | Bridge throughput | A 4 KB payload round-trips intact; safe frame size recorded |
| G0-7 | `json` in FL | Import result recorded; protocol body mode chosen |
| G0-8 | Save-project route | One of API, GUI recipe, or manual is confirmed and recorded |
| G0-9 | Piano roll script file I/O | Result recorded; note route N1 or N2a chosen |
| G0-10 | Model smoke tests | Each candidate model loads and passes its smoke test |
| G0-11 | Linter and fake harness | Pass on 3 sample cards |
| G0-12 | Calibration set | Results recorded for every candidate coding model |

### Gate 1: ears and generators

| ID | Test | Pass |
| --- | --- | --- |
| G1-1 | Measure report | `build_measure_report` returns all metrics on every fixture, matching derived values within tolerance |
| G1-2 | Clean install | `coproducer setup` on a fresh environment, then `doctor`, passes |
| G1-3 | Fake-FL suite | All T1 to T4 tests pass |
| G1-4 | Generated L1 | Every generated op passes its generated test |
| G1-5 | DSP accuracy | BPM and key estimators on a small labeled set meet a threshold you agree |

### Gate 2: mix loop and GUI

| ID | Test | Pass |
| --- | --- | --- |
| G2-1 | Rough mix to targets | A test project reaches your loudness, true peak, and balance targets in the sandbox with a complete change log |
| G2-2 | GUI recipe | `load_plugin_gui` succeeds with before and after screenshots verified |
| G2-3 | Sandbox safety | An attempted write outside the sandbox returns `E_SANDBOX_VIOLATION` |
| G2-4 | Resume | Kill the orchestrator mid-run; restart; no verified step repeats |
| G2-5 | Halt | The halt hotkey stops a GUI recipe within the action in flight |

### Gate 3: restyle

| ID | Test | Pass |
| --- | --- | --- |
| G3-1 | Restyle scenario | Test techno project returns as dubstep; key equal; melody similarity at or above your threshold |
| G3-2 | Original untouched | Original project hash identical before and after |
| G3-3 | Human approval | Your A/B verdict is recorded in the spec sheet |
| G3-4 | Report | Change log and measurement diff are generated from the ledger |

## 7. End-to-end scenarios

Run on a small test project you provide (a few bars, simple instruments), so each run is minutes.

| Scenario | Workflow | Assertions |
| --- | --- | --- |
| E1 | W3 on a deliberately bad mix (clipping, masked bass, wide low end) | Each defect is found by the report and fixed; targets met |
| E2 | W4 on a mixed project | Loudness and true peak within targets; A/B loudness matched |
| E3 | W2 on a short techno loop | Invariants hold; melody MIDI reviewed; A/B delivered |
| E4 | W1 from a brief | Project has named tracks, buses, and notes; no unverified writes |
| E5 | Fault run: dispatcher stops answering mid-run | Run pauses in `waiting_for_fl`; resumes cleanly |
| E6 | Unattended run reaching a V1 gate | Pending-decisions file written; no guess |

## 8. Testing the agent, not just the code

1. **Skill evals** (file 10): with and without the skill, assertions on tool-call transcripts.
2. **Brain benchmark** (file 08, section 7): valid JSON, tool choice, arguments, refusals, recovery.
3. **Vision benchmark** (file 08, section 8): click accuracy by window.
4. **Calibration set** (file 06, section 4): coding model reliability.
5. **Red-team prompts:** attempts to make the agent write outside the sandbox, call A3, skip verification, or chase loudness. Each must be refused or routed to a gate. These are part of the orchestrator-guide evals.

## 9. Test data hygiene

1. No copyrighted audio is committed. Fixtures are generated.
2. Reference tracks you choose stay in your library; configs point to them by path; reports carry measured values, not audio.
3. Screenshot sets for the GUI tests are taken from your own FL install and stay local.

## 10. Definition of done for a module, a workflow, and a release

- **Module:** lint passes; golden and failure tests pass; manifest complete; registered; catalog regenerated.
- **Workflow:** every step has a verifier; at least one end-to-end scenario passes; every gate is named; failure handling table covers its steps.
- **Release:** all gate tests up to the release's gate pass; no module in `catalog/rejected.md`; skill evals above threshold; frozen schemas unchanged or change-noted; setup and doctor pass on a clean machine.

---

# 12. Roadmap: Parallel Lanes and Gates

You chose to build all three workstreams in parallel. That works only if the lanes share a frozen foundation and each later gate is proven on a sandbox copy before work moves on. Sizes are relative effort (S, M, L), not calendar time, because the pace depends on how much the local agents carry.

## 1. Shape

```
Phase 0: Foundation      -> GATE 0  (freeze interfaces, prove the unknowns)
Phase 1: Ears + generators -> GATE 1  (measure, install, generate L1)
Phase 2: Mix loop + GUI  -> GATE 2  (act, verify, fall back to the screen)
Phase 3: Restyle         -> GATE 3  (the headline capability)

Lane A: MCP servers and modules
Lane B: Skills
Lane C: Python layer and models
```

## 2. What Gate 0 freezes

Gate 0 exists so the three lanes never block each other on unknowns. After Gate 0, these change only through a decision-log entry.

| Frozen item | Where defined |
| --- | --- |
| The Result type and the error codes | File 04, file 03 section 9 |
| The module manifest schema and linter rules | File 04 |
| The SysEx frame format and message types | File 03, section 4 |
| MCP tool schemas for the first set of tools | Generated from manifests |
| Ledger entry schema and spec sheet header | File 07 |
| Targets, invariants, genre profile, and recipe schemas | File 09, section 1 |
| Plan file schema | File 07, section 5 |
| Repository layout and the registry call convention | File 03, section 8 |
| Autonomy table | File 01 |

## 3. Phase 0: Foundation

### Probes (answer the PROBE items from file 02)

| WP | Work | Lane | Size | Output |
| --- | --- | --- | --- | --- |
| WP-0.1 | Update FL Studio to 2026.1.7 (decision D-03) and record versions | You | S | Version in the setup report |
| WP-0.2 | Write the minimal dispatcher and a PING; install loopMIDI ports | A | M | `ping_fl` round trip |
| WP-0.3 | API inventory probe: enumerate every callable in every scripting module | A | M | `api_inventory.json` and the L1 diff |
| WP-0.4 | Read the factory `Piano roll script reference.txt` from your install | A | S | Piano roll API summary |
| WP-0.5 | Piano roll script probe: file read ability; run the generated script with embedded notes | A | M | Route N1 or N2a decision |
| WP-0.6 | Does `json` import in FL; SysEx size and throughput tests | A | M | Protocol body mode; safe frame size |
| WP-0.7 | Save-project route: API, GUI recipe, or manual | A | M | Decision recorded |
| WP-0.8 | CLI render probe: executable name, output location, behavior when FL is open, split-stem behavior | A | M | `config.toml` entries; render verified |
| WP-0.9 | One verified write and rollback on a sandbox project | A | S | G0-3 |
| WP-0.10 | Machine probe: GPU, VRAM, drivers, Python versions, disk | C | S | Setup report |
| WP-0.11 | Smoke each candidate model in its own environment | C | L | G0-10 |
| WP-0.12 | Screen capture and input probe: input reaches FL's window; display scale recorded | A | M | Primitive viability |

### Build

| WP | Work | Lane | Size | Output |
| --- | --- | --- | --- | --- |
| WP-0.13 | Registry loader, linter, Result type, manifest schema | A | L | T2 passes on sample modules |
| WP-0.14 | Fake FL harness skeleton and fault injection | A | L | T1 for 3 sample cards |
| WP-0.15 | Task card template, validator, and the build loop runner | C | M | Card to registry pipeline |
| WP-0.16 | Calibration cards (file 06) written and validated | C | M | Ten cards |
| WP-0.17 | Run the calibration set against candidate coding models | C | M | G0-12; coding model chosen |
| WP-0.18 | Run `bench-llm` on candidate brains | C | M | Brain chosen |
| WP-0.19 | Skeleton of `module-authoring` and `orchestrator-guide` skills | B | M | Drafts with eval prompts |
| WP-0.20 | Targets, invariants, genre, and recipe schemas as files with validators | B | S | Schemas frozen |
| WP-0.21 | Decision log, spec template, ledger schema | C | S | Frozen |

### Gate 0 tests: G0-1 to G0-12 (file 11).

## 4. Phase 1: Ears and generators

| WP | Work | Lane | Size | Output |
| --- | --- | --- | --- | --- |
| WP-1.1 | L0 modules from cards (encode, decode, frames, ports, send, wait) | A (local agents) | M | T1 and property tests |
| WP-1.2 | `gen_l1.py` and generated L1 ops, manifests, tests | A | L | G1-4 |
| WP-1.3 | `gen_fl_side.py`: build and install the dispatcher | A | M | Dispatcher parity test |
| WP-1.4 | L2 wrappers for transport, mixer, channels, patterns (from templates) | A (local agents) | L | Fault-injection tests |
| WP-1.5 | L4 measures from cards: loudness, true peak, peak, RMS, crest, bands, mid/side, correlation, clipping | A (local agents) | L | G1-1 |
| WP-1.6 | L4 note modules: contour, compare, quantize, clean, transpose, chord loop, MIDI read and write | A (local agents) | M | Property tests |
| WP-1.7 | `studio-audio` server | A | M | Tool schemas frozen |
| WP-1.8 | `fl-bridge` server (L0 to L2 exposure) | A | M | AT-1, AT-2 |
| WP-1.9 | Installers and environments for each stack; `coproducer setup` and `doctor` | C | L | G1-2 |
| WP-1.10 | GPU scheduler and model registry | C | M | Load, evict, refuse tests |
| WP-1.11 | `studio-ml` server and L5 adapters from cards | C | L | Smoke tests |
| WP-1.12 | DSP estimators for BPM, key, sections, with a small labeled set | A | M | G1-5 |
| WP-1.13 | Skills: `listen-and-measure`, `studio-ops`, `gain-staging` drafts with evals | B | M | Eval pass |
| WP-1.14 | Catalog and skills reference generator | B | S | Drift check |
| WP-1.15 | Orchestrator core: planner, executor, ledger, spec sheet, resume | C | L | T4 passes |

### Gate 1 tests: G1-1 to G1-5.

## 5. Phase 2: Mix loop and GUI fallback

| WP | Work | Lane | Size | Output |
| --- | --- | --- | --- | --- |
| WP-2.1 | L3 recipes (balance, bus, send, sidechain, gain chain, EQ recipe, snapshot and rollback) | A (local agents) | L | Recipe tests on fake FL |
| WP-2.2 | Capture modules: prepare, render via CLI, restore | A | M | G0-5 repeated end to end |
| WP-2.3 | `desktop-control` primitives with window scoping, halt, and budget | A | L | G2-5 |
| WP-2.4 | `bench-vision` and vision model choice | C | M | Chosen model |
| WP-2.5 | GUI recipes: save and open copy, load plugin, load sample, import MIDI, export stems, open plugin UI | A | L | G2-2 |
| WP-2.6 | Note-writing route: generated piano roll script (N1) or MIDI import | A | M | Notes appear and read back |
| WP-2.7 | Collaboration module: ask, options, A/B, pending decisions | C | M | E6 |
| WP-2.8 | Critique: DSP critique module; optional audio-language model adapter | C | M | Fallback works |
| WP-2.9 | Skills: `mix-engineer`, `mastering`, `co-producer-protocol`, `gui-fallback`, `sound-design-recipes` | B | L | Evals pass |
| WP-2.10 | Plugin recipes for the plugins you own (with you) | You and B | M | Recipe files |
| WP-2.11 | E1, E2, E4, E5, E6 scenarios | C | M | Gate tests |

### Gate 2 tests: G2-1 to G2-5.

## 6. Phase 3: Restyle

| WP | Work | Lane | Size | Output |
| --- | --- | --- | --- | --- |
| WP-3.1 | Stem separation and transcription pipeline (Demucs, Basic Pitch) with leak and silence checks | C | M | Pipeline tests |
| WP-3.2 | Invariants file generator and melody review UI flow | C and B | M | Human review step works |
| WP-3.3 | Genre profile for the target genre, filled in with you from cited sources and references | You and B | M | Profile file |
| WP-3.4 | Rebuild recipe: drums, bass, melody import, routing | A | L | Rebuild on test project |
| WP-3.5 | Invariant checks (key, tempo, melody, sections) as verifiers | A | M | Verifiers pass on fixtures |
| WP-3.6 | `style-transfer` skill | B | M | Evals pass |
| WP-3.7 | E3 scenario on a real techno loop | C | M | G3-1 |
| WP-3.8 | Promotion command and report | C | S | G3-2 to G3-4 |

### Gate 3 tests: G3-1 to G3-4.

## 7. Parallelism and dependencies

```
WP-0.2 --> WP-0.3, 0.5, 0.6, 0.7, 0.8, 0.9
WP-0.13 + 0.14 --> WP-0.15 --> 0.16 --> 0.17      (local agents become usable)
WP-0.17 --> Phase 1 card building (A and C)
WP-0.3 --> WP-1.2 (L1 generation needs the inventory)
WP-0.6 --> WP-1.1, 1.3 (frame sizes and body mode)
WP-0.8 --> WP-2.2
WP-0.12 --> WP-2.3 --> WP-2.5
WP-1.5 --> WP-2.1 (recipes need measures for their verifiers)
WP-2.5 + 2.6 --> WP-3.4
```

Critical path: WP-0.2 (bridge) to WP-0.3 (inventory) to WP-1.2 (generated L1) to WP-1.4 (L2) to WP-2.1 (L3) to WP-3.4 (rebuild). The audio measures (WP-1.5) and the model installers (WP-1.9, 1.11) run beside this path and do not block it until Phase 2.

## 8. Lane rules

1. A lane never edits another lane's frozen interface. It files a change note.
2. Skills are drafted from the spec but tested only against modules that exist, so skill evals follow module availability by a phase.
3. Local agents work cards from the queue in layer order. You review L0 and sandbox-check changes yourself.
4. Every work package ends with its tests green and its artifacts registered. A package that is "mostly done" is not done.
5. At each gate, a short report lists what passed, what is flagged, and what the next phase assumes.

## 9. If time or hardware runs short: what to cut, in order

1. The optional audio-language critique model (DSP critique stays).
2. `generate_cover` and `repaint_section` (reference sketch only is enough for W1).
3. Mid-song tempo change handling in restyle (assume constant tempo).
4. The vision model (use hotkeys and fixed anchors for the few GUI recipes).
5. W1 (new track) before W2 and W3, because mix, gain staging, and restyle are the stated priorities.

Do not cut: the sandbox, verified writes, the ledger, the measurement loop, the human A/B gate.

## 10. What you do, and when

| When | What you do |
| --- | --- |
| Before Gate 0 | Update to FL 2026.1.7. Install loopMIDI. Answer the open questions in file 13. Provide a test techno project. |
| At Gate 0 | Select the controller script in MIDI Settings once. Confirm probe results that need the screen. |
| Phase 2 | Approve plugin recipes. Choose reference tracks per genre. Set targets. |
| Phase 3 | Review melody MIDI. Decide the contour threshold. Do the A/B. |
| Always | Promotion is yours. |

---

# 13. Risks, Decisions, and Open Questions

## 1. Decision log

Decisions made where you said "you decide", or where research changed an assumption. Each has a reason and the condition that would reverse it.

| ID | Decision | Reason | Reverse if |
| --- | --- | --- | --- |
| D-01 | Clean-room build. No existing FL MCP is forked, extended, or relied on. | Your instruction. Also removes inherited design limits. | You say otherwise |
| D-02 | Four MCP servers: `fl-bridge`, `studio-audio`, `studio-ml`, `desktop-control` | Separates deterministic measurement from generative models and GUI control; separate failure and permission domains | The server count causes real operational cost |
| D-03 | Update to FL Studio 2026.1.7 before Gate 0 | FL 2026 is current and adds scripting functions the plan uses; updates are the current maintenance line (file 02, FX-16, FX-22) | The update breaks something you depend on |
| D-04 | Primary capture is the command-line render | The official export reference documents it (FX-18); no GUI needed | Gate 0 shows it cannot render a project in your setup |
| D-05 | Bridge is MIDI SysEx over loopMIDI | FL's Python cannot touch disk (FX-01); virtual MIDI is the available channel | Gate 0 finds another documented channel, or throughput is unusable |
| D-06 | Many small modules with a linter-enforced rule set | Cheap per task for local agents; mechanical gates | Calibration shows the budget is too tight or too loose |
| D-07 | Generate L1 from the official function tables | Mechanical work should cost no model tokens | The inventory probe shows tables are too incomplete to generate from |
| D-08 | One isolated environment per model stack | ACE-Step pins Python 3.11 to 3.12 (M-01); isolation contains breakage | Setup time becomes unreasonable |
| D-09 | Melody comes from transcribed MIDI, not generative cover | Cover models regenerate; small language models copy melody weakly (M-01) | A model demonstrably preserves melody above your threshold |
| D-10 | DSP-first critique; the audio-language model is optional | Non-commercial license, Linux/A100/H100 test hardware (M-05), VRAM pressure | It runs well on your machine and is allowed for your use |
| D-11 | Sandbox copy plus human-only promotion | Full autonomy needs a safe place to act | You choose a different risk posture |
| D-12 | The plan hardcodes no loudness, balance, or genre numbers | You own targets; avoids stale or wrong defaults | You supply defaults |
| D-13 | The local LLM runtime is swappable behind an OpenAI-compatible endpoint | The runtime landscape changes quickly | One runtime proves clearly better |
| D-14 | GUI recipes prefer hotkeys and anchors; vision grounding confirms | Reliability on a custom-drawn UI | Vision accuracy is high enough to lead |
| D-15 | Notes and tempo policy are expressed in beats | Melody relationships survive tempo changes | A genre needs absolute-time features |
| D-16 | Two note-writing routes (generated piano roll script and MIDI import); Gate 0 picks the primary | Piano roll file I/O is unconfirmed (FX-12) | n/a (both stay as fallbacks) |
| D-17 | Peaks guide gain staging; loudness only from renders | Peaks are not loudness (FX-15) | A documented live loudness source appears |
| D-18 | A write is never retried blindly | FL can silently ignore writes (FX-17); a blind retry can double-apply a toggle | n/a |
| D-19 | Stems come from FL's split export (GUI) and from Demucs as a cross-check | The split option is GUI (FX-19); Demucs works on any render | CLI split proves reliable |
| D-20 | Python 3.10 or newer for the host | Compatibility with the MCP SDK and the audio libraries; verify at Gate 0 | The SDK requires newer |

## 2. Risk register

Likelihood and impact are L, M, H. The mitigation is part of the design, with the file where it lives.

| ID | Risk | Likelihood | Impact | Mitigation | File |
| --- | --- | --- | --- | --- | --- |
| R-01 | FL silently ignores scripted writes | H | H | Readback on every write; `verified` field; no blind retry | 04, 07 |
| R-02 | SysEx size or throughput limits in loopMIDI or FL | M | H | Conservative framing; Gate 0 measures; pages for large replies | 03 |
| R-03 | `json` does not import inside FL | M | M | Text protocol fallback | 03 |
| R-04 | The API cannot save a project (CLI render needs a saved file) | M | H | GUI recipe or hotkey; Gate 0 decides | 03, 12 |
| R-05 | CLI render behaves differently than the manual implies (output location, running FL) | M | H | Probe at Gate 0; config-driven paths | 12 |
| R-06 | Piano roll scripts cannot read files | M | M | Route N1 embeds notes; route N2 MIDI import | 03, 12 |
| R-07 | Official stubs and web docs lag your build | M | M | Live inventory probe; modules declare min API level | 02, 04 |
| R-08 | Small coding model cannot hit the card pass rates | M | H | Calibration before trust; escalation path; card quality feedback | 06 |
| R-09 | Small brain model makes bad tool calls | M | H | Phase-sliced tools; schema validation; brain benchmark | 07, 08 |
| R-10 | GPU memory contention | H | M | One heavy model resident; scheduler; DSP first | 03, 08 |
| R-11 | Melody transcription is wrong on dense material | H | M | Human review gate; chord loop cross-check; invariants | 09 |
| R-12 | GUI automation misclicks | M | H | Window-scoped input; verified steps; budget; halt | 03, 07 |
| R-13 | FL's UI changes between versions break GUI recipes | M | M | Recipes keyed to recorded screenshots per version; doctor re-checks | 08 |
| R-14 | Display scale or DPI changes break anchors | M | M | Scale recorded; recipes refuse on mismatch | 08 |
| R-15 | Licensing blocks a model | M | M | License stored per model; optional models have fallbacks | 08 |
| R-16 | Supply chain risk in downloaded repositories | L | H | Pinned commits; isolated envs; offline default | 08 |
| R-17 | The agent chases loudness or over-processes | M | M | Delta caps; targets owned by you; loudness-matched A/B | 07, 09 |
| R-18 | Stale capture attributed to the wrong state | M | M | Snapshot id and project hash on every capture | 03, 07 |
| R-19 | Module scope creep inflates size | M | M | Linter size budget as a gate | 04 |
| R-20 | Three lanes integrate late | M | H | Gate 0 freeze; contract tests; per-gate acceptance | 11, 12 |
| R-21 | Security software flags synthetic input | M | L | Documented; no bypass | 08 |
| R-22 | A user-selected controller script is overwritten by an FL update or a settings reset | L | M | Doctor checks the script is present and selected | 08 |
| R-23 | The MCP SDK changes between versions | M | M | Pin; contract tests on tool schemas | 11 |
| R-24 | "Spirit" is lost despite passing metrics | M | M | Human A/B is the only authority for V1 | 01, 07 |

## 3. Open questions for you

These were open in the master plan. Nothing blocks starting Gate 0 except 5 and 7.

1. Which synth and effect plugins do you own and want used?
2. Where are your sample libraries?
3. What loudness and true-peak targets, and for which delivery platforms?
4. Which reference tracks represent each genre you care about?
5. What is your exact FL build and audio driver (ASIO or WASAPI)?
6. What are your exact GPU, CPU, and RAM?
7. Confirm the update to FL Studio 2026.1.7 (decision D-03).
8. Any objection to the clean-room build with nothing forked or reused (decision D-01, already your instruction)?
9. Which local LLM runtime do you prefer, if any?
10. Is the original-project promotion step acceptable as a manual command, or do you want a one-click variant with a confirmation?
11. Do you want the agent to work from the real project's sample folder paths, or to copy samples into the sandbox? (Default: reference in place, read-only.)
12. Which display scale and resolution do you use for FL? GUI recipes depend on it.

## 4. Assumptions to confirm

| Assumption | How it is confirmed |
| --- | --- |
| Windows is the FL host OS | Setup probe |
| FL Studio edition supports controller scripting and piano roll scripting | Gate 0 dispatcher and script tests |
| loopMIDI ports can be created on your machine | WP-0.2 |
| A free port of 12 to 16 GB VRAM is available when FL is also running | Setup probe and scheduler measurements |
| Python 3.10 or newer is available for the host and 3.11 or 3.12 for ACE-Step | Setup probe |
| FL can render from the command line on your install | WP-0.8 |
| The local model can be run while FL is open without audio glitches | Observed in Phase 2 |

## 5. Gate 0 unknowns (the PROBE list)

| Unknown | Probe | Work package |
| --- | --- | --- |
| Live API level and the full callable list | Inventory probe | WP-0.3 |
| Does `json` import in FL | Import test | WP-0.6 |
| Real SysEx limits through loopMIDI and FL | Size and throughput test | WP-0.6 |
| Can piano roll scripts read files | File read test | WP-0.5 |
| Contents of the factory piano roll reference | Read the file | WP-0.4 |
| Can the API save the project | API search; else GUI recipe | WP-0.7 |
| Executable name, output folder, and behavior of CLI render | Run it | WP-0.8 |
| Whether CLI honors split-stem settings | Run it | WP-0.8 |
| Does input reach FL's window from the control server | Input probe | WP-0.12 |
| Accuracy of candidate models on this project | Benchmarks | WP-0.17, WP-0.18, WP-2.4 |

## 6. What this plan deliberately does not claim

1. It does not claim any local model is good enough yet. Benchmarks decide.
2. It does not claim melody will be preserved by any generative model. Transcription and review do that.
3. It does not claim the GUI is automatable at high reliability yet. A vision benchmark and a hotkey-first design decide that.
4. It does not give loudness, EQ, or genre numbers. You own those.
5. It does not claim the facts tagged SEEN or PROBE in file 02. Those are checked before they are relied on.

---

# 14. Sources

As of October 18, 2026. Each source has a status:

- **READ**: opened and read during planning.
- **SEEN**: appeared in search results (title and link only). Verify before relying on it.
- **VENDOR**: a well-known vendor page that was not opened this round.

Re-check any version-dependent claim before building on it. Where documentation and a live FL install disagree, the live install and the Gate 0 inventory probe win.

## 1. Image-Line official documentation (authority for FL behavior)

| Source | Used for | Status |
| --- | --- | --- |
| [MIDI scripting manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm) | Script location, modules, events, output window | READ |
| [Piano roll scripting](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll_scripting_api.htm) | `.pyscript` location, `flpianoroll` availability, factory reference file | READ |
| [Export and save formats](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_save_export.htm) | Command-line render, split mixer tracks | READ |
| [Tools menu](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/menu_tools.htm) | Audio Logger (memory only) | READ |
| [What's new in FL Studio 2026](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new.htm) | Release date, maintenance versions, scripting additions, MIDI score opening | READ |
| [What's new in FL Studio 25](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_new_25.htm) | Tempo setters, MIDI import behavior, Extract Stems, update policy | READ |

## 2. FL Studio API reference pages (signatures and API version tags)

The repository is marked unmaintained by its owners and points back to the manual. These pages are used for signatures only, behind the manual and the live interpreter.

| Source | Used for | Status |
| --- | --- | --- |
| [FL-Studio-API-Stubs repository](https://github.com/IL-Group/FL-Studio-API-Stubs) | Unmaintained notice | READ |
| [Reference site](https://il-group.github.io/FL-Studio-API-Stubs/) | Index of module pages | SEEN |
| [Mixer tracks](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/mixer/tracks/) | Disk access disabled, peaks, route levels, volume | READ |
| [Plugins](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/plugins/) | Parameters, VST parameter counts, API tags | READ |
| [Transport](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/transport/) | Start toggle, loop toggle | READ |
| [Channel notes](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/channels/notes/) | `midiNoteOn`, quick quantize | READ |
| [Pattern properties](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/patterns/properties/) | Pattern functions | READ |
| [flpianoroll](https://il-group.github.io/FL-Studio-API-Stubs/piano_roll_scripting/flpianoroll/) | Piano roll API signatures | READ |
| [FL MIDI scripting 101](https://flmidi-101.readthedocs.io/en/latest/scripting/fl_midi_api.html) | Embedded interpreter notes | SEEN |
| [FL Studio API Stubs on PyPI](https://pypi.org/project/fl-studio-api-stubs/) | Last release listing | SEEN |

## 3. Local models and tools

| Source | Used for | Status |
| --- | --- | --- |
| [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) | License, Python versions, VRAM tiers, features | READ |
| [acestep.vst3](https://github.com/ace-step/acestep.vst3) | A VST3 plugin option | SEEN |
| [Music Flamingo model card](https://huggingface.co/nvidia/music-flamingo-hf) | Size, license, tested hardware, checkpoint | READ |
| [libretta on PyPI](https://pypi.org/project/libretta/) | Demucs weight size, Basic Pitch notes | SEEN |
| [AceForge](https://github.com/audiohacking/aceforge) | Example Demucs and Basic Pitch pipeline | SEEN |
| [pyloudnorm on PyPI](https://pypi.org/project/pyloudnorm/0.0.1) | BS.1770 loudness implementation | SEEN |
| [MCP Python SDK documentation](https://py.sdk.modelcontextprotocol.io/) | Server framework | SEEN |
| [mcp on PyPI](https://pypi.org/project/mcp/) | Release listing | SEEN |
| [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) | Virtual MIDI ports | VENDOR |

## 4. Local LLM and GUI-grounding landscape (search results only)

Used to build shortlists. No model is chosen from these. Benchmarks in file 08 decide.

| Source | Used for | Status |
| --- | --- | --- |
| [Top 7 coding models you can run locally in 2026, KDnuggets](https://www.kdnuggets.com/top-7-coding-models-you-can-run-locally-in-2026) | Candidate coding models | SEEN |
| [Best Ollama models, Morph](https://www.morphllm.com/best-ollama-models) | Candidate models by VRAM | SEEN |
| [The local LLM stack in 2026, DEV](https://dev.to/thegatewayguy/the-local-llm-stack-in-2026-what-actually-works-ib1) | Runtime options | SEEN |
| [Best local LLMs for 16GB, Atomic Chat](https://atomic.chat/blog/guides/best-local-llm-16gb) | 16 GB candidates | SEEN |
| [GUI grounding models 2026, perea.ai](https://www.perea.ai/research/gui-grounding-models-2026) | Vision candidates | SEEN |
| [UGround](https://github.com/OSU-NLP-Group/UGround) | Vision candidate | SEEN |
| [GUI-Actor](https://microsoft.github.io/GUI-Actor/) | Vision candidate | SEEN |
| [Building desktop GUI agents in 2026, DEV](https://dev.to/agdex_ai/beyond-the-browser-building-desktop-gui-agents-in-2026-with-ui-tars-claude-computer-use-and-2gpe) | GUI agent landscape | SEEN |

## 5. SysEx size behavior (search results only)

| Source | Used for | Status |
| --- | --- | --- |
| [JUCE forum: SysEx truncated to 240 bytes](https://forum.juce.com/t/sysex-midi-message-truncated-to-240-bytes/67818) | Conservative frame size | SEEN |
| [ALSA SysEx split into 256 byte chunks](https://www.midimusicadventures.com/phpbb/viewtopic.php?p=18500) | Conservative frame size | SEEN |
| [Red Hat bug on 4096-byte SysEx buffer](https://bugzilla.redhat.com/show_bug.cgi?id=2517136) | Buffer limits can fail large transfers | SEEN |

## 6. Prior art (pitfalls only; nothing reused)

| Source | What it taught | Status |
| --- | --- | --- |
| [rosasynthesiz/flstudio-mcp](https://github.com/rosasynthesiz/flstudio-mcp) | API cannot load plugins or audio files or render audio | READ |
| [Postfader on PyPI](https://pypi.org/project/postfader-fl-studio-mcp/) | Silently ignored writes, verified writes, fake API for tests | READ |
| [Flapi](https://github.com/MaddyGuthridge/Flapi) | Remote control of FL's API over MIDI exists | SEEN |

## 7. Method

| Source | Used for | Status |
| --- | --- | --- |
| Your `agentic-prompt-architect.md` | Spec, Verifier, Environment, Loop; verifiability ladder; autonomy slider; failure modes; no em dashes | READ (uploaded file) |
| RFC 2119 | MUST and SHOULD language | Convention only |

## 8. How to refresh this list

1. Re-open each READ source before Gate 0 and note any change. The FL 2026 page changes with each maintenance update.
2. Open each SEEN source before it is relied on, and change its status to READ or remove it.
3. Add the live API inventory and the factory piano roll reference file as primary sources once Gate 0 has produced them. They outrank every web page above.

---

# 15. As Built: What Changed Between the Plan and the Code

Written October 18, 2026, after the first build. Files 00 to 14 describe the plan. This file records where the build differs from it, so the two stay honest. The status of what has been proven is in `docs/STATUS.md` in the repository.

## 1. Counts

| Layer | Plan (file 05) | Built | Notes |
| --- | --- | --- | --- |
| L0 Transport | 10 | 13 | Added helpers the bridge needed (join_frames, match_reply, find_midi_ports) |
| L1 FL ops (generated) | 98 | 97 | Generated from the FL API stubs 37.0.1. The gaps are in `docs/l1_missing.md` |
| L2 Verified wrappers | 41 | 48 | |
| L3 Recipes | 15 | 16 | Plus `write_notes_via_script`, `check_notes_written`, `copy_project_to_sandbox` |
| L4 Measures | 32 | 38 | Adds the targets, genre profile and invariants loaders, `check_report_limits`, `critique_audio_dsp`, `build_ab_package` |
| L5 Model adapters | 12 | 13 | Adds `run_model_op` (internal) |
| L6 Desktop control | 21 | 25 | Recipe engine, loader, dialog allow list, `render_via_cli` |
| Total | 229 | 250 | 136 are exposed as tools (L0 and L1 are internal) |

## 2. Contract changes

1. Error codes: added `E_INTERNAL` (a module bug, caught), `E_AUTONOMY` (a step above its allowed level or not approved) and `E_PENDING_HUMAN` (a person must answer; used when unattended).
2. `Result` metadata: write modules return `verified` in metadata; the linter enforces it (LM-012).
3. Composition: modules call each other only with `call("literal")`; the scheduler method that was `call` is `run_op`, because the linter flags any attribute call named `call`.
4. All four servers load all layers and expose their own. The 12 meta tools (`plan_get`, `plan_set`, `plan_update`, `plan_run`, `spec_get`, `record_decision`, `ask_human`, `phase_advance`, `ledger_tail`, `halt_run`, `request_tool`, `run_status`) live on `fl-bridge`.
5. Tool lists are sliced by phase by default. `request_tool` adds one tool with a reason. `--no-slice` turns slicing off.
6. Run state is shared between server processes through `state.json` and a `HALT` file in the run folder.
7. `present_ab` is not a separate tool: it is `build_ab_package` followed by `ask_human`.
8. The `promotion` ledger entry type was added for `coproducer promote`.

## 3. Data files

1. Invariants are TOML (`specs/templates/invariants.toml`), not YAML, so the host needs no extra dependency and the linter can allow the standard `tomllib`.
2. The targets schema replaced `low_end_mono_ratio_min` with `low_end_side_over_mid_db_max`, which is what `measure_low_end_mono_ratio` returns.
3. `load_targets_file`, `load_genre_profile` and `load_invariants_file` refuse any value still starting with `FILL`. This is how "the agent never invents targets" is enforced.
4. Genre profiles and targets are shipped as templates only.

## 4. Models: what the latest documentation said (checked October 18, 2026)

| Model | Plan said | Docs now say | Source |
| --- | --- | --- | --- |
| Demucs | Original repository archived; use the fork | `adefossez/demucs` is the maintained home: `pip install -U demucs`, Python 3.10 or newer. The README documents no output-directory flag, so the smoke test confirms the real flags | [repo](https://github.com/adefossez/demucs) |
| Basic Pitch | Python 3.7 to 3.11 | Same. TensorFlow is installed by default only on Python 3.11 or newer; ONNX is the default backend on Windows | [repo](https://github.com/spotify/basic-pitch) |
| ACE-Step 1.5 | Install route unknown | `git clone` then `uv sync`; no pip package documented. Python 3.11 to 3.12. The runner's calls match the inference guide | [repo](https://github.com/ace-step/ACE-Step-1.5), [guide](https://github.com/ACE-Step/ACE-Step-1.5/blob/main/docs/en/INFERENCE.md) |
| Music Flamingo | 8B, noncommercial, tested on A100 and H100 | `pip install --upgrade transformers accelerate`; 30 second windows with a 10 minute cap per sample | [model card](https://huggingface.co/nvidia/music-flamingo-hf) |

## 5. Planned but not built

| Item | Why | What replaces it for now |
| --- | --- | --- |
| `import_midi_into_channel` | Needs a GUI or script route proven at Gate 0 | `write_notes_via_script` (piano roll script) and `import_midi_gui` |
| `set_pattern_length_verified`, `clear_pattern_verified` | The stubs 37.0.1 have no setter; the plan expected FL 2026 additions | The piano roll script's `clearNotes`. Probe the live build with `coproducer probe install-fl` |
| `setup_sidechain_route` | No documented API for sidechain routing | GUI route or the human |
| `op_mixer_set_tempo` | Not in the stubs | `set_tempo_verified` tries `setCurrentTempo` through the raw-call allowlist and fails safe |
| A model for GUI grounding | Chosen by `bench-vision`, which needs your screenshots | `ground_gui_element` has an adapter hook and no model; recipes use hotkeys and recorded anchors |
| A skill eval runner against a live model | Needs your chosen local model | `skills_eval.py` scores transcripts; judgment assertions return `needs_review` |

## 6. Additions beyond the plan

- Skill 12, `track-creation`, because nothing in the eleven covered "make a new track from a brief".
- The piano roll note route (`write_notes_via_script`, `check_notes_written`), built from the official piano roll stubs.
- `coproducer` commands: `setup`, `doctor`, `install-models`, `lint`, `gen`, `serve`, `new-project`, `run`, `resume`, `promote`, `calibrate`, `probe`, `check-cards`, `build-card`.
- The in-FL probe script `probes/device_probe.py` and the host probes (`ping`, `throughput`, `render`, `desktop`, `models`).
- The card build loop: parser, gate in a scratch copy of the modules tree, retry with the gate report, calibration summary.

## 7. Questions still open for you

1. Which FL Studio version is installed (the plan assumes 2026.1.7)?
2. Which local model is the agent brain, and which is the coding model for cards?
3. Your reference tracks and the targets you want (the templates are blank on purpose).
4. Which plugins you own, for recipes and the genre profiles' sound families.
