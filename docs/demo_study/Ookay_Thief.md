# Ookay - Thief

FL Studio 2026 demo project `Ookay - Thief.flp`, studied on a sandbox copy (the original is untouched). Genre as the project names it: Future Bass.

| Tempo | Key (from the notes) | Key (from the render) | Bars | Length | Saved in FL | PPQ |
| --- | --- | --- | --- | --- | --- | --- |
| 150.0 | C# major | F# major | 144 | 3:50 | 25.2.3.5164 | 96 |

The render's audio reads F# major (a chroma vote over the first two minutes, margin 0.3242; it often lands a fifth away on bass-heavy mixes): not settled without listening. 8 playlist clips are muted and play nothing; the readings above leave them out.

Future bass at 150 bpm: half-time drops, an 808 snare roll rising in pitch, saw chords and bass gated by Gross Beat, a music-box bell arp doubled in octaves.

## What it does and how

**Form.** Verse, build, half-time drop, verse, build, drop, with a tempo automation clip.

**Rhythm and drums.** Snare (two snareclaps and a conga) on beat 3 only; a skipping kick (X...o...x...x.o.); a ride on 1 and 3; the 808 snare rolling 16ths in builds with its pitch automated.

**Bass.** Harmless synth bass held; a 3x Osc saw bass through Gross Beat in the drop (B2 for 9 steps, Ab2 for 4); white noise from 3x Osc playing the bass's rhythm.

**Harmony.** C# major: bVII, V, I, II as power chords (the major II is a Lydian lift).

**Sounds and synths.** Tinke Bell (FLEX General Midi Library) doubled two octaves (Bb4+Bb6) on a fast arp; Piano Dark (FLEX); sax samples.

**Vocal production.** A vocal with a Vocodex send; Free Filter sweeps on the vocal bus.

**Mix and sidechain.** Pump 12.1 dB, the second deepest: Gross Beat and a Balance 'Volume Duck' clip; the kick feeds buses as a sidechain source.

**Automation.** The 808 snare's pitch, Gross Beat, Free Filter, crash reverb, tempo.

**Transitions.** The pitched snare roll is the build.

## How it sounds (measured on the full render)

The project automates its tempo, so section times after the first change are approximate (bars are placed at the starting tempo).

| LUFS | True peak dB | LRA LU | Crest dB | Width (side/mid dB) | Width under 120 Hz | Centroid Hz | Pump dB (loudest section) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -8.32 | 3.59 | 10.71 | 10.95 | -9.08 | -15.89 | 1017.8 | 12.08 |

Band balance (dB of the total): sub -4.76, bass -6.62, low_mid -8.04, mid -8.21, high_mid -10.94, presence -14.1, air -17.29.

| Section | Bar | Bars | LUFS | Centroid | Width | Sub dB | Air dB |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 1 | 16 | -12.79 | 1243.2 | -5.76 | -10.29 | -16.5 |
|  | 17 | 8 | -6.37 | 985.3 | -9.7 | -4.45 | -15.85 |
|  | 25 | 16 | -6.59 | 1148.7 | -11.57 | -4.92 | -19.19 |
|  | 41 | 8 | -9.22 | 905.7 | -8.24 | -3.55 | -16.76 |
|  | 49 | 16 | -11.02 | 768.2 | -8.61 | -5.52 | -20.4 |
|  | 65 | 8 | -8.69 | 866.3 | -9.44 | -5.38 | -18.49 |
|  | 73 | 8 | -6.28 | 972.4 | -10.07 | -4.41 | -15.67 |
|  | 81 | 16 | -6.55 | 1146.8 | -11.53 | -4.93 | -19.18 |
|  | 97 | 8 | -12.33 | 1436.4 | -1.67 | -10.96 | -14.71 |
|  | 105 | 8 | -6.31 | 948.5 | -9.17 | -4.31 | -15.5 |
|  | 113 | 16 | -7.95 | 994.8 | -8.01 | -3.75 | -16.81 |
|  | 129 | 16 | -16.7 | 442.7 | -6.41 | -7.25 | -24.93 |

## How its instruments sound (solo renders, soundbrief.describe)

