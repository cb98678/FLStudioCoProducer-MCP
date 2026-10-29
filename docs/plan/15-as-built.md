# 15. As Built: What Changed Between the Plan and the Code

Written October 18, 2026, after the first build. Files 00 to 14 describe the plan. This file records where the build differs from it, so the two stay honest. The status of what has been proven is in `docs/STATUS.md` in the repository.

## 1. Counts

| Layer | Plan (file 05) | Built | Notes |
| --- | --- | --- | --- |
| L0 Transport | 10 | 13 | Added helpers the bridge needed (join_frames, match_reply, find_midi_ports) |
| L1 FL ops (generated) | 98 | 97 | Generated from the FL API stubs 37.0.1. The gaps are in `docs/l1_missing.md` |
| L2 Verified wrappers | 41 | 48 | |
| L3 Recipes | 15 | 16 | Plus `write_notes_via_script`, `check_notes_written`, `copy_project_to_sandbox` |
| L4 Measures | 32 | 40 | Adds the targets, genre profile and invariants loaders, `check_report_limits`, `critique_audio_dsp`, `build_ab_package` |
| L5 Model adapters | 12 | 13 | Adds `run_model_op` (internal) |
| L6 Desktop control | 21 | 25 | Recipe engine, loader, dialog allow list, `render_via_cli` |
| Total | 229 | 281 | 154 are exposed as tools (L0 and L1 are internal). Counts at the 2026-10-23 save point; the L-rows above were last itemised on 2026-10-18 except L4 |

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
| A model for GUI grounding | Chosen by `bench-vision`, which needs your screenshots | `ground_gui_element` has an adapter hook and no model; recipes use hotkeys and recorded anchors. Candidate: Qwen3.5-9B, see `docs/LOCAL_MODELS.md` |
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

## 8. Beyond the plan: the remix work (added 2026-10-23)

The plan stopped at restyle (W3). The build has since grown a second line of work that the plan does not describe: remixing a song from FL's own stems into a finished arrangement, editable first.

- **Library**: `flpfile` (FLP reader and patcher), `drumplan`, `oneshots`, `tension`, `fxbed`, `automation`, `vocalfx`, `vocalclips`, `vocalchops`, `cutrefine`, `remixplan`, `drumhits`, `mixtools`, `synthmatch`, `edison`. All are in `src/coproducer/`; `FILE_MAP.md` lists them.
- **Host tools**: `tools/` holds the pipeline scripts (`refine_cuts`, `techhouse_audio`, `build_techhouse`, `render_report`), and `tools/queue_runner.ps1`, a job queue on the host. The cloud container cannot reach FL, so it drops `.cmd` files into `sandbox\queue` and the runner executes them. This replaces the plan's assumption that the agent runs next to FL.
- **Two working copies**: the cloud copy is edited and tested, the host copy is updated by numbered tar files (`sandbox\deploy\cp_updateNN.tar`).
- **Direct file patching** (`flpfile`) is used where the plan expected only the FL API and GUI. It is limited to sandbox copies and proven by FL opening and rendering the result.
- **Policy**: `docs/PRODUCTION_POLICY.md` (editable first) and the skill `editable-first` with `references/vocal-chops.md`.
- **Modules added in this line**: `add_automation_clip`, `list_automation_clips`, `remove_automation_clip`, `list_effect_slots`, `set_effect_active_verified`, `set_eq_db_verified`, `check_vocal_edges`, `find_final_s_end`, among others. Two L4 measures (`check_vocal_edges`, `find_final_s_end`) run in phase P5.
- **Docs**: `HANDOFF.md` (start here), `FILE_MAP.md` (generated), `WORKED_EXAMPLE_DTP.md`, `WORKED_EXAMPLE_FRIENDS.md`, `STEM_REMIX_PIPELINE.md`, `VOCAL_CHOP_RECIPE.md`, `FLP_FORMAT.md`, `SERUM_MCP.md`.
- **Third party**: Serum 2 is installed; the Serum MCP (`Celian-mrc/serum-mcp`) is audited and not yet run (`SERUM_MCP.md`).

## 9. Realignment (2026-10-25)

The remix line was built for one genre (house and tech house) on one song. `docs/ROADMAP.md` measures the build against the person's goal
(any song, any genre the person names, evaluators that check each other, today's club sound, the fullest FL control), lists the code review's
fixes and open findings, and proposes the build order. Where this plan and the roadmap differ, the roadmap is newer.
