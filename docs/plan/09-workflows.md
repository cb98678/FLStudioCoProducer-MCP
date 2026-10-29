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
