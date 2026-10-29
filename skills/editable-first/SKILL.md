---
name: editable-first
description: Use whenever you build or remix parts in FL Studio (drums, bass, chords, leads, FX): drums go in the channel rack as sampler channels plus patterns, synths and bass as plugin channels plus piano-roll notes, and generated audio clips only when not conducive or clearly better.
---

# Editable first

This is the user's standing preference for all building and remixing. The user can change a note, a velocity, a sample or a patch later without a re-render, so parts are built as channels and notes. Audio is the exception and needs a reason. Generating sounds, samples and vocals is fine, except a clone of a real person's recorded voice; the rule is where the result lives in the project. Full policy and tools: `docs/PRODUCTION_POLICY.md`.

## Decide per part

| Part | Build it as |
| --- | --- |
| Kick, snare, clap, hats, shaker, rim, toms, crash | Sampler channels with generated or existing one-shots, beat written as patterns |
| Bass, sub, chords, leads, arps, plucks | A synth the user owns as a channel, notes in the piano roll |
| Vocals and vocal chops, risers, downlifters, reverse crashes, impacts, long textures, resampled material, the user's own recordings | Audio clips (the allowed exceptions) |

If a part is not in the table, build it editable. If you deliver a part as audio, name the reason with `record_decision`.

## Steps

1. **Intake.** `read_project_summary`, `list_channels_summary`. Work in the sandbox copy only. List every channel by global index, because new channels and clips sit in a different index group.
2. **Classify.** Put each part in the table. Say which parts will be audio and why.
3. **Grid.** Measure where the reference sits against the project grid (tempo, bar start, offset in sixteenth steps) with `listen-and-measure`. Shift generated parts to match.
4. **Section map.** Write sections as data (intro, kick in, groove, break, build, drop, main, dip, outro) and get it approved (`ask_human`, V1) before building.
5. **Drums.** Make the kit (`python tools/flp_tool.py kit DIR`), find or add sampler channels with `find_channel_by_name`, point them at the samples, generate the drum plan from the section map, review it as data, then write patterns into the sandbox FLP with `python tools/flp_tool.py add-drums`. Save the project from FL first, patch the closed copy, reopen it.
6. **Bass and synths.** Pick the synth the user owns whose patch matches the target's tonality and frequency; compare spectra, not names. Clone that channel in the file (`flp_tool.py clone`), give it its own mixer track, write notes with `flp_tool.py add-notes`, and mute (do not delete) any audio version it replaces. Cut bass notes where the next kick lands, since the API has no sidechain.
7. **Tension.** Use the recipe in the policy doc: break swell, build with snare-roll density 4th to 32nd, kick thinning, rising arp, gated sub, held note, impact and reverse crash into the drop. FX are audio clips on one FX channel.
8. **Verify.** Reopen, list channels and patterns, `check_notes_written` where the piano roll route was used, then `save_sandbox_project`, `render_with_restart` and measure with `build_measure_report`. Compare bands, crest and loudness with the reference numbers.
9. **Mix.** Only then touch faders (`gain-staging`, `mix-engineer`). Compare against the reference bar by bar (`tools/spec_match.py`), not by whole-file band numbers. After any plugin edit prove it is audible with a render, because a bypassed slot still reads back as verified. Present an A/B (`build_ab_package`) and ask.

- Vocal chops and phrase clips must be whole words. Before cutting any, read `references/vocal-chops.md`.

## Learn from the person's hand fixes

When the person fixes a build by hand and saves a copy (`..._v3e_userfix.flp`, `..._v13_2.flp`), run `diff_flp_projects` on the build and the copy before touching anything. It lists channels added or removed, samples and presets swapped, mixer changes in dB, note rhythm per channel and audio clips that moved. Then for each finding either change the recipe that made the build (so the next build already has it) or log it as song specific in `docs/LESSONS_TO_RECIPES.md`. Do not rebuild over their copy, and keep the audio files they edited: never write a build into a folder an earlier build used (use a new `audio_vNN`).

What the first remix showed: generated hats were swapped for FL's factory 909 closed hat and 707 open hat, so offer the factory packs for hats first (`build_techhouse.py --kit hat=...`).

## Rules

- Name and colour every part you add in the house style (`docs/PROJECT_STANDARD.md`); `apply_project_standard` does it for a whole project. A build from `build_remix_project` already comes out that way.

- Never write the user's original project. Patching is on the sandbox copy and the output path must be under a sandbox folder.
- Never patch a file FL has open. Save, close, patch, reopen.
- Pattern ids are unique across every part you add; the tool refuses reuse.
- Replace by muting, not deleting, so the human can A/B the audio and the editable version.
- In "mix and master only" mode do not rebuild parts. Gain stage, EQ and limit what is there.

## Ask when

- The section map, the synth choice or the sample kit sound is a taste call.
- The plan would put a part in audio with no reason from the table.
- The human's own recording would be replaced by a rebuilt part.

Changes over time follow the same rule: levels, pans, sweeps and effect knobs are editable automation clips in the playlist (`add_automation_clip`), not a baked render.
