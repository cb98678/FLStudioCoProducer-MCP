# Jay Cactus x Confz - Mic Check Ready

FL Studio 2026 demo project `Jay Cactus x Confz - Mic Check Ready.flp`, studied on a sandbox copy (the original is untouched). Genre as the project names it: UK Drill.

| Tempo | Key (from the notes) | Key (from the render) | Bars | Length | Saved in FL | PPQ |
| --- | --- | --- | --- | --- | --- | --- |
| 143.0 | Eb minor | G minor | 129 | 3:36 | 25.2.3.5164 | 96 |

The render's audio reads G minor (a chroma vote over the first two minutes, margin 0.1177; it often lands a fifth away on bass-heavy mixes): not settled without listening. 120 playlist clips are muted and play nothing; the readings above leave them out: Pad 1 (608 muted notes, 0 playing), Pad 2 (608 muted notes, 0 playing), Pad 3 (608 muted notes, 0 playing), Pad 4 (416 muted notes, 0 playing), Choir (416 muted notes, 0 playing), Piano (44 muted notes, 0 playing); the song plays audio bounces (Melody (Resampled), Piano (Rendered)), so the muted MIDI is likely their score.

UK drill at 143 bpm in loop blocks: one dark loop, drums dropping out every third block, a vocal production chain with driven ad-libs and tempo delays.

## What it does and how

**Form.** 16 blocks of 8 bars; intro and outro are pads and vocal only; every third block has no drums.

**Rhythm and drums.** The snare on beat 3 with a late answer (........x...o.o.), a kick that changes every bar, 'counter snare' hats in uneven 16th groups (Bb3 . . Bb3 . Bb3 Bb3 . . . . . Bb3 Bb3 Bb3 .), a perc on the 'a' of 1 and 2.

**Bass.** A throaty 808 held for most of the bar; a drill reese sample under it.

**Harmony.** C minor: i add9 against bVI, with a flat-II sus2 turn (Phrygian).

**Sounds and synths.** FLEX Arksun Cityscape pad (Phasic Anomoly), a Harmless pad, FLEX Strung Space strings (Olbaid Compendium), a high Sytrus pad through Gross Beat, a Sytrus choir, FL Keys high notes with delay.

**Vocal production.** Lead Vocal Bus, Lead Vocal Adlib Bus (Blood Overdrive), Hook Vocal Bus, Hook Stab Bus, sends REVERB, 1/4 DELAY, 1/2 DELAY; pan offset thrown on single words.

**Mix and sidechain.** A Beat Bus with a soft clipper over Melody and Drum buses, the 808 through Spreader and a limiter; pump 4.6 dB is the 808 and kick, not a sidechain.

**Automation.** The master balance, the Bell delay mix, two short pan throws.

**Transitions.** Gunshot impact, risers, a drum-fill sample at block edges.

## How it sounds (measured on the full render)

| LUFS | True peak dB | LRA LU | Crest dB | Width (side/mid dB) | Width under 120 Hz | Centroid Hz | Pump dB (loudest section) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -10.74 | 0.48 | 12.14 | 13.57 | -13.63 | -24.66 | 1072.4 | 4.62 |

Band balance (dB of the total): sub -6.37, bass -6.79, low_mid -5.55, mid -9.18, high_mid -11.13, presence -11.46, air -20.03.

| Section | Bar | Bars | LUFS | Centroid | Width | Sub dB | Air dB |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | 1 | 8 | -20.77 | 1160.2 | -4.22 | -78.96 | -56.98 |
|  | 9 | 8 | -15.64 | 1110.2 | -10.33 | -4.01 | -17.37 |
|  | 17 | 8 | -10.01 | 1162.2 | -13.95 | -6.44 | -19.56 |
|  | 25 | 8 | -9.37 | 1028.8 | -13.89 | -6.41 | -19.83 |
|  | 33 | 8 | -10.48 | 1090.5 | -15.52 | -6.78 | -20.07 |
|  | 41 | 8 | -9.99 | 863.9 | -15.17 | -6.2 | -20.8 |
|  | 49 | 8 | -11.35 | 1264.5 | -12.62 | -6.33 | -20.71 |
|  | 57 | 8 | -10.02 | 1163.1 | -14.06 | -6.45 | -19.55 |
|  | 65 | 8 | -9.36 | 1020.9 | -13.87 | -6.41 | -19.88 |
|  | 73 | 8 | -10.51 | 952.3 | -15.54 | -6.96 | -20.97 |
|  | 81 | 8 | -10.04 | 995.5 | -14.46 | -6.28 | -21.06 |
|  | 89 | 8 | -12.16 | 1293.8 | -12.71 | -5.66 | -19.83 |
|  | 97 | 16 | -9.79 | 1082.5 | -13.86 | -6.37 | -19.72 |
|  | 113 | 8 | -21.07 | 1242.8 | -5.31 | -18.95 | -23.25 |
|  | 121 | 8 | -26.42 | 1470.6 | -3.0 | -92.0 | -35.21 |

