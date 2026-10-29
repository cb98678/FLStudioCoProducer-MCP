# Electroconductor (aka nucleon) - Inner Days - SH-1 Rework (feat. Maja Mannila)

FL Studio 2026 demo project `Electroconductor - Inner Days - SH-1 Rework (feat. Maja Mannila).flp`, studied on a sandbox copy (the original is untouched). Genre as the project names it: Lo-Fi.

| Tempo | Key (from the notes) | Key (from the render) | Bars | Length | Saved in FL | PPQ |
| --- | --- | --- | --- | --- | --- | --- |
| 75.0 | Bb minor | A# minor | 41 | 2:11 | 24.1.0.4212 | 96 |

The notes are written in D minor, but the project's master pitch is -400 cents, so it sounds (and renders) in Bb minor. 1 playlist clips are muted and play nothing; the readings above leave them out.

The same song reworked (SH-1 Rework feat. Maja Mannila): a model of what a rework changes and keeps, the closest thing in the set to what the co-producer does.

## What it does and how

**Form.** The original's loop and parts, with a sung vocal added and the energy reshaped around it.

**Rhythm and drums.** The same drums as the original.

**Bass.** The held bass re-cut as a syncopated line (x---x--x--x-x---) and doubled two octaves down by a Heavy 808 (Sytrus): the same harmony with a hip-hop pocket.

**Harmony.** Kept: the original's chords.

**Sounds and synths.** A Harmor octave pluck (D4+D5 in a syncopated 16th figure) replaces a melodic line; piano, guitar and strings kept.

**Vocal production.** Lead and harmonies with mid and side EQ and LuxeVerbs; a VOX bus.

**Mix and sidechain.** New buses: SC (kick and snare into a bus that keys Limiter sidechain gates on the music), KS, Music, VOX; the master gets a WaveShaper and a limiter; reverb and delay wet, a band-pass and a master filter are automated.

**Automation.** Reverb and delay wet, band-pass, master filter.

**Transitions.** Filter moves on the master.

**What the rework changes and keeps.**

- keep the harmony, the drums and the signature instruments
- change the bass's rhythm and add a register (an 808 two octaves down)
- replace one melodic part with a new instrument (an octave pluck) instead of adding on top
- add a sidechain bus that keys the music from kick and snare
- put the space under control: reverb and delay wet automated per section

## How it sounds (measured on the full render)

| LUFS | True peak dB | LRA LU | Crest dB | Width (side/mid dB) | Width under 120 Hz | Centroid Hz | Pump dB (loudest section) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -13.79 | 0.01 | 8.93 | 13.84 | -13.21 | -34.94 | 169.9 | 2.42 |

Band balance (dB of the total): sub -2.13, bass -7.05, low_mid -9.8, mid -11.1, high_mid -23.4, presence -29.57, air -34.01.

| Section | Bar | Bars | LUFS | Centroid | Width | Sub dB | Air dB |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 1 | 8 | -19.5 | 388.3 | -7.4 | -10.48 | -50.85 |
|  | 9 | 8 | -13.06 | 138.1 | -13.22 | -1.92 | -34.42 |
|  | 17 | 4 | -13.64 | 111.8 | -15.48 | -1.68 | -38.78 |
|  | 21 | 4 | -13.47 | 121.8 | -14.98 | -1.79 | -37.64 |
|  | 25 | 8 | -12.39 | 213.4 | -15.03 | -2.33 | -32.67 |
|  | 33 | 4 | -12.88 | 143.3 | -13.06 | -1.95 | -34.1 |
|  | 37 | 4 | -17.1 | 417.5 | -5.85 | -5.53 | -26.85 |
|  | 41 | 1 | -48.84 | 6891.8 | -0.86 | -77.66 | -8.93 |

## How its instruments sound (solo renders, soundbrief.describe)

| Part | Role | Plugin | Attack s | Decay s | Sustain | Centroid Hz | Register | Width | In words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Piano | chords | DirectWave | 0.1132 | 2.2175 | 0.0 | 499.15 | G#1 | wide | soft, slow attack; decaying (long tail); lots of upper harmonics (bright or driven) |
| Bass | bass | Sytrus | 0.107 | 0.35 | 0.0 | 102.15 | F#2 | narrow | soft, slow attack; plucked (short decay); brightness falls after the attack (filter envelope) |
| Heavy 808 | bass | Sytrus | 0.001 | 0.1925 | 0.0 | 77.9 | D#1 | mono | sharp, percussive attack; plucked (short decay); dark, few upper harmonics |
| Pluck | lead | Harmor | 0.001 | 0.035 | 0.33 | 732.7 | A#4 | mono | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 33 % before the cut; dark, few upper harmonics |
| Guitar | chords | DirectWave | 0.001 | 0.5725 | 0.0 | 431.75 | A#4 | medium | sharp, percussive attack; decaying (long tail); dark, few upper harmonics |
| Strings | pad | sampler | 0.1439 | 1.1085 | 0.0 | 1003.1 | A#5 | wide | soft, slow attack; decaying (long tail); dark, few upper harmonics |
| Kick | kick | sampler | 0.0257 | 0.06 | 0.699 | 34.85 |  | mono | quick attack; notes cut off by their length (staccato or gated), held at 70 % before the cut; chords or several notes at once |

