# Astes - Bien Duro (Clean Version)

FL Studio 2026 demo project `Astes - Bien Duro.flp`, studied on a sandbox copy (the original is untouched). Genre as the project names it: Reggaeton.

| Tempo | Key (from the notes) | Key (from the render) | Bars | Length | Saved in FL | PPQ |
| --- | --- | --- | --- | --- | --- | --- |
| 95.0 | F minor | F major | 94 | 3:57 | 25.1.0.4858 | 96 |

The render's audio reads F major (a chroma vote over the first two minutes, margin 0.0487; it often lands a fifth away on bass-heavy mixes): not settled without listening.

A reggaeton production organized like a textbook: its own notebook explains the layout (vocals, radio ad-libs, drums, instruments, bass, SFX, a sidechain ghost), and every section gets a different drum kit on the same dembow.

## What it does and how

**Form.** Verse and chorus sections at 95 bpm with an intro; energy is made by swapping kits and adding instrument layers, not by builds.

**Rhythm and drums.** The dembow: kick on 1 and 3 (X.......X.......), the snare's 3-3-2 answer (...X..X...xX..X.), a rim between (o.xx..x.o.xx..x.), timbal runs (x..X.XXxxxXXX.X.) at phrase ends. Kits per section: Oldschool, Darker, Hard, Metal (with Ogun hits), Tibetan, Chase, Pokepop, an epic orchestral tom.

