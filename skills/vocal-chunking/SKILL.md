---
name: vocal-chunking
description: Use when a long vocal ripped from a whole song must be fitted to the beat or tuned (Newtime, Newtone), when a vocal should be split into phrase chunks that align with its phrasing and syllables, when the person asks for chunks, slices or pieces of a vocal placed across the grid, or when a vocal fit needs checking chunk by chunk. The general method, the tools, the checks and what was measured.
---

# Vocal chunking: phrases first, then Newtime and Newtone

The person (2026-11-03): "when dealing with vocals that are long because we rip them from an entire song we should consider splitting
them up into chunks that align with the phrasing and syllables so that when we Newtime and Newtone them they are easier to work with
and easier to get to fall correctly on beat without having to make major stretches to long vocal files. The slicing should be very
careful to evaluate the syllables' beginnings and ends and ensure that we're clipping them correctly. This is a careful and meticulous
process but well worth it for the final results."

Why it works (measured on Hello Toni 2): one 96 s file needed three Newtime passes to converge (24.7, 11.5, 7.6 ms median left) and
every pass stretched the whole file a little; a phrase chunk carries five to twenty syllables, so one small stretch per chunk lands it,
each chunk is verified on its own, and a phrase that sits a whole 16th off as a block is moved as a clip instead of stretched.

These are guidelines, not guardrails: when a song asks for something else (a rap verse with no silences, a held note across a bar
line), say so in the plan and do what sounds right.

## The pipeline (any song)

| Step | Tool | What it does |
| --- | --- | --- |
| 0 | `build_song_analysis`, `tools/beats_from_strums.py`, `tools/warp_to_grid.py`, `tools/warp_words.py` | the stems, the words; a free recording (no click) gets a steady grid first: beats from the harmony stem's strums (the tracker's pulse refined to each strum's start, a syncopated strum next to a beat left alone), one warp per stem, the words moved onto the warped clock by the same tempo map (no second Whisper run) |
| 1 | `tools/level_vocal.py` | whole phrases sung far under the rest (a whispered bridge, 20 dB down) lifted part of the way, the file normalized to -1 dBFS: the chunker, the onset detector and Newtime's drawing all need to hear the quiet lines |
| 2 | `split_vocal_phrases` (module, `coproducer.vocalchunk`) | the chunks: one file per phrase, cut only in silence, every file starting on a grid line; the manifest `chunks.json` |
| 3 | `tools/check_vocal_chunks.py` | every cut evaluated: the level before and after it, the release kept, the attack margin, words straddling it, the grid line |
| 4 | `quantize_vocal_chunks_gui` (module) via `tools/vocal_gui_run.py chunks` | Newtime on each chunk in one fresh FL on a bench at the vocal's tempo; the residual measured after each pass; another pass only where needed |
| 5 | `join_vocal_chunks` (module) | the fitted chunks laid back on one clock as one file (and, with `shifts_16ths`, a chunk moved as a block) |
| 6 | `apply_vocal_tuning_gui` via `tools/vocal_gui_run.py newtone` | Newtone once on the joined file: the tuned voice and its MIDI for the lead (skill `newtime-newtone`) |
| 6b | `tools/vocal_gui_run.py` (every run), `tools/save_vocal_projects.py` (stages, backfill) | every session saved as an FL project in the song's `projects` folder: one per chunk, the Newtone session, the stages (see Saved projects) |
| 7 | the plan | one playlist clip per chunk, tiled at the chunks' grid lines (`beat` in the manifest plus the plan's offset), from the tuned file; `tools/check_vocal_coverage.py` afterwards |

Worked example: `sandbox/songs/hellotoni2_take2/warped` (18 chunks, 230 of 230 words, every cut clean) and the remake plan
`sandbox/remix/hellotoni2_organic_v1/edit_plan.py`.

## How the chunker cuts (coproducer.vocalchunk)

* **Voice or silence.** The 10 ms RMS envelope against a floor 30 dB under the file's loud level (the 95th percentile of its sounding
  frames), so a quiet recording reads like a loud one; breaths and bleed stay under it.
* **Phrase gaps and syllable gaps.** A silence of 0.25 s or more ends a phrase. A silence of 0.15 s or more is a syllable gap, used
  only to split a phrase that would run past `max_beats` (16); shorter gaps never split: a stop consonant's closure ("a-gainst",
  "ex-pect") is 50 to 120 ms of silence inside a word. A gap that lies inside a transcript word's span (shrunk 60 ms at each end, since a
  recogniser's edges are loose) is never a cut whatever its length.
* **Where the cut goes.** 50 ms before the next phrase's first voiced frame when the gap also leaves 60 ms after the last voiced frame of
  the phrase before (the release and a closing s kept); in the middle of the gap when it is shorter. The cut moves to the nearest zero
  crossing and gets a 5 ms fade on both files.
* **Every file starts on a grid line.** Newtime's grid starts at the file's start, so the file starts on the latest beat of the song's
  grid that lies in the gap at or before the cut (a 16th when no beat does), and is silent from that line to the cut. Two consecutive
  files overlap only in that silence, and the manifest's `beat` (16ths from the origin / 4) is where the chunk goes in the playlist.
* **The manifest** carries, per chunk: `grid_s`, `grid_16ths`, `beat`, `audio_s` (the cut), `end_s`, `voiced_s`, `on_beat`, `padded`, its
  words and text, its onsets and each onset's distance from the nearest 16th (`offsets_ms`, negative early), `median_offset_ms` and
  flags: `long` (over max_beats and no gap to split at), `no_beat_line`, `padded`, `short`, `off_grid` (the median offset is past
  `max_move_s`: the phrase sits off as a block, so move the clip by a 16th rather than stretch it).