## How its instruments sound (solo renders, soundbrief.describe)

| Part | Role | Plugin | Attack s | Decay s | Sustain | Centroid Hz | Register | Width | In words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 808 | bass | sampler | 0.0303 | 0.474 | 0.2775 | 120.65 | A#1 | medium | quick attack; plucked (short decay); medium stereo image |
| Sub Bass | bass | sampler | 0.0242 | 0.0925 | 0.0 | 56.5 | D#1 | wide | quick attack; plucked (short decay); chords or several notes at once |
| Kick | kick | sampler | 0.001 | 0.04 | 0.855 | 50.6 | G#1 | mono | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 86 % before the cut; chords or several notes at once |
| Pad 1 | pad | FLEX, Harmless | 1.3779 | 6.18 | 0.0 | 582.9 |  | wide | soft, slow attack; decaying (long tail); chords or several notes at once |
| Pad 3 | pad | FLEX | 1.2289 | 10.04 | 0.0 | 2043.7 |  | wide | soft, slow attack; decaying (long tail); chords or several notes at once |
| Pad 4 | pad | Sytrus | 0.6898 | 4.4175 | 0.0 | 2250.05 |  | wide | soft, slow attack; decaying (long tail); chords or several notes at once |
| Piano | chords | FL Keys | 0.001 | 0.5735 | 0.0 | 831.15 | D#5 | wide | sharp, percussive attack; decaying (long tail); dark, few upper harmonics |

## The data

**Sections** (from the markers, or 8-bar phrases merged by what plays):

| # | Bar | Bars | Name | Energy | Plays |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 8 |  | 0.0 | audio, vocal |
| 2 | 9 | 8 |  | 0.8 | arp, audio, bass, fx |
| 3 | 17 | 8 |  | 0.73 | arp, audio, bass, drums, vocal |
| 4 | 25 | 8 |  | 1.0 | arp, audio, bass, drums, fx, vocal |
| 5 | 33 | 8 |  | 0.65 | arp, audio, bass, drums, vocal |
| 6 | 41 | 8 |  | 0.93 | arp, audio, bass, drums, fx, vocal |
| 7 | 49 | 8 |  | 0.36 | arp, audio, bass, vocal |
| 8 | 57 | 8 |  | 0.73 | arp, audio, bass, drums, vocal |
| 9 | 65 | 8 |  | 1.0 | arp, audio, bass, drums, fx, vocal |
| 10 | 73 | 8 |  | 0.65 | arp, audio, bass, drums, vocal |
| 11 | 81 | 8 |  | 0.92 | arp, audio, bass, drums, fx, vocal |
| 12 | 89 | 8 |  | 0.36 | arp, audio, bass, vocal |
| 13 | 97 | 8 |  | 0.73 | arp, audio, bass, drums, vocal |
| 14 | 105 | 8 |  | 1.0 | arp, audio, bass, drums, fx, vocal |
| 15 | 113 | 8 |  | 0.06 | audio, bass |
| 16 | 121 | 9 |  | 0.0 | audio |

**Harmony** (a chord per bar from every pitched part): none x8, Eb5 (I5) x3, F#maj7 (bIIImaj7) x1, Eb5 (I5) x1, Bbsus4 (Vsus4) x1, Abmadd9 (ivadd9) x1, Bb5 (V5) x1, Eb5 (I5) x3, F#maj7 (bIIImaj7) x1, Eb5 (I5) x1, Bbsus4 (Vsus4) x1, Abmadd9 (ivadd9) x1, Bb5 (V5) x1, Eb5 (I5) x3, F#maj7 (bIIImaj7) x1, Eb5 (I5) x1, Bmaj7 (bVImaj7) x1, Abmadd9 (ivadd9) x1, Bb5 (V5) x1, Bmaj7 (bVImaj7) x2, Eb5 (I5) x1, F#maj7 (bIIImaj7) x1, Eb5 (I5) x1, Bbsus4 (Vsus4) x1

**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):

| Voice | Channel | Pattern | Hits a bar | Late | Velocity | Bars |
| --- | --- | --- | --- | --- | --- | --- |
| kick | Kick | `x...o.o.o.o.o...` | 2.02 | 0.0 | [53, 128] | 64 |
| perc | Perc | `...X..X.........` | 2.0 | 0.0 | [100, 100] | 10 |
| snare | Snare 2 | `........x...x.o.` | 1.3 | 0.0 | [128, 128] | 67 |
| snare | Snare 3 | `........x...x.o.` | 1.3 | 0.0 | [128, 128] | 67 |
| snare | Counter Snare 3 | `.X.X..X.........` | 3.0 | 0.0 | [48, 100] | 8 |

