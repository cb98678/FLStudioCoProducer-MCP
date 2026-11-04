---
name: reference-copy
description: Use when the person brings an original and a remix (or any reference track) and asks to copy what the reference did as practice, to make "our own remix similar to" it, or to sample sounds, loops or notes from the reference into a remix. Covers measuring the reference's moves (form, melody bends, drums, bass, sounds), capturing its loops, kit, bass note and one synth note, building a practice copy, comparing it against the reference, and turning what was learned into options, a style and skill notes.
---

# Copying a reference as practice

The person (2026-10-29, with Better Off Alone and the Pickle remix): "sometimes the remix is simple but complex ... examine the original
and the remix, see what they did and write new skills, recipes and creative options, then make your own remix similar to the remix I
gave you. A practice in copying this will help us build the skills." A copy is a test of understanding: if the copy sounds like the
reference, the moves were read right; where it does not, the difference is the next lesson. It works on top of `remix-craft` (the study),
`loops-and-kits` (the capture), `serum-wavetables` (the sounds) and `remix-from-stems` (the build); their rules hold.

## Rules

- Measure before naming a move: tempo, key, tuning per stem, the form in functions, every part's pattern, how the melody moves between
  notes. The person hears the move ("only a small pitch bend"); the numbers say what it is (a 22 ms constant-time glide from the last note).
- Keep what the reference kept. If it kept the melody, the copy keeps it note for note; changing it is a different remix.
- The voice rules still hold: whole lines, its own pitch, at most 6 % slower than sung. When the reference broke a rule (Pickle slowed the
  voice 6.6 %), the copy keeps the rule and says how close it got (129 bpm, 5.8 %).
- Sounds taken from the reference are study material: the practice copy stays private. A release keeps the moves and rebuilds the
  sounds (a Serum table or preset from the measurement, the person's own kit and loops).

## Steps

1. **Split and analyse both** (FL's own stem split, `build_song_analysis`), then tools/study_remix_pair.py for the line map and the 8-bar
   loudness blocks. Write the form as functions with bar numbers (`remix-craft`, study protocol).
2. **Tuning per stem** (spectral peaks over the whole stem): a remix can retune one part only (Pickle's bass 21 cents flat, everything
   else in tune). Set the copy's vocal pitch_ratio so the voice lands on concert pitch.
3. **The melody's notes and their moves.** Transcribe the riff or lead (note onsets, then pitch every 2.5 ms over the first 60 to 80 ms of
   each note against the note's own pitch). Read: where each note starts (the last note's pitch: a glide; a fixed amount low: a scoop),
   how long it takes and whether that depends on the interval (constant time: portamento), when it does not happen (after a rest, on a
   repeat), and what happens at the end (a fall). Also the gate: how long a note holds before its level drops.
4. **Capture** with `extract_song_loops` (sections on the analysis grid, 1-based): drum loops, kit, bass loop and notes. Pick one note of
   the lead with nothing gliding into it and little under it, and lift it out (`prepare_sampler_sound` options isolate, pitch_midi,
   fade_out_s). Slice one beat of the averaged bass loop for the bass (options tune, in cents measured over the whole stem).
5. **Sounds.** The note on a Sampler (plan sampler_lead), and `build_wavetable` on the same note for a Serum layer (`serum-wavetables`).
   Top loops stretched to the copy's tempo and high-passed (plan drum_loops). The bass slice as plan bass_sample.
6. **Options first, then the plan.** Every move becomes an option (bass, drums, form, chords) with the reference under "remixes" in
   sources.json, and a style pack when the moves make a whole genre recipe. Draft with `build_song_plan` locking those options, then
   write the sections, clips, roots, lead notes and captured parts by hand (an edit_plan.py beside the plan).
7. **Build, render, master** with `tools/remix_song.py --plan`, then compare against the reference: 8-bar loudness blocks, the form, the
   lead's glide measured the same way as in step 3, the low end's pitch. Write what matches and what does not in the study page.
8. **Write it down**: the study page (docs/remix_studies), the skill notes (this skill's worked example, `song-blueprints` reference page,
   `remix-craft` moves), LESSONS_TO_RECIPES rows, tests for every new code path.

## Worked example: Better Off Alone, the Pickle remix (2026-10-29)

The study: docs/remix_studies/better_off_alone_pickle.md. The moves: the riff note for note, a 22 ms glide into every note while the last
one rings, a G# pedal bass one pumped note a beat with an A-G#2-G#1-A turnaround, four on the floor, pads only in the breakdowns, the title
line as the only vocal, a DJ intro and outro. Made into: options form.dj_revival, drums.euro_revival_four, bass.pedal_pump_neighbor; style
euro_revival_house; plan fields sampler_lead (glide), drum_loops, bass_sample. The copy: sandbox\remix\boa_pickle_style_v1 (pick_note.py,
make_sounds.py, edit_plan.py), 129 bpm, five builds: the drops first sat under the vocal blocks (lead, loops and bass raised) and the
captured kick's low tail covered the pedal bass between the beats until it was shelved and shortened (v5; the study page has the table). Found on the way: the bass sample had played off key in every song not in A (fixed in
`remixplan.reese_key`).
