---
name: bass-tension
description: Use when a remix or track must build tension and land its drops from the bass instead of noise risers, air sweeps, filter sweeps or snare rolls (the person asks for "something bass related", "no white noise", a raw or tek house feel, or a drop that hits from the low end): the ten bass moves, which style-pack and production-recipe fields make each one, the Serum spec a bass needs to carry them, and how to check them on a render.
---

# Bass tension: the low end builds the drop

The person (2026-11-05, the third Hello Toni remix): "No white noise sweeps, let's do something bass related for the tension and
drops." The earlier answer to "no sweeps" (2026-11-02, pack `tribal_tech`) moved the tension to the record's own material and the
toms. This skill moves it to the bass, which is where raw tech house, tek house, bass house and bassline keep it anyway: the bass is
the star, and a drop lands when the bass arrives, changes or returns. The first pack built on it is `styles/tek_house.json` with
`recipes/production/tek_house.json`. The standing rules hold: editable first (the bass is a channel with notes, every move an
automation clip or a pattern), the vocal never cut, sandbox only.

## The ten moves

Each row names where the move lives, so the next pack or plan gets it without code.

| # | Move | What it does | Where it lives |
| --- | --- | --- | --- |
| 1 | Density ramp | the bass goes from off-8ths to 8ths to 16ths with octaves to a 32nd trill over the build's bars (sparse to a full grid, The Producer School) | the pack: `bass.build` as a list of one pattern per bar, the last one 32 characters (`"xxxxxxxxxxxxxxxxoooooooo5o5o5o5o"`) |
| 2 | Octave jumps | an octave-up note on the first hit, more of them bar by bar; the drop's second half adds the bounce | the pack: `o` in `bass.drop` (bars 5 to 8 `"Xo..5xoxXo..5xox"`) and in the build's third bar |
| 3 | Pitch rise on the bass | the whole bass climbs 12 semitones over the last two bars and snaps back to the root on the downbeat (clips end neutral, LESSONS row 14) | the recipe: `{"recipe": "pitch_rise", "on": "bass", "bars": 2, "semitones": 12}` under `build>drop`; a pitch rise is a channel clip, and since 2026-11-05 `production._transitions` rides the first channel on the role's insert (before, only `snare` and `tom` resolved to channels); the clip spans -48 to +48 semitones (LESSONS row 10), so the rise is exact on a Sampler bass; on a Serum bass it is limited by the plugin's bend range, so keep the bass part a Sampler when the rise must be an octave |
| 4 | The filter opening is the build | the bass low-pass opens over the whole build instead of a sweep on the music bus; back from a break it returns through its filter | the recipe: `{"recipe": "lowpass_open", "on": "bass", "bars": 4}` under `build>drop` and `break>build`, 2 bars under `break>groove`; the velocity-to-cutoff link in the Serum spec does the small version on every accent |
| 5 | The bass hang | the drums leave for the last beat (or two) while the bass keeps rolling, then the downbeat | the recipe: `{"recipe": "gap", "on": "drum_bus", "beats": 1}`; the pack: the build's `last` bar with the kick `"X...X..........."` and the hats out, the bass bar still full |
| 6 | Sub drop under the downbeat | a pitched sub fall on beat 1 of the drop, the only "impact" | the plan's fx cues: option `fx.silence_and_sub` (a silent beat and a sub drop), or a `sub_drop` cue by hand |
| 7 | Drop halves | the first 8 bars bright (filter open, the hook up front), the second 8 darker (the bass closed by about 14 dB above 250 Hz, Freejak's Sorry) | not a section change, so by hand: `add_automation_clip` on the bass insert's filter, or a low-pass dip clip; the vocal moves back on the same bars |
| 8 | Pedal then release | the bass pedals the tonic under the verses (hypnotic) and follows the roots in the drops (release); under I V IV V the tonic pedal is consonant (a maj9 over the V, a second-inversion IV) | the pack: `bass.pedal: ["groove"]`, the sub pedalling the intro, grooves and breaks; the stabs always play the chords |
| 9 | Contrast by subtraction | the band stops for two beats under a sung line in the second drop, or the bass leaves for a bar every 16, so the drops can sit near the groove's level and still land (Freejak: breaks 1.7 to 3.6 LU down, stop bars 3 to 12) | the plan's `band_rests` [[start beat, end beat], ...] (strips kit, reese, sub and stab notes; the pad, lead and voice stay) |
| 10 | The record's own riser | her held word or a strum reversed into the downbeat, from the vocal or other stem, instead of noise | the plan's fx cue `reverse_sample` (fxbed), as `tribal_tech` did on 2026-11-02; its `bar` is the bar whose end is the downbeat (0-based: 31 for a drop at bar 32), since fxbed places the slice to end at `bar * 4 + 4` beats |

What is left out on purpose: `noise_riser`, `noise_downlifter`, `impact_synth`, `filter_sweep` on the music bus, `fx_swell`, a
snare `roll`. A tape stop on the bass into a break (`{"recipe": "tape_stop", "on": "bass", "bars": 1}`) is allowed: it is the bass
leaving, with the sub pedal holding under it.

## The bass that can carry these moves

A sub-only bass cannot show a filter opening, a pitch rise or a glide (The Producer School: "a bass that is too sub-heavy with no
high-end content will not translate the glide effect"). Design the bass in two parts, both Serum 2 by spec (skill
`sound-design-recipes`, `generate_serum_preset` then `render_serum_sound`):

- **The bass**: a saw and a square (or a saw at 30 to 40 % under a sine), unison 1, mono mode on, glide 0 (or a short glide for a
  legato talking pass), soft saturation or overdrive, a 24 dB low-pass near 200 Hz with a 40 % filter envelope that opens to 600 to
  800 Hz on each note, velocity to cutoff so accents open it more. This is the channel the recipe's `pitch_rise`, `lowpass_open` and
  `tape_stop` act on; in the remix builder it is the bass Sampler, playing the bass sound chosen for the song (`select_part_sound`, one A1 note in the plan's
  `bass_sample`); the tek_house pack's stand-in voice, when none was chosen, is "Tek Bass" (reese_pluck with `cut_lo` 7, `cut_hi` 36, `saw_mix` 0.9,
  `sub_mix` 0.35, `drive` 3.2, so there is crunch above the sub; the default reese_pluck rests its filter at 3 f0 and measured a 141 Hz
  centroid in the drops, too dark for an opening to be heard). The bass's Serum sound reaches the Sampler as that rendered note (the builder's `serum_states` take
  stab, pad, sub and arp); the Sampler is also what makes the pitch rise exact.
