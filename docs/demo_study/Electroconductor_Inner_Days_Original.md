# Electroconductor (aka nucleon) - Inner Days

FL Studio 2026 demo project `Electroconductor - Inner Days - Original.flp`, studied on a sandbox copy (the original is untouched). Genre as the project names it: Lo-Fi.

| Tempo | Key (from the notes) | Key (from the render) | Bars | Length | Saved in FL | PPQ |
| --- | --- | --- | --- | --- | --- | --- |
| 75.0 | Bb minor | A# minor | 41 | 2:11 | 21.2.99.4033 | 96 |

The notes are written in D minor, but the project's master pitch is -400 cents, so it sounds (and renders) in Bb minor.

Lo-fi at 75 bpm: a jazzy minor loop of sevenths on piano and guitar, a swung boom bap, a held bass, instruments entering and leaving.

## What it does and how

**Form.** No builds or drops: parts enter and leave every 4 to 8 bars.

**Rhythm and drums.** HIP kit: kick on 1, the 'a' of 2 and 3 (X......X..X....x), snare on 2 with late ghosts (....X......ox.x.), a swung hat with small doubles (..X..xX...X..xxX), a shaker on every 16th.

**Bass.** Sytrus bass held a bar per chord.

**Harmony.** D minor: i7, bIII maj7, bVI maj7, IV7 (the Dorian IV as a dominant seventh), every chord a seventh or ninth.

**Sounds and synths.** DirectWave piano (wide voicings D3+C4+D4 under F4+A4) and guitar (a melodic 16th riff), strings.

**Vocal production.** None in the original.

**Mix and sidechain.** Simple: the sound is the samples and the swing.

**Automation.** One clip.

**Transitions.** Entries and exits.

## How it sounds (measured on the full render)

| LUFS | True peak dB | LRA LU | Crest dB | Width (side/mid dB) | Width under 120 Hz | Centroid Hz | Pump dB (loudest section) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -11.58 | -0.04 | 5.37 | 12.76 | -10.28 | -26.12 | 231.9 | 4.9 |

Band balance (dB of the total): sub -4.29, bass -5.55, low_mid -7.25, mid -8.17, high_mid -22.27, presence -32.24, air -48.78.

| Section | Bar | Bars | LUFS | Centroid | Width | Sub dB | Air dB |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 1 | 8 | -14.32 | 234.9 | -8.31 | -3.79 | -69.17 |
|  | 9 | 8 | -12.08 | 179.9 | -11.07 | -3.58 | -50.15 |
|  | 17 | 4 | -11.12 | 235.2 | -12.0 | -4.37 | -50.66 |
|  | 21 | 4 | -10.61 | 235.7 | -11.54 | -4.48 | -51.13 |
|  | 25 | 8 | -9.94 | 275.0 | -9.61 | -5.23 | -45.66 |
|  | 33 | 4 | -12.44 | 182.5 | -11.1 | -3.35 | -49.7 |
|  | 37 | 4 | -16.24 | 315.8 | -7.93 | -5.77 | -52.83 |
|  | 41 | 1 | -58.43 | 6298.8 | -4.62 | -81.89 | -24.31 |

## How its instruments sound (solo renders, soundbrief.describe)

| Part | Role | Plugin | Attack s | Decay s | Sustain | Centroid Hz | Register | Width | In words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Piano | chords | DirectWave | 0.1037 | 2.1575 | 0.0 | 494.3 | C2 | wide | soft, slow attack; decaying (long tail); chords or several notes at once |
| Guitar | chords | DirectWave | 0.0051 | 0.786 | 0.0 | 466.7 | C5 | medium | sharp, percussive attack; decaying (long tail); dark, few upper harmonics |
| Bass | bass | Sytrus | 0.001 | 0.27 | 0.747 | 72.1 | A#1 | mono | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 75 % before the cut; dark, few upper harmonics |
| Strings | pad | sampler | 2.542 | 11.635 | 0.0 | 2653.0 | A#5 | wide | soft, slow attack; decaying (long tail); dark, few upper harmonics |
| Kick | kick | sampler | 0.001 | 0.115 | 0.386 | 43.45 | F1 | mono | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 39 % before the cut; brightness falls after the attack (filter envelope) |

## The data

**Sections** (from the markers, or 8-bar phrases merged by what plays):

| # | Bar | Bars | Name | Energy | Plays |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 8 |  | 0.23 | audio, chords, drums |
| 2 | 9 | 8 |  | 0.67 | audio, bass, chords, drums |
| 3 | 17 | 4 |  | 0.71 | audio, bass, chords, drums, pad |
| 4 | 21 | 4 |  | 0.69 | audio, bass, chords, drums |
| 5 | 25 | 8 |  | 1.0 | audio, bass, chords, drums, pad, vocal |
| 6 | 33 | 4 |  | 0.68 | audio, bass, chords, drums, pad |
| 7 | 37 | 4 |  | 0.25 | audio, bass, chords, drums |
| 8 | 41 | 1 |  | 0.0 | audio |

