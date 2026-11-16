# Hello Toni tech house: the person's final against the build

Study of 2026-11-16. The person handed back `hellotoni_tech_house_groove_aligned_2.flp` (saved 2026-11-15) and asked: "Compare this
meticulously vs what you did and lets update the recipes and understanding of what a finished track looks like. Note the vocal timings
and syllables dropping on the metronome. Notice the layers of Serum synths, the sound design and the bass design. Notice the plugins,
echoes, what's turned off and what's turned down and changed."

## The four projects

| Tag | File | Who | What |
| --- | --- | --- | --- |
| build | `sandbox/remix/hellotoni_tech_house_slower_v1/hellotoni_tech_house_groove_produced.flp` | co-producer | the build the person opened (the contrast pass with its Section Gain clips came after it and was never opened) |
| produced_8 | `.../hellotoni_tech_house_aligned_v1/user_project/..._produced_8.flp` | person, 2026-11-02 | their first edit: vocal sliced and dragged by hand |
| aligned_1 | `.../project/hellotoni_tech_house_groove_aligned_1.flp` | co-producer, 2026-11-02 | produced_8 with every phrase moved onto her strummed beats plus a 25 ms lead |
| final | `.../user_final/hellotoni_tech_house_groove_aligned_2.flp` | person, 2026-11-15 | the finished track |

Read from the files (`diff_flp_projects`, which now reports effects, routes, stretch and Serum parameters), from FL with the final open
(`snapshot_project_params` on inserts 5, 10, 16, 17, `list_tracks_summary`), and from the vocal file's onsets against the clip positions
(`sandbox/remix/hellotoni_tech_house_aligned_v1/compare`). Not done: a render of the final (FL was open with the person's project, and a
command-line render needs it closed), so nothing here is a loudness or a spectrum of the finished mix.

## Tempo

119 to 114 bpm. The vocal file is the 86 bpm warp on FL's Stretch, so it followed by itself (1.38 times her tempo became 1.33). The chops
and the FX bed are files rendered at 119: the person set each one to Stretch with TIME its own length in beats (Fit to tempo), ten
channels by hand, so they followed too. The build now writes that itself.

## Vocal timing

The onsets are the marker detector's (135 in the 64.8 s file). "Her grid" is the guitar's strummed beat in the warped file (86 bpm, origin
0.0755 s); one of her beats is one project beat.

| | aligned_1 (co-producer) | final (person) |
| --- | --- | --- |
| clips on the vocal insert | 18 | 34 (27 windows of the long file and 7 slice files: the same lines cut at phrase ends, plus an outro reprise) |
| her beats against the project's beats, phrases left on her grid | +16 ms on every clip (the lead added) | mean +0.5 ms, spread 15 ms (22 clips): placed by ear, no lead added |
| onsets to the nearest 16th, all clips | median 10 ms, 72 % within 20 ms | median 26 ms, 40 % within 20 ms, 16 ms early in the median |
| phrases moved off her grid | none (that was the rule) | verse 1 an 8th, "not a sin, not a crime" a 16th early, "They might not know your face" about an 8th, the outro reprise an 8th |

So the final is not tighter to the 16th grid than aligned_1 by the detector; what differs is which syllables take the clicks.

* **Verse 1** (0 to 13.1 s): the person had it 0.56 beat off her bar in produced_8, aligned_1 moved it onto her beats, and the final has
  it an 8th off again (her beats at +0.47 and -0.45 of a project beat, in two slices). A deliberate choice, made twice. On her grid the
  syllable weight is 42 % on her beats and 35 % on her ands; the 8th swaps them, so "day" and "(pre)tending" take beats 2 and 4.
* **"It's only a matter of time, not a sin, not a crime, you ask me, I'll do it and say just fine"** (28.9 to 36.2 s): she sings this a
  16th behind her own guitar: 61 % of the syllable weight on the e and 26 % on the a of her beat, 7 % on the beat. The person moved it
  a 16th early (-0.18 to -0.26 beat) both times it plays (bars 26 and 66), which puts the 61 % on the clicks. aligned_1 left it on her
  grid, a 16th behind the kick.
* **"They might not know your face right now"** (25.7 to 28.9 s): +0.41 beat, in two slices.
* **Choruses and verse 3**: where aligned_1 put them, within 0.05 beat (-28 to +26 ms), cut into two to four slices each.
* **Outro** (bars 97 to 106): a reprise of the second chorus and verse 3 that the build did not have, an 8th off her grid.

