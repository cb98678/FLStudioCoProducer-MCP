---
name: track-creation
description: Use when the user wants a new track made in FL Studio from a brief, such as "make a dubstep track at 140 in F minor": tempo, structure, MIDI parts, instruments, routing and a first mix, using the plugins the user owns.
---

# Track creation (new track from a brief)

You build the track from MIDI and the human's own instruments. Generated audio is a reference sketch or a texture, never a silent replacement for a MIDI part. Drums are sampler channels plus patterns and synths are plugin channels plus piano-roll notes (see `editable-first`); generated sounds and samples are fine as the source material.

## Steps

1. **Intake.** `ping_fl`, `read_project_summary`, `get_fl_versions`. Work in a sandbox copy of a template project (`copy_project_to_sandbox`, `open_project_copy`). Load the genre profile with `load_genre_profile`; if it has blanks, ask the human to fill them.
2. **Brief (V1).** `ask_human`: genre profile, tempo, key, length, mood. Put the answers in the spec sheet with `record_decision`.
3. **Plan.** Write a section map and chord plan from the genre profile. Take the form, groove, bass line, chord treatment, arp, harmony loop, instruments, transitions and mix from the option bank the FL demo songs taught (skill `creative-variety`, `docs/DEMO_STUDY.md`): choose per brief, never the last track's set, and say which demo song each choice comes from. Present it for approval (V1) before building.
4. **Tempo.** `set_tempo_and_swing` (read back).
5. **Sketch (optional).** `check_gpu_budget`, then `generate_audio` for a reference or texture. Check the result is not silent; measure it with `build_measure_report` as a tonal and loudness reference only.
6. **Parts.** Write drum, bass, chord and lead notes as note lists in beats (`pitch`, `start`, `duration`, `velocity`). `write_midi_file` keeps a copy. Put notes in the piano roll with `write_notes_via_script`, run it with `arm_piano_roll_script_gui` and `run_piano_roll_script_gui`, and confirm with `check_notes_written`. `import_midi_gui` is the alternative route.
7. **Sounds.** `load_plugin_gui` and `load_sample_gui` for the instruments and samples the genre profile names. Set parameters with `apply_param_recipe` (see `sound-design-recipes`).
8. **Layers and tuning.** Stack parts the way the reference does with `build_layer_channel`: a kick of a body sample and a top sample on one insert, a clap of two or three, a bass of a sub and a mid bass on their own inserts. The Layer takes the part's notes, so nothing plays twice. Then `apply_drum_tuning` moves kicks, toms and 808s to the nearest root or fifth of the key (at most 3.5 semitones; samples with no clear pitch are left alone and listed). Confirm on a kick solo render that the body pitch landed on the target note.
9. **Routing.** `route_channel_to_track_verified`, `set_track_name_verified`, then `apply_project_standard` on the sandbox copy (names, colours, channel groups) and, with the copy open in FL, `build_family_buses` for the Drums, Vocals and FX buses (`docs/PROJECT_STANDARD.md`). Use `build_bus` for any other group.
10. **Sections and transitions.** For a whole arrangement, `apply_production_recipe` does all of this step and the buses, chains and pump in one pass (see `remix-from-stems`, step 4); the moves below are the same recipes one at a time.
     Write the section map as time markers (`add_section_markers`; `build_remix_project` writes them itself, numbered where a name repeats: Drop 1, Drop 2), then the transitions the reference uses into each drop with `add_transition_automation`: a high-pass filter sweep on the music, a reverb throw on the last beats, a rising snare roll pitch (`semitones`, 12 by default; measured on a sampler snare, it rises steadily into the drop), the sub fading in, and a one-beat gap before the drop. Add editable risers with `add_transition_synths`: a noise riser ending on the drop, a one-beat impact chord in the key on it, a noise downlifter starting a break; they come in at the reference's channel levels, which sit far under our mix, so set them with `gain-staging` (or a `volume`). Pump the music and sub on the kick with `build_volume_pump`. Check each on a render around the marker (`measure_section_levels`, `measure_pump_depth`).
11. **First mix.** `set_rough_balance`, then follow `gain-staging` and `mix-engineer`. Measure with `listen-and-measure`.
12. **Deliver.** `build_ab_package` against the sketch or the previous version, and `ask_human` for approval.

## Rules

- Everything happens in the sandbox copy.
- Genre numbers (tempo range, patterns, registers) come from the genre profile, the style pack or the option bank's cited sources, never from memory.
- Keep each part short at first (a loop), check it, then extend.
- Pitches stay in the key the human chose unless the plan says otherwise; check with `estimate_key_dsp` on a render.

## Ask when

- The brief, plan, or any instrument choice is open.
- The genre profile or targets file has blanks.
- A part sounds wrong and the fix is a taste call.
