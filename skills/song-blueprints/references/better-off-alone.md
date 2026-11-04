# Better Off Alone (Alice Deejay, 1998) and the Pickle remix

Checked 2026-10-29. The person brought the original and the Pickle remix as files, to copy the remix's moves as practice.

## Confirmed

| Fact | Value | Source |
| --- | --- | --- |
| Release | December 1998 in the Netherlands; the riff first came out as a DJ Jurgen instrumental in 1997 | Wikipedia (https://en.wikipedia.org/wiki/Better_Off_Alone) |
| Writers, producers | Sebastiaan Molijn and Eelke Kalberg; produced with Wessel van Diepen and Dennis van den Driesschen | Wikipedia |
| Tempo, key | 137 bpm, G# minor | Wikipedia; our grid reads 136.99 bpm and the bass votes G# minor |
| Chords | E, D#m, G#m, F# a bar each (VI, v, i, VII), under the riff's four bars | measured: the original's bass stem, bar by bar |
| The Pickle remix | 128 bpm, G# minor, the riff note for note, a constant-time glide of about 22 ms into every note, a G# pedal bass with an A-G#2-G#1-A turnaround, the title line as the only vocal | measured on the person's file: docs/remix_studies/better_off_alone_pickle.md |

No public release details for the Pickle remix were found; everything about it here is measured.

## The moves

| Move | Option or plan field |
| --- | --- |
| The record's riff kept note for note, a glide added between notes | plan sampler_lead with `glide` (slide notes); lead_notes for a Serum layer |
| One note of a synth sampled and played from the piano roll | `prepare_sampler_sound` (isolate, pitch_midi, tune) |
| The same note as a wavetable | `build_wavetable` on the isolated note |
| Four on the floor under a captured top loop | drums.euro_revival_four; plan drum_loops |
| Tonic pedal, one pumped note a beat, a semitone-neighbour turnaround | bass.pedal_pump_neighbor; plan bar_roots, bass_sample |
| DJ intro and outro, pad breakdowns, short vocal blocks, instrumental drops | form.dj_revival; style euro_revival_house |

## Practice copies

A copy built from the reference remix's own sounds (its loops, its bass, its lead note) is study: it shows whether the moves are
understood, and it stays private. For a release, keep the moves and replace the sounds: the Serum table and preset routes rebuild the
timbre from a measurement, and the kit and loops come from the person's own packs (`find_matching_loops`).
