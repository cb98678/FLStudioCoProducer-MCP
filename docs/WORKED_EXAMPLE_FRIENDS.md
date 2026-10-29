# Worked example: "Friends in Low Places" as a tech-house remix (v12)

What was built from FL Studio's four stems of the song, how each part is made, and the numbers it reached. It is the second worked example after `WORKED_EXAMPLE_DTP.md` and the first built entirely from stems. Policy: `PRODUCTION_POLICY.md`. Vocal cutting rules and their history: `VOCAL_CHOP_RECIPE.md`. Pipeline status per step: `STEM_REMIX_PIPELINE.md`. How to rebuild it: `HANDOFF.md`.

## Inputs

- Four stems from FL's "Extract stems from sample" in `sandbox\stemstest\Audio\` (bass, drums, instruments, vocals, about 264 s each, stereo float).
- Measured from the stems: 108.478 bpm (`coproducer.drumhits`, mean distance from the sixteenth grid 12.8 ms), key A major, the first drum hit at 27.3085 s (the origin of the bar grid; it is a detected hit, not a verified downbeat).
- The DTP project, only to borrow two Sytrus patches (Remix Sub, Trance pluck).

## Result

| Item | Value |
| --- | --- |
| Tempo, key | 124 bpm (the vocal is stretched by 124 / 108.478 = 1.1431), A |
| Length | 104 bars, 201.3 s of music, 205.2 s rendered with the tail |
| Loudness (render7) | -16.4 LUFS integrated, peak -2.86 dBFS, no clipped samples; master fader -3 dB, no limiter yet |
| Notes | 3242 drum events, 550 reese, 412 sub, 624 stab, 384 arp, 79 chop triggers, 18 FX cues |

Section map (0-based bars): intro 0 to 7, groove 8 to 23, break 24 to 31, build 32 to 39, drop 40 to 55, break 56 to 63, build 64 to 71, drop 72 to 95, outro 96 to 103. Chord roots per 8 bars: A A A A B B E E (`remixplan.ROOTS8`).

## What each part is made of (editable first)

