# Better Off Alone: the original against the Pickle remix

The person's files, studied on sandbox copies on 2026-10-29: "Better Off Alone" (Alice Deejay, 1998; written by Sebastiaan Molijn and
Eelke Kalberg, 137 bpm, G# minor, its riff first released as a DJ Jurgen instrumental in 1997, per
[Wikipedia](https://en.wikipedia.org/wiki/Better_Off_Alone)) and "Better Off Alone (Pickle Remix)". Both went through FL Studio's own stem
split (`extract_stems_gui`), `build_song_analysis` and tools/study_remix_pair.py; then the Pickle remix's loops and kit were captured
(`extract_song_loops`), its lead was transcribed note by note around every onset, and the pitch of its lead was tracked every 2.5 ms into
22 notes. Lines are named by function, never quoted. What only ears can confirm is marked.

## The reading

Simple but complex, as the person put it: Pickle kept the record's riff note for note and changed almost nothing about it except how it
moves between notes. The riff plays on a plucky mono lead that glides from the last note's pitch into each new one in about 22 ms, whatever
the interval, while the last note still rings; after a rest or on a repeated note it does not glide. That is the "small pitch bend" on
every note. Around it, a modern four-on-the-floor house record: a kick on every beat, the clap on 2 and 4, an open hat on every off-beat,
a G# pedal bass pumping one note a beat with a semitone-neighbour turnaround, pads only in the breakdowns, the title line as the only
vocal, and a DJ intro and outro. The drops carry the song with the riff alone over the pedal.

## Facts

| | Original | Pickle remix |
| --- | --- | --- |
| Length | 3:39, about 122 bars of 1.752 s | 3:41, about 118 bars of 1.875 s |
| Tempo | 137.0 bpm | 128.0 bpm: the vocal 6.6 % slower, pitch kept |
| Key | G# minor (bass votes; the mix reads B major, the relative major) | G# minor |
| Progression | E, D#m, G#m, F# a bar each (VI, v, i, VII), the riff's four bars on it | the same chords implied by the riff; the bass stays on G# in the drops |
| Tuning (cents from A440, spectral peaks) | vocal +7, instruments +3, bass +1 | vocal -1, instruments +1, bass -21 (the bass alone sits a fifth of a semitone flat) |
| Loudness per 8 bars (short-term LUFS) | - | drops -5.8 to -6.5, first breakdown -17.9, vocal blocks -9.1 to -9.7 |
| Lines of the original heard | 19 transcribed | 1: the title line, used as a chop in the vocal blocks |

## Form (remix bars at 128 bpm)

| Bars | Function | What plays |
| --- | --- | --- |
| 0 to 7 | DJ intro | drums alone |
| 8 to 15 | mix-in | drums and the G#1 bass, one note a beat |
| 16 to 29 | breakdown | held pads; the riff comes in on the lead around bar 26 |
| 30 to 40 | build | drums back, rising |
| 41 to 48 | vocal block | the title line with the drums, the bass on E D# G# F#, a pad, no lead |
| 50 to 65 | drop 1 | kick, clap, hats, the G# pedal bass, the riff quieter than the drums |
| 66 to 77 | breakdown 2 | the title line over pads |
| 78 to 85 | vocal block | the title line with the drums |
| 86 to 101 | drop 2 | as drop 1 |
| 102 to 117 | DJ outro | drums and bass, then drums alone |

## The lead: the melody kept, a glide added

- **Notes.** The riff is the original's four bars: E5 D#5 B4 G#4 B4 B4 / A#4 A#4 F#4 F#5 F#5 F#5 / B4 B4 G#4 B4 B4 B4 / A#4 A#4 F#4 E5
  E5 D#5 (sandbox/remix_study/better_off_alone/boa_riff_4bar.json, beats and MIDI).
- **The bend.** Pitch every 2.5 ms after each onset, against the note's own pitch: B4 to G#4 starts at +302 cents and settles in 28 ms;
  G#4 to B4 from -303 in 19 ms; A#4 to F#4 from +409 in 23 ms; B4 to A#4 from +100 in 22 ms. The glide takes the same time for one
  semitone or four: a synth's portamento in constant-time mode, about 20 to 25 ms. B4 after B4, and notes 0.6 s or more after the last
  one, start on pitch. Nothing bends at the end of a note.
- **The sound.** Each note is gated at an eighth (level steady for about 0.23 s, then 14 dB down at 0.25 s) with a short release, bright
  (a square-like pluck). The B4 at 50.44 s of FL's Instruments stem has no glide in it and only a quiet pad under it: lifted out with
  `prepare_sampler_sound` (isolate), 22 dB of pad came out.
- **In FL.** A slide note that overlaps a note bends it to the slide note's pitch over the slide note's length; native instruments only,
  not VSTs ([FL Studio manual, piano roll](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll.htm)).
  Render-checked on a Sampler on 2026-10-29: a slide note on the same tick as its note scoops it in, and one later in the note makes a
  fall. `remixplan.sampler_lead_notes` writes the glide: a note within a beat of a different one starts on that note's key with a
  0.05-beat slide note to its own.

## Drums, bass and harmony

- **Drums** (median of every repetition, `extract_song_loops`): kick `X...X...X...X...`; the snare band `o.X.X.X.o.X.X.X.` and the hat
  band `o.Xox.XoooXox.Xo` in the drop; the intro lighter (`o.x.X.x.`, `o.X.x.X.ooX.x.X.`). One-bar loops leave -20 dB (intro) and
  -18.6 dB (drop) of what does not repeat.
- **Bass.** G#1 on every beat, three 16ths long, in the mix-in; in the drop G#1 held and pumped, then A1, G#2, G#1, A1 in the second
  half of every fourth bar: the semitone above the root leaning back into the next phrase (Phrygian colour in a minor key). Under the
  vocal blocks it follows E D# G# F#.
- **Harmony.** No stabs. Pads only in the breakdowns and under the vocal; the drops are bass, drums and riff, the riff carrying the chords.

## Moves to take

| Move | Where it lives |
| --- | --- |
| Keep the riff note for note; add a constant-time glide between notes | `sampler_lead` with `glide` (remixplan.sampler_lead_notes); skill loops-and-kits, "One note of a synth" |
| Sample one note of the remix's synth and play the riff with it from the piano roll | `prepare_sampler_sound` options isolate, pitch_midi, tune; plan `sampler_lead` |
| The same note as a Serum wavetable layer | `build_wavetable` on the isolated note, `serumspec.table_osc`; skill serum-wavetables |
| Capture the drum loop and play it from a Sampler, high-passed under one kick | `extract_song_loops`, plan `drum_loops`; option `drums.euro_revival_four` |
| One bass note sliced from the averaged bass loop (its pump inside it) as the bass sample | plan `bass_sample`; option `bass.pedal_pump_neighbor` |
| Tonic pedal in the drops, the record's chords under the voice | plan `bar_roots`; option `bass.pedal_pump_neighbor` |
| DJ intro and outro, pad breakdowns, short vocal blocks, instrumental drops | option `form.dj_revival`; style `euro_revival_house` |

## The practice copy

sandbox/remix/boa_pickle_style_v1 (edit_plan.py, make_sounds.py, pick_note.py): the original's vocal at 129 bpm (5.8 % slower, 6 cents
down onto concert pitch), every part made from the Pickle remix's own material: its kick, clap and open hat; its drum intro and drop loops
stretched to 129 bpm and high-passed at 150 Hz; one beat of its bass, tuned 22 cents up onto G#1; its B4 lifted out of the pad playing the
riff with the glide; a Serum wavetable from the same note doubling the riff in the drops.

