# Asher Postman - AP - FUTURE HOUSE (Stock Plugins Only)

FL Studio 2026 demo project `Asher Postman - Future House.flp`, studied on a sandbox copy (the original is untouched). Genre as the project names it: Future House.

| Tempo | Key (from the notes) | Key (from the render) | Bars | Length | Saved in FL | PPQ |
| --- | --- | --- | --- | --- | --- | --- |
| 126.0 | D minor | A minor | 34 | 1:04 | 20.99.3000.3031 | 96 |

The render's audio reads A minor (a chroma vote over the first two minutes, margin 0.237; it often lands a fifth away on bass-heavy mixes): not settled without listening.

A 34-bar future house sketch made with stock plugins only: an 8-bar buildup, a 16-bar drop, an outro. Short, but every element is a lesson in layering.

## What it does and how

**Form.** Buildup 8, Drop 16, Outro 8, Tail 2 (marker names). The buildup already has bass, chords and vocal chops; the drop adds the lead.

**Rhythm and drums.** Three kicks on one pattern (Grv Kick 18, MA Round Kick 02, Grv Kick 16) make one kick. Three claps on 2 and 4 are nudged apart: Attack Clap 19 sits 0.17 of a 16th early, Attack Clap 12 0.08 early, Fracture Clap 04 on the grid, so the clap is wide and long. Hats: an off-beat open hat plus a closed hat on the last 16th of every beat (...X), shakers syncopated (..o..Xo...o..Xo.).

**Bass.** GMS sub and GMS mid bass on the same notes, D minor, a short bouncy line.

**Harmony.** The buildup hangs on A sus4 and Bb (V sus4 against bVI) and only reaches D minor in the drop: tension held until the drop.

**Sounds and synths.** A MIDI Out channel plays the chords into FL Keys and a scrape sample (MA CoffeePot Scrape) layered as one chord; Wavvyy Synth (Harmless, six-note polyphony) plays the chords as a 16th lead; Wow Synth (3x Osc) for one-shots; white noise breakdowns from 3x Osc.

**Vocal production.** Laurie Webb sample chops (Come On, Baby, Feel It, Ahh) grouped as the drop's hook instrument.

**Mix and sidechain.** Basic Sidechain: a Fruity Envelope Controller fired on every beat ducks the music; measured 13.2 dB of pump in the drop (the deepest of the twenty).

**Automation.** 18 clips: filter and volume moves around the drop.

**Transitions.** SFX Noise Punch, SFX Mega Sub and Electro Shock hits on the drop instead of a long riser.

## How it sounds (measured on the full render)

| LUFS | True peak dB | LRA LU | Crest dB | Width (side/mid dB) | Width under 120 Hz | Centroid Hz | Pump dB (loudest section) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -9.11 | 2.77 | 5.31 | 11.94 | -9.01 | -28.89 | 1435.5 | 13.19 |

Band balance (dB of the total): sub -3.98, bass -6.27, low_mid -9.74, mid -10.38, high_mid -12.41, presence -12.1, air -13.58.

| Section | Bar | Bars | LUFS | Centroid | Width | Sub dB | Air dB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Buildup | 1 | 8 | -11.78 | 2522.5 | -5.62 | -11.53 | -11.63 |
| Drop | 9 | 16 | -8.1 | 1314.5 | -9.0 | -3.91 | -14.43 |
| Outro | 25 | 8 | -9.25 | 1431.1 | -10.73 | -3.29 | -12.55 |
| Tail | 33 | 2 | -18.22 | 1203.1 | -13.9 | -2.1 | -13.06 |

## How its instruments sound (solo renders, soundbrief.describe)

