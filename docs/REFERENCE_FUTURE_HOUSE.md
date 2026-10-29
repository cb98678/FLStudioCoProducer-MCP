# Reference study: Asher Postman, "Future House" (FL demo, stock plugins only)

Studied 2026-10-24/25 at the person's request: a finished FL project, examined closely and critically, to learn organization, effects, automation and sound design, and to plan the skills and modules we do not have yet. Plan: `docs/PLAN_FROM_REFERENCE.md`.

## Source and method

- Project: Image-Line demo song "Asher Postman - Future House.flp" (title "AP - FUTURE HOUSE (Stock Plugins Only)"), opened by the person from a zip into FL's temp folder. Sandbox copies: `sandbox\futurehouse\FutureHouse_open.flp` (FL 26.1.7 save) and `FutureHouse_demo2019.flp` (the FL 20.0.3 copy in the demo folder; same content, older format). Samples copied to `sandbox\futurehouse\samples`; `FutureHouse_render.flp` points at them.
- File read with our own parser (`coproducer.flpfile` plus scratch decoders; PyFLP 2.x fails to import its event enums on Python 3.13). Every plugin parameter read live through the bridge with the new read-only `tools/dump_project_live.py` (18,441 calls, 0 errors, 16 minutes): `sandbox\futurehouse\live_dump.json`.
- Rendered with FL's command line (`render_folder_via_cli`): full mix plus one solo project per mixer insert. Caveat: the person's FL edition has Transient Processor only as a trial, which put a modal "trial plugin" dialog in front of the command-line render and stalled it until the 40-minute timeout. The measured render (`FutureHouse_render_noTP.flp`) has the two Transient Processor slots removed (Vocal Chop slot 6, FL Keys slot 1); everything else is as the author left it.

## The song

- 126 BPM, 4/4, D minor. Progression Dm, Am, Bb, C (i, v, VI, VII), played as syncopated sixteenth-note stabs; the bass follows the chord roots in the same rhythm with octave jumps. The build voicing is four notes, the drop voicing six to seven notes spread wider (same rhythm, thicker chord).
- 35 bars, about 67 seconds. Time markers: Buildup (bar 1), Drop (9), Outro (25), Tail (33), End (35).
- Two arrangements: "Arrangement" (an older 33-bar version, no markers) and "Different Chords" (current, the one FL plays and renders).
- Project metadata filled in: title, artist, genre, comments, URL; a Fruity NoteBook 2 on the master.

## Measured (full-mix render, Transient Processor removed)

| Measure | Whole song | Buildup 1-9 | Drop 9-25 | Outro 25-33 | Tail 33-35 |
| --- | --- | --- | --- | --- | --- |
| Integrated loudness (LUFS) | -9.31 | -12.8 | -8.26 | -9.3 | -17.95 |
| Sample peak (dBFS) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| RMS (dB) | -12.1 | -16.9 | -10.4 | -11.1 | -20.4 |
| Clipped samples | 8,415 | 309 | 6,207 | 1,890 | 9 |

True peak +2.9 dBTP (intersample overs), loudness range 6.4 LU, crest 12.1 dB (whole song; about 10.4 dB in the drop), correlation 0.81, low end very mono (side minus mid below 120 Hz -29 dB), spectral centroid 1,439 Hz.

Band levels against our approved tech-house master (v14_master pass 5): this mix is 5 to 8 dB brighter from the low mids up (low mid -13.4 vs -19.0, mid -10.5 vs -15.5, high mid -13.6 vs -19.7, presence -13.3 vs -19.2, air -11.4 vs -19.7) with less sub (-3.9 vs -2.0). That brightness is why it reads -9.3 LUFS with a 12 dB crest: K-weighted loudness counts mids and highs more than bass, so its LUFS sits about 2 dB above its RMS, where our darker mix sits 0.6 dB above. Our mastering note that "-9 LUFS needs a crest near 5.6 dB" held only for our mix's spectrum; it has been corrected in the mastering skill.

## Organization

