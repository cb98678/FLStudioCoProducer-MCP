# Mehran Abbasi - With You

FL Studio 2026 demo project `Mehran Abbasi - With You.flp`, studied on a sandbox copy (the original is untouched). Genre as the project names it: Melodic Techno.

| Tempo | Key (from the notes) | Key (from the render) | Bars | Length | Saved in FL | PPQ |
| --- | --- | --- | --- | --- | --- | --- |
| 126.0 | D minor | D minor | 104 | 3:18 | 24.2.99.4831 | 96 |

Melodic techno at 126 bpm made almost entirely from FLEX's Melodic Techno pack and Fruity DrumSynth Live, with a vocal that ducks the leads.

## What it does and how

**Form.** Start 8, Vocal P1 28, Vocal Break Down 16, Build up 8, Drop 32, Outro 12.

**Rhythm and drums.** Every drum from DrumSynth Live: kick four on the floor, closed hat on every 16th, open hat and a percussion tone on the off-beat, a ride on 8ths, a reverb clap hit at section starts.

**Bass.** BAS Lottunma (FLEX) and a Harmor sub on every 16th of D, the release and cutoff automated over 128 beats; a Patcher does multiband sidechain.

**Harmony.** D minor: sixteen bars of a bare fifth, then minor seventh and major sixth on the same root, then bVI maj7, bVII6, i, v.

**Sounds and synths.** FLEX presets PLK Navid (the 16th sequence A4 F4 D5 D5 D4 D4 C5 D5 ...), PLK Diaco, PLK Shirin, PLK Sadaf, LED Hannaneh, LED Arnika, LED Kian, KEY Eligash, PAD Minoo, SFX Crasha; a five-note Sytrus pad; 3x Osc noise and saw sweeps.

**Vocal production.** Pitch Shifter, Pitcher, Maximus and a Peak Controller on the vocal; Stereo Vocal and Vocal Widness buses; a vocal reverb gated by Gross Beat and ducked under the next line; a shimmer reverb.

**Mix and sidechain.** Master: Patcher mid and side EQ, a make-up EQ, WaveShaper hard clip, Emphasis limiter; -6.0 LUFS at 7.9 dB crest, the densest master of the set.

**Automation.** 71 clips, most of them FLEX macros (Space, Metal, Plucked, OSCEX, TuneX, FlungDL, LPF, arpeggio gate and time), a low-frequency EQ band, delay input wet.

**Transitions.** Noise and saw sweeps from 3x Osc, filter automation, SFX Crasha.

## How it sounds (measured on the full render)

| LUFS | True peak dB | LRA LU | Crest dB | Width (side/mid dB) | Width under 120 Hz | Centroid Hz | Pump dB (loudest section) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -5.98 | 0.05 | 5.0 | 7.92 | -9.36 | -33.56 | 481.1 | 5.18 |

Band balance (dB of the total): sub -8.19, bass -2.92, low_mid -7.27, mid -9.89, high_mid -16.44, presence -17.53, air -22.34.

| Section | Bar | Bars | LUFS | Centroid | Width | Sub dB | Air dB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Start | 1 | 8 | -6.1 | 169.7 | -16.39 | -7.59 | -38.89 |
| Vocal P1 | 9 | 28 | -5.62 | 463.2 | -11.44 | -8.38 | -22.45 |
| Vocal Break Down | 37 | 16 | -7.99 | 1114.3 | -5.95 | -8.66 | -18.63 |
| Build up | 53 | 8 | -10.4 | 764.1 | -4.0 | -13.72 | -21.72 |
| Drop | 61 | 32 | -4.97 | 449.3 | -8.62 | -7.95 | -22.54 |
| Outro | 93 | 12 | -6.89 | 454.8 | -9.81 | -8.29 | -21.3 |

## How its instruments sound (solo renders, soundbrief.describe)

