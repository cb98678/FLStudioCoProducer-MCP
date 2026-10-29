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
