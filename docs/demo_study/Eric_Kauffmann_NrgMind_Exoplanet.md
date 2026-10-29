# Eric Kauffmann & NrgMind - Exoplanet

FL Studio 2026 demo project `Eric Kauffmann & NrgMind - Exoplanet.flp`, studied on a sandbox copy (the original is untouched). Genre as the project names it: Trance.

| Tempo | Key (from the notes) | Key (from the render) | Bars | Length | Saved in FL | PPQ |
| --- | --- | --- | --- | --- | --- | --- |
| 140.0 | C major | A minor | 261 | 7:27 | 12.9.3.321 | 96 |

1 playlist clips are muted and play nothing; the readings above leave them out.

Trance at 140 bpm, built in additive 8-bar blocks named 1er Cambio to 6to Cambio (changes), with a long pre-drop and breakdown: the clearest lesson in pacing.

## What it does and how

**Form.** Intro blocks of 8 to 16 bars, each adding a part or opening a filter; PRE DROP 32; BREAKDOWN; drop.

**Rhythm and drums.** Four on the floor plus a GHOST kick channel (the sidechain trigger); closed hats on the three 16ths after each kick (.XXX), an open hat and a ride on the off-beat, two percussion voices on the 'a' of beats (...X..X....X..X.), claps on 2 and 4 from two channels; snare rolls in 16ths from velocity 31 to 100 over the build.

**Bass.** The rolling bass: per beat a rest where the kick hits, then root, root, octave, the second beat swapping the octave for the minor seventh (. A1 A1 A2 . A1 G2 A1); Harmor, 3x Osc, Harmless and Sytrus layers into a bass bus with EQ, WaveShaper, Maximus, limiters and two filters; a very short 3x Osc sub (0.08 beats).

**Harmony.** A minor: F, G, Dm, E (VI, VII, iv, major V); the breakdown turns to C (Am G C Cmaj7 Am7 Fadd9).

**Sounds and synths.** Main Lead stack: four MiniSynths, two Sytrus, two Harmor and a vocal sample on the same gated chord line with the bass octave between the hits; Pluck - Saku (Sakura) falling C5 B4 G4 E4; Harmless pedal arp (A3 between rising tones); Energic Pads (MiniSynth), Pads 2 (Sytrus); FL Keys piano layers; a Sytrus cello and Sakura lead in the breakdown.

**Vocal production.** A vocal sample doubled into the lead stack.

**Mix and sidechain.** Pump only 0.9 dB measured: the GHOST trigger works on the bass and pads, not the whole mix; -6.0 LUFS, the loudest with With You.

**Automation.** 85 clips: kick low-pass in the breakdown, bass bus filters and WaveShaper mix, pad and arp filters opening over 32 to 260 beats, MiniSynth filter velocity, master reverb wet and master filter, a 12-point tempo clip.

**Transitions.** The low-pass opening is the build; the master reverb is the breakdown.

## How it sounds (measured on the full render)

The project automates its tempo, so section times after the first change are approximate (bars are placed at the starting tempo).

| LUFS | True peak dB | LRA LU | Crest dB | Width (side/mid dB) | Width under 120 Hz | Centroid Hz | Pump dB (loudest section) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -6.03 | 2.23 | 9.23 | 8.86 | -7.87 | -22.86 | 1173.4 | 0.87 |

Band balance (dB of the total): sub -7.05, bass -5.03, low_mid -7.61, mid -7.81, high_mid -11.4, presence -12.54, air -16.75.