| Part | Role | Plugin | Attack s | Decay s | Sustain | Centroid Hz | Register | Width | In words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BAS Lottunma | arp | FLEX, Harmor | 0.236 | 0.02 | 0.781 | 132.05 |  | narrow | soft, slow attack; notes cut off by their length (staccato or gated), held at 78 % before the cut; chords or several notes at once |
| PLK Navid | arp | FLEX | 0.001 | 0.107 | 0.0 | 841.8 |  | wide | sharp, percussive attack; plucked (short decay); chords or several notes at once |
| PLK Diaco | arp | FLEX | 0.001 | 0.0175 | 0.0 | 1188.0 |  | medium | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 0 % before the cut; chords or several notes at once |
| BAS Lottunma | arp | FLEX | 0.0051 | 0.981 | 0.0 | 1046.25 | E4 | wide | sharp, percussive attack; decaying (long tail); wide stereo image |
| BAS Lottunma #2 | arp | FLEX | 0.0029 | 0.523 | 0.0 | 1099.6 | D4 | wide | sharp, percussive attack; decaying (long tail); chords or several notes at once |
| PLK Sadaf | arp | FLEX | 0.001 | 0.33 | 0.0 | 1495.6 | F4 | wide | sharp, percussive attack; plucked (short decay); chords or several notes at once |
| PLK Shirin | arp | FLEX | 0.001 | 0.257 | 0.0 | 843.8 | G#3 | wide | sharp, percussive attack; plucked (short decay); chords or several notes at once |
| Synth Pad  | pad | Sytrus | 0.0289 | 3.196 | 0.0 | 830.3 |  | wide | quick attack; decaying (long tail); chords or several notes at once |
| IL Kick_MT | kick | sampler | 0.001 | 0.245 | 0.0 | 46.05 | F#1 | mono | sharp, percussive attack; plucked (short decay); brightness falls after the attack (filter envelope) |

## The data

**Sections** (from the markers, or 8-bar phrases merged by what plays):

| # | Bar | Bars | Name | Energy | Plays |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 8 | Start | 0.69 | arp, audio, bass, drums |
| 2 | 9 | 28 | Vocal P1 | 0.8 | arp, audio, bass, drums, lead, vocal |
| 3 | 37 | 16 | Vocal Break Down | 0.45 | arp, audio, lead, pad, vocal |
| 4 | 53 | 8 | Build up | 0.29 | arp, audio, lead, vocal |
| 5 | 61 | 32 | Drop | 1.0 | arp, audio, bass, drums, lead, pad, vocal |
| 6 | 93 | 12 | Outro | 0.68 | arp, audio, bass, drums, lead |

**Harmony** (a chord per bar from every pitched part): D5 (I5) x16, Dm7 (i7) x8, D6 (I6) x8, Dm (i) x5, D7 (I7) x1, Bbmaj7 (bVImaj7) x1, C6 (bVII6) x1, Dm (i) x1, Am (v) x1, Bbmaj7 (bVImaj7) x1, Am (v) x1, Bbmaj7 (bVImaj7) x1, Gm7 (iv7) x1, Am (v) x1, C6 (bVII6) x1, Bbmaj7 (bVImaj7) x1, Gm7 (iv7) x1, Am (v) x2, Bbmaj7 (bVImaj7) x8, D5 (I5) x6, Dm (i) x3, Bbadd9 (bVIadd9) x1, Bb (bVI) x6, Dm (i) x1

**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):

| Voice | Channel | Pattern | Hits a bar | Late | Velocity | Bars |
| --- | --- | --- | --- | --- | --- | --- |
| kick | IL Kick_MT | `X...X...X...X...` | 3.94 | 0.0 | [100, 100] | 72 |

**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):