| Part | Role | Plugin | Attack s | Decay s | Sustain | Centroid Hz | Register | Width | In words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tinke Bell | lead | FLEX | 0.018 | 1.3805 | 0.0 | 2848.65 | F#5 | wide | quick attack; decaying (long tail); chords or several notes at once |
| Piano Dark | chords | FLEX | 0.1036 | 4.3125 | 0.0 | 357.95 | F#2 | medium | soft, slow attack; decaying (long tail); lots of upper harmonics (bright or driven) |
| Saw Bass | bass | 3x Osc | 0.016 | 0.02 | 0.816 | 176.15 | G#1 | mono | quick attack; sustained; mono |
| Synth Bass | bass | Harmless | 0.001 | 1.508 | 0.0 | 72.7 | B1 | wide | sharp, percussive attack; decaying (long tail); brightness falls after the attack (filter envelope) |

## The data

**Sections** (from the markers, or 8-bar phrases merged by what plays):

| # | Bar | Bars | Name | Energy | Plays |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 16 |  | 0.02 | audio, bass, drums, vocal |
| 2 | 17 | 8 |  | 0.02 | audio, drums, vocal |
| 3 | 25 | 16 |  | 1.0 | audio, bass, drums, fx, lead, vocal |
| 4 | 41 | 8 |  | 0.12 | audio, bass, drums, fx, vocal |
| 5 | 49 | 16 |  | 0.02 | audio, bass, drums, vocal |
| 6 | 65 | 8 |  | 0.11 | audio, bass, chords, drums, vocal |
| 7 | 73 | 8 |  | 0.1 | audio, chords, drums, vocal |
| 8 | 81 | 16 |  | 1.0 | audio, bass, drums, fx, lead |
| 9 | 97 | 8 |  | 0.11 | audio, bass, chords, vocal |
| 10 | 105 | 8 |  | 0.1 | audio, chords, drums, vocal |
| 11 | 113 | 16 |  | 1.0 | audio, bass, drums, fx, lead, vocal |
| 12 | 129 | 16 |  | 0.11 | audio, bass, chords |

**Harmony** (a chord per bar from every pitched part): B5 (bVII5) x1, Ab5 (V5) x1, C#5 (I5) x1, Eb5 (II5) x1, B5 (bVII5) x1, Ab5 (V5) x1, C#5 (I5) x1, Eb5 (II5) x1, B5 (bVII5) x1, Ab5 (V5) x1, C#5 (I5) x1, Eb5 (II5) x1, B5 (bVII5) x1, Ab5 (V5) x1, C#5 (I5) x1, Eb5 (II5) x1, B5 (bVII5) x1, Ab5 (V5) x1, C#5 (I5) x1, Eb5 (II5) x1, B5 (bVII5) x1, Ab5 (V5) x1, C#5 (I5) x1, none x1

**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):

| Voice | Channel | Pattern | Hits a bar | Late | Velocity | Bars |
| --- | --- | --- | --- | --- | --- | --- |
| clap | WA_BHB_Kit4_Snap_126BPM | `........X.......` | 1.0 | 0.0 | [100, 100] | 16 |
| crash | 909 Crash | `x..............o` | 1.0 | 0.0 | [100, 100] | 6 |
| kick | Grv Kick 27 | `X...o...x...x.o.` | 2.9 | 0.0 | [100, 100] | 93 |
| perc | 808 Conga | `........X.......` | 1.0 | 0.0 | [100, 100] | 96 |
| ride | Importer Ride | `X.......X.......` | 2.0 | 0.0 | [100, 100] | 40 |
| snare | Grv Snareclap 13 | `........X.......` | 1.0 | 0.0 | [100, 100] | 56 |
| snare | Grv Snareclap 06 | `........X.......` | 1.0 | 0.0 | [100, 100] | 56 |
| snare | 808 Snare | `XxXXXxXxXxXXXXXX` | 16.57 | -0.017 | [100, 100] | 21 |
| tom | Titey Tom #4 | `x.............x.` | 1.0 | 0.0 | [100, 100] | 12 |
| tom | Titey Tom #2 | `........X.......` | 1.0 | 0.0 | [100, 100] | 7 |
| tom | Titey Tom | `..........X.....` | 1.0 | 0.0 | [100, 100] | 7 |
| tom | Titey Tom #3 | `............X...` | 1.0 | 0.0 | [100, 100] | 7 |

**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):

