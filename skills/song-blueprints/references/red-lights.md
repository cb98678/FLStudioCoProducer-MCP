# Red Lights (Tiesto, 2013)

Checked 2026-10-29. The person's breakdown called it "Red Light"; the record is "Red Lights".

## Confirmed

| Fact | Value | Source |
| --- | --- | --- |
| Chords | Gm Eb Bb F the whole song: i VI III VII in G minor, the same chords as vi IV I V in B flat major (the breakdown uses both names; they agree) | guitar chord sheet, Em C G D with a capo on 3 (https://tabs.ultimate-guitar.com/tab/1481013) |
| Key and tempo | G minor / B flat major, 125 bpm | AcousticBrainz reads A sharp major at 125 bpm (https://acousticbrainz.org/4fb749e9-1b5a-4bef-9fd0-91a3ce4dcdb1) |
| Release and credits | released 13 December 2013; produced by Tiesto, Carl Falk and Rami Yacoub | Wikipedia (https://en.wikipedia.org/wiki/Red_Lights_(song)) |

## From the breakdown only

- The pad voicing: Gm D5 Bb4 G4, Eb Eb5 Bb4 G4, Bb D5 Bb4 F4, F C5 A4 F4 over a bass G2 Eb2 Bb1 F2. The upper three voices move four semitones in four bars (Bb4 held over three chords) while the bass leaps. Not checked against the record, but it is good voice leading in any song: chords.voice_led_pad does it with `stylepack.lead_voices`.
- The verse pluck: 3+3+2 groups of 16ths, X..X..X.X..X..X., velocities 110 95 85 105 90 85. At 125 bpm a 16th is 120 ms. chords.tresillo_332_pluck.
- The verse leaves the low end empty; a distorted mono square bass takes 100 to 300 Hz at the drop. bass.empty_verse_square_drop.
- The drop lead is three layers with opposite jobs (a wide detuned supersaw, a mono percussive pluck, a mono saturated mid core). references/sound-recipes.md.
- The synth bus ducking: silent for 40 ms after each kick, about -3 dB by 100 ms, full by about 140 ms, gain 1 - e^(-(t-40)/50). This project's pump (hold 0.1 beat, back by 0.3 beat, measured on the Future House reference) is already that length at 125 bpm (48 ms, 144 ms); mix.exp_recovery_pump adds the curve.
- The master: about -5 LUFS in the last chorus with a 1.5 dB dip at 150 to 300 Hz. The dip is a mix move worth trying (references/mix-guide.md); the loudness is not this project's target.