| Role | Name | Plugin or sample | Preset | Insert chain | Range | Poly | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arp | BAS Lottunma | FLEX | Melodic Techno / BAS Lottunma | Fruity Parametric EQ 2 > Spreader > Fruity Parametric EQ 2 > Patcher | Bb2-D3 | 1.18 | 1352 |
| bass | Sub Bass | Harmor |  | Patcher > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 | Bb2-D3 | 1.18 | 1352 |
| arp | Closehat | Fruity DrumSynth Live |  | Fruity Stereo Shaper | F#4-F#4 | 1.0 | 698 |
| arp | PLK Navid | FLEX | Melodic Techno / PLK Navid | Fruity Love Philter > Fruity Reeverb 2 > Fruity Parametric EQ 2 > Fruity Balance | D4-D5 | 1.0 | 632 |
| arp | Snare | Fruity DrumSynth Live |  | Fruity Reeverb 2 > Fruity Parametric EQ 2 | B4-B4 | 1.0 | 424 |
| arp | PLK Diaco | FLEX | Melodic Techno / PLK Diaco | Fruity WaveShaper > Fruity Reeverb 2 > Fruity Parametric EQ 2 | D3-C5 | 1.0 | 320 |
| lead | Ride | Fruity DrumSynth Live |  |  | Bb4-Bb4 | 1.0 | 317 |
| arp | BAS Lottunma | FLEX | Melodic Techno / BAS Lottunma |  | Bb4-G6 | 1.03 | 272 |
| arp | BAS Lottunma #2 | FLEX | Melodic Techno / BAS Lottunma |  | D5-G7 | 1.03 | 272 |
| lead | Percussion | Fruity DrumSynth Live |  | Fruity Stereo Shaper > Fruity Reeverb 2 > Fruity Parametric EQ 2 | C5-C5 | 1.0 | 246 |
| arp | PLK Sadaf | FLEX | Melodic Techno / PLK Sadaf |  | Bb3-G5 | 1.03 | 228 |
| arp | PLK Shirin | FLEX | Melodic Techno / PLK Shirin | Fruity Parametric EQ 2 > Maximus | G3-C6 | 1.17 | 224 |
| lead | Openhat | Fruity DrumSynth Live |  | Fruity Stereo Shaper | F4-F4 | 1.0 | 158 |
| pad | Synth Pad  | Sytrus |  | Fruity Parametric EQ 2 > Fruity Parametric EQ 2 | D3-A4 | 4.44 | 151 |
| arp | LED Hannaneh | FLEX | Melodic Techno / LED Hannaneh | Fruity Reeverb 2 > Fruity Parametric EQ 2 | F3-Bb4 | 1.0 | 113 |
| lead | Clap | Fruity DrumSynth Live |  | Fruity Parametric EQ 2 | Eb3-Eb3 | 1.0 | 95 |
| lead | KEY Eligash | FLEX | Melodic Techno / KEY Eligash | Fruity Reeverb 2 > Fruity Parametric EQ 2 | D4-D5 | 1.0 | 63 |
| lead | BAS Uobaa | FLEX | Melodic Techno / BAS Uobaa | Fruity Parametric EQ 2 > Hyper Chorus | G3-F4 | 1.0 | 20 |
| fx | Sweep Down Saw | 3x Osc |  | Fruity Parametric EQ 2 | Bb2-Bb4 | 2.0 | 20 |
| lead | Sytrus #2 | Sytrus |  | Fruity Reeverb 2 | G2-D4 | 1.0 | 10 |
| fx | Noise FX | 3x Osc |  | Fruity Parametric EQ 2 | D2-D2 | 1.0 | 9 |
| lead | LED Arnika | FLEX | Melodic Techno / LED Arnika | Hyper Chorus > Gross Beat > Fruity Parametric EQ 2 > Fruity Reeverb 2 | F2-Bb3 | 1.33 | 8 |
| lead | Clap Hit | Fruity DrumSynth Live |  | Fruity Reeverb 2 | Eb3-Eb3 | 1.0 | 6 |
| lead | Sytrus | Sytrus |  | Hyper Chorus | Bb1-Bb4 | 2.0 | 6 |
| lead | LED Vut feda | FLEX | Melodic Techno / LED Vut feda | Spreader > Fruity Reeverb 2 > Fruity Love Philter > Fruity Parametric EQ 2 | C3-D3 | 1.0 | 4 |
| fx | SFX Crasha #2 | FLEX | Melodic Techno / SFX Crasha | Fruity Parametric EQ 2 > Maximus | D3-D3 | 1.0 | 3 |
| fx | SFX Crasha #3 | FLEX | Melodic Techno / SFX Crasha | Fruity Reeverb 2 | D2-D3 | 1.0 | 3 |
| lead | Sytrus #3 | Sytrus |  | Fruity Reeverb 2 | Bb2-Bb3 | 1.0 | 2 |
| bass | Snare Time Gate | Fruity DrumSynth Live |  | Fruity Reeverb 2 > Fruity Parametric EQ 2 | B2-B2 | 1.0 | 1 |
| lead | BAS Feddra | FLEX | Melodic Techno / BAS Feddra | Fruity Parametric EQ 2 > Spreader > Fruity PanOMatic | D4-D4 | 1.0 | 1 |

**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):

arp, BAS Lottunma (FLEX), from bar 1:

```
D3  D3  D3  D3+D3 D3  D3  D3  D3+D3 D3  D3  D3  D3+D3 D3  D3  D3  D3 
D3  D3  D3  D3+D3 D3  D3  D3  D3+D3 D3  D3  D3  D3+D3 D3  D3  D3  D3 
```

bass, Sub Bass (Harmor), from bar 1:

```
D3  D3  D3  D3+D3 D3  D3  D3  D3+D3 D3  D3  D3  D3+D3 D3  D3  D3  D3 
D3  D3  D3  D3+D3 D3  D3  D3  D3+D3 D3  D3  D3  D3+D3 D3  D3  D3  D3 
```