**Bass.** BooBass (FL's modelled bass guitar) playing the dembow bounce: root, held root, octave, root, a gap, root again (F3 . F3 - F4 - F3 - . . F3 . F3 - - -), pumped by Gross Beat.

**Harmony.** F minor: i, bIII, IV with the colours changing by section (sus4 and add9 in the intro, sixths in the verse, plain triads in the chorus).

**Sounds and synths.** Glass pluck (Harmor, release, decay and unison automated), Saw pluck (Harmless), Wasp (Harmor high arp through Blood Overdrive and Flangus), Formanter (Sytrus), Resonator (Sytrus, Mod X and Y automated), a FLEX pad (Olbaid Compendium), ear-candy layers.

**Vocal production.** One lead into seven inserts: Main, Duo, Trio, Low, Separated, High, Far, with Pitcher harmonies, a Pitch Shifter formant and delay sends; Radio ad-libs filtered and panned by automation on their own delay.

**Mix and sidechain.** Sidechain from a silent Sytrus trigger (the notebook: just the pulse behind the pump), so the pump runs on its own grid; send buses for vocal delays, radio delay, instrument delays and reverbs.

**Automation.** 46 clips: pluck envelopes, Sytrus mod X and Y, the sidechain mix, vocal gains and reverbs.

**Transitions.** Reverse SFX and impacts (Cymc, Noiz) at section starts; filler toms from 909 and RD kits.

## How it sounds (measured on the full render)

| LUFS | True peak dB | LRA LU | Crest dB | Width (side/mid dB) | Width under 120 Hz | Centroid Hz | Pump dB (loudest section) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -8.64 | -1.44 | 2.58 | 9.48 | -10.5 | -27.89 | 815.3 | 4.86 |

Band balance (dB of the total): sub -6.97, bass -5.44, low_mid -6.27, mid -7.37, high_mid -13.75, presence -13.89, air -19.98.

| Section | Bar | Bars | LUFS | Centroid | Width | Sub dB | Air dB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Start | 1 | 1 | -99.0 | 898.2 | -2.91 | -25.75 | -24.58 |
| Intro | 2 | 8 | -8.41 | 483.0 | -10.74 | -6.53 | -25.24 |
| Verse | 10 | 8 | -8.61 | 858.6 | -12.06 | -5.94 | -19.67 |
| Build | 18 | 8 | -7.9 | 863.0 | -11.11 | -8.67 | -19.67 |
| Chorus | 26 | 8 | -8.31 | 943.8 | -9.53 | -8.35 | -19.35 |
| Rap | 34 | 8 | -8.99 | 812.6 | -10.59 | -6.63 | -19.29 |
| Verse | 42 | 8 | -7.95 | 936.3 | -10.4 | -6.87 | -19.34 |
| Chorus | 50 | 8 | -8.47 | 952.9 | -9.51 | -8.29 | -19.11 |
| Interlude | 58 | 8 | -9.44 | 632.7 | -10.38 | -6.03 | -21.12 |
| Verse | 66 | 8 | -9.31 | 636.9 | -12.63 | -5.72 | -21.07 |
| :O | 74 | 1 | -99.0 | 954.1 | -8.42 | -9.14 | -20.57 |
| Chorus | 75 | 8 | -8.04 | 1151.4 | -9.25 | -8.58 | -17.55 |
| Outro | 83 | 12 | -10.64 | 732.6 | -10.45 | -6.34 | -21.46 |

## How its instruments sound (solo renders, soundbrief.describe)

| Part | Role | Plugin | Attack s | Decay s | Sustain | Centroid Hz | Register | Width | In words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4.5.1 Wasp | arp | Harmor | 0.0468 | 0.065 | 0.5745 | 835.0 | E4 | wide | quick attack; notes cut off by their length (staccato or gated), held at 57 % before the cut; dark, few upper harmonics |
| 5.1 Bass | bass | BooBass | 0.0057 | 0.035 | 0.69 | 56.55 | F1 | narrow | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 69 % before the cut; chords or several notes at once |
| 4.6 Lead | lead | Harmor | 0.0282 | 0.035 | 0.495 | 1208.35 | G#4 | wide | quick attack; notes cut off by their length (staccato or gated), held at 50 % before the cut; chords or several notes at once |
| 4.9 Pad | pad | FLEX | 0.5668 | 20.15 | 0.0 | 335.0 |  | wide | soft, slow attack; decaying (long tail); chords or several notes at once |
| 4.5.2 Wasp high | arp | Harmor | 0.0528 | 0.0225 | 0.0 | 1634.2 | F#6 | wide | quick attack; plucked (short decay); dark, few upper harmonics |
| 3.3.2 Tibetan | arp | Ogun | 0.001 | 0.04 | 0.3245 | 4815.3 | E1 | medium | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 32 % before the cut; lots of upper harmonics (bright or driven) |
| 3.8.1 Oldschool Kick: Kick | kick | sampler | 0.0424 | 0.04 | 0.4265 | 71.85 | E1 | mono | quick attack; notes cut off by their length (staccato or gated), held at 43 % before the cut; brightness falls after the attack (filter envelope) |

## The data

**Sections** (from the markers, or 8-bar phrases merged by what plays):

| # | Bar | Bars | Name | Energy | Plays |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | Start | 0.0 | audio, drums, fx, vocal |
| 2 | 2 | 8 | Intro | 0.91 | arp, audio, bass, drums, lead, other, pad, vocal |
| 3 | 10 | 8 | Verse | 0.65 | arp, audio, bass, drums, lead, other, vocal |
| 4 | 18 | 8 | Build | 1.0 | arp, audio, bass, drums, lead, other, vocal |
| 5 | 26 | 8 | Chorus | 0.96 | arp, audio, bass, drums, lead, other, pad, vocal |
| 6 | 34 | 8 | Rap | 0.63 | arp, audio, bass, drums, lead, other, vocal |
| 7 | 42 | 8 | Verse | 0.86 | arp, audio, bass, drums, lead, other, pad, vocal |
| 8 | 50 | 8 | Chorus | 0.92 | arp, audio, bass, drums, lead, other, pad, vocal |
| 9 | 58 | 8 | Interlude | 0.61 | arp, audio, bass, drums, lead, other, vocal |
| 10 | 66 | 8 | Verse | 0.36 | arp, audio, bass, drums, lead, other, vocal |
| 11 | 74 | 1 | :O | 0.17 | arp, audio, drums, fx, other |
| 12 | 75 | 8 | Chorus | 0.91 | arp, audio, bass, drums, lead, other, pad, vocal |
| 13 | 83 | 12 | Outro | 0.53 | arp, audio, bass, drums, lead, other, pad, vocal |

**Harmony** (a chord per bar from every pitched part): none x1, Fsus4 (Isus4) x2, Abadd9 (bIIIadd9) x1, Bbadd9 (IVadd9) x1, Fsus4 (Isus4) x2, Abadd9 (bIIIadd9) x1, Bbadd9 (IVadd9) x1, F5 (I5) x2, Ab6 (bIII6) x1, Bb5 (IV5) x1, F5 (I5) x2, Ab6 (bIII6) x1, Bb5 (IV5) x1, Fm (i) x1, Fm7 (i7) x1, Ab6 (bIII6) x1, Bbsus2 (IVsus2) x1, Fm (i) x1, Fm7 (i7) x1, Ab6 (bIII6) x1, Bbsus2 (IVsus2) x1, Fm (i) x2, Ab (bIII) x1, Bb (IV) x1

**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):