| Part | Role | Plugin | Attack s | Decay s | Sustain | Centroid Hz | Register | Width | In words |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Wavvyy Synth | lead | Harmless | 0.0111 | 0.1185 | 0.0 | 500.6 | D2 | wide | sharp, percussive attack; plucked (short decay); chords or several notes at once |
|  | chords | FL Keys, sampler | 0.001 | 0.03 | 0.0 | 3464.9 |  | narrow | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 0 % before the cut; chords or several notes at once |
| FUTURE Sub | bass | GMS | 0.001 | 0.04 | 0.424 | 54.75 | F#1 | mono | sharp, percussive attack; notes cut off by their length (staccato or gated), held at 42 % before the cut; chords or several notes at once |
| FUTURE Bass | bass | GMS | 0.001 | 0.185 | 0.0 | 586.75 | F#1 | wide | sharp, percussive attack; plucked (short decay); chords or several notes at once |
| Wow Synth | lead | 3x Osc | 0.0451 | 0.31 | 0.0 | 210.7 | D2 | wide | quick attack; plucked (short decay); chords or several notes at once |
| Grv Kick 18 | kick | sampler | 0.001 | 0.2 | 0.0 | 37.45 | D1 | mono | sharp, percussive attack; plucked (short decay); brightness falls after the attack (filter envelope) |

## The data

**Sections** (from the markers, or 8-bar phrases merged by what plays):

| # | Bar | Bars | Name | Energy | Plays |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 8 | Buildup | 0.4 | audio, bass, chords, drums, fx, other, vocal |
| 2 | 9 | 16 | Drop | 1.0 | audio, bass, chords, drums, lead, other, vocal |
| 3 | 25 | 8 | Outro | 1.0 | audio, bass, drums, lead, other |
| 4 | 33 | 2 | Tail | 0.02 | audio, bass, drums, other |

**Harmony** (a chord per bar from every pitched part): Asus4 (Vsus4) x1, Bb (bVI) x1, Asus4 (Vsus4) x1, Bb (bVI) x1, Asus4 (Vsus4) x1, Bbadd9 (bVIadd9) x1, Asus4 (Vsus4) x1, Am (v) x1, Dm (i) x1, Bbsus2 (bVIsus2) x1, D5 (I5) x1, Bb5 (bVI5) x1, D5 (I5) x1, Bbsus2 (bVIsus2) x1, D5 (I5) x1, Bbsus2 (bVIsus2) x1, Dm7 (i7) x1, Bb (bVI) x1, Dm7 (i7) x1, Bb (bVI) x1, Dm7 (i7) x1, Bb (bVI) x1, Dm7 (i7) x1, Bb (bVI) x1