- Channel rack groups: Drums, Vocal Chops, Instruments, Audio (audio clips), Automation (automation clips), Unsorted. Ours has Drums, Bass, Synths, Vocals, FX and no Audio or Automation group.
- Playlist rows named by part: DRUMS (rows 1 to 4), Asher Postman (signature), Vocal Chops, Future Bass, Piano, Synth, SFX (rows 11 to 15), Automation (rows 16 to 27: every automation clip parked in one block at the bottom).
- Mixer inserts named by part or bus; colours by family (drums one blue-grey, synths another, FX and SFX a teal); a "BUTTON" insert (100) holds a Control Surface panel.
- Signature: a MIDI Out channel "ASHER POSTMAN" with 915 notes that spell the name in the piano roll; silent.
- Two arrangement versions kept in one project.

## Routing

| Source inserts | Goes to | Notes |
| --- | --- | --- |
| 3 Kick, 4 Clap, 5 Hats | 2 Drum Group | Drum bus: Multiband and Flanger, both bypassed at the playhead; the Control Surface macro is linked to both slots (inferred: it switches them in for transitions); Wave Candy meter |
| 1 Vocal Chop, 10 FL Keys, 11 FutureBass, 15 Outro Synth | 13 Sidechain | The music bus: Fruity Filter, Reeverb 2 and a Love Philter, all automated (filter sweep, reverb throws) and pumped |
| 6 Fill Samples, 7 Clap layer, 8 Toms/Snare, 9 Crash, 12 FutureSub, 14 Wow Synth, 16 to 21 FX | Master | Fills and FX skip the drum bus; the sub skips the music bus and gets its own pump |
| 2 Drum Group, 13 Sidechain, 100 BUTTON | Master | |

All sends are at unity (0.8). No send buses for reverb or delay: every reverb is an insert effect with its own low and high cut.

## Effect chains (live values at the playhead; "(off)" means the slot was bypassed there)

