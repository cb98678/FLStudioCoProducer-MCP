# P.Priime - Use Me

FL Studio 2026 demo project `P.Priime - Use Me.flp`, studied on a sandbox copy (the original is untouched). Genre as the project names it: Afrobeats.

| Tempo | Key (from the notes) | Key (from the render) | Bars | Length | Saved in FL | PPQ |
| --- | --- | --- | --- | --- | --- | --- |
| 100.0 | C# minor | C# minor | 74 | 2:57 | 25.2.5.5319 | 96 |

Afrobeats at 100 bpm, minimal: two kicks (a four on the floor and a tresillo), two percussion hits, a sus-cell arp through overdrive, the vocal.

## What it does and how

**Form.** Intro, verse, hook, verse, hook, a 'try me' section, bridge, outro (marker names).

**Rhythm and drums.** Priime kick four on the floor, gbe kick on the 3-3-2 tresillo (X..X..X.X..X..X.), percussion on the last 16th of beats 1 and 3, a tight snare.

**Bass.** A one-shot bass sample, a 16th Sytrus synth bass through Effector, a Peak Controller on the sub.

**Harmony.** C# minor, mostly the sus-cell arp's notes (1, 2, 4, 5): the third is never stated.

**Sounds and synths.** Synth Arp (Sytrus through Blood Overdrive, Reeverb 2, Love Philter, Effector): C#5 Eb5 F#5 Ab5 C#5 Eb5 Eb5 C#5, its reverb dry and wet automated.

**Vocal production.** Acapella and vox channels, no chops.

**Mix and sidechain.** Master only Emphasis; a percussion bus.

**Automation.** The arp's plate reverb mix and Reeverb 2 dry and wet, the percussion bus mix.

**Transitions.** Arrangement only.

## How it sounds (measured on the full render)

| LUFS | True peak dB | LRA LU | Crest dB | Width (side/mid dB) | Width under 120 Hz | Centroid Hz | Pump dB (loudest section) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -10.37 | 0.74 | 5.6 | 11.46 | -12.62 | -13.47 | 312.6 | 7.91 |

Band balance (dB of the total): sub -5.12, bass -4.97, low_mid -5.47, mid -12.34, high_mid -16.63, presence -21.98, air -27.68.

| Section | Bar | Bars | LUFS | Centroid | Width | Sub dB | Air dB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| intro | 1 | 8 | -14.98 | 520.0 | -10.0 | -49.82 | -31.55 |
| verse | 9 | 8 | -9.34 | 413.2 | -11.25 | -22.73 | -31.32 |
| hook | 17 | 8 | -9.57 | 279.6 | -11.25 | -4.44 | -26.89 |
| verse | 25 | 16 | -9.64 | 329.7 | -13.07 | -4.6 | -26.44 |
| hook | 41 | 8 | -10.57 | 328.8 | -10.01 | -24.78 | -32.1 |
| try me | 49 | 8 | -9.67 | 191.5 | -16.63 | -2.76 | -28.52 |
| bridge | 57 | 8 | -9.74 | 311.7 | -16.26 | -3.34 | -26.15 |
| bridge | 65 | 8 | -13.76 | 349.7 | -9.79 | -49.95 | -35.22 |
| outro | 73 | 2 | -53.86 | 393.0 | -3.2 | -50.56 | -46.21 |

## How its instruments sound (solo renders, soundbrief.describe)

| Part | Role | Plugin | Attack s | Decay s | Sustain | Centroid Hz | Register | Width | In words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Synth Arp | chords | Sytrus | 0.001 | 0.0275 | 0.937 | 1242.35 | C#5 | wide | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 94 % before the cut; chords or several notes at once |
| Synth Bass | bass | Sytrus | 0.2534 | 0.015 | 0.675 | 86.25 |  | mono | soft, slow attack; notes cut off by their length (staccato or gated), held at 68 % before the cut; chords or several notes at once |
| USE ME Bass One Shot | bass | sampler | 0.0104 | 1.31 | 0.0 | 54.5 | E1 | narrow | sharp, percussive attack; decaying (long tail); dark, few upper harmonics |
| gbe kick | kick | sampler | 0.005 | 0.02 | 0.0 |  |  | mono | sharp, percussive attack; plucked (short decay); chords or several notes at once |

