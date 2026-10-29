---
name: newtime-newtone
description: Use when the person wants a vocal fitted to the beat, quantized or time-warped with FL Studio's Newtime, or auto-tuned, pitch-corrected, robotic, smooth or natural with Newtone, wants the tuned voice's melody as MIDI to drive the synths and bass, or asks where the Newtime and Newtone work lives: the modules, GUI recipes, knob styles, steps and what was measured on this machine.
---

# Newtime and Newtone

The person (2026-10-29, Girlish Type Men): "use both Newtone and Newtime and make the vocals fit into a beat perfectly ... make sure we save it into the MCP as well for both". FL's two editors have no Python API, so they are driven through the interface by GUI recipes, measured and verified on rtxclub (FL 26.1.7 at 2560 x 1440). This skill is the map of that work; the interface rules are skill `gui-fallback`.

## Where everything is

| Piece | What it does | File |
| --- | --- | --- |
| `quantize_vocal_gui` | fits a vocal to the beat: warp markers on its own syllables, quantized to 1/4 beat (16ths), saved as a new WAV | modules/l6_gui/quantize_vocal_gui |
| `detect_warp_markers` | where the markers go: syllable onsets plus the singer's own lead, one per grid line, skipped when the move is too big | modules/l4_measures/detect_warp_markers |
| `add_warp_markers_gui` | Shift+clicks each marker at its pixel, page by page, reading Newtime's view from screenshots | modules/l6_gui/add_warp_markers_gui |
| `prepare_rate_copy` | the 442/441 slow-down before Newtime and the speed-back after (Newtime's grid on this machine) | modules/l3_recipes/prepare_rate_copy |
| `apply_vocal_tuning_gui` | auto-tunes in Newtone with a style and saves the tuned WAV and the notes as MIDI | modules/l6_gui/apply_vocal_tuning_gui |
| `newtime_load_gui` | recipe: opens Newtime from the clip menu and loads the vocal (draft) | src/coproducer/data/gui_recipes/newtime_load_gui.json |
| `newtime_quantize_save_gui` | recipe: snap, quantize, save, close (verified) | src/coproducer/data/gui_recipes/newtime_quantize_save_gui.json |
| `newtone_tune_save_gui` | recipe: CENTER, VARIATION and TRANS by reading the knob arcs, save audio and MIDI, close (verified) | src/coproducer/data/gui_recipes/newtone_tune_save_gui.json |
| newtimeview | onsets, the singer's lead, marker planning, reading Newtime's bar lines, waveform and scroll handle | src/coproducer/newtimeview.py |
| knobread | a knob's value from the coloured arc in a screenshot | src/coproducer/knobread.py |
| voiceharmony | the tuned voice's MIDI on the remix grid: a lead line in key (`lead_rows`), one chord loop (`best_loop`), chords per section (voiceharmony.section_loops) | src/coproducer/voiceharmony.py |
| splice_takes | joins the three tuned takes section by section (smooth verses, robotic choruses) | tools/splice_takes.py |
| measured notes | knob semantics, dialogs, the edge auto-scroll, the grid ratio | skill `gui-fallback`, references/recipe-notes.md, "Newtime and Newtone" |
| the worked example | Girlish Type Men: padded, slowed, 127 markers, quantized, sped back, tuned three ways, spliced | sandbox\songs\girlish_type_men\gui; remixes gtm_vocal_v5 and gtm_vocal_v6 |

## Tuning styles

| Style | CENTER | VARIATION | TRANS | Sounds like |
| --- | --- | --- | --- | --- |
| robotic | 1.0 | 0.0 | 0.0 | hard snap to the semitone, flat notes, jumps between them: the T-Pain effect |
| middle | 1.0 | 0.23 | 0.33 | on pitch, a little life and glide left |
| smooth | 0.83 | 0.44 | 0.88 | corrected but sung: most of the vibrato and the slides kept |
| natural | 0.6 | 0.5 | 1.0 | gentle correction, the voice as sung |

CENTER 0 leaves a note's pitch centre, 1 puts it on the semitone; VARIATION 0.5 is the voice as sung, 0 flat, 1 doubled; TRANS 1 keeps the glides, 0 jumps. Any knob can be set on its own (center, variation, trans in 0..1 override the style). A mix works well: smooth verses, middle pre-choruses, robotic choruses, spliced by section.

## Steps

1. FL must be open with a sandbox project (the person's originals are never edited); opening another project or closing FL asks the person first.
2. Fit: `quantize_vocal_gui` with the remix tempo and division 4. It slows the voice 442/441, plans the markers (`detect_warp_markers`, the singer's lead kept so the feel stays), loads it in Newtime, places the markers, quantizes, saves and speeds it back. It fails verification when under 80 % of the markers were seen placed.
3. Tune: `apply_vocal_tuning_gui` once per style wanted, each with a MIDI path; splice the takes by section with tools/splice_takes.py when the song wants more than one.
4. Use the notes: voiceharmony places the MIDI on the remix grid; a plan's `lead_notes` let a synth double the voice, and the chords can follow the voice (skill `song-blueprints`, the vocal-led layers recipe).
5. Build with the tuned voice: `tools/remix_song.py ... --vocals TUNED.wav --plan PLAN.json` (skill `remix-from-stems`).

## What was learned (LESSONS_TO_RECIPES.md rows 77 to 86)

- Newtime's own transient detection is built for drums: on a voice it left a few markers on note peaks and quantizing moved almost nothing. Markers at the syllable onsets, moved by the singer's own lead (about 40 ms early on Girlish Type Men), fit the voice to the beat (a median 6 ms from the 16ths afterwards).
- Newtime drew 130 bpm as 1.85034 s a bar here, as if the samples ran at 44200 Hz; the 442/441 slow-down puts the voice on its grid.
- Keep Shift+clicks 50 px inside the editor: within about 25 px of an edge the view scrolls 15 px. Page with clicks at the far end of the scroll track, alternating 10 px apart so two clicks are not a double click.
- Knob drags are not linear (105 px moved VARIATION 57 % up and 36 % down), so the recipe reads the arc back and drags again (`knob_in_window`).
- Delete all markers asks first ("Delete all markers", Yes); both editors close with their X without asking.