- **The sub**: a sine an octave below, no width, no brightness compared (LESSONS row 63), pumped `full` by the kick, held a bar at a
  time (`"x---------------"`) so the pedal reads as a floor, re-struck each half bar in the drops so the pump has a fresh attack.

Sidechain the bass to the kick 5 to 7 dB with a 90 to 130 ms release (The Producer School); in this system that is the recipe's pump
on the bass (`{"on": "bass", "depth": "medium"}`), measured with `measure_pump_depth` on a solo render. The low end stays mono
(`measure_low_end_mono_ratio`, the master's mono below the targets' `low_end_mono_below_hz`).

## Steps for a build

1. Write the brief (`remix-from-stems/references/creative-brief.md`): which moves this song earns and why. A density ramp under a
   sung build line competes with the voice; pick moves 3, 4 and 5 there and keep the pattern simpler. An instrumental build takes
   all of 1 to 5.
2. Pack: the bass patterns per section kind with the ramp in `build`, the pedal kinds, the `last` bar with the kick out. Validate
   with `stylepack.validate` (tests/test_stylepack.py builds the first song's plan with every pack).
3. Recipe: the bass transitions under the section pairs the form uses; `production.check_recipe` must be clean. Run
   `apply_production_recipe` with `dry_run: true` first and read every step it could not apply. Know two things about the merge:
   a plan's `production_overrides` are merged per section pair over the style's recipe and lists are joined, so an empty list does not
   remove a base recipe's noise moves (the first tek house dry run on 2026-11-05 kept club_house's noise_riser and filter_sweep next to the bass
   moves); use a base recipe with no noise (`tek_house`, `tribal_tech`) or install the recipe file. And a role target resolves by the channel
   names on the insert (`partmix.role_of`): the Sampler bass is role `bass` whatever its label ("Tek Bass" or "Rolling Bass"), not `reese`. A plan
   that wants a new pack names it in `style`: `style_overrides` carry patterns, chords, arp, pad, form and (since 2026-11-05) the sound and mix
   fields in `variety.WHOLE_KEYS`, nothing else.
