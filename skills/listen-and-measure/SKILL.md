---
name: listen-and-measure
description: Use when the user wants the project analyzed, listened to, or measured: capturing a render, choosing which measurement answers which question, reading a measure report, comparing to a reference, and cross-checking key and tempo.
---

# Listen and measure

You cannot hear. You measure, then say what the numbers mean. Every claim has a number and a unit.

## Get audio to measure

1. Prefer a fresh render of the sandbox copy: `prepare_for_render`, then `render_via_cli`, then `restore_after_render`. The render is checked for silence.
2. If the command-line render fails, ask for a manual export or use the GUI route (`export_split_stems_gui` for one file per mixer track).
3. A capture is stale if the project changed after it. Keep the snapshot id and the project hash with every measurement. Re-render after any change.

## Pick the measure that answers the question

| Question | Tool |
| --- | --- |
| Whole picture | `build_measure_report` |
| How loud is it? | `measure_integrated_loudness`, `measure_short_term_loudness`, `measure_loudness_range` |
| Will it clip? | `measure_true_peak`, `count_clipped_samples`. Sample peak (`measure_sample_peak`) is not enough |
| How punchy or squashed? | `measure_crest_factor`, `measure_rms` |
| Tonal balance | `measure_band_energy`, `measure_spectral_centroid` |
| Width and mono safety | `measure_mid_side_ratio`, `measure_stereo_correlation`, `measure_low_end_mono_ratio` |
| Do two parts fight? | `measure_masking_overlap` (name the pair) |
| Is a stem clean? | `detect_leakage`, `detect_silence` |
| Per section (Buildup against Drop) | `measure_section_levels` with the project, so sections come from its time markers |
| Tempo, key, sections | `estimate_bpm_dsp`, `estimate_key_dsp`, `detect_sections_dsp`; cross-check key and tempo with `estimate_key_bpm_ml` when a model is loaded |
| Versus a target or reference | `load_targets_file` then `check_report_limits`, or `compare_to_reference` |
| Describe in words | `critique_audio` (model) or `critique_audio_dsp` (no model); treat words as hints, numbers as evidence |

Peaks are not loudness. A loud-sounding track can have a low peak, and the reverse.

## Targets

Never state a target number from memory. Read the targets file with `load_targets_file`. If it refuses because values are blank, tell the human which ones and stop. If the human has no file yet, ask what they want (see `co-producer-protocol`).

## How to report

Write findings as: what was measured, the value with unit, the target or reference value, the difference, and what it suggests. Example shape: "integrated loudness X LUFS, target Y LUFS, 1.4 LU over". Separate facts from guesses. If a model critique disagrees with a measurement, report both and trust the measurement.

## Order of work

1. Measure the whole report.
2. Compare with targets or a reference.
3. Dig into the failing area with the specific measure.
4. Cross-check tempo and key if the task depends on them.
5. Only then ask a model for words.

## Ask when

- No targets file or reference exists and the question needs one.
- Two measures disagree and the difference changes the advice.
- The capture is older than the last change and a re-render needs a human to export.
