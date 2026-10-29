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

## 11. Where the work stands (updated 2026-10-23)

Gate 0 passed on the real machine (FL 26.1.7, see `GATE0.md` and `FL_API_FINDINGS.md`). The work since then went to the remix line described in `15-as-built.md`, section 8, rather than to W3 restyle. Next lanes, in the order the user set them:

| Lane | Work | Size | Proof |
| --- | --- | --- | --- |
| Sound | Serum 2 stabs, arp, sub through the Serum MCP; swap into the builder; re-set mixer levels | M | Load test in FL, render v13 vs v12, listening |
| Vocal | Designed gabber or high-pitched stab for drop 2 | S | Listening; `chop_conflicts` clean |
| Generalise | Second song: song analysis, automatic chop planning, verified downbeat, hands-off stems, regression set | L | The same render report and listening on a new song |
| Recipe | Original-element reminiscence (stretched original guitar clips in chosen sections) | M | Listening |
| Mix | Master limiter and target loudness for the remix (the render is minus 16.4 LUFS with no limiter) | S | `render_report.py`, targets file |

Details and commands: `HANDOFF.md`, `STEM_REMIX_PIPELINE.md`, `SERUM_MCP.md`.