## The data

**Sections** (from the markers, or 8-bar phrases merged by what plays):

| # | Bar | Bars | Name | Energy | Plays |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 8 |  | 0.2 | audio, chords, drums |
| 2 | 9 | 8 |  | 0.73 | audio, bass, chords, drums |
| 3 | 17 | 4 |  | 0.77 | audio, bass, chords, drums, pad |
| 4 | 21 | 4 |  | 0.73 | audio, bass, chords, drums |
| 5 | 25 | 8 |  | 1.0 | audio, bass, chords, drums, lead, pad |
| 6 | 33 | 4 |  | 0.73 | audio, bass, chords, drums, pad |
| 7 | 37 | 4 |  | 0.37 | audio, bass, chords, drums |
| 8 | 41 | 1 |  | 0.0 | audio |

**Harmony** (a chord per bar from every pitched part): Bbm7 (i7) x1, C#maj7 (bIIImaj7) x1, F#maj7 (bVImaj7) x1, Ebadd9 (IVadd9) x1, Bbm7 (i7) x1, Ab6 (bVII6) x1, Ebadd9 (IVadd9) x1, F#add9 (bVIadd9) x1, Bbm7 (i7) x1, C#maj7 (bIIImaj7) x1, Ebmadd9 (ivadd9) x1, Ebadd9 (IVadd9) x1, Bbm7 (i7) x1, Ab6 (bVII6) x1, Ebadd9 (IVadd9) x1, C#sus4 (bIIIsus4) x1, Bbm (i) x1, C#6 (bIII6) x1, Ebmadd9 (ivadd9) x1, Ebsus4 (IVsus4) x1, Bbm (i) x1, Bbmadd9 (iadd9) x1, Ebsus2 (IVsus2) x1, F#maj7 (bVImaj7) x1

**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):

| Voice | Channel | Pattern | Hits a bar | Late | Velocity | Bars |
| --- | --- | --- | --- | --- | --- | --- |
| hat | Hat | `..X..xX...X..xxX` | 5.54 | -0.006 | [100, 100] | 28 |
| kick | Kick | `X......X..X....x` | 3.64 | 0.0 | [64, 104] | 39 |
| shaker | Shaker | `XXXXXXXXXXXXXXXX` | 15.86 | 0.0 | [26, 100] | 28 |
| snare | Snare | `....X......ox.x.` | 2.42 | 0.0 | [100, 100] | 38 |

**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):

| Role | Name | Plugin or sample | Preset | Insert chain | Range | Poly | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chords | Piano | DirectWave |  |  | F2-D5 | 2.05 | 219 |
| bass | Bass | Sytrus |  |  | E2-G3 | 1.0 | 164 |
| bass | Heavy 808 | Sytrus |  |  | D1-Bb1 | 1.0 | 164 |
| lead | Pluck | Harmor |  |  | C4-A5 | 2.0 | 128 |
| chords | Guitar | DirectWave |  |  | C4-G5 | 1.06 | 76 |
| pad | Strings | MIXO_C5(L)ogg.wav |  |  | A4-A5 | 1.0 | 22 |
| fx | SFX Wind Chimes Reverse | FX_WindChimes.wav |  |  | C3-C4 | 2.0 | 10 |
| fx | Foley Noise | Sytrus |  |  | C4-C4 | 1.0 | 5 |
| fx | Foley Nature | FLS_Nature 001.wav |  |  | Eb3-Eb3 | 1.0 | 5 |
| fx | SFX Wind Chimes | FX_WindChimes.wav |  |  | C3-C3 | 1.0 | 3 |
| audio | Maja Harmonies Merged | Maja Harmonies Merged.ogg |  |  |  | 0.0 | 0 |
| audio | Maja Lead 1 | Maja Lead 1.ogg |  |  |  | 0.0 | 0 |
| audio | Maja Lead 2 | Maja Lead 2.ogg |  |  |  | 0.0 | 0 |