**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):

| Role | Name | Plugin or sample | Preset | Insert chain | Range | Poly | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arp | Counter Snare 2 | 2DEEP_NYD_Hi Hat_01_Sample_2137308.wav |  | Fruity Parametric EQ 2 | Bb3-G4 | 1.32 | 993 |
| arp | Counter Snare | KK_Jersey_HiHat_Closed_GRime_3437123.wav |  |  | Bb3-G4 | 1.33 | 987 |
| bass | 808 | throaty808_2106413.wav |  | Fruity Parametric EQ 2 > Spreader > Fruity Limiter | Bb3-F6 | 1.22 | 271 |
| fx | FX - Gunshot | KK_Jersey_Drill_Impact_3437100.wav |  | Gross Beat > Fruity Delay 3 > Fruity Reeverb 2 | C4-C4 | 1.0 | 58 |
| bass | Sub Bass | 26_Dramatic_Drill_Reese_02_140BPM_F#_3345570.wav |  | Fruity Fast Dist > Fruity Parametric EQ 2 | Eb4-B4 | 1.0 | 16 |
| vocal | Vocals (Low) | CS_01_Saw U_Fx Vocals_A_165_G#min_3334268.wav |  | Fruity Parametric EQ 2 > Fruity Delay 2 |  | 0.0 | 0 |
| vocal | Vocals (High) | CS_01_Saw U_Fx Vocals_A_165_G#min_3334268.wav |  | Fruity Parametric EQ 2 > Fruity Delay 2 |  | 0.0 | 0 |
| vocal | VOX | PL_SH_02_Runnin_Away_Vocal_128_Cmaj_Dry_3526545.wav |  | Fruity Parametric EQ 2 > Fruity Delay 2 > Fruity Reeverb 2 |  | 0.0 | 0 |
| audio | Melody (Resampled) | Track 1 (consolidated).wav |  | Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 |  | 0.0 | 0 |
| audio | Melody (Low | Track 1 (consolidated).wav |  | Fruity Parametric EQ 2 > Fruity Balance |  | 0.0 | 0 |
| audio | Piano (Rendered) | Track 6 (consolidated).wav |  |  |  | 0.0 | 0 |
| fx | Riser 2 | DIJ_02_Rage_Riser_02_143_Dbmin_3219400.wav |  |  |  | 0.0 | 0 |
| fx | Riser | DIJ_05_Blade_Drill Riser_143_Bmin_3219550.wav |  |  |  | 0.0 | 0 |
| fx | Fill | UKD_01_Kingpin_Drum Fill Fx_B_140_Dmin_2792492.wav |  |  |  | 0.0 | 0 |
| audio | Bell | USD_02_Raid_Bell_140_Bbmin_3220273.wav |  | Fruity Parametric EQ 2 > Fruity Delay 2 > Edison |  | 0.0 | 0 |
| audio | Bell #2 | USD_02_Raid_Bell_140_Bbmin_3220273.wav |  | Fruity Parametric EQ 2 > Fruity Delay 2 > Edison |  | 0.0 | 0 |
| vocal | Confz Lead Vocal | Track 37 (consolidated).wav |  | Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Compress |  | 0.0 | 0 |
| vocal | Confz Hook Adlib | Track 22 (consolidated).wav |  | Fruity Parametric EQ 2 > Fruity Compressor > Fruity Multiband Compressor > Fruity Blood Ov |  | 0.0 | 0 |
| audio | Confz Hook Stab 1 | Track 24 (consolidated).wav |  |  |  | 0.0 | 0 |
| audio | Confz Hook Stab 2 | Track 26 (consolidated).wav |  |  |  | 0.0 | 0 |
| audio | Confz Hook Stab 3 | Track 28 (consolidated).wav |  |  |  | 0.0 | 0 |
| audio | Confz Hook Stab 4 | Track 30 (consolidated).wav |  |  |  | 0.0 | 0 |
| vocal | Confz Lead Adlib 1 | Track 31 (consolidated).wav |  |  |  | 0.0 | 0 |
| vocal | Confz Lead Adlib 2 | Track 33 (consolidated).wav |  |  |  | 0.0 | 0 |
| vocal | Confz Lead Adlib 3 | Track 35 (consolidated).wav |  |  |  | 0.0 | 0 |
| vocal | Confz Lead Adlib 4 | Track 37 (consolidated)_2.wav |  |  |  | 0.0 | 0 |
| vocal | Confz Lead Vocal | Lead Vocal (consolidated).wav |  | Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Compress |  | 0.0 | 0 |
| vocal | Confz Hook Vocal | Hook Vocal (consolidated).wav |  | Fruity Parametric EQ 2 > Fruity Parametric EQ 2 > Fruity Compressor > Fruity Multiband Com |  | 0.0 | 0 |

**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):