| Voice | Channel | Pattern | Hits a bar | Late | Velocity | Bars |
| --- | --- | --- | --- | --- | --- | --- |
| clap | 3.4.2 Clap #2 | `...........X..X.` | 2.0 | 0.0 | [75, 86] | 10 |
| clap | 3.4.1 Clap | `X...............` | 1.0 | 0.0 | [100, 100] | 8 |
| clap | 3.4.3 Clap faded | `X...............` | 1.0 | 0.0 | [100, 100] | 5 |
| crash | 6.8 Cymbals | `X...............` | 1.0 | 0.0 | [100, 100] | 13 |
| hat | 3.8.1 Oldschool Kick: Hat | `X.......X.......` | 1.96 | 0.001 | [43, 100] | 48 |
| hat | 3.7.1.1 Darker Kick: Hat | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| hat | 3.7.1.1 Darker Kick: Hat Closed | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| kick | 3.8.1 Oldschool Kick: Kick | `X.......X.......` | 1.96 | 0.001 | [43, 100] | 48 |
| kick | 3.8.1 Oldschool Kick: Shaker | `X.......X.......` | 1.96 | 0.001 | [43, 100] | 48 |
| kick | 3.8.2 Oldschool Kick #2 | `....X.......X...` | 1.94 | 0.0 | [100, 100] | 31 |
| kick | 3.9.2 Hard Kick #2 | `....X.......X...` | 2.07 | 0.0 | [100, 100] | 27 |
| kick | 3.5.1.2 Kick TNDR | `X...o...x...o...` | 2.05 | 0.017 | [74, 100] | 20 |
| kick | 3.5.1.1 Kick Nasa | `X...x...x...x...` | 2.8 | 0.013 | [128, 128] | 20 |
| kick | 3.7.1 Darker Kick: High | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| kick | 3.7.1 Darker Kick: Low | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| kick | 3.7.1 Darker Kick: Mid | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| kick | 3.7.1.1 Darker Kick: Snare | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| kick | 3.7.1.1 Darker Kick: Shake #1 | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| kick | 3.7.1.1 Darker Kick: Metal Tom | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| kick | 3.7.1.1 Darker Kick: Shake #2 | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| kick | 3.7.1.1 Darker Kick: Shake #3 | `X.......x.......` | 1.7 | 0.0 | [100, 100] | 20 |
| kick | 3.7.2 Darker Kick #2: Snare | `....X.......X...` | 1.81 | 0.0 | [100, 100] | 16 |
| kick | 3.7.2 Darker Kick #2: Kick | `....X.......X...` | 1.81 | 0.0 | [100, 100] | 16 |
| kick | 3.7.2 Darker Kick #2: Snap | `....X.......X...` | 1.81 | 0.0 | [100, 100] | 16 |

**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):