| Role | Name | Plugin or sample | Preset | Insert chain | Range | Poly | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lead | Tinke Bell | FLEX | General Midi Library / Tinke Bell | Fruity Parametric EQ 2 > Maximus > Fruity Chorus > Fruity Balance | Bb4-F#7 | 2.0 | 1920 |
| fx | White Noise | 3x Osc |  | Fruity Reeverb 2 | C4-C4 | 1.0 | 210 |
| chords | Piano Dark | FLEX | General Midi Library / Piano Dark | Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Maximus | Eb2-C#5 | 4.26 | 196 |
| bass | Saw Bass | 3x Osc |  | Fruity Multiband Compressor > Fruity Parametric EQ 2 > Gross Beat > Fruity Parametric EQ 2 | Eb2-C#3 | 1.0 | 94 |
| bass | Synth Bass | Harmless |  |  | Eb2-Eb3 | 1.0 | 85 |
| audio | SAX 4 | ookay thief saxophone.wav |  | Maximus > Fruity Parametric EQ 2 > Fruity Reeverb 2 |  | 0.0 | 0 |
| audio | SAX 3 | ookay thief saxophone.wav |  | Maximus > Fruity Parametric EQ 2 > Fruity Reeverb 2 |  | 0.0 | 0 |
| audio | SAX 5 | ookay thief saxophone.wav |  | Maximus > Fruity Parametric EQ 2 > Fruity Reeverb 2 |  | 0.0 | 0 |
| audio | SAX | ookay thief saxophone.wav |  | Maximus > Fruity Parametric EQ 2 > Fruity Reeverb 2 |  | 0.0 | 0 |
| audio | SAX 2 | ookay thief saxophone.wav |  | Maximus > Fruity Parametric EQ 2 > Fruity Reeverb 2 |  | 0.0 | 0 |
| audio | YELP | Dragged sample_678.wav |  | Fruity Reeverb 2 > Fruity Stereo Shaper |  | 0.0 | 0 |
| fx | Riser Noise Metal | Riser Noise Metal.wv |  | Fruity Parametric EQ 2 > Fruity Limiter |  | 0.0 | 0 |
| fx | Riser Noise | Riser Noise.wv |  |  |  | 0.0 | 0 |
| vocal | Main Vox | ookay thief vox.wav |  |  |  | 0.0 | 0 |
| vocal | VOCAL PITCHED #2 | Dragged sample_677.wav |  | Fruity Parametric EQ 2 > Fruity Reeverb 2 > Fruity Stereo Shaper > Maximus > Fruity Free F |  | 0.0 | 0 |
| vocal | VOCAL PITCHED | Dragged sample_677.wav |  | Fruity Parametric EQ 2 > Fruity Reeverb 2 > Fruity Stereo Shaper > Maximus > Fruity Free F |  | 0.0 | 0 |
| audio | CUTS | Untitled project - _4 (consolidated)_2.wav |  | Fruity Reeverb 2 > Fruity Parametric EQ 2 > Fruity Delay 3 > Maximus > Fruity Limiter > Fr |  | 0.0 | 0 |
| vocal | PITCHED VOX | Dragged sample_699 #2 (consolidated).wav |  | Fruity Limiter > Fruity Parametric EQ 2 |  | 0.0 | 0 |
| audio | FALSETTO #2 | Dragged sample_675 (consolidated)_2.wav |  | Fruity Reeverb 2 > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 |  | 0.0 | 0 |
| vocal | MAIN VOX | Dragged sample_699 (consolidated)_4.wav |  | Fruity Parametric EQ 2 > Fruity Multiband Compressor > Fruity Stereo Enhancer > Maximus >  |  | 0.0 | 0 |
| vocal | MAIN VOX #2 | Dragged sample_699 (consolidated)_4.wav |  | Fruity Parametric EQ 2 > Fruity Multiband Compressor > Fruity Stereo Enhancer > Maximus >  |  | 0.0 | 0 |
| audio | FALSETTO | Dragged sample_675 (consolidated)_3.wav |  | Fruity Reeverb 2 > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 |  | 0.0 | 0 |
| audio | CUTLAYER2 (consolidated) (consolidated) | CUTLAYER2 (consolidated) (consolidated).wav |  | Fruity Free Filter > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 |  | 0.0 | 0 |

**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):

lead, Tinke Bell (FLEX), from bar 27:

