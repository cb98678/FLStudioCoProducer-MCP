---
name: study-reference-project
description: Use when the person hands over a finished FL Studio project (a demo, a pro track, a pack template) to learn from: "examine this project", "what can we learn from this song", "study how this is built", "copy what they did". Not for mixing or mastering our own song.
---

# Study a reference project

The procedure used on the FL demo "Future House" (2026-10-25, `docs/REFERENCE_FUTURE_HOUSE.md` and `docs/PLAN_FROM_REFERENCE.md`): read everything the file and FL can tell, render and measure it safely, judge it, and turn what is worth copying into a gap map and a build plan the person approves.

## Order of work

1. **Copy first.** `copy_project_to_sandbox`; the original is never written. The readers now read projects saved by FL 12 to FL 26 (the demo study read FL 12.9 and 20.99 files); writing an old project is still refused: render copies are written whole, and for edits ask the person to open it in FL 26 and save a copy into the sandbox.
2. **Read the file.** `read_project_anatomy`: channels with type (sampler, plugin, Layer and the channels it plays, audio clip, automation clip), pitch and group; mixer inserts with names, routing and every effect slot; automation clips with their targets named ("Sidechain insert, slot 1, Fruity Filter, cutoff"); controllers; arrangements and the current one; time markers. Note what a part is made of, not only what it is called.
3. **Read live parameters.** With the person's go-ahead, open the copy in FL and run `snapshot_project_params` on the inserts in use (about 80 ms a call, so a 22-insert project takes about 16 minutes; pass only the inserts you need). Parameter texts say what the file cannot: filter type, reverb decay, compressor thresholds.
4. **Check before rendering.** `check_project_health`: orphan automation clips, a master that can pass 0 dBFS, plugins this FL edition has only as a trial (config `fl.not_owned`, a trial dialog stalls a command-line render), unnamed channels, alternate arrangements.
5. **Render and measure, with permission.** The full mix and one solo per part with the master bypassed (`split_part_projects` with bypass_master, `render_folder_via_cli`). Then `measure_section_levels` on the project's own markers, `measure_part_levels` for the balance, `measure_band_energy`, `measure_crest_factor`, `measure_stereo_correlation`, and `measure_pump_depth` where something pumps.
6. **Judge it.** What is worth copying (chains, routing, layering, automation moves, section contrast) and what is not (a clipping master, unnamed channels, orphan clips). Say what you could not read or confirm.
7. **Coverage.** List every technique found (routing, every effect chain, the pump or sidechain, every automation clip, sound design, organization) against the module or recipe that does it and how far it is proven, as `docs/REFERENCE_COVERAGE.md` does for the first reference. A technique without a recipe is a gap; a recipe that is only tested, not rendered, is not done.
8. **Gap map and plan.** A table of technique seen, what we have, and the gap, then proposed work in the order that unblocks the rest. Ask the person to approve the order and each choice that changes their standard, and record the answers in the plan.
9. **Turn it into options.** What the project does that the bank lacks becomes an option (`src/coproducer/data/options`, skill `creative-variety`), the way the twenty FL demo songs did on 2026-10-28 (`docs/DEMO_STUDY.md`): projmusic reads its song notes (looped clips unrolled), roles, key, chords per bar, each drum voice's 16th or triplet grid with its lateness, sections and the parts' typical bars; a groove, bass line, chord rhythm, arp shape, form, harmony loop, transition, mix move or instrument goes into its category file with the song as its source; tools/gen_demo_options.py rebuilds the kits and instruments, tools/demo_study_docs.py the study pages (the whole pipeline, in order, is tools/demo_study/README.md), and tests/test_variety.py proves every option is valid. Projects saved by older FL versions are read too (playlist items of 32, 60, 80 or 88 bytes by version, any PPQ). Read what plays, not what is written: clips muted in the playlist are left out (a producer often bounces a part to audio and mutes its MIDI; that MIDI is the bounce's score and its patch is still worth studying), the master pitch knob moves the key the notes sound in (both Inner Days demos sit at -400 cents), and the key from the notes is checked against the render's own key (`estimate_key_dsp`); when they differ, say so instead of picking one.
10. **Solo renders cheaply.** For measuring instruments, cut the playlist to the 8 to 16 bars where the part plays most (flpfile window_playlist on a solo copy, looped clips unrolled) before rendering: a whole-song solo of every part takes hours.
11. **Keep what is reusable, with permission.** Effect and channel settings (not audio) go into the effect library with `python tools/fx_library.py extract-all` or `extract-channel`, each entry with its source and parameter texts; `list_effect_library` shows them.

## Rules

- Take reference values (section contrast, band balance, part levels) from the reference, not its loudness when its master clips.
- A finding is a measured fact or a read value; an inference is marked as one ("the macro is linked to both slots, so it probably switches them in for transitions").
- The goal is recipes that work on any song, never a better mix of one song: each finding becomes a module, a recipe file or a skill rule, and is checked on a project other than the one it came from.
- Fix our readers when the reference breaks them (several arrangements, Layer channels, controllers) before trusting a measure.
- Renders and opening projects in FL need the person's go-ahead; never close their project to render.

## Ask when

- The project uses plugins the person may not own, or samples that are not on this computer.
- Saving the reference's settings into the library: ask once, before the first entry.