**Drums** (each voice's 16th grid: X in most bars, x in many, o in some; late is the average offset in 16ths):

| Voice | Channel | Pattern | Hits a bar | Late | Velocity | Bars |
| --- | --- | --- | --- | --- | --- | --- |
| clap | MA Heliocentric Clap | `.........X......` | 1.0 | 0.083 | [100, 100] | 25 |
| clap | Attack Clap 19 | `....X.......X...` | 2.0 | -0.167 | [100, 100] | 24 |
| clap | Attack Clap 12 | `....X.......X...` | 2.0 | -0.083 | [100, 100] | 24 |
| clap | Fracture Clap 04 | `....X.......X...` | 2.0 | 0.0 | [100, 100] | 24 |
| clap | MA Heliocentric Clap #2 | `X...X...X...X...` | 4.57 | 0.0 | [100, 100] | 7 |
| clap | Attack Clap 19 #2 | `X...X...X...X...` | 4.57 | 0.0 | [100, 100] | 7 |
| clap | Attack Clap 22 | `x...x...........` | 1.0 | 0.0 | [100, 100] | 5 |
| clap | Fracture Clap 04 #2 | `.............X..` | 1.0 | 0.208 | [100, 100] | 5 |
| clap | Fracture Clap 02 | `...........X...X` | 2.0 | 0.208 | [100, 100] | 5 |
| clap | Attack Snap 03 | `..............X.` | 1.0 | 0.0 | [100, 100] | 5 |
| clap | Fracture Clap 04 #3 | `x...x..xxx.xx...` | 3.5 | 0.113 | [100, 100] | 4 |
| crash | 909 Crash #2 | `X...X...X...X...` | 4.16 | 0.0 | [84, 100] | 19 |
| crash | 909 Crash | `x...x...........` | 1.0 | 0.0 | [100, 100] | 5 |
| crash | SFX Cym Airy | `......o.X.......` | 1.0 | 0.0 | [100, 100] | 4 |
| hat | Attack Hat 06 | `..X...X...X...X.` | 3.94 | 0.0 | [100, 100] | 16 |
| hat | Collider Slack CHat 02 | `...X...X...X...X` | 3.94 | 0.0 | [100, 100] | 16 |
| kick | Grv Kick 18 | `X...X...X...X...` | 3.76 | 0.0 | [100, 100] | 25 |
| kick | MA Round Kick 02 | `X...X...X...X...` | 3.76 | 0.0 | [100, 100] | 25 |
| kick | Grv Kick 16 | `X...X...X...X...` | 3.76 | 0.0 | [100, 100] | 25 |
| ohat | Collider Slack OHat 02 | `..X...X...X...X.` | 3.94 | 0.0 | [100, 100] | 16 |
| perc | Grv CH 03 | `.X.o...o.X.o.o.o` | 2.55 | 0.0 | [100, 100] | 20 |
| shaker | Attack Shaker 10 | `..o..Xo...o..Xo.` | 2.4 | 0.0 | [100, 100] | 20 |
| shaker | Hyper GoldenDays Shaker | `.......X.X......` | 2.0 | 0.0 | [100, 100] | 16 |
| snare | Collider Reverso Snare 01 | `XXXXXXXXXXXXXXXX` | 16.25 | 0.062 | [100, 100] | 4 |

**Parts** (role read from names and notes; plugin, FLEX preset, insert chain):

| Role | Name | Plugin or sample | Preset | Insert chain | Range | Poly | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lead | Wavvyy Synth | Harmless |  |  | A2-F5 | 6.22 | 796 |
| chords |  | MA CoffeePot Scrape 01.wv |  |  | A2-F5 | 4.93 | 493 |
| chords |  | FL Keys |  |  | A2-F5 | 4.93 | 493 |
| bass | FUTURE Sub | GMS |  |  | D2-D3 | 1.0 | 179 |
| bass | FUTURE Bass | GMS |  |  | D2-D3 | 1.0 | 174 |
| vocal | Laurie Webb Come On A | Laurie Webb Come On A.wav |  |  | G2-G4 | 1.33 | 73 |
| vocal | Laurie Webb Come On A #2 | Laurie Webb Come On A.wav |  |  | F3-F4 | 1.35 | 46 |
| vocal | Laurie Webb Feel It | Laurie Webb Feel It.wav |  |  | Eb2-C5 | 1.39 | 46 |
| vocal | Laurie Webb Baby | Laurie Webb Baby.wav |  |  | C3-C5 | 1.41 | 31 |
| vocal | Laurie Webb Ahh D | Laurie Webb Ahh D.wav |  |  | D3-D4 | 1.36 | 15 |
| lead | Wow Synth | 3x Osc |  |  | D2-A4 | 6.0 | 12 |
| fx | White Breakdown 01 | 3x Osc |  |  | C3-C3 | 1.0 | 3 |
| fx | White Breakdown 02 | 3x Osc |  |  | C3-C3 | 1.0 | 1 |
| fx | MA StaticShock RetroFuture FX | MA StaticShock RetroFuture FX.wv |  |  |  | 0.0 | 0 |
| fx | SFX Noise Punch | SFX Noise Punch.wav |  |  |  | 0.0 | 0 |
| fx | SFX Mega Sub | SFX Mega Sub.wav |  |  |  | 0.0 | 0 |
| audio | Collider Fifth I | Collider Fifth I.wv |  |  |  | 0.0 | 0 |
| fx | SFX Electro Shock | SFX Electro Shock.wav |  |  |  | 0.0 | 0 |
| fx | SFX Electro Shock #2 | SFX Electro Shock.wav |  |  |  | 0.0 | 0 |

**Typical bars** (two bars from each part's busiest bar, a 16th a column, - holds):

lead, Wavvyy Synth (Harmless), from bar 25:

```
D3+A3+D4+F4+A4+D5+F5 D3+A3+D4+F4+A4+D5+F5 D3+A3+D4+F4+A4+D5+F5 D3+A3+D4+F4+A4+D5+F5 D3+A3+D4+F4+A4+D5+F5 D3+A3+D4+F4+A4+D5+F5 D3+A3+D4+F4+A4+D5+F5 A2+A3+C4+E4+A4+C5 A2+A3+C4+E4+A4+C5 A2+A3+C4+E4+A4+C5 A2+A3+C4+E4+A4+C5 A2+A3+C4+E4+A4+C5 A2+A3+C4+E4+A4+C5 A2+A3+C4+E4+A4+C5 A2+A3+C4+E4+A4+C5 A2+A3+C4+E4+A4+C5
A2+A3+C4+E4+A4+C5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 Bb2+Bb3+D4+F4+Bb4+D5 C3+C4+E4+G4+C5+E5 C3+C4+E4+G4+C5+E5
```

chords, None (MA CoffeePot Scrape 01.wv), from bar 1:

```
D3+A3+D4+F4 -   .   .   D3+A3+D4+F4 -   .   A2+E3+A3+C4 .   A2+E3+A3+C4 -   .   A2+E3+A3+C4 -   A2+E3+A3+C4 -  
.   .   Bb2+F3+Bb3+D4 .   Bb2+F3+Bb3+D4 -   A2+E3+A3+C4 Bb2+F3+Bb3+D4 .   Bb2+F3+Bb3+D4 .   .   Bb2+F3+Bb3+D4 .   C3+G3+C4+E4 .  
```

chords, None (FL Keys), from bar 1:

```
D3+A3+D4+F4 -   .   .   D3+A3+D4+F4 -   .   A2+E3+A3+C4 .   A2+E3+A3+C4 -   .   A2+E3+A3+C4 -   A2+E3+A3+C4 -  
.   .   Bb2+F3+Bb3+D4 .   Bb2+F3+Bb3+D4 -   A2+E3+A3+C4 Bb2+F3+Bb3+D4 .   Bb2+F3+Bb3+D4 -   .   Bb2+F3+Bb3+D4 .   C3+G3+C4+E4 .  
```

bass, FUTURE Sub (GMS), from bar 1:

```
D3  -   -   .   D3  -   .   A2  .   A2  -   .   A2  -   A2  -  
.   .   Bb2 .   Bb2 -   A2  Bb2 .   Bb2 -   .   Bb2 -   C3  -  
```

bass, FUTURE Bass (GMS), from bar 5:

```
D3  -   -   .   D3  -   .   A2  .   A2  -   .   A2  -   A2  -  
.   .   Bb2 .   Bb2 -   A2  Bb2 .   Bb2 -   .   Bb2 -   C3  -  
```

vocal, Laurie Webb Come On A (Laurie Webb Come On A.wav), from bar 1:

```
G4  -   -   .   C4  -   .   .   .   .   .   .   .   .   .   .  
.   Bb3 C4  -   .   .   .   .   .   .   C4  -   .   .   .   .  
```

**Mixer buses and the master:**

- 0 Master: Fruity Balance > Fruity Multiband Compressor > Maximus > Fruity Limiter > Fruity NoteBook 2 (note)
- 2 Drum Group (fed by [3, 4, 5]): Fruity Multiband Compressor > Fruity Flanger > Wave Candy
- 13 Sidechain (fed by [1, 10, 11, 15]): Fruity Filter > Fruity Reeverb 2 > Fruity Love Philter

**Automation:** 18 clips, by target: generator 13, ? 2, Harmless 2, channel 1.

**Kit** (the most played sample of each voice): kick Grv Kick 18.wav; clap Attack Clap 19.wv; crash 909 Crash.wav; hat Attack Hat 06.wv; ohat Collider Slack OHat 02.wv; shaker Attack Shaker 10.wv; perc Grv CH 03.wav; snare Collider Reverso Snare 01.wv; tom Titey Tom.wav.

## What it adds to the option bank

- `drums.future_house_flam` (Future house: layered kicks, flammed claps, off-16th hats)
- `chords.chord_lead_poly` (Poly chord lead in 16ths)
- `harmony.future_house_Vsus_bVI` (V sus4 against bVI, then i)
- `mix.pump_deep` (Deep pump on music and bass (volume shaper from the kick))
- `fx.silence_and_sub` (A beat of silence, then a sub drop and an impact)
- `vocal.chop_instrument` (Vocal chops as the drop's instrument (ask first))
- `kit.future_house` (AP - FUTURE HOUSE kit (Future House))
- `sound.wavvyy_poly` (Wavvyy poly synth (Harmless))
- `sound.gms_future_bass` (GMS future house bass)