| Syllable weight by 16th of her own beat | on the beat | e | and | a |
| --- | --- | --- | --- | --- |
| verse 1, first half | 0.42 | 0.23 | 0.35 | 0.00 |
| verse 1, second half | 0.31 | 0.25 | 0.43 | 0.00 |
| chorus 1 | 0.36 | 0.15 | 0.45 | 0.04 |
| "They might not know" | 0.40 | 0.00 | 0.54 | 0.06 |
| "not a sin, not a crime" | 0.07 | 0.61 | 0.06 | 0.26 |
| chorus 2 | 0.38 | 0.14 | 0.42 | 0.06 |
| verse 3 | 0.32 | 0.12 | 0.35 | 0.21 |

A weight on e and a is a measurable fault against a four-on-the-floor kick and has one fix. Beat against and is a choice of which words
take the kick: the person made it by ear, differently for the same chorus line in the drops (on her grid) and in the outro (an 8th off).

**The wet double.** 31 of the 34 vocal clips are copied to a second channel on insert 17 at the same tick: a parallel layer, not a
delayed double. **The throw.** The word "Just" (41.94 to 42.55 s) is copied onto bar 25 beat 4, then onto bar 26 beats 1 and 2 on
channels in Resample mode with TIME set, which play it 4.9 semitones higher: an echo built from the word itself, on the beats.

## Mixer levels (FL's dB, within half a dB)

| Insert | build | final | change |
| --- | --- | --- | --- |
| Master | -3.1 | -5.4 | -2.3 |
| Kick | -3.1 | -3.7 | -0.6 |
| Snare Clap | -3.5 | -3.7 | -0.2 |
| Hats | -3.5 | -3.0 | +0.5 |
| Perc | -9.9 | -10.1 | -0.2 |
| Rolling Bass | -4.8 | -6.4 | -1.6 |
| Sub Bass | -6.2 | -14.6 | -8.4, and Serum's own master volume 0.5 to 0.066 |
| Chord Stab | -2.7 | -3.5 | -0.8 |
| Rising Arp (now three synths) | -2.7 | -4.7 | -2.0 |
| Chops | -1.6 | -6.7 | -5.1 |
| Vocal | -1.6 | -6.5 | -4.9 |
| FX | -2.7 | -6.7 | -3.9 |
| Original Instruments | -4.8 | -4.8 | 0 |
| Pad | -5.7 | -5.8 | 0 |
| Music Bus | -3.9 | -3.8 | 0 |
| Drum Bus | -5.7 | -5.3 | +0.4 |
| Vocal throws (insert 16) | none | -9.2 | new |
| Vocal wet double (insert 17) | none | -10.1 | new |

The drums stayed. The voice went from 1.5 dB over the kick's fader to 2.8 dB under it, the chops with it, the risers and impacts 4 dB
down, and the sub is all but gone.

## Effects: added, changed, switched off