## The checks (what "careful" means here)

`tools/check_vocal_chunks.py MANIFEST` prints, per cut: the level 40 ms before and after it (a cut inside a sound fails), the release
kept behind it, the attack margin ahead of it (at least 20 ms), whether a transcript word straddles it (a failure in a short gap, a
note when the silence around the cut is 150 ms or longer: the transcript's edges are loose, the audio decides), the grid line, and
that the file exists and covers its audio. On Hello Toni 2 all 18 cuts sat in silence 60 ms to 1 s long with 50 to 60 ms of attack
margin; the three transcript straddles were Whisper's loose word ends over real silences.

After Newtime: `quantize_vocal_chunks_gui` measures each chunk's residual (its syllables' distance from where they should sit, by the
marker detector's own onsets) before and after each pass and keeps the record in the manifest under `fit`; chunks already within
`target_ms` (10) are skipped, a chunk whose markers were not seen is closed and reported, and the loop goes on. The detector marks a
burst about 12 ms before its attack on synthetic tests, so 10 ms is a floor, not a target to chase.

## Newtime per chunk, in practice

* FL must be closed first (the run reports a running FL and stops; it never kills the person's session); the runner starts FL on a
  bench project at the vocal's tempo (`tools/vocal_gui_run.py bench --from sandbox/gui_work/gtm_vocal_bench_130.flp --bpm 117.5`),
  fits every chunk, and kills that FL. `newtime_load_gui` waits 4 s plus 0.3 s per second of audio, 12 to 30 s (under 12 s the
  Sample properties dialog ignores Accept even for a 2 s chunk), and drags Newtime to (120, 90) first so its scroll bar is on screen.
* Every chunk file ends with two bars of silence: Newtime shows about 5 s and reads its bar lines where the waveform is quiet, so a
  chunk that is voice from end to end showed fewer than two lines. The join places files by their grid line, so the tail costs nothing.
* A failed chunk is left by state: Escape only while a dialog sits over the editor, Newtime's X only while it is open, F5 when the
  playlist went (an Escape too many once closed the playlist and every later chunk found no clip menu).
* Measured on Hello Toni 2 (18 chunks, one FL session, about 50 s a chunk): residuals 1.7 to 8.9 ms median after one pass each (two
  for the first), 97 % of the markers seen placed; `--min-share 0.6` for chunks (13 of 21 seen still landed at 2.6 ms).
* The first pass uses the singer's measured lead (how early the syllables sit) unless the person wants them on the lines (`--lead 0`);
  every later pass and the measurement count from the same place.
* `max_move_s` 0.1 for chunks: a phrase is short, so every syllable within 100 ms of its line moves; on a whole file 45 ms was the
  safe limit.
* A chunk flagged `off_grid` (median offset past the limit) is a block that sits a 16th off: shift it with `join_vocal_chunks
  --shifts_16ths` (or in the plan's clip position) rather than stretching.

## Saved projects (every element can be reopened)

The person (2026-11-03): "save every Newtone and Newtime ... so I can go in and make little adjustments if needed ... every element that you
work on save it, it's okay if you get a bunch of .flp, saved in the folder." The editors run in a disposable bench FL that is killed after
each run, so the sessions are written as projects instead, by `coproducer.sessionflp` (module `save_session_project`), by default:

* `projects/newtime/STEM_NN_newtime.flp`, one per chunk: row 1 the file Newtime last opened (the `_q1_newtime_in.wav`, its `.zpw` holds the
  markers), row 2 the chunk as cut, row 3 the fitted copy that went into the song. Open it, clip menu > Time-warp sample: the markers come back
  (checked in FL 26 on Hello Toni 2 chunk 2). Newtime shows its own guess at the sample tempo, so press F2 and enter the project's bpm (in
  the README) before adjusting; Ctrl+S saves a new wav, then `join_vocal_chunks` and Newtone again if the fit changed.
* `projects/newtone/NAME_newtone.flp`: row 1 the file Newtone opened (tuning in its `.zpa`), row 2 the tuned result.
* `projects/stages/`: `01_vocal_chunks_cut`, `02_vocal_chunks_fitted` (every chunk on the song's clock at its grid line, a negative start
  trimmed), `03_vocal_fitted_joined`, `04_vocal_tuned`, each with the instrumental stem under it (`--bed`).
* `projects/README.txt` lists them. Files are referenced, not copied, so the wavs and their `.zpw`/`.zpa` stay where they are.

`vocal_gui_run.py chunks|newtone` writes the first two after each run (`--projects DIR` moves them, `--no-projects` skips them);
`tools/save_vocal_projects.py` writes the stages and backfills a song worked on before. The other elements of a remake (its sounds, the
remix project) are already files in the remix folder: the Serum states and wavs under `sounds/`, the built `.flp` and its zip.

## In the plan

One clip per chunk from the joined, tuned file, tiled at the chunks' grid lines: clip k runs from its grid line to the next chunk's,
so the release of one phrase and the silence before the next are never doubled. A plan clip row is [the project bar where the singer's
bar 0 (origin_s) lands, 0.0, grid_s, next grid_s, label, "bars", "vocals"]: the build places each window by its start on her grid, so a
chunk whose file starts on her 16th g sits at project beat OFF + g / 4 without any arithmetic in the row (a row carrying the chunk's own
bar in the first field put the song 80 s long). The pluck or lead that doubles the voice comes from
Newtone's MIDI read at the bench's tempo (`voiceharmony.midi_notes(path, bpm=...)`, `to_remix` on the clips). Band rests at the
singer's own stops sit between chunks by construction.