arp, Closehat (Fruity DrumSynth Live), from bar 25:

```
F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4
F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4 F#4
```

arp, PLK Navid (FLEX), from bar 1:

```
A4  F4  D5  D5  D4  D4  C5  D5  D5  F4  D5  D5  C5  C5  D5  D5 
A4  F4  D5  D5  D4  D4  C5  D5  D5  F4  D5  D5  C5  C5  D5  D5 
```

arp, Snare (Fruity DrumSynth Live), from bar 25:

```
B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4 
B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4  B4 
```

arp, PLK Diaco (FLEX), from bar 17:

```
D4  E4  F4  G4  C5  D4  F4  A4  D4  E4  F4  G4  C5  D4  F4  A4 
D4  E4  F4  G4  C5  D4  F4  A4  D4  E4  F4  G4  C5  D4  F4  A4 
```

**Mixer buses and the master:**

- 0 Master: Patcher (Mid | Side EQ) > Fruity Parametric EQ 2 (MakeUp EQ) > Fruity WaveShaper (Hard Clip) > Emphasis (Emphasis Limiter)
- 2 Stereo Vocal (fed by [1]): Spreader > Hyper Chorus > Fruity Balance
- 3 Vocal Widness (fed by [1]): Fruity Stereo Shaper > Hyper Chorus > Fruity Balance
- 5 Vocal Delay (fed by [1]): Fruity Delay 3 > Fruity Parametric EQ 2 (EQ 2)
- 6 Delay Vocal (fed by [1]): Fruity Delay 3 > Fruity Parametric EQ 2 (EQ 2)
- 7 Vocal Reverb (fed by [1, 4, 5]): Fruity Reeverb 2 > Gross Beat (Gross Beat - Gate) > Fruity Parametric EQ 2 (EQ 2) > Fruity Balance > Fruity Balance (Reverb Sidechain) > Fruity Love Philter
- 16 Bass Submix (fed by [17, 20]): Fruity Parametric EQ 2 (Sub Boost)
- 18 Low FRQ (fed by [8, 16]): Fruity Parametric EQ 2 (EQ 2) > Fruity Parametric EQ 2 (EQ 2)
- 19 Vocal Master (fed by [1, 2, 3]): Fruity Parametric EQ 2 (EQ 2) > Maximus
- 32 Reverb Shimmer (fed by [30]): Fruity Reeverb 2 > Fruity Parametric EQ 2 (EQ 2)
- 37 Reverb (fed by [36]): Fruity Reeverb 2 > Fruity Balance
- 39 Lead Group (fed by [40, 41]): Fruity Peak Controller (Fruity Peak Controller) > Fruity Love Philter > Spreader > Fruity Parametric EQ 2 (EQ 2) > Maximus
- 42 Lead Reverb (fed by [39]): Fruity Reeverb 2 > Fruity Balance
- 43 LEad Delay (fed by [41]): Fruity Delay 3 > Fruity Parametric EQ 2 (EQ 2) > Fruity Balance

**Automation:** 71 clips, by target: FLEX 37, 3x Osc 8, Fruity Balance 6, channel 4, Gross Beat 4, Sytrus 3, Fruity Parametric EQ 2 2, Fruity Delay 3 2.

**Kit** (the most played sample of each voice): kick IL Kick_MT.wav.

## What it adds to the option bank

- `form.journey` (Journey: vocal first, breakdown, one long drop)
- `drums.melodic_techno_synth` (Melodic techno: drum synth kit, 16th hats, offbeat open hat, ride 8ths)
- `bass.ostinato_16` (16th ostinato on one note, accents moving)
- `harmony.drone_then_bVI_bVII_v` (Tonic drone, then bVI maj7, bVII6, v)
- `arp.techno_sequence` (Melodic techno 16th sequence with repeated notes)
- `vocal.techno_pitched_gated` (Melodic techno vocal: pitched, widened, gated reverb, it ducks the leads)
- `mix.vocal_ducks_music` (The vocal ducks the music)
- `mix.master_clip_chain` (Master: mid-side EQ, hard clip, limiter)
- `automation.flex_macros` (FLEX macros moving over a phrase)
- `automation.low_cut_break` (Low end taken out of the break with an EQ band)
- `sound.flex_bas_lottunma` (FLEX BAS Lottunma (Melodic Techno pack))
- `sound.flex_plk_navid` (FLEX PLK Navid (Melodic Techno pack))
- `sound.sytrus_mtechno_pad` (Sytrus five-note pad)