| Section | Bar | Bars | LUFS | Centroid | Width | Sub dB | Air dB |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 1 | 8 | -15.33 | 2503.0 | -5.99 | -25.74 | -12.66 |
| 1er Cambio | 9 | 8 | -12.95 | 2400.9 | -7.93 | -12.89 | -13.12 |
| 2nd Cambio | 17 | 16 | -7.97 | 1121.9 | -12.85 | -6.31 | -15.75 |
| 4to Cambio | 33 | 8 | -7.37 | 366.5 | -13.05 | -4.86 | -22.99 |
| 5to Cambio | 41 | 8 | -6.96 | 516.4 | -12.23 | -5.24 | -21.09 |
| 6to Cambio | 49 | 16 | -6.18 | 877.3 | -11.68 | -6.27 | -17.98 |
| PRE DROP | 65 | 32 | -6.06 | 1153.8 | -9.96 | -6.63 | -16.31 |
| BREAKDOWN | 97 | 165 | -5.57 | 1287.1 | -6.79 | -7.6 | -16.54 |

## How its instruments sound (solo renders, soundbrief.describe)

| Part | Role | Plugin | Attack s | Decay s | Sustain | Centroid Hz | Register | Width | In words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B - Harmor | bass | 3x Osc, Harmless, Harmor, Sytrus | 0.1617 | 0.161 | 0.0 | 629.75 | A2 | medium | soft, slow attack; plucked (short decay); chords or several notes at once |
| Pluck - Saku | lead | Sakura | 0.0299 | 0.5065 | 0.0 | 506.7 | G4 | medium | quick attack; decaying (long tail); chords or several notes at once |
| SUB | bass | 3x Osc | 0.0353 | 0.0975 | 0.0 | 44.0 |  | mono | quick attack; plucked (short decay); chords or several notes at once |
| Main Lead 1 | lead | Harmor, MiniSynth, Sytrus | 0.0277 | 1.705 | 0.0 | 737.0 |  | wide | quick attack; decaying (long tail); chords or several notes at once |
| Pluck Harmonies | lead | MiniSynth | 0.001 | 0.1915 | 0.0 | 920.15 | F2 | medium | sharp, percussive attack; plucked (short decay); chords or several notes at once |
| Harmless #2 | arp | Harmless | 0.001 | 0.125 | 0.0 | 846.35 | B4 | medium | sharp, percussive attack; plucked (short decay); medium stereo image |
| DOPE Melody | lead | Sytrus | 0.008 | 0.2975 | 0.0 | 357.6 | A3 | narrow | sharp, percussive attack; plucked (short decay); dark, few upper harmonics |
| Energic Pads | chords | MiniSynth | 1.7439 | 10.3325 | 0.0 | 1996.05 |  | wide | soft, slow attack; decaying (long tail); chords or several notes at once |
| Downstream Kick 12 | kick | sampler | 0.0236 | 0.2 | 0.0 | 105.8 | F#1 | mono | quick attack; plucked (short decay); chords or several notes at once |

## The data

**Sections** (from the markers, or 8-bar phrases merged by what plays):

| # | Bar | Bars | Name | Energy | Plays |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 8 |  | 0.4 | audio, bass, drums |
| 2 | 9 | 8 | 1er Cambio | 0.51 | audio, bass, drums |
| 3 | 17 | 16 | 2nd Cambio | 0.59 | audio, bass, drums |
| 4 | 33 | 8 | 4to Cambio | 0.53 | audio, bass, chords, drums, lead |
| 5 | 41 | 8 | 5to Cambio | 0.72 | audio, bass, chords, drums, lead |
| 6 | 49 | 16 | 6to Cambio | 0.79 | audio, bass, chords, drums, lead |
| 7 | 65 | 32 | PRE DROP | 0.85 | arp, audio, bass, chords, drums, lead |
| 8 | 97 | 165 | BREAKDOWN | 1.0 | arp, audio, bass, chords, drums, lead |

**Harmony** (a chord per bar from every pitched part): A7 (VI7) x32, Am (vi) x32, F (IV) x2, G (V) x2, Dm (ii) x3, E5 (III5) x1, F (IV) x2, G (V) x2, Dm (ii) x3, E5 (III5) x1, F (IV) x2, G (V) x2, Dm (ii) x3, E5 (III5) x1, F (IV) x2, G (V) x2, Am (vi) x3, G (V) x1, C (I) x1, Cmaj7 (Imaj7) x1, Am7 (vi7) x2, Fadd9 (IVadd9) x2, C (I) x1, Cmaj7 (Imaj7) x1