## The data

**Sections** (from the markers, or 8-bar phrases merged by what plays):

| # | Bar | Bars | Name | Energy | Plays |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 8 | intro | 0.2 | audio, chords, vocal |
| 2 | 9 | 8 | verse | 0.29 | audio, bass, drums, vocal |
| 3 | 17 | 8 | hook | 0.29 | audio, bass, drums, vocal |
| 4 | 25 | 16 | verse | 0.28 | audio, drums, vocal |
| 5 | 41 | 8 | hook | 0.28 | audio, chords, vocal |
| 6 | 49 | 8 | try me | 1.0 | audio, bass, chords, drums, vocal |
| 7 | 57 | 8 | bridge | 0.58 | audio, bass, chords, drums, vocal |
| 8 | 65 | 8 | bridge | 0.0 | audio, vocal |
| 9 | 73 | 2 | outro | 0.0 | audio |

**Harmony** (a chord per bar from every pitched part): C#sus2 (Isus2) x4, none x2, C#sus2 (Isus2) x1, none x33, C#sus2 (Isus2) x7, none x1, Ebdim (IIdim) x1, C#dim (Idim) x1, Ebdim (IIdim) x1, C#dim (Idim) x1, Ebdim (IIdim) x1, C#dim (Idim) x1, Ebdim (IIdim) x1, C#dim (Idim) x1, none x1, Gdim (#IVdim) x1, F#m6 (iv6) x1, Gdim (#IVdim) x1, F#m6 (iv6) x1, Gdim (#IVdim) x1, C#sus2 (Isus2) x2, none x10

**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):

| Voice | Channel | Pattern | Hits a bar | Late | Velocity | Bars |
| --- | --- | --- | --- | --- | --- | --- |
| kick | Priime kick | `X...X...X...X...` | 3.83 | 0.0 | [100, 100] | 46 |
| kick | gbe kick | `X..X..X.X..X..X.` | 5.72 | 0.0 | [100, 100] | 46 |
| kick | Kick Top | `X...............` | 1.03 | 0.0 | [100, 100] | 38 |
| perc | USE ME Percussion #2 | `...X.......X....` | 1.96 | 0.0 | [100, 100] | 45 |
| perc | USE ME Percussion | `......X.......X.` | 1.95 | 0.0 | [100, 100] | 44 |
| snare | Use Me Tight Snare | `......X.XX.X.XX.` | 6.0 | 0.021 | [100, 100] | 4 |

**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):

