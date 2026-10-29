---
name: style-transfer
description: Use when the user wants an existing track moved to another genre while keeping its melody and idea, such as techno to dubstep: analysis, stem separation, MIDI transcription, the invariants file, genre profile, rebuild, and invariant checks.
---

# Style transfer (restyle)

Melody comes from transcribed MIDI, not from generation. A cover model regenerates a song; it does not preserve one. Use it only to make reference sketches.

## Pipeline

1. **Intake (P0).** `copy_project_to_sandbox` (the original is never written; its hash is recorded), `open_project_copy`, `ping_fl`. Load the genre profile with `load_genre_profile`; refuse blanks. Ask for anything the spec sheet lacks: target genre, tempo policy, delivery targets.
2. **Analyze (P1).** Render (`prepare_for_render`, `render_via_cli`, `restore_after_render`). Then `estimate_bpm_dsp`, `estimate_key_dsp`, `detect_sections_dsp`; cross-check with `estimate_key_bpm_ml` if a model is loaded.
3. **Separate.** FL Studio's own stem split first: `extract_stems_gui` on the rendered mix (vocals, drums, bass, other). Only when FL cannot run it, `check_gpu_budget`, then `separate_stems` (Demucs). Verify no stem is silent (`stems_not_silent`).
4. **Transcribe.** `transcribe_to_midi` on the melodic stem, not the full mix. Clean: `clean_midi_notes`, `quantize_notes`. Summarize: `extract_melody_contour`, `detect_chord_loop`. Save with `write_midi_file`.
5. **Invariants.** Draft the invariants file from the above (template: `specs/templates/invariants.toml`, schema: `references/invariants-schema.md`). Check it loads: `load_invariants_file`.
6. **Human gate (V1).** Present the melody MIDI and the invariants file. Offer options, recommended first. The human edits and approves; set the contour threshold they choose. Do not rebuild before approval.
7. **Rebuild (P3).** Tempo per the tempo policy. Notes are stored in beats, so changing tempo keeps every relationship. Set tempo with `set_tempo_and_swing`. Write notes with `write_notes_via_script` (then run it through the GUI recipes, then `check_notes_written`) or `import_midi_gui`. Load sounds from the genre profile's families with `load_plugin_gui` and `load_sample_gui`. Build drums, bass and fx from the genre profile. Use `transpose_notes` only if the invariants allow it.
8. **Mix and listen (P4, P5).** Follow `mix-engineer` and `listen-and-measure`.
9. **Invariant checks after every render.** Key unchanged (`key_match` against the source). Melody similarity at or above the human's threshold (`compare_note_sequences`). Section order matches (`detect_sections_dsp`). Chord loop matches (`detect_chord_loop`).
10. **Master (P6)** with `mastering`.
11. **Deliver (P7).** `build_ab_package` (source versus restyle at matched loudness), `write_report_file` with a change log, `original_untouched` verifier, then ask the human for approval. Promotion is theirs alone.

## Rules

- The invariants file is the definition of "keep the spirit". If a requested change breaks it, say which line and ask.
- Never edit the source project. Everything is in the sandbox copy.
- If a check fails, report the number and the threshold. Do not lower the threshold yourself.
- If the human says "just run the whole thing through the cover model", explain that it regenerates the song and will not keep the melody, and offer it as a sketch only.

## Ask when

- Any V1 gate above: melody review, tempo policy, genre profile choice, final A/B.
- The transcription looks wrong (wrong octave, too many notes, wrong stem). Show a short summary and ask before cleaning further.
- GPU memory is short (`check_gpu_budget` says what would be unloaded).