**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):

| Voice | Channel | Pattern | Hits a bar | Late | Velocity | Bars |
| --- | --- | --- | --- | --- | --- | --- |
| clap | HouseGen Clap 09 | `............X...` | 1.18 | 0.0 | [100, 100] | 174 |
| clap | HouseGen Clap 09 #2 | `....X...........` | 1.18 | 0.0 | [100, 100] | 174 |
| crash | Grv Crash 01 | `X...............` | 1.04 | 0.0 | [100, 100] | 46 |
| crash | Volt CleanCrash 01 | `X...............` | 1.04 | 0.0 | [100, 100] | 46 |
| crash | Reverse Crash | `.........X......` | 1.0 | -0.375 | [100, 100] | 7 |
| crash | Grv Crash 01 #2 | `X...............` | 1.0 | 0.0 | [100, 100] | 5 |
| crash | Volt CleanCrash 01 #2 | `X...............` | 1.0 | 0.0 | [100, 100] | 5 |
| crash | Grv Crash 01 #3 | `....X...........` | 1.0 | 0.0 | [100, 100] | 4 |
| hat | HH_2 | `.XXX.XXX.XXX.XXX` | 12.0 | 0.0 | [65, 100] | 190 |
| hat | HH_3 | `.XXX.XXX.XXX.XXX` | 12.0 | 0.0 | [58, 100] | 174 |
| hat | HH | `..X...X...X...X.` | 4.0 | 0.0 | [100, 100] | 160 |
| kick | GHOST | `X...X...X...X...` | 4.0 | 0.0 | [100, 100] | 207 |
| kick | Downstream Kick 12 | `X...X...X...X...` | 4.04 | -0.001 | [51, 100] | 192 |
| kick | Reverb Kick | `X...............` | 1.0 | 0.0 | [100, 100] | 9 |
| kick | Reverse Kick | `..............X.` | 1.0 | -0.333 | [100, 100] | 6 |
| perc | Perc 1 | `...X.......X....` | 2.0 | 0.0 | [100, 100] | 190 |
| perc | Perc 2 | `......X.......X.` | 2.0 | 0.0 | [100, 100] | 190 |
| perc | Perc 3 | `...X..X....X..X.` | 4.0 | 0.0 | [100, 100] | 190 |
| perc | Perc 4 | `.XXX.XXX.XXX.XXX` | 12.0 | 0.0 | [57, 100] | 174 |
| ride | Ride | `..X...X...X...X.` | 4.0 | 0.0 | [100, 100] | 72 |
| snare | Snare | `XXXXXXXXXXXXXXXX` | 17.08 | 0.0 | [31, 100] | 48 |
| snare | Attack Snare 05 | `............X...` | 1.0 | 0.0 | [100, 100] | 4 |

**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):

