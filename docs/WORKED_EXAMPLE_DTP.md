# Worked example: DTP remix, editable first

What was built on the Notorious_DTP_28 project (140 BPM, F major) and the numbers it reached. Follow the same order for another track. The policy is in `PRODUCTION_POLICY.md`, the file format in `FLP_FORMAT.md`. The original project is never written; all work is on `sandbox/DTP_work`.

## Inputs
- The user's project and a target remix MP3 (110.5 s). Both 140 BPM. The remix content sits about 2 sixteenth steps later than the project grid, so generated drums and bass were shifted by minus 2 steps.
- A bar map from remix bar to project bar (DTW on vocal chroma) is what makes bar-by-bar comparison possible.

## Section map used (project bars)
intro 0 to 3, kick in 4 to 7, groove 8 to 23, break 24 to 27, build 28 to 31, drop 32 to 42, main 43 to 60, dip 61, main 62 to 75, outro 76 to 78. Fills at bars 7, 15, 23, 39, 47, 55, 63, 71, 75; crashes on section starts and every fourth bar of long sections.

## Drums (channel rack)
Nine sampler channels got generated one-shots (`oneshots.write_kit`): kick 2, snare 3, clap 4, closed hat 5, open hat 46, shaker 0, rim 1, tom 6, crash 45. Old drum notes were stripped from the existing patterns, 42 de-duplicated patterns (`DR ...`) were written from `drumplan.plan_drums` and placed one bar per clip on playlist track 43. Risers, impacts and reverse crashes are one audio clip (`FX Risers`, channel 159, mixer track 46) because they are long evolving noise.

## Bass (plugin channel and notes)
The generated sub (F1, 43.65 Hz) was replaced by a clone of the Deep2 Sytrus channel as channel 160 (`Remix Sub`, mixer track 45). Raw key 36 sounds as F1 on that patch (the patch applies minus 19 semitones). Notes were shifted by minus half a beat and cut where the next kick lands. Tension notes (`tension.drop_build`): pedal swell bars 24 to 27, gated sub bars 28 to 30, held note then octave pickup in bar 31, accent at bar 32. A Trance pluck arp (channel 12) rises across the build. The audio sub (channel 158) was muted, not deleted.

## Mix pass (what moved the numbers)
| Step | Result |
| --- | --- |
| Plugin EQ edits on the master | No change: both EQ slots were bypassed (`list_effect_slots` shows it) |
| Built-in master EQ, high shelf about minus 4.5 dB | Air band minus 10.6 to minus 13.9 dB, centroid 1811 to 976 Hz |
| Snare and clap track plus 2.5 dB, toms minus 5 dB | Hits moved by under 1 dB: the master limiter (gain 16.3 dB) hid the faders |
| Limiter ceiling minus 3.1 to minus 2.4 dB | minus 14.47 to minus 13.75 LUFS at minus 1.79 dBTP (reference minus 13.9 LUFS) |

Bar-matched spectrum against the remix after these changes: within about 3 dB from 40 Hz to 4 kHz, 126 to 200 Hz about 2 dB light, 63 to 100 Hz about 3 dB hot, 5 to 10 kHz about 2 dB hot.

## Loop used for each step
Edit with verified modules, `save_sandbox_project`, `render_with_restart`, stage the WAV, then `tools/mix_compare.py` and `tools/hit_meter.py`. `tools/mix_iter.py` does the first half and refuses edits aimed at bypassed slots.

## Vocals, toms and sweeps (second pass)

| Step | Result |
| --- | --- |
| Rebuilt `FX_v1.wav`: 8 bar break sweep reduced to a quiet top-only air sweep, build riser starts at 2.5 kHz and is lower, midrange ducked 10 dB while a vocal clip sounds | Vocal against mix in the build bars (28 to 31) improved by about 4 dB on its own |
| Cleaned the vocal sources (high-pass 100 Hz, noise reduction, 250 Hz cut, presence, air, de-ess, compression, saturation, same voiced level) and repointed 40 channels | Vocal against mix up by 1 to 2 dB in the sections, 1.5 to 2.5 dB more energy at 1.6 to 5 kHz |
| Trimmed the lead-in of 30 clips and snapped 24 off-grid clips (the `drugs` roll at a quarter step late, `Whitepowederdrop` early) | Every onset within 12 ms of a sixteenth |
| Vocal track plus 2 dB (minus 16.5 dB), toms track minus 14 then minus 17 dB, limiter ceiling raw 0.41 | Vocal against mix 4 to 6 dB better than before the pass, toms 3.7 dB lower at their hits (kick minus 16.7, toms minus 18.4, snare minus 19.2 in the hit meter), minus 13.95 LUFS, minus 1.56 dBTP |

The limiter ceiling moved 0.77 dB of loudness for 0.02 of raw value: it is a coarse control, so step it by 0.01. A cleaned copy of an mp3 that was cut short
made FL render 400 s; keep the length (`docs/FLP_FORMAT.md`).

## Automation pass (A/B copy, 2026-10-22)
The second pass baked a vocal duck into `FX_v1.wav`, and the generator script was not kept. The FX bed was rebuilt without any baked ducking by `coproducer.fxbed` and `tools/fx_bed.py` from `fx_plan_dtp.json` (5 impacts, 7 phrase end air sweeps, a 8 bar break and build riser, a riser into bar 62), each cue level fitted to `FX_v1.wav` per bar (riser fit 2.2 dB RMS in the 4 to 16 kHz band). The duck became one automation clip on the built-in EQ band 1 gain of mixer track 46 (`add_automation_clip`, 71 points: 8 dB under the 17 merged vocal windows, 14 dB at the start of the riser easing to 0 by bar 31). EQ gain scale measured on a noise source: about 29 dB per unit of knob at the band centre, 0.5 is flat.
Result on a render of `Notorious_DTP_28_auto.flp` against the current `Notorious_DTP_28.flp`: LUFS minus 14.20 both, true peak minus 2.32 to minus 2.27, bands within 0.2 dB, centroid 1040 to 1016 Hz, per bar 4 to 16 kHz and 200 Hz to 4 kHz within 0.8 dB except two bars at the impacts (bar 32 minus 2.2 dB, bar 62 minus 1.4 dB). Noise seeds differ, so the riser is not sample identical. `DTP_work/Notorious_DTP_28.flp` was not touched. Listen to both before replacing it.

## Open at the time of writing
Mid-bass layer for 126 to 200 Hz, word-level re-timing of the long vocal phrases, and an unlistened arp and Deep patch. The vocal clean-up, toms and sweeps are in the second pass above.