What five builds taught (sandbox\remix\boa_pickle_style_v1 to v5, same plan):

| Build | Change | Measured |
| --- | --- | --- |
| v1 | as planned | drops 1.5 LU under the vocal blocks; between the kicks the low end read E, not the bass's G# |
| v2 | lead, loops and bass louder; no bass in the builds until their last two bars | drops 0.4 to 0.6 LU over the vocal blocks (the Pickle remix: about 0.8); the low end still E |
| v3, v4 | no second pump on the pre-pumped bass; bass up, kick down | the low band between kicks 3.8 dB under the kick (the remix: 2 dB); still E |
| v5 | the captured kick shelved 3 dB at 60 Hz and ended at 0.24 s | between the kicks the bass reads G# in the mix-in, E D# G# F# under the vocal, G# in the drops and A on every fourth drop bar's turnaround; -8.1 LUFS, LRA 7.7 LU, -0.3 dBTP; the riff's notes within 20 cents, each leap starting on the last note's pitch |

The kick captured from the remix carried a 42 to 46 Hz tail that the remix's own louder bass hides; under a pedal bass it read as a second
bass note a tone below. Shelve and shorten a captured kick before a pedal bass goes under it.

## For the ears

- Whether the glide sounds like the remix's (0.05 beat is 23 ms at 129 bpm) or wants the synth's own portamento instead.
- Whether the Pickle remix's bass sits 21 cents flat on purpose (a detuned sub against an in-tune lead) or from a pitch-down.
- The vocal: the remix plays only the title line; the copy keeps whole sung blocks.