| Role | Name | Plugin or sample | Preset | Insert chain | Range | Poly | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| chords | Synth Arp | Sytrus |  | Fruity Blood Overdrive > Fruity Parametric EQ 2 > Fruity Reeverb 2 > Fruity Love Philter > | C#5-Ab5 | 1.0 | 407 |
| bass | Synth Bass | Sytrus |  | Fruity Parametric EQ 2 > Effector | C#1-E1 | 1.0 | 120 |
| bass | USE ME Bass One Shot | USE ME Bass One Shot.wav |  | Fruity Parametric EQ 2 > Fruity Peak Controller > Spreader | G3-Bb3 | 1.0 | 20 |
| bass | t.y. - Amount Too_bass | t.y. - Amount Too_bass.wav |  |  |  | 0.0 | 0 |
| vocal | t.y. - Amount Too_vocals | t.y. - Amount Too_vocals.wav |  |  |  | 0.0 | 0 |
| vocal | USE ME ACAPELLA 2 | USE ME ACAPELLA 2.wav |  |  |  | 0.0 | 0 |
| vocal | USE ME ACAPELLA 2 #3 | USE ME ACAPELLA 2.wav |  |  |  | 0.0 | 0 |
| vocal | USE ME ACAPELLA 2 #2 | USE ME ACAPELLA 2.wav |  |  |  | 0.0 | 0 |
| vocal | USE ME ACAPELLA 2 - Part_3 | USE ME ACAPELLA 2 - Part_3.wav |  |  |  | 0.0 | 0 |
| audio | Amount Too - Amount Too | Amount Too - Amount Too.wav |  |  |  | 0.0 | 0 |
| bass | Amount Too - Bass | Amount Too - Bass.wav |  |  |  | 0.0 | 0 |
| bass | REV BASS | REV BASS.wav |  |  |  | 0.0 | 0 |
| audio | Amount Too - Delay GTR | Amount Too - Delay GTR.wav |  |  |  | 0.0 | 0 |
| audio | Amount Too - EL GTR | Amount Too - EL GTR.wav |  | Fruity Parametric EQ 2 |  | 0.0 | 0 |
| audio | Amount Too - Harms | Amount Too - Harms.wav |  | Fruity Reeverb 2 |  | 0.0 | 0 |
| audio | Amount Too - Nylon GTR | Amount Too - Nylon GTR.wav |  | Fruity Parametric EQ 2 |  | 0.0 | 0 |
| audio | Amount Too - Verbed GTR | Amount Too - Verbed GTR.wav |  |  |  | 0.0 | 0 |
| vocal | USE ME vox 25 2 | USE ME vox 25 2.wav |  |  |  | 0.0 | 0 |
| vocal | USE ME vox 25 2 #2 | USE ME vox 25 2.wav |  |  |  | 0.0 | 0 |
| audio | New Recording 234 | New Recording 234.wav |  | Pitcher > Fruity Flangus > Fruity Parametric EQ 2 > Fruity Delay 3 > Fruity Reeverb 2 |  | 0.0 | 0 |
| audio | Tamborine | USE ME FL26 Tamborine.wav |  |  |  | 0.0 | 0 |
| audio | Percussion | USE ME FL26 Percussion.wav |  |  |  | 0.0 | 0 |

**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):

chords, Synth Arp (Sytrus), from bar 1:

```
C#5 Eb5 F#5 Ab5 C#5 Eb5 Eb5 C#5 C#5 Eb5 F#5 Ab5 C#5 Eb5 Eb5 C#5
C#5 Eb5 F#5 Ab5 C#5 Eb5 Eb5 C#5 C#5 Eb5 F#5 Ab5 C#5 Eb5 Eb5 C#5
```

bass, Synth Bass (Sytrus), from bar 49:

```
Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1 Eb1
E1  E1  E1  E1  C#1 C#1 C#1 C#1 C#1 C#1 C#1 C#1 C#1 C#1 C#1 C#1
```

bass, USE ME Bass One Shot (USE ME Bass One Shot.wav), from bar 50:

```
Bb3 -   -   -   G3  -   -   -   -   -   -   -   -   -   -   -  
A3  -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
```

**Mixer buses and the master:**

- 0 Master: Emphasis
- 12 Percussion (fed by [8, 9, 11]): Fruity Parametric EQ 2 (Fruity Parametric EQ 2)

**Automation:** 6 clips, by target: mixer 3, Fruity Reeverb 2 2, ? 1.

**Kit** (the most played sample of each voice): kick gbe kick.wav; perc USE ME Percussion.wav; snare Use Me Tight Snare.wav.

## What it adds to the option bank

- `drums.afrobeats_tresillo` (Afrobeats: four kicks under a tresillo kick, percs on the 'a')
- `arp.sus_cell` (Sus-cell arp: 1 2 4 5, 1 2 2 1)
- `form.pop_verse_chorus` (Verse, lift, chorus (no riser build))
- `vocal.sparse_hook` (Sparse: the hook once in the intro, nothing between choruses)
- `sound.overdrive_sytrus_arp` (Sytrus arp through Blood Overdrive and Love Philter)
- `kit.use_me` (Use Me kit (Afrobeats))