4. Plan: `fx.silence_and_sub` (or your own `sub_drop` and `reverse_sample` cues), `band_rests` for move 9, and the drop-half
   automation as a listed manual move.
5. Build, produce, render (FL closed), then check (below). A move that cannot be heard on the render is not done.

## Checks

- **The rise is real**: `measure_part_timing` is not the tool; render the bass alone (`split_part_projects`, `render_folder_via_cli`)
  and read its pitch over the last two bars of the build (`analyze_sample_file` on a cut, or `transcribe_vocal_melody` on the solo):
  it should climb to the octave and sit on the root at the downbeat.
- **The opening is real**: `measure_spectral_centroid` on the solo bass, first bar of the build against the last: the centroid rises.
- **The hang is silent on the drums**: `measure_section_levels` with a one-beat section before the drop on the drum bus solo, 20 dB
  or more under the beat before it.
- **The drop lands**: `measure_section_levels` contrast, 3 to 5.5 LU over the build (targets/club_release.toml); if it is short,
  the fix is more bass before more air: a longer pitch rise, a denser last bar, a sub drop cue, in that order.
- **The pump is right**: `measure_pump_depth` on the bass solo, 5 to 7 dB a kick.
- **Nothing white**: `read_project_anatomy` lists no channel named Noise Riser, Noise Downlifter or Filter Sweep on the music bus;
  `list_automation_clips` shows the clips on the bass insert and the drum bus.

## Rules

- Outside the tension moves the bass is the rhythm-section anchor of skill `session-arranger`: one groove cell per section, locked to the
  kick, an approach note only at phrase ends. The tension moves are the deliberate exceptions, placed in builds and before drops.
- Guidelines, not guardrails (the person, 2026-11-02): when a song's build is a sung line, let the voice win and thin the ramp.
- One bass per remix is the star; a second low part (an acid line, a reese) joins only in the second drop so drop two differs.
- The pedal-then-release harmony move is checked against the vocal's notes before it is locked (skill `remix-craft`, harmony).
- A move that lives in the plan is song specific; a move that holds across songs goes into the pack or the recipe, and a new one
  into this table with its source.

## Sources

- The Producer School, [Building a Rolling Bassline Like Chris Stussy](https://theproducerschool.com/blogs/featured-blogs/building-a-rolling-bassline-like-chris-stussy-the-3-note-pattern-that-defines-modern-tech-house) (read 2026-11-05): the three-note roll, note lengths, velocities, the Serum starting point, sidechain numbers, the verse variation and the drop loop.
- The Producer School, [Master Modern Tech House Bass Lines](https://theproducerschool.com/blogs/featured-blogs/master-modern-tech-house-bass-lines-complete-tutorial-guide) (read 2026-11-05): density, octave jumps, velocity to cutoff, glides, a bass with crunch above the sub.
- Beatportal, [Step-by-Step Guide to Producing Tech House](https://www.beatportal.com/articles/692607-step-by-step-guide-to-producing-tech-house-like-fisher-chris-lake-cloonee-and-michael-bibi): the kick light in the sub so the bassline carries the low end, the bass sidechained to the kick.
- Wikipedia, [Styles of house music](https://en.wikipedia.org/wiki/Styles_of_house_music) (read 2026-11-05): tech house's distorted off-beat bass; bass house around 128 bpm with heavy distortion, one bass pattern filling the drop.
- Splice, [Firestarters Vol. 2: Build the Build](https://splice.com/blog/firestarters-vol-2-build-the-build) (read 2026-11-05): a 2 to 4 dB pull-back through the build; a reversed reverb tail of the record's own material as a riser.
- mixgraph, [Tech House Mixing Guide](https://www.mixgraph.io/mixing-guide/tech-house) (read 2026-11-05): a brief silence before a downbeat creates impact, used sparingly.
- This project: `docs/remix_studies/sorry_freejak.md` (drop halves, contrast by subtraction), `docs/LESSONS_TO_RECIPES.md` rows 10, 14, 63, 126 and 133.
