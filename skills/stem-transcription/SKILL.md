---
name: stem-transcription
description: Use when the person wants a stem written down as notes rather than remixed (every note the singer hits, the guitar's chords and the notes it plays, a bass line under them) as quantized piano rolls in an FL Studio project next to the stems, for checking by ear and editing, with the chords named per bar and the close calls listed; the two transcribers, the grid, the bar-line check, the out-of-scale notes, the project layout and the hearing check.
---

# Stem transcription: what she sings and plays, as piano rolls

**Read this first (2026-11-06).** The rolls this skill writes are a reading of the song, never the parts of a remix or an arrangement. The
person heard them played back and said: "you try to use math to replicate notes you heard in the music exactly and it sounds terrible."
Use the chord table, her range and where she sings to feed skill `session-arranger`, which writes the keys, pad, bass and answer line;
play a transcribed roll only when the person asks to hear the notes themselves.

The person (2026-11-05, after the third Hello Toni remix): "listen to the vocal stem, note every note her voice hits, the entire thing, then
make a piano roll quantized to match the vocal track; then listen to the guitar and listen to the chord and notes play and in a quantized
piano roll re-create it ... do not remix, just make piano and bass lines for vocal and guitar matching ... show me the results and save the
FLP file with the piano rolls in it". The first one is `sandbox\songs\hellotoni2_take2\transcription\` (README.md, the scripts, the FLP).
Editable first holds: the result is notes on instruments, the stems only as reference clips.

## The two transcribers

| Stem | Tool | Why | Watch for |
| --- | --- | --- | --- |
| a voice | `transcribe_vocal_melody` (torchcrepe, one pitch at a time, with cents) | a sung line is monophonic and slides; crepe gives the pitch with its cents, which says which side of a scale tone a note leans to | a quiet stem (Hello Toni sits near -50 dBFS) gives almost nothing: run it on the level-raised copy (`warped\vocals_117_lev.wav`, or peak-normalize first). Spoken or whispered passages come out as low notes (D3 to G3 for a woman): keep them if every note was asked for, say which bars they are |
| a guitar, keys, anything polyphonic | `transcribe_to_midi` (Basic Pitch, in beats at the tempo given) | chords need a polyphonic reader | on a phone recording the low strings are missing, so the notes sit in one octave (C4 to B4 here); thirds are often missed, so A reads as A5 and the chord name must come from the chroma too (below) |

Transcribe the **warped** stems (the steady grid the warp wrote; `warped\*.map.json` carries bpm and `origin_s`), not the raw
recording: a live take drifts and nothing quantizes to it. A note's grid beat is `(t - origin_s) * bpm / 60` (Basic Pitch's beats are from
the file start, so subtract `origin_s * bpm / 60`).

## The grid and her bars

1. Quantize starts and lengths to 16ths (`round(b / 0.25) * 0.25`, a length of at least one 16th). Same-pitch notes that land on one
   16th merge; a one-voice line never overlaps itself (a note ends where the next starts).
2. Check the bar lines before naming chords: sum Basic Pitch's onset velocities per 8th over each four-beat window and read where the
   downbeat-led strums sit. A live take can gain or lose a beat (Hello Toni 2: the whisper's first bar holds five beats, grid beats 104 to 109,
   so from then on her downbeats sit on beat 2 of the steady grid). Two ways, the person's choice (ask, it changes the song): keep the steady grid, put a marker at the odd bar and name
   every bar from her real bar starts (a 5/4 time signature marker in FL shows it); or cut one beat out of every stem at the quietest one-beat
   window inside the odd bar (`cut_beat.py`: energy per 0.1 beat of voice and guitar, the window with the least, a 10 ms crossfade, the
   same samples from every stem, the originals untouched, `config.json` says what was cut) so the song sits in 4/4. Hello Toni 2 took the
   cut (grid beats 106.75 to 107.75, a gap between two whispered words).
3. The tuning of the recording: the chroma script's energy histogram and crepe's cents histogram say how far off A440 the take is; her
   voice here sat near 0 (median +9 cents) while the guitar's partials leaned +20 to +40. Round pitches at A440 unless the voice's
   median says otherwise.

## Chords per bar

`sandbox\songs\hellotoni2_take2\transcription\chords_true_bars.py` (after `warped\bar_chords.py`): log chroma 150 Hz to 1.5 kHz with the
tuning offset removed, scored against the 24 triads per bar, per half bar and per beat. Combine it with the pitch classes Basic Pitch heard
in the bar (the chroma hears the low strings and the ring of the previous chord, Basic Pitch the plucked notes); a tie on the third goes to
the key's own chords. A change inside a bar is taken only when the last two beats read one other diatonic chord AND the plucked notes carry
its root and no longer the bar's root. Settle the remaining close calls by the song's form (verse 2 repeats verse 1, a tag ends on the V) by
hand and write each one down with its reason (`chord_flags` in transcription.json, the README's list): the person listens and decides.

## The project (build_project.py, from an FL-saved stem base)

Rows: the stems as audio clips (peak-normalized copies, the clip's content from `origin_s` so project beat 0 is her beat 0, no stretch), then
one channel per roll: the melody as sung on a piano, the melody snapped to the key on a second piano row with its clips **muted** (the
person compares by unmuting), the guitar's notes on the piano, the roots on BooBass (the demo instruments are imported from
`sandbox\demo_study\render` with `flpfile.import_channel`: Never Out channel 20 for DirectWave's Piano Grand DUO 2, Bien Duro channel 9
for BooBass). Not FL Keys from the demos: in a command-line render it misses its first notes and plays about 20 dB down, so the hearing
check heard one note of 276 (`instr_test.py`, a scale on each candidate rendered alone, is how an instrument earns its place). Piano rolls
in 16-bar blocks (`add_part_blocks`), markers for the sections and the odd bar, the base's own channels, clips and muted rows removed
(`strip_notes`, `clear_playlist`, `reset_playlist_tracks`), tempo set, song mode on. The bass: the bar's root in the bass octave (D2 38, E2 40,
G2 43, A2 45) on every beat the guitar strums in and on every chord change, held to the next hit, at most two beats.

## Showing the result

A picture of the three rolls over the stems' own readings (grey what the tracker heard, colour what was written, bar numbers on her bars,
chord names on the bass row) is what the person reads first; the README lists the chord per bar with its evidence, the out-of-scale notes
with their cents and where they went, the whisper's bars, and what is pending.

## Hearing it back (verify.py)

`split_part_projects` on the FLP, `render_folder_via_cli` (FL closed; never close it unasked), then torchcrepe on the melody roll's render
and Basic Pitch on the guitar roll's render against the notes written (pitch match per note within 0.3 beat; `compare_note_sequences`), and
the bass render's pitch classes per bar against the chord list. A roll that cannot be heard back is not checked.

## Rules

- Every note the voice hits means every one: out-of-scale notes stay on the main row (F4 between E4 and F#4 is what she sang), the snapped
  row is the alternative, and the list of them with cents is in the README.
- The guitar roll is what Basic Pitch heard, quantized, not idealized chord shapes; the chord names are a reading of it and the chroma,
  for the bass and the person's ear.
- Nothing is cut, stretched or re-arranged: the stems play as they are.

## Sources

- torchcrepe (MIT) and Basic Pitch (Spotify, Apache 2.0) as wired in `modules/l5_models`; the chroma method from `warped/bar_chords.py` (2026-11-03).
- This project: `docs/LESSONS_TO_RECIPES.md` rows 116, 119, 126, 151 (her grid), 160 and 161 (this skill).