| Role | Name | Plugin or sample | Preset | Insert chain | Range | Poly | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bass | B - Harmor | Harmor |  |  | D1-C3 | 1.0 | 2649 |
| bass | B - 3xOsc | 3x Osc |  |  | D1-C3 | 1.0 | 2649 |
| bass | B- Harm | Harmless |  |  | D1-C3 | 1.0 | 2649 |
| bass | Default | Sytrus |  |  | D1-C3 | 1.0 | 2649 |
| lead | Pluck - Saku | Sakura |  |  | E4-C5 | 1.0 | 2032 |
| bass | SUB | 3x Osc |  |  | D0-C1 | 1.0 | 1725 |
| arp | Laurie Webb Come On A - D6_2 - D6_2 |  |  |  | F1-G4 | 1.38 | 1573 |
| lead | Main Lead 1 | MiniSynth |  |  | F2-G5 | 1.38 | 1573 |
| lead | Main Lead 1 #2 | MiniSynth |  |  | F2-G5 | 1.38 | 1573 |
| lead | Main Lead 1 #3 | MiniSynth |  |  | F2-G5 | 1.38 | 1573 |
| lead | Main Lead 1 #4 | MiniSynth |  |  | F2-G5 | 1.38 | 1573 |
| lead | Main Lead 1 #5 | Sytrus |  |  | F2-G5 | 1.38 | 1573 |
| lead | Main Lead 1 #6 | Sytrus |  |  | F2-G5 | 1.38 | 1573 |
| lead | Main Lead #6 | Harmor |  |  | F2-G5 | 1.38 | 1573 |
| lead | Main Lead #7 | Harmor |  |  | F2-G5 | 1.38 | 1573 |
| lead | Pluck Harmonies | MiniSynth |  |  | G4-C5 | 2.0 | 1488 |
| arp | Harmless #2 | Harmless |  |  | A3-C5 | 1.0 | 744 |
| lead | DOPE Melody | Sytrus |  |  | A3-E5 | 1.0 | 680 |
| chords | Energic Pads | MiniSynth |  |  | B2-E5 | 4.11 | 456 |
| chords | Energic Pads #2 | MiniSynth |  |  | B2-E5 | 4.11 | 456 |
| lead | Pluck Bacano! | Harmless |  |  | G4-E5 | 1.0 | 98 |
| chords | Pads 2 | Sytrus |  |  | D3-E5 | 2.83 | 68 |
| chords | Pads 2 | Sytrus |  |  | G2-G5 | 2.79 | 67 |
| chords | Piano | FL Keys |  |  | E4-A6 | 2.0 | 36 |
| chords | Piano #2 | FL Keys |  |  | E3-A5 | 2.0 | 36 |
| chords | Piano #3 | FL Keys |  |  | E3-A5 | 2.0 | 36 |
| fx | FX1 | 3x Osc |  |  | G3-G3 | 1.0 | 25 |
| fx | FX2 | 3x Osc |  |  | G3-G3 | 1.0 | 24 |
| bass | Sub Pad | 3x Osc |  |  | A2-A3 | 1.0 | 22 |
| lead | Sakura | Sakura |  |  | C5-C6 | 1.0 | 18 |

**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):

bass, B - Harmor (Harmor), from bar 1:

```
.   A1  A1  A2  .   A1  G2  A1  .   A1  A1  A2  .   A1  G2  A1 
.   A1  A1  A2  .   A1  G2  A1  .   A1  A1  A2  .   A1  G2  A1 
```

bass, B - 3xOsc (3x Osc), from bar 1:

```
.   A1  A1  A2  .   A1  G2  A1  .   A1  A1  A2  .   A1  G2  A1 
.   A1  A1  A2  .   A1  G2  A1  .   A1  A1  A2  .   A1  G2  A1 
```

bass, B- Harm (Harmless), from bar 1:

```
.   A1  A1  A2  .   A1  G2  A1  .   A1  A1  A2  .   A1  G2  A1 
.   A1  A1  A2  .   A1  G2  A1  .   A1  A1  A2  .   A1  G2  A1 
```

bass, Default (Sytrus), from bar 1:

```
.   A1  A1  A2  .   A1  G2  A1  .   A1  A1  A2  .   A1  G2  A1 
.   A1  A1  A2  .   A1  G2  A1  .   A1  A1  A2  .   A1  G2  A1 
```

lead, Pluck - Saku (Sakura), from bar 41:

```
C5  B4  G4  E4  C5  B4  G4  E4  C5  B4  G4  E4  C5  B4  G4  E4 
C5  B4  G4  E4  C5  B4  G4  E4  C5  B4  G4  E4  C5  B4  G4  E4 
```

bass, SUB (3x Osc), from bar 33:

```
A0  A0  A0  -   A0  A0  A0  -   A0  A0  A0  -   A0  A0  A0  -  
A0  A0  A0  -   A0  A0  A0  -   A0  A0  A0  -   A0  A0  A0  -  
```