**Harmony** (a chord per bar from every pitched part): Bbm7 (i7) x1, C#maj7 (bIIImaj7) x1, F#maj7 (bVImaj7) x1, Eb7 (IV7) x1, Bbm7 (i7) x1, Ab6 (bVII6) x1, Eb7 (IV7) x1, F#maj7 (bVImaj7) x1, Bbm7 (i7) x1, C#maj7 (bIIImaj7) x1, Ebm7 (iv7) x1, Eb7 (IV7) x1, Bbm7 (i7) x1, Fm7 (v7) x1, Eb7 (IV7) x1, F#maj7 (bVImaj7) x1, Bbm (i) x1, C#6 (bIII6) x1, Ebmadd9 (ivadd9) x1, C#add9 (bIIIadd9) x1, Bbm (i) x1, Bbmadd9 (iadd9) x1, Ebsus2 (IVsus2) x1, F#maj7 (bVImaj7) x1

**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):

| Voice | Channel | Pattern | Hits a bar | Late | Velocity | Bars |
| --- | --- | --- | --- | --- | --- | --- |
| hat | Hat | `..X..xX...X..xxX` | 5.54 | -0.006 | [100, 100] | 28 |
| kick | Kick | `X......X..X....x` | 3.6 | 0.0 | [64, 104] | 40 |
| shaker | Shaker | `XXXXXXXXXXXXXXXX` | 15.86 | 0.0 | [26, 100] | 28 |
| snare | Snare | `....X......ox.x.` | 2.42 | 0.0 | [100, 100] | 38 |

**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):

| Role | Name | Plugin or sample | Preset | Insert chain | Range | Poly | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chords | Piano | DirectWave |  |  | F2-D5 | 1.9 | 219 |
| chords | Guitar | DirectWave |  |  | C4-A5 | 1.0 | 146 |
| vocal | Vocal | Harmor |  |  | C4-A4 | 1.0 | 64 |
| bass | Bass | Sytrus |  |  | F2-G3 | 1.0 | 44 |
| pad | Strings | MIXO_C5(L)ogg.wav |  |  | A4-A5 | 1.0 | 22 |
| fx | SFX Wind Chimes Reverse | FX_WindChimes.wav |  |  | C3-C4 | 2.0 | 10 |
| fx | Foley Noise | Sytrus |  |  | C4-C4 | 1.0 | 5 |
| fx | Foley Nature | FLS_Nature 001.wav |  |  | Eb3-Eb3 | 1.0 | 5 |
| fx | SFX Wind Chimes | FX_WindChimes.wav |  |  | C3-C3 | 1.0 | 3 |

**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):

chords, Piano (DirectWave), from bar 1:

```
D3+C4+D4 F4+A4 -   -   -   -   -   -   -   -   -   -   -   -   C5  -  
F3+A3+F2+C4 E4  -   -   -   -   -   -   -   -   -   -   .   .   D4  .  
```

chords, Guitar (DirectWave), from bar 17:

```
D5  .   D4  E5  .   .   F5  D4  .   .   F5  F4  .   E5  D4  .  
D5  .   C4  A4  .   .   D5  C4  .   .   .   C4  .   D4  A4  .  
```

vocal, Vocal (Harmor), from bar 25:

```
D4  .   D4  D4  .   D4  .   D4  .   D4  .   .   D4  .   D4  .  
C4  .   C4  C4  .   C4  .   C4  .   C4  .   .   C4  .   C4  .  
```

bass, Bass (Sytrus), from bar 9:

```
D3  -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
F2  -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
```

pad, Strings (MIXO_C5(L)ogg.wav), from bar 17:

```
D5  -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
-   -   -   -   -   -   -   -   C5  -   -   -   -   -   -   -  
```

**Mixer buses and the master:**

- 0 Master: Fruity Compressor > Fruity Parametric EQ 2 > Fruity Love Philter > Fruity Soft Clipper
- 4 Bass (fed by [6]): Fruity Limiter > Hyper Chorus

**Automation:** 1 clips, by target: generator 1.

**Kit** (the most played sample of each voice): kick HIP_Kick_2.wav; snare HIP_Snare_6.wav; hat HIP_Hat_3.wav; shaker RD_Shaker.wav.

## What it adds to the option bank

- `drums.lofi_boom_bap` (Lo-fi boom bap: swung hats, ghost snares, shaker 16ths)
- `harmony.lofi_i7_bIIImaj7_bVImaj7_IV7` (i7, bIII maj7, bVI maj7, IV7 (jazzy minor))
- `chords.lofi_rhodes` (Lo-fi Rhodes: one voicing per bar, struck and let ring)
- `form.lofi_loop` (Lo-fi loop with entries and exits)
- `kit.inner_days` (Inner Days kit (Lo-Fi))