| Insert | The person's change |
| --- | --- |
| Master | Emphasizer (the build's) off; Soundgoodizer added on 2026-11-02 and its saved amount turned down from 486 to 166 (read as the knob at about 49 % and 17 %; FL exposes no parameter for it); Edison, Maximus "Pow", Parametric EQ 2 and Spectroman present and off; fader -5.4 dB. A mix with headroom, not a master |
| Kick | Fruity Limiter (default, ceiling 0 dB) added last; a send to the bass insert at level 0 (a sidechain feed); the channel's pan knob 12 % right (probably a slip) |
| Snare Clap | the build's CP_Snare and CP_Clap replaced by FL pack samples: 909 Snare (257 ms, centroid 6.7 kHz) and Grv Snareclap 05 (234 ms, stereo, centroid 2.1 kHz); the build's snare was 320 ms at 5.0 kHz |
| Rolling Bass | reverb mix knob 100 % to 34 %; EQ: high shelf -14 dB at 9.7 kHz added; order now compressor, distortion, reverb, Soundgoodizer, EQ, then a Fruity Limiter named "Transient shaping" (ceiling 0 dB, comp ratio 1:1, so no ducking); the automated Pump (Fruity Balance) switched off: the bass no longer pumps by itself, only with the Music Bus |
| Sub Bass | see levels: 8.4 dB down on the fader and Serum's volume from 0.5 to 0.066 |
| Chops | routed to the Master instead of the Music Bus (out of its pump and filter moves); EQ band 3 from -3.4 to +10.4 dB; Fruity Soft Clipper and Stereo Enhancer "Subtle" added; the stutter fill's Gross Beat off |
| Vocal | EQ: low shelf from -4.4 to +3.7 dB at 103 Hz, 342 Hz from -3.4 to -0.1 dB, 768 Hz from -4.7 to -3.2 dB, 1.3 kHz 0 to -1.9 dB, 2.8 kHz from -2.6 to +0.9 dB, high shelf +7.3 dB kept: the build had put the reference's chop EQ on a sung lead and it was thin. Stereo Enhancer "Subtle" (42 % separated, 0.2 ms) added. Compressor (-24.5 dB, 5.8:1), multiband and the short reverb (25 % wet, 1.0 s, 75 ms pre-delay) kept |
| Music Bus | the tape stop's Gross Beat off; the pump and the filter moves kept |
| Insert 16, throws | Fruity Delay 2: time 4:00 (a quarter note), feedback 50 %, dry 21 %, cutoff 46 % |
| Insert 17, wet double | Parametric EQ 2 (low shelf -18 dB at 94 Hz, high shelf -14 dB at 13.1 kHz), LuxeVerb "Male Vocal Dark" (decay 1.29 s, pre-delay 26 ms, brightness 30 %, size 63 m, input cut 69 Hz to 8.3 kHz), Stereo Enhancer "Subtle"; a second enhancer and a Reeverb 2 "Drum Room" present and off |

Switched off in all: the Emphasizer, both Gross Beats (stutter fill and tape stop), the bass pump, one Serum layer on the bass, and the
analysis tools on the master. Nothing is muted in the playlist or the mixer.

## Synth layers and sound design

* **Lead (Rising Arp):** three synths on the same 241 notes. The build's Serum 2 "CP - Hello Toni Voice Lead" unchanged; a copy of it with
  oscillator A an octave down, attack 20 to 7 ms, the filter opened from 0.48 to 0.82 with a free LFO at 1.6 Hz moving the cutoff, volume
  0.4 to 0.24; and a Serum (version 1) patch whose state this project cannot decode. The arp is cut out of bars 22 to 26, where the hook
  loops and the throw plays.
* **Bass:** the Reese sample kept, with the chain above. A Serum 2 layer on the same 752 notes ("CP - No Sleep Till Brooklyn Stab") was
  tried and is switched off.
* **Stab, pad:** the build's Serum 2 patches unchanged (only a running LFO's phase differs).
* **Sub:** the patch unchanged, the level nearly out.
* **Notes:** bass, sub and stab note ends quantized to the grid (23 to 24 ticks, 67 to 72, 182 to 192); starts were already on it.

## Chops and echoes

The chops rendered with an echo tail (Dontgiveup Echo, Fallinplace Echo) lost their notes in the intro, build 1, drop 1 and break; the
"don't give up" chop went from 1 to 3 hits in build 1; the last bar of the intro, drop and break chop patterns is trimmed; build 1's chop
pattern plays again over the outro in place of the outro's own chop pattern; and eight chops have a second channel into the wet double (two of the copies sit on the Drum Bus
and the Music Bus, probably by accident).

## What changed in the co-producer

| Finding | Change |
| --- | --- |
| A phrase's 8th or 16th against her grid is the person's choice | `vocalalign.plan_moves` keeps the 16th the person chose (phase "kept") and no longer adds her lead by default; `tools/align_vocal_clips.py --phase`, `--lead` |
| She sings a passage a 16th behind her guitar | `vocalalign.syllable_slots` and `phase_advice`: the share of syllable weight on e and a, and the 16th that puts it on the clicks; printed per phrase by the tool |
| Tempo changed after the build | the build sets Stretch with TIME in beats on every chop and on the FX bed |
| Note ends on the grid | the build writes bass, sub and stab lengths on the 16th grid |
| The lead vocal had a chop's EQ | `plugins/chains.json` vocal chain: the person's EQ and enhancer; new chains vocal_wet and vocal_throw; ten library entries named "ht ..." |
| The comparison itself | `diff_flp_projects` reports effects (added, removed, switched off, mix, settings, order), routes, stretch, channel knobs and Serum parameters |
| What done looks like | skill `finished-track`; lessons 176 to 184 |

Open: the levels as a profile (`tools/part_levels.py measure --save-profile` on solo renders of the final, FL closed), the wet double and
the throw insert as steps of the build, and the lead's layers as a plan option.