**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):

chords, Piano (DirectWave), from bar 1:

```
D3+C4+D4 F4+A4 -   -   -   -   -   -   -   -   -   -   -   -   C5  -  
F3+A3+F2+C4 E4  -   -   -   -   -   -   -   -   -   -   .   .   D4  .  
```

bass, Bass (Sytrus), from bar 9:

```
D3  -   -   -   D3  -   -   D3  -   -   D3  -   D3  -   -   -  
F2  -   -   -   F2  -   -   F2  -   -   -   F2  -   -   F2  -  
```

bass, Heavy 808 (Sytrus), from bar 9:

```
D1  -   -   -   D1  -   -   D1  -   -   D1  -   D1  -   -   -  
F1  -   -   -   F1  -   -   F1  -   -   -   F1  -   -   F1  -  
```

lead, Pluck (Harmor), from bar 25:

```
D4+D5 .   D4+D5 D4+D5 .   D4+D5 .   D4+D5 .   D4+D5 .   .   D4+D5 .   D4+D5 .  
C4+C5 .   C4+C5 C4+C5 .   C4+C5 .   C4+C5 .   C4+C5 .   .   C4+C5 .   C4+C5 .  
```

chords, Guitar (DirectWave), from bar 17:

```
D5  .   D4  E5  .   .   F5+G5 D4  .   .   F5  F4  .   E5  D4  .  
D5+E5 D5  C4  A4  .   .   D5  C4  .   .   .   C4  .   D4  A4  .  
```

pad, Strings (MIXO_C5(L)ogg.wav), from bar 17:

```
D5  -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
-   -   -   -   -   -   -   -   C5  -   -   -   -   -   -   -  
```

**Mixer buses and the master:**

- 0 Master: Fruity Compressor > Fruity Parametric EQ 2 > Fruity Love Philter > Fruity WaveShaper > Fruity Limiter
- 1 SC (fed by [9, 10]): Fruity Parametric EQ 2 > Fruity Limiter (Transients) > Fruity Limiter (Hard Noise Gate)
- 2 KS Bus (fed by [9, 10]): Fruity Parametric EQ 2 > Fruity Limiter > Fruity Love Philter
- 3 Music Bus (fed by [4, 5, 6, 8, 14, 15, 16, 17]): Fruity Limiter > Fruity Parametric EQ 2
- 4 Piano (fed by [1]): Fruity Parametric EQ 2 > Fruity Delay 3 > Fruity Delay 3 > Fruity Reeverb 2 > Fruity Limiter
- 5 Guitar (fed by [1]): Fruity Delay 3 > Fruity Parametric EQ 2 > Fruity Delay 3 > Hyper Chorus > Fruity Reeverb 2 > Fruity Limiter > Fruity Parametric EQ 2
- 6 Pluck (fed by [1]): Fruity Parametric EQ 2 > Fruity Delay 3 > Fruity Reeverb 2 > Fruity Limiter
- 7 Bass (fed by [1]): Fruity Parametric EQ 2 > Fruity Blood Overdrive > Hyper Chorus > Fruity Parametric EQ 2 > Fruity Compressor > Fruity Limiter > Fruity Parametric EQ 2
- 8 Strings (fed by [1, 9]): Hyper Chorus > Fruity Parametric EQ 2 > Fruity Limiter (SC)
- 11 HF Perc (fed by [12, 13]): Fruity Parametric EQ 2
- 13 Shaker (fed by [10]): Fruity Limiter
- 14 SFX Chimes (fed by [1]): Fruity Delay 3 > Fruity Parametric EQ 2 (Fruity parametric EQ 2) > Fruity Limiter
- 15 Foley Noise (fed by [1]): Fruity Limiter
- 16 Foley Nature (fed by [1]): Fruity Parametric EQ 2 > Fruity Limiter
- 17 Heavy 808 (fed by [1]): Fruity Limiter > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Compressor > Fruity Limiter
- 18 VOX Bus (fed by [19, 20]): Fruity Parametric EQ 2

**Automation:** 5 clips, by target: generator 5.

**Kit** (the most played sample of each voice): kick HIP_Kick_2.wav; snare Snare_2.wav; hat Hat_2.wav; shaker Shaker_2.wav.

## What it adds to the option bank

- `bass.rework_808_syncopated` (Rework: held bass turned into a syncopated 808 two octaves down)
- `mix.limiter_gate_bus` (Sidechain bus: kick and snare gate a limiter on the music)
- `sound.heavy_808_sytrus` (Sytrus heavy 808)
- `sound.harmor_octave_pluck` (Harmor octave pluck)