| Role | Name | Plugin or sample | Preset | Insert chain | Range | Poly | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arp | 4.5.1 Wasp | Harmor |  | Fruity Blood Overdrive > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Flangus  | C4-C5 | 1.01 | 526 |
| bass | 5.1 Bass | BooBass |  | Fruity Stereo Shaper > Fruity Parametric EQ 2 > Frequency Splitter > Patcher > Fruity Para | F2-Bb4 | 1.01 | 479 |
| lead | 4.8 Resonator (Sytrus) | Sytrus |  | Fruity NoteBook 2 > Fruity NoteBook 2 > Fruity Limiter > Fruity Parametric EQ 2 > Fruity P | F3-Bb4 | 1.12 | 304 |
| arp | 3.3.1 Metal Drums: Drum | Ogun |  | Fruity Parametric EQ 2 > Transient Processor | F#3-Bb5 | 1.11 | 304 |
| arp | 3.3.1 Metal Drums: Click | Ogun |  | Fruity Parametric EQ 2 > Transient Processor | F#3-Bb5 | 1.12 | 287 |
| arp | 3.1 Epic Tom | WADOT_Percussion_Tom_06_Shot_511315.ogg |  | Transient Processor | Eb3-C#5 | 1.05 | 250 |
| lead | 4.6 Lead | Harmor |  | Fruity Peak Controller > Fruity Parametric EQ 2 > Fruity Flangus > Fruity Flangus > Fruity | Bb3-C5 | 1.0 | 206 |
| pad | 4.9 Pad | FLEX | Olbaid Compendium / Simmering Spheres | Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Limiter | Eb1-Bb3 | 5.5 | 198 |
| arp | 7 Sidechain | Sytrus |  | Fruity Stereo Shaper | C4-C4 | 1.0 | 180 |
| arp | 4.5.2 Wasp high | Harmor |  | Fruity Blood Overdrive > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Flangus  | Eb6-Bb6 | 1.0 | 152 |
| arp | 3.3.2 Tibetan | Ogun |  | Fruity Blood Overdrive > Fruity Parametric EQ 2 > Spreader | E3-C4 | 1.0 | 123 |
| lead | 4.4 Glass pluck | Harmor |  | Transient Processor > Fruity Stereo Shaper > Fruity Parametric EQ 2 > Fruity Delay Bank >  | C3-C5 | 1.28 | 122 |
| arp | 3.3.3 Chase | Ogun |  | Transient Processor > Fruity Parametric EQ 2 | F3-C6 | 1.17 | 118 |
| lead | 4.3 Saw pluck | Harmless |  | Fruity WaveShaper > Frequency Splitter > Fruity Limiter > Fruity Balance | C#3-F5 | 1.46 | 102 |
| lead | 4.2.3 WADOT_Melody_Loop_65_130BPM_Am_Brass_Stac_511445 |  |  | Transient Processor > Spreader | C4-F#4 | 1.01 | 96 |
| arp | 4.7 Formanter | Sytrus |  | Fruity Flangus > Fruity Balance | C#3-Ab4 | 1.15 | 84 |
| lead | 4.2.3 WADOT_Melody_Loop_70_144BPM_C#m_Brass_Stac_511257 |  |  | Transient Processor > Spreader | F2-F3 | 1.0 | 35 |
| fx | 6.3 SFX Reverse: Big | FX Big Reverse.wav |  | Fruity Parametric EQ 2 |  | 0.0 | 0 |
| fx | 6.3 SFX Reverse: Noise Punch | SFX Noise Punch.wav |  | Fruity Parametric EQ 2 |  | 0.0 | 0 |
| audio | 2.1 Radio #2 | 1.1 Intro #2.ogg |  | Fruity Parametric EQ 2 > Fruity Limiter > Patcher > Fruity Fast Dist > Fruity Parametric E |  | 0.0 | 0 |
| fx | 6.4 SFX Reverse #2: Noise | Riser Noise.wv |  |  |  | 0.0 | 0 |
| vocal | 6.4 SFX Reverse #2: Vocal | Riser Vocal.wv |  |  |  | 0.0 | 0 |
| fx | 6.5 SFX Impact: Noiz | SFX Splash Noiz.wav |  |  |  | 0.0 | 0 |
| vocal | 1.3 Chorus #3 (1.1 #2) | 1.1 Chorus #2.ogg |  | Pitcher > Pitcher > Fruity Parametric EQ 2 > Fruity Stereo Shaper > Fruity Stereo Enhancer |  | 0.0 | 0 |
| vocal | 1.3 Interlude #2 | 1.3 Interlude #2.ogg |  | Pitcher > Pitcher > Fruity Parametric EQ 2 > Fruity Stereo Shaper > Fruity Stereo Enhancer |  | 0.0 | 0 |
| vocal | 1.3 Interlude #1 | 1.3 Interlude #1.ogg |  | Pitcher > Pitcher > Fruity Parametric EQ 2 > Fruity Stereo Shaper > Fruity Stereo Enhancer |  | 0.0 | 0 |
| vocal | 1.3 Chorus #2 | 1.3 Chorus #2.ogg |  | Pitcher > Pitcher > Fruity Parametric EQ 2 > Fruity Stereo Shaper > Fruity Stereo Enhancer |  | 0.0 | 0 |
| vocal | 1.2 Verse #8 | 1.2 Verse #8.ogg |  | Pitcher > Pitcher > Fruity Parametric EQ 2 > Fruity Stereo Shaper > Fruity Stereo Enhancer |  | 0.0 | 0 |
| vocal | 1.3 Build #1 | 1.3 Build #1.ogg |  | Pitcher > Pitcher > Fruity Parametric EQ 2 > Fruity Stereo Shaper > Fruity Stereo Enhancer |  | 0.0 | 0 |
| vocal | 1.3 Build #3 | 1.3 Build #3.ogg |  | Pitcher > Pitcher > Fruity Parametric EQ 2 > Fruity Stereo Shaper > Fruity Stereo Enhancer |  | 0.0 | 0 |