| Insert | Fader | Out | Chain |
| --- | --- | --- | --- |
| 0 Master | +0.0 dB | - | Balance (volume automated) → MB comp: L -16.9dB 2.0:1, M -9.0dB 1.7:1, H -11.0dB 2.0:1, out 3.3dB → Maximus: bands pre 4.0dB/4.1dB/3.9dB post -2.0dB, low 50% merged, mid 10% separated, high 14% separated, master post 2.0dB ceil -0.2dB → Limiter: gain 5.0dB, ceiling 4.0dB → NoteBook |
| 1 Vocal Chop | -3.2 dB | 13 | WaveShaper mix 65% → EQ: HP 126Hz, pk 303Hz -3.4dB, pk 992Hz -4.7dB, pk 2830Hz -2.6dB, hs 5385Hz 7.3dB → Reverb: size 50, decay 1.0sec, predelay 75ms, cut 238Hz-6.4kHz, wet 25%, dry 100% → Comp: -24.5 dB, 5.8 : 1, att 15.0 ms, rel 200 ms → MB comp: L -18.0dB 2.0:1, M -34.7dB 1.5:1, H -40.7dB 1.2:1 → Soundgoodizer → Transient: attack 60%, release 10%, split 253.8 Hz → EQ: HP 145Hz, pk 268Hz -5.2dB, pk 588Hz -4.1dB, pk 10471Hz -1.6dB, pk 4822Hz -1.8dB → Gross Beat (time slot automated) → Love Philter (pump, filter automated) |
| 2 Drum Group | +0.0 dB | Master | MB comp: L -18.0dB 2.0:1, M -15.3dB 2.0:1, H -18.0dB 2.0:1 (off) → Flanger: depth 3.3 ms, rate 0.15 Hz, fb 61%, wet -7.1 dB (off) → Wave Candy |
| 3 Kick | +0.0 dB | 2 | EQ: HP 35Hz, pk 47Hz -1.3dB, pk 147Hz -4.6dB, pk 396Hz -7.2dB, pk 1381Hz -2.1dB, pk 9825Hz 3.6dB, hs 11229Hz 0.9dB → MB comp: L -27.4dB 1.3:1, M -22.8dB 1.2:1, H -12.6dB 1.2:1 → Edison |
| 4 Clap | -8.7 dB | 2 | EQ: HP 140Hz, pk 978Hz -1.8dB, pk 290Hz -5.0dB, pk 2050Hz -3.5dB, pk 4799Hz -2.0dB, hs 9829Hz 1.1dB → Reverb: size 50, decay 0.4sec, predelay 26ms, cut 736Hz-4.0kHz, wet 32% (slot mix 90%) → Soundgoodizer |
| 5 Hats | -1.5 dB | 2 | EQ: HP 20Hz, pk 1770Hz -1.8dB, pk 8064Hz -2.3dB, hs 13680Hz -1.5dB → Reverb: decay 0.2sec, cut 75Hz-5.8kHz, wet 40% |
| 6 Fill Samples | -1.5 dB | Master | EQ: pk 494Hz +2.0dB, pk 7356Hz -1.8dB → Reverb: size 60, decay 0.4sec, cut 666Hz-4.0kHz, wet 20% |
| 7 Clap layer | -15.0 dB | Master | EQ: HP 92Hz, pk 171Hz -6.5dB, pk 837Hz -5.8dB, pk 3385Hz -3.9dB → Reverb: size 69, decay 1.2sec, cut 995Hz-4.0kHz, wet 59% |
| 8 Titey Snare | -3.0 dB | Master | EQ: HP 67Hz, pk 149Hz -2.3dB, pk 9944Hz +6.0dB, pk 720Hz -2.1dB → MB comp (out +2.9dB) → Soundgoodizer → Comp: -20.0 dB, 4.1:1, att 18 ms, rel 272 ms |
| 9 Crash | -3.0 dB | Master | EQ: HP 306Hz, pk 609Hz -4.6dB, pk 11751Hz +1.5dB → Delay 2: 4:00 ping-pong, fb 61%, dry 80% → Reverb: decay 2.1sec, cut 497Hz-6.4kHz, wet 70% |
| 10 FL Keys | -5.0 dB | 13 | EQ: HP 55Hz, cuts 122 to 2466 Hz → Transient: attack 40%, release -50% → Maximus used as a -10 dB trim → Comp: -16.8 dB, 22.6:1, att 6 ms, rel 575 ms, gain -4.0 dB → MB comp (out -3.1 dB) → Reverb: size 77, decay 1.5sec, cut 531Hz-2.8kHz, wet 82% → Soundgoodizer → EQ: HP 100Hz, cuts 231 to 2690 Hz, hs 9651Hz +1.3dB → Love Philter (pump) |
| 11 FutureBass | -10.5 dB | 13 | Comp: -9.0 dB, 12.7:1, att 28 ms, rel 499 ms, gain +3.2 dB → Fast Dist: pre 48%, thr 80%, type A, mix 71% → EQ: HP 82Hz, cuts 115 to 4777 Hz → Reverb: size 54, decay 0.3sec, cut 75Hz-4.0kHz, wet 80% → Soundgoodizer → Edison → Love Philter (pump, "LP" filter automation) → Gross Beat ("Bass Reverse" automation) → Balance (volume automation) |
| 12 FutureSub | -9.0 dB | Master | Love Philter (pump; fade-in automation) → EQ: pk 66Hz +6.4dB, pk 163Hz -9.6dB, pk 864Hz -3.9dB, LP 2411Hz → Comp: -30.0 dB, 5.0:1, att 22 ms, rel 200 ms, gain +15.0 dB → MB comp |
| 13 Sidechain | +0.0 dB | Master | Fruity Filter (cutoff automated) → Reverb: size 98, decay 3.2sec, cut 559Hz-4.0kHz, wet automated 0 to 100% (dry too) → Love Philter (pump) |
| 14 Wow Synth | -4.0 dB | Master | Flangus (off) → EQ: HP 44Hz, cuts 171 to 12830 Hz → Reverb: decay 0.1sec, predelay 98ms, wet 52% → Soundgoodizer |
| 15 Outro Synth | -3.8 dB | 13 | Effector: Lo-fi, X 23% → Soundgoodizer → EQ: HP 95Hz, cuts 200 to 5118 Hz |
| 16 Sidechain FX | -14.0 dB | Master | EQ: boosts 1.8k, 3.8k, hs 7.6k → Reverb: decay 4.1sec, cut 742Hz-18.6kHz, wet 75%, dry 50% → Soundgoodizer → Love Philter (pump) |
| 17 Sidechain FX Crash | -17.9 dB | Master | Reverb: decay 8.0sec, wet 80%, dry 80% → Love Philter (pump) |
| 18 SFX | +0.0 dB | Master | Love Philter (pump) |
| 19 Low Hit | -13.3 dB | Master | EQ: HP 26Hz, pk 45Hz +1.5dB, pk 177Hz -3.6dB, LP 479Hz → Delay Bank (off) → Reverb: decay 2.8sec, wet 70% |
| 21 Power Click | +0.0 dB | Master | EQ: HP 454Hz → Reverb: decay 0.9sec, predelay 70ms, wet 41% |