**Mixer buses and the master:**

- 0 Master: Fruity Parametric EQ 2 > Fruity Reeverb > Fruity Filter > Fruity Parametric EQ 2 > Maximus
- 3 Perc Bus (fed by [4, 5, 6, 7, 8, 9, 10]): Fruity Filter > Fruity Parametric EQ 2
- 15 Sub Bass (fed by [1]): Fruity Filter > Fruity Parametric EQ 2 > Fruity Limiter > Fruity Balance
- 17 BASS BUS (fed by [1, 18, 19, 20]): Fruity Parametric EQ 2 > Fruity WaveShaper > Maximus > Fruity Limiter > Fruity Filter > Fruity Filter > Effector > Fruity Limiter > Fruity Limiter
- 21 LEAD BUS (fed by [1, 24, 25, 26, 27, 28, 29, 30, 32]): Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Compressor > Fruity Filter > Fruity Reeverb > Patcher > Fruity Limiter > Fruity Balance
- 23 Lead Inicio (fed by [1]): Fruity Fast Dist > Fruity Compressor > Fruity Filter > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Delay 2 > Fruity Limiter > Fruity Balance
- 26 LEAD 3 (fed by [1]): no effects
- 29 LEAD 6 (fed by [1]): Fruity Limiter > Fruity Filter > Fruity Parametric EQ 2
- 31 LEAD BREAK (fed by [1]): Fruity Parametric EQ 2 > Fruity Limiter
- 33 Energic Pads (fed by [1]): Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Filter > Fruity Limiter
- 34 PLUCK (fed by [1]): Fruity Filter > Fruity Parametric EQ 2 > Fruity Reeverb > Fruity Limiter > Fruity Balance
- 35 Arp (fed by [1]): Fruity Filter > Fruity Parametric EQ 2 > Fruity Limiter
- 37 Pads 2 (fed by [1]): Fruity Filter > Fruity Filter > Fruity Parametric EQ 2 > Fruity Balance
- 43 PIANO BUS (fed by [40, 41, 42]): Fruity Parametric EQ 2 > Fruity Limiter
- 44 FX BUS (fed by [1, 45, 46, 47]): Fruity Parametric EQ 2 > Fruity Limiter

**Automation:** 85 clips, by target: generator 57, ? 20, MiniSynth 4, channel 3, Harmor 1.

**Kit** (the most played sample of each voice): kick Grv Kick 03.wav; clap HouseGen Clap 09.wv; hat Attack Hat 06.wv; perc Collider Desert Rattle 01.wv; ride 909 Ride.wav; snare Attack Snare 11.wv; crash Grv Crash 01.wav.

## What it adds to the option bank

- `form.additive_layers` (Additive 8-bar blocks, one long breakdown, one big drop)
- `drums.trance_rolling` (Trance: three-of-four hats, syncopated percs, offbeat ride)
- `bass.rolling_16` (Rolling trance bass: three 16ths after each kick, a seventh in the roll)
- `harmony.trance_VI_VII_iv_V` (VI, VII, iv, V (minor with a major dominant))
- `chords.gated_trance_lead` (Gated chord lead with the bass octave between)
- `arp.fall` (Falling major-seventh pluck)
- `arp.pedal` (Pedal-tone arp: root between rising tones)
- `fx.kick_filter_in` (Low-passed music opening into the drop, master reverb in the breakdown)
- `automation.reverb_breakdown` (Master reverb up for the breakdown, thrown out on the drop)
- `mix.ghost_trigger_pulse` (Ghost-trigger pump: the pulse without a kick)
- `sound.trance_lead_stack` (Trance lead stack (MiniSynth, Sytrus, Harmor on one part))
- `sound.sakura_pluck` (Sakura string pluck)
- `sound.rolling_bass_layers` (Rolling bass in four layers)
- `kit.exoplanet` (Exoplanet kit (Trance))