**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):

arp, 4.5.1 Wasp (Harmor), from bar 11:

```
C4  .   F4  .   C4  -   Ab4 .   G4  .   .   .   .   .   .   .  
C4  .   Ab4 .   G4  .   Bb4 .   .   .   .   .   Eb4 .   F4  .  
```

bass, 5.1 Bass (BooBass), from bar 6:

```
F3  .   F3  -   F4  -   F3  -   .   .   F3  .   F3  -   -   -  
F3  .   F3  -   F4  -   F3  -   .   .   F3  .   F3  -   -   -  
```

lead, 4.8 Resonator (Sytrus) (Sytrus), from bar 2:

```
F3  .   F3  -   F4  -   F3  -   .   .   .   .   .   .   .   .  
F3  .   F3  -   F4  -   F3  -   .   .   .   .   .   .   .   .  
```

arp, 3.3.1 Metal Drums: Drum (Ogun), from bar 18:

```
C4  .   .   C4  -   .   C4  .   .   B3  B3  B3  D4  -   C4  -  
C4  -   .   C4  -   .   C4  -   .   Eb4 .   C4  .   C4  C4  C4 
```

arp, 3.3.1 Metal Drums: Click (Ogun), from bar 18:

```
C4  .   .   C4  -   .   C4  .   .   B3  B3  B3  D4  -   C4  -  
C4  -   .   C4  -   .   C4  -   .   Eb4 .   C4  .   C4  C4  C4 
```

arp, 3.1 Epic Tom (WADOT_Percussion_Tom_06_Shot_511315.ogg), from bar 11:

```
F4  .   .   .   .   .   .   .   .   .   F4  .   Eb4 .   F4  -  
.   .   .   .   .   .   F4  .   .   .   F4  .   .   .   F4  -  
```

**Mixer buses and the master:**