arp, Counter Snare 2 (2DEEP_NYD_Hi Hat_01_Sample_2137308.wav), from bar 9:

```
Bb3 .   .   Bb3 .   Bb3 Bb3 .   .   .   .   .   Bb3 Bb3 Bb3 .  
Bb3 Bb3 .   Bb3 .   .   Bb3 .   .   .   .   Bb3 .   Bb3 Bb3 .  
```

arp, Counter Snare (KK_Jersey_HiHat_Closed_GRime_3437123.wav), from bar 9:

```
Bb3 .   .   Bb3 .   Bb3 Bb3 .   .   .   .   .   Bb3 Bb3 Bb3 .  
Bb3 Bb3 .   Bb3 .   .   Bb3 .   .   .   .   Bb3 .   Bb3 Bb3 .  
```

bass, 808 (throaty808_2106413.wav), from bar 9:

```
Eb4 -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
.   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
```

bass, Sub Bass (26_Dramatic_Drill_Reese_02_140BPM_F#_3345570.wav), from bar 49:

```
Eb4 -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
-   -   -   -   -   -   -   -   -   -   -   -   -   -   -   -  
```

**Mixer buses and the master:**

- 0 Master: Fruity Parametric EQ 2 (Fruity Parametric EQ 2) > Maximus > Fruity Balance
- 1 Beat Bus (fed by [2, 15]): Fruity Soft Clipper
- 2 Melody Bus (fed by [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]): Fruity Parametric EQ 2 (Fruity Parametric EQ 2)
- 15 Drum Bus (fed by [16, 17, 18, 19, 20, 21, 22, 23, 24]): no effects
- 16 808 (fed by [18]): Fruity Parametric EQ 2 (Fruity Parametric EQ 2) > Spreader > Fruity Limiter
- 25 FX Bus (fed by [26, 27, 28, 29]): no effects
- 30 Lead Vocal Bus (fed by [31, 32]): no effects
- 32 Lead Vocal Adlib Bus (fed by [33, 34, 35, 36]): Fruity Parametric EQ 2 (Fruity Parametric EQ 2) > Fruity Compressor > Fruity Multiband Compressor > Fruity Blood Overdrive > Fruity Compressor > Fruity Parametric EQ 2 (Fruity Parametric EQ 2)
- 37 Hook Vocal Bus (fed by [38, 39]): no effects
- 40 Hook Stab Bus (fed by [41, 42, 43, 44]): Fruity Parametric EQ 2 (Fruity Parametric EQ 2) > Fruity Compressor > Fruity Multiband Compressor > Fruity Blood Overdrive > Fruity Compressor
- 45 REVERB (fed by [31, 32, 38, 39, 40]): Fruity Reeverb 2
- 46 1/4 DELAY (fed by [31, 32, 38, 39]): Fruity Delay 3 > Fruity Parametric EQ 2 (Fruity Parametric EQ 2) > Fruity Limiter
- 47 1/2 DELAY (fed by [40]): Fruity Delay 3 > Fruity Parametric EQ 2 (Fruity Parametric EQ 2)
- 48  (fed by [38]): no effects

**Automation:** 4 clips, by target: channel 2, Fruity Balance 1, mixer 1.

**Kit** (the most played sample of each voice): kick 58. Drill Kick_3449443.wav; snare 2DEEP_NYD_04_Snare_01_Sample_2137359.wav; perc KK_Jersey_Percussion_Open_3437131.wav.

## What it adds to the option bank

- `drums.uk_drill` (UK drill: snare on 3, counter hats, sliding kick)
- `bass.808_held` (Long 808 with a Phrygian step)
- `harmony.phrygian_i_bVI_bII` (i add9 against bVI, a flat-II turn)
- `form.loop_blocks` (8-bar loop blocks, drums drop out every third block)
- `fx.drill_block_marks` (Block marks: a drum-fill sample, a riser, an impact on the block edge)
- `vocal.drill_adlib_drive` (Drill: lead bus, driven ad-lib bus, hook stabs, quarter and half delays)
- `mix.beat_bus_clip` (Beat bus with a soft clipper)
- `sound.cityscape_pad` (FLEX Arksun Cityscape pad (Phasic Anomoly))
- `sound.strung_space` (FLEX Strung Space strings)
- `kit.mic_check` (Mic Check Ready kit (UK Drill))