```
Bb4+Bb6+F#5+F#7+F#5+F#7 F#5+F#7 F#5+F#7+F5+F7+F5+F7 F5+F7 F5+F7+C#5+C#7+C#5+C#7 C#5+C#7 C#5+C#7+Bb4+Bb6+Bb4+Bb6 Bb4+Bb6 Bb4+Bb6+F#5+F#7+F#5+F#7 F#5+F#7 F#5+F#7+F5+F7+F5+F7 F5+F7 F5+F7+C#5+C#7+C#5+C#7 C#5+C#7 C#5+C#7+Bb4+Bb6+Bb4+Bb6 Bb4+Bb6
Bb4+Bb6+F#5+F#7+F#5+F#7 F#5+F#7 F#5+F#7+F5+F7+F5+F7 F5+F7 F5+F7+C#5+C#7+C#5+C#7 C#5+C#7 C#5+C#7+Bb4+Bb6+Bb4+Bb6 Bb4+Bb6 Bb4+Bb6+F#5+F#7+F#5+F#7 F#5+F#7 F#5+F#7+F5+F7+F5+F7 F5+F7 F5+F7+C#5+C#7+C#5+C#7 C#5+C#7 C#5+C#7+Bb4+Bb6+Bb4+Bb6 Bb4+Bb6
```

chords, Piano Dark (FLEX), from bar 65:

```
B2+Eb3+C#4+F#4+Bb4 -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
Ab2+C#4+F#4+Ab4 -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
```

bass, Saw Bass (3x Osc), from bar 25:

```
B2  -   -   -   -   -   -   -   -   .   .   .   Ab2 -   -   -  
-   -   -   -   -   -   -   -   C#3 -   -   -   -   -   -   .  
```

bass, Synth Bass (Harmless), from bar 1:

```
B2  -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
Ab2 -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
```

**Mixer buses and the master:**

- 0 Master: Fruity Soft Clipper (Fruity Soft Clipper)
- 11 Saw Bass (fed by [1]): Fruity Multiband Compressor > Fruity Parametric EQ 2 (1 Fruity Parametric EQ 2) > Gross Beat > Fruity Parametric EQ 2 (1 Fruity Parametric EQ 2) > Maximus > Fruity Limiter (2 Fruity Limiter)
- 12 BELL (fed by [1]): Fruity Multiband Compressor > Fruity Parametric EQ 2 > Fruity Stereo Enhancer > Maximus > Fruity Balance > Fruity Limiter (2 Fruity Limiter)
- 14 CUTS (fed by [1, 24]): Fruity Reeverb 2 > Fruity Parametric EQ 2 (1 Fruity Parametric EQ 2) > Fruity Delay 3 > Maximus > Fruity Limiter (2 Fruity Limiter) > Fruity Parametric EQ 2 (1 Fruity Parametric EQ 2) > Fruity Limiter (2 Fruity Limiter)
- 21 DOWNSWEEP (fed by [1]): Fruity Parametric EQ 2 (1 Fruity Parametric EQ 2) > Fruity Limiter (2 Fruity Limiter)
- 27  (fed by [24]): Fruity Limiter (2 Fruity Limiter) > Vocodex > Fruity Reeverb 2 > Fruity Stereo Enhancer > Fruity Limiter (2 Fruity Limiter) > Fruity Parametric EQ 2 (1 Fruity Parametric EQ 2)

**Automation:** 8 clips, by target: Fruity Balance 2, mixer 2, channel 2, Fruity Free Filter 2.

**Kit** (the most played sample of each voice): kick Grv Kick 27.wav; tom Titey Tom.wav; perc 808 Conga.wav; crash 909 Crash.wav; snare 808 Snare.wav; ride Importer Ride.wav; clap WA_BHB_Kit4_Snap_126BPM_3222812.wav.

## What it adds to the option bank

- `form.halftime_switch` (Future bass: build, then a half-time drop)
- `drums.future_bass_halftime` (Future bass: half-time snare on 3, pitched 808 snare rolls)
- `bass.halftime_wobble` (Half-time saw bass, gated by Gross Beat)
- `harmony.lydian_bVII_V_I_II` (bVII, V, I, II (major with a Lydian lift))
- `arp.octave_doubled` (Octave-doubled fast arp)
- `fx.snare_pitch_roll` (Pitched snare roll and a tape stop)
- `mix.gross_beat_gate` (Gross Beat volume gate on bass and chords)
- `vocal.vocoder_texture` (Vocoder or robot texture under the lead)
- `sound.tinke_bell` (FLEX Tinke Bell (General Midi Library))
- `sound.saw_bass_gated` (3x Osc saw bass through Gross Beat)
- `kit.thief` (Thief kit (Future Bass))