- 0 Master: Fruity NoteBook 2 (Notebook... read me :)) > Fruity NoteBook 2 (Earcandy) > Fruity Limiter (Limiter) > Fruity Parametric EQ 2 (Parametric EQ A) > Fruity Parametric EQ 2 (Parametric EQ B) > Maximus (Maximus) > Emphasis
- 8 1.7 Far (fed by [81]): Frequency Splitter (Freq Splitter) > Pitcher > Fruity Parametric EQ 2 (Parametric EQ) > Patcher (De-esser) > Patcher (Flangus + Distructor) > Fruity Limiter (Limiter) > Fruity Delay Bank (Delay Bank) > Fruity Reeverb 2 (Reverb) > Patcher (Filter)
- 11 2.1 Radio (fed by [9, 10]): Fruity Parametric EQ 2 (Parametric EQ) > Fruity Limiter (Limiter) > Patcher (De-esser) > Fruity Fast Dist (Fast Dist) > Fruity Parametric EQ 2 (Parametric EQ) > Fruity Balance (Balance)
- 17 3.3 Metal (fed by [14, 15, 16, 81]): Frequency Shifter (Freq Splitter) > Fruity Limiter (Limiter) > Maximus > Fruity Parametric EQ 2 (Parametric EQ) > Fruity Parametric EQ 2 (Parametric EQ B) > Patcher (Low Sidechain) > Fruity Balance (Balance)
- 24 3.5 Pokepop (fed by [19, 20, 21, 22, 23]): Fruity Balance (Balance)
- 26 3.7.1 Darker Kick (fed by [27]): Fruity Parametric EQ 2 (Parametric EQ) > Fruity Limiter > Transient Processor
- 31 3.7 Darker (fed by [26, 28, 29, 30]): Fruity Parametric EQ 2 (Parametric EQ)
- 36 3.8.5 Oldschool Timbals (fed by [37]): Fruity Stereo Shaper (Stereo Shaper) > Spreader
- 39 3.8 Oldschool (fed by [32, 33, 34, 35, 36, 38]): Patcher (Filter)
- 43 3.9 Hard (fed by [40, 41, 42]): no effects
- 44 4.1 Choir (fed by [81]): Fruity Parametric EQ 2 (Parametric EQ) > Fruity Flangus (Flangus) > Maximus > Gross Beat (Gross Beat) > Fruity Limiter (Limiter) > Fruity Balance (Balance) > Fruity Convolver (Fruity Convolver)
- 45 4.2 Orchestra (fed by [46, 47, 48, 81]): Fruity Parametric EQ 2 (Parametric EQ) > Spreader (Spreader) > Fruity Limiter (Limiter) > LuxeVerb > Fruity Limiter (Limiter) > Fruity Balance (Balance)
- 49 4.4 Glass pluck (fed by [81]): Transient Processor > Fruity Stereo Shaper (Stereo Shaper) > Fruity Parametric EQ 2 (Parametric EQ) > Fruity Delay Bank (Delay Bank) > Fruity Limiter (Limiter)
- 50 4.3 Saw pluck (fed by [81]): Fruity WaveShaper (Fruity WaveShaper) > Frequency Splitter (Freq Splitter) > Fruity Limiter (Limiter) > Fruity Balance (Balance)
- 51 4.5 Wasp (fed by [81]): Fruity Blood Overdrive (Blood Overdrive) > Fruity Parametric EQ 2 (Parametric EQ) > Fruity Parametric EQ 2 (Parametric EQ) > Fruity Flangus (Flangus) > Fruity Parametric EQ 2 (Parametric EQ)
- 52 4.6 Lead (fed by [81]): Fruity Peak Controller (Peak Controller) > Fruity Parametric EQ 2 (Parametric EQ) > Fruity Flangus (Flangus old) > Fruity Flangus (Flangus New) > Fruity Stereo Enhancer (Stereo Enhancer)

**Automation:** 46 clips, by target: Fruity Balance 11, mixer 9, mixer plugin 5, channel 4, Fruity Parametric EQ 2 4, Harmor 3, Sytrus 2, Fruity NoteBook 2 2.

**Kit** (the most played sample of each voice): perc Attack Timbale 03.wv; crash SFX Cym Noisy.wav; snare WAMR_Kick_11_538574.ogg; tom 909 Tom.wav; kick WAER_Kick_06_Gas_Pedal_540891.ogg; rim WAER_Snare_01_Thinner_540958.ogg; shaker shake3.wav; clap 909 Clap.wav; hat PL_Travesura_Kit_1_90bpm_Kick_2119475.ogg.

## What it adds to the option bank

- `drums.dembow` (Reggaeton dembow, a new kit each section)
- `bass.reggaeton_bounce` (Reggaeton bounce bass with the octave)
- `harmony.reggaeton_i_bIII_IV` (i, bIII, IV (with sus and add9 colours))
- `vocal.reggaeton_stack` (Reggaeton stack: Main, Duo, Trio, Low, High, Far)
- `mix.ghost_trigger_pulse` (Ghost-trigger pump: the pulse without a kick)
- `fx.radio_vocal_drop` (Radio filter on the vocal before the chorus)
- `automation.pluck_decay_ride` (Pluck decay and release ridden longer through the drop)
- `sound.boobass_bounce` (BooBass bounce bass)
- `sound.wasp_harmor_arp` (Wasp arp (Harmor through Blood Overdrive and Flangus))
- `sound.resonator_sytrus` (Resonator (Sytrus) with Mod X/Y moves)
- `kit.bien_duro` (Bien Duro kit (Reggaeton))