Patterns worth copying: a high-pass on everything but the sub and kick, several narrow cuts between 150 Hz and 1 kHz instead of boosts, reverb as an insert with low and high cuts (240 Hz to 6 kHz typical) and short decays on drums, serial compression (single-band then multiband) on vocals and keys, distortion plus saturation (Fast Dist, Soundgoodizer) on the mid bass, and the master doing band-wise widening (Maximus mid and high separated, low merged).

Soundgoodizer exposes no parameters through FL's API, so its A to D mode and amount are unknown from here.

## Pumping (the "sidechain")

There is no compressor sidechain. A Fruity Envelope Controller channel called "Basic Sidechain" is triggered by four notes per bar in the Kick + Clap pattern; its output is linked to the same Love Philter parameter (param 7, "Modulation Y") on five inserts: 13 Sidechain bus, 12 FutureSub, 16 Sidechain FX, 17 Sidechain FX Crash, 18 SFX. One envelope drives every pumped part, so they duck together and the shape is drawn once. The envelope shape lives in the plugin state, not in parameters, so copying it means copying the plugin state.

## Automation (18 clips)

| Clip | Target | Shape and placement | Purpose (read from the shape and placement) |
| --- | --- | --- | --- |
| Filter - Sidechain - Cutoff frequency | Fruity Filter on the music bus | 5 points over the song | Low-pass build into the drop |
| Reeverb 2 - Sidechain - Wet level / Dry level | Reverb on the music bus | wet 0 to 100% at transitions, dry dips to 82% | Reverb throws at the end of sections |
| LP | Love Philter cutoff on FutureBass | 3 points over 134 beats | Bass filter opening |
| Love Philter - Vocal Chop - Filter 1 - Cutoff / Output volume | Vocal chop Love Philter | 5 points each | Vocal filter and level rides |
| Love Philter - FutureSub - Filter 1 - Output volume | Sub | 0 to 100% over the build | Sub fades in for the drop |
| Love Philter - FutureBass - Filter 1 - Output volume | Bass | 6 points | Bass level rides |
| Gross Beat - Vocal Chop - Time slot | Gross Beat on vocals | 6 instances, 7 points in 16 beats | Stutter and halftime patterns |
| Bass Reverse | Gross Beat on FutureBass | 2 instances of a 2-beat clip | Reverse at transitions |
| Balance - FutureBass - Volume | Balance on FutureBass | 3-beat clip | Likely a gap before the drop |
| Balance - Master - Volume | Balance on the master | 0.80 to 0.75 | A small master level ride |
| Attack Snare 44 - Channel pitch | Snare channel pitch | 0.5 to 1.0 over the build | Rising snare roll |
| Harmless - Filter env amount | Harmless synth | one 1-beat clip placed 64 times | A repeated wobble without an LFO |
| Wavvyy Synth - Filter frequency | Harmless synth | 4 points | Outro filter |
| Surface - Insert 100 - Transition FX | Control Surface macro | 13 points over 112 beats | Drives the macro linked to the drum-bus Multiband and Flanger slots (inferred: transition FX on and off) |
| SHELTER CHORDS - Channel pitch, Attack Snare 51 - Swing mix | nothing | in the playlist | Orphans: linked to no parameter, they do nothing |

