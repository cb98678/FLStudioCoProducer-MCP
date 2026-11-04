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
4. Use the notes: Newtone's Save as MIDI holds no tempo message and 400 ticks a beat at the bench project's tempo, so read it with that tempo (`voiceharmony.midi_notes(path, bpm=130.0)` for the 130 bpm bench; read as 120 its notes run 8 % slow, LESSONS row 118); voiceharmony places the MIDI on the remix grid; a plan's `lead_notes` let a synth double the voice, and the chords can follow the voice (skill `song-blueprints`, the vocal-led layers recipe).
5. Build with the tuned voice: `tools/remix_song.py ... --vocals TUNED.wav --plan PLAN.json` (skill `remix-from-stems`).

## When not to (Rick Rolled, 2026-10-31, LESSONS rows 113 to 115)

- **Check before fitting.** Run `detect_warp_markers` on the padded voice first: its mean_move_ms is how far the syllables sit from the
  16ths. Under about 10 ms (a comedy recording made over a 130 bpm beat read 8.9 ms) the voice is on the grid already and Newtime would
  only blur it. A dense voice also hides Newtime's grid lines (the editor scales the waveform to its full height, and newtimeview reads the
  lines above it), so the fit fails with "fewer than two bar lines"; a quieter copy does not help.
- **Speech is not a melody.** Newtone robotic on talking snaps each syllable to the nearest semitone, scattered across the octave, and it
  fights any chord loop. Use natural for speech (a light correction, the voice stays talking) and robotic for sung or chanted lines.
- **The bench.** Newtime and Newtone open from the clip menu of the audio clip at the start of playlist track 1. After FL's stem split the
  stems bench shows the mixer and its source clip is muted: open a vocal bench copy first (sandbox\gui_work\gtm_vocal_bench_130.flp
  copied next to the song), answering No to saving the stems bench and Keep for its stem files.

## What was learned (LESSONS_TO_RECIPES.md rows 77 to 86)

- Newtime's own transient detection is built for drums: on a voice it left a few markers on note peaks and quantizing moved almost nothing. Markers at the syllable onsets, moved by the singer's own lead (about 40 ms early on Girlish Type Men), fit the voice to the beat (a median 6 ms from the 16ths afterwards).
- Newtime drew 130 bpm as 1.85034 s a bar here, as if the samples ran at 44200 Hz; the 442/441 slow-down puts the voice on its grid.
- Keep Shift+clicks 50 px inside the editor: within about 25 px of an edge the view scrolls 15 px. Page with clicks at the far end of the scroll track, alternating 10 px apart so two clicks are not a double click.
- Knob drags are not linear (105 px moved VARIATION 57 % up and 36 % down), so the recipe reads the arc back and drags again (`knob_in_window`).
- Delete all markers asks first ("Delete all markers", Yes); both editors close with their X without asking.

## Long vocals and a quiet screen (Hello Toni 2, 2026-11-03)

* The bench project must run at the vocal file's own tempo (a copy with `flpfile.set_tempo`): at another tempo Newtime draws the
  tempo-synced sample stretched to the project and `add_warp_markers_gui` matches nothing (0.33).
* A 96 s file needs Newtime and Newtone to finish analysing before the next click: the recipes wait 30 s and 45 s after loading. Newtone's
  knobs ignore drags until then; `desktop_win.drag` presses, holds, moves in steps and releases.
* Her beat 0 must sit on a whole beat of the file (pad the warped file; `sandbox/songs/hellotoni2/warped/pad_for_grid.py`), since Newtime's
  grid starts at the file's start.
* Run each GUI step in a fresh FL started on the bench and killed afterwards (`sandbox/songs/hellotoni2/gui/tune_run.py newtime|newtone`);
  FL's command-line render needs FL closed. When the person is at the PC, ask for FL in front and hands off first; a window in front of FL
  takes the clicks.
* Newtone's velocities follow the recording's level: scale them for a lead synth. Its tuning is chromatic (nearest semitone): a lead that
  doubles the voice plays Newtone's notes as they are, not key-snapped.


## Long vocals: chunk them first (2026-11-03, skill `vocal-chunking`)

* A whole-song vocal took three Newtime passes to converge (24.7, 11.5, 7.6 ms median left) and each pass stretched everything. Cut it
  into phrase chunks first (`split_vocal_phrases`, every file starting on a grid line), fit each chunk on its own
  (`quantize_vocal_chunks_gui`: one FL session, a measured residual per chunk, a second pass only where needed), join them
  (`join_vocal_chunks`) and run Newtone once on the joined file. `tools/vocal_gui_run.py` starts the fresh FL on a bench at the vocal's Each run also saves its sessions as FL projects in the song's `projects` folder (one per chunk, one for Newtone) so they can be reopened and adjusted by hand: skill `vocal-chunking`, Saved projects.
  tempo for either step and refuses to run while the person's FL is open.
* The Sample properties dialog needs a Tab after the typed tempo before Accept (LESSONS row 132); the stalls had nothing to do with
  windows in front of FL.
* `newtime_load_gui` waits 4 s plus 0.3 s per second of audio after loading (a phrase in seconds, a whole song 30 s).
* `tools/level_vocal.py` before any of it: a quiet stem normalized to -1 dBFS and the whispered phrases lifted part of the way, so
  Newtime's drawing, the onset detector and Newtone hear them.