| Part | Made of | Made by |
| --- | --- | --- |
| Drums (9 voices) | Sampler channels, one pattern per distinct bar, one-shots synthesised for the project | `remixplan.drums`, `drumplan`, `oneshots`, `tools/techhouse_audio.py` |
| Reese bass | One recorded reese pluck (A1 on key 60) on a sampler channel, transposed per bar, notes in patterns | `remixplan.reese_notes` |
| Sub bass | Sytrus patch "Remix Sub" cloned from the DTP project, raw key = MIDI + 7 | `remixplan.sub_notes` (kick-aware truncation) |
| Chord stabs, rising arp | Sytrus patch "Trance pluck" and "Trance pluck #2" cloned from the DTP project | `remixplan.stab_notes`, `arp_notes` |
| Vocal chops | 10 sampler channels ("Chop hook" ...), 6 with a baked 3/16 echo version, triggered from one pattern ("Chops N" = one bar's unique content) | `CHOPS`, `chop_events`, `cutrefine`, `vocalchops` |
| Long vocal phrases | 3 audio clips of the stretched vocal on the vocal row, edges snapped to syllable onsets and phrase ends | `VOCAL_CLIPS`, `CLIP_WORDS` |
| Risers, impacts, sweeps, downlifters | One audio clip ("FX bed") because they are long and evolving | `remixplan.fx_cues`, `fxbed` |

Mixer inserts 1 to 11 carry kick, clap, hats, perc, reese, sub, stab, arp, chops, vocal, fx (levels in `remixplan.GROUPS`). The stabs and arp sit at +5 and +3 dB because the Trance pluck patches are very quiet (peak -20 dBFS at 0 dB).

## Vocal chops: what had to be true

The vocal work took most of the iterations. The rules that came out of it are in `VOCAL_CHOP_RECIPE.md`; the short version:

1. A chop starts at a syllable onset and ends at a word onset or the end of the sung phrase, snapped by signal; Whisper (large-v3) only votes on the result, because its word times drift 0.2 to 0.7 s on singing.
2. A final s or z (blues, places, friends) is found by signal plus the lexical rule `cutrefine.final_s` (hiss in the 4 to 12 kHz band within 16 dB of the level, prominence 5 dB, bridging up to 2 frames, 15 ms tail). The earlier end rules stopped at the first dip and cut the s off. Measured moves on the stem: blues 142.56 to 142.94 s, hook 137.19 to 137.32, friends 134.92 to 135.19, drowns unchanged.
3. Every cut keeps a 0.25 s ring-out, and the echo version is baked into its own file, so nothing depends on a plugin.
4. Two vocals may overlap only if the later one starts inside the earlier one's echo tail, never inside its dry part, and no echo may ring into the next section's pick-up (`remixplan.chop_conflicts`; `build_techhouse.py` prints the result, 19 informational notes in v12, mostly intended).
5. A long phrase clip plays until the phrase ends, not to a grid line (rule 5d): the break-2 verse clip runs to 78.44 s of the original, 0-idx bar 63.1 of the remix.

## What the listener changed along the way (v9 to v12)

| Report | Fix (in the recipe, then applied to every cut) |
| --- | --- |
| "My blue" instead of "my blues", "low place", "friend" | `final_s` rule, `wants_final_s` (lexical: last word ends in s and the next does not start with s, z, sh, ch, j) |
| Pattern 22 muddy, bleeding into the drop | Last hook of a drop is dry, the last answer is dropped, the closing okay lands on clear air; drop 1 closes on dry okay |
| Break-2 vocal should play out to marker 64 | `VOCAL_CLIPS[1]` end hint 78.20 and a tail word check "low places" |
| Chops 23 to 27 cluttered, inaudible | The 16th chatter at bars 80 to 87 was removed (see "Next" below) |
| Synths cartoonish | Not fixed yet; Serum 2 is the plan (`SERUM_MCP.md`) |

The user's hand-fixed copy `FriendsInLowPlaces_TechHouse_v3e_userfix.flp` is kept as a regression baseline: its break clip start and the "Vocal 124 bpm" timing were placed by ear and are known good.

## Checks that exist

- `tests/test_cutrefine.py`, `tests/test_vocalchops.py`, `tests/test_remixplan.py` (cuts on synthetic voices, chop placement, no chatter, teasers clear the next entry, clip hints).
- Two read-only measures as modules: `check_vocal_edges` (level at start and end, abrupt end, ends on hiss, tail HF) and `find_final_s_end` (where a final s ends, moved seconds). Both are in phase P5.
- `tools/render_report.py` prints loudness, peak, clipped samples and band energies for a render.
- Not checked by any tool: how a chop sounds. The user's ears are the final check and each listening note became a rule.

## Known weak spots

- The "z" of `friends` is voiced and quiet, so its end is the least certain cut. `check_vocal_edges` cannot tell the first s of "places" from the last.
- `bluesaway` start and end, `blues` start, and `pickup` start and end are signal-only; Whisper cannot confirm them.
- Whisper varies from run to run on short isolated chops; the recipe votes, it does not trust one read.
- The build-section `friends` stutters overlap themselves (intended; longer now that the s is kept).
- "The" before "whiskey drowns" is not in the chop on purpose.
- Playlist track names do not match their rows; the master has no limiter (headroom comes from the -3 dB fader).

## Next on this song

Serum 2 stabs, arp and sub in place of the Sytrus patches (`SERUM_MCP.md`); a designed gabber or high-pitched stab for drop 2 where the chatter was; the original-guitar reminiscence recipe (`VOCAL_CHOP_RECIPE.md`, "Tagged for later"); then a second song to test that the pipeline generalises (`STEM_REMIX_PIPELINE.md`, "Generalising").