Automation targets plugin knobs (Fruity Balance, Love Philter, Gross Beat), not mixer faders, so the faders stay free for mixing.

## Sound design

- Kick: a Layer channel triggering three kick samples, each pitched down 1 to 2 semitones, with different fade-outs and filters, all on one insert.
- Clap: three claps on one insert, two panned left and right, two pitched up (+1.3 and +2.8 semitones); a separate clap layer on its own insert with a big reverb.
- Hats and shakers: seven samples (with a crash) on one insert, most pitched up 1 to 8 semitones, some panned.
- Bass: a Layer channel triggering two GMS patches, "FUTURE Sub" (mono, octave down) and "FUTURE Bass" (4 unison voices, noise, modulation), on separate inserts with different chains.
- Keys: FL Keys layered with a coffee-pot scrape sample playing the same notes (texture layer), into one insert.
- Leads: Harmless "Wavvyy Synth" (unison 6, filter envelope, phaser, harmonizer octave up) for the outro; 3x Osc "Wow Synth" (osc 2 and 3 at +24, pitch envelope down) for transitions.
- Risers: two 3x Osc noise patches (band-pass filter, pitch envelope up to +24 semitones, filter envelope) as white-noise breakdowns.
- Vocal chops: five sampler channels slicing a vocal (Laurie Webb), played as a melody in the piano roll, with volume envelopes, one an octave higher in a second pattern.
- Snare build: a pattern of 16 snare plus 16 crash hits with the snare pitch automated upward.
- FX: one-shot audio clips (impacts, reverse snares, noise punch, sub drop, airy cymbal, electro shocks) on rows 11 to 15 around each transition.

## Critical review

1. The master clips: Fruity Limiter gain +5 dB with its ceiling at +4 dB lets the output pass 0 dBFS; the render has 8,415 clipped samples and a true peak of +2.9 dBTP. Loud, but not a clean master.
2. Two automation clips are linked to nothing and do nothing (leftovers from another project).
3. Edison sits in the chains of the kick and the mid bass with nothing recorded, and Wave Candy on the drum bus: harmless but they cost CPU and add confusion.
4. Uses Transient Processor, which is not in every FL edition; on such an edition the project shows a trial warning and our command-line render stalls.
5. Two channels have no name (the FL Keys channel and its scrape layer); insert 3 is called "Grv Kick 18_2" while the part is the whole kick; insert 20 "Misc" is empty.
6. Fills and the crash skip the drum bus, so the drum-bus processing does not apply to them (a choice, but inconsistent).
7. An old arrangement version is left in the project.

## What this study broke in our tools (fixed 2026-10-25 unless noted)

1. `flpfile` read the first arrangement; FL plays the current one (here the second). Fixed: `Flp.current_arrangement()`, playlist and row reads follow it, renumbering and clip removal touch every arrangement.
2. `partmix` solo splits disabled Layer parents (the kick solo rendered silent), controller channels (the pump) and automation clips, and left the master chain on (every solo hit the limiter at 0 dBFS). Fixed: those stay on, `bypass_master` switches the master's slots off, and a part named only by its insert takes its role from the insert. Re-run: the kick solo measures -27.0 LUFS and no solo reaches 0 dBFS.
3. Mixer records in an FL 20 file use a different insert base than FL 26 saves. `read_project_anatomy` reads the base from the file and marks FL 20 files unsupported; the editing helpers still assume FL 26, so re-save old projects in FL 26 first.
4. FL 26 trims trailing zeros from the routing event (lengths 1, 3 and 104 here instead of 127). `read_project_anatomy` handles it.
5. A trial-plugin dialog stalled the command-line render until its timeout. Fixed: renders refuse a project using a plugin in config `fl.not_owned` (set to Transient Processor on this machine) and stop FL when no WAV appears or grows for `stall_s` seconds (default 300).
6. Our mastering arithmetic ignored the spectrum's effect on LUFS (corrected).
