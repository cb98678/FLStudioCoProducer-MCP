---
name: mastering
description: Use when finishing a track: hitting loudness and true-peak targets, limiting, reference matching, low-end mono, and delivering a master. Use for "master this", "make it streaming ready", or "match this reference".
---

# Mastering

You finish a mix against targets the human chose. Every check is made on a fresh render.

When the person says a part is "too high" or is "killing the loudness", measure before cutting: solo renders (`tools/part_levels.py split`, `render_folder_via_cli`) with band levels, then offline trials on the summed solos through `mastering.master` (sandbox\diag\curse_kick_trials.py is the worked example). On The Curse of Curves the kick's sub, not its level, was the problem: a 60 Hz shelf on the kick sample, not a lower fader (the claps already measured louder than the kick). Offer two masters when a balance change goes beyond what they asked; they picked by ear.

## Steps

1. Read the targets: `load_targets_file`. If it refuses because values are blank, name the blanks and ask the human to fill them. Do not substitute numbers.
2. Snapshot: `snapshot_state`.
3. Render and measure the current state: `prepare_for_render`, `render_via_cli`, `restore_after_render`, then `build_measure_report`.
4. Compare: `check_report_limits` with the limits from the targets file. List what fails.
5. Fix in this order, one change at a time, within delta caps:
   1. Level into the master chain (see `gain-staging`): `apply_gain_trim` on the sources or buses.
   2. Tonal balance against the reference (`compare_to_reference`, `measure_band_energy`).
   3. Low end: `measure_low_end_mono_ratio`; fix width on the offending tracks.
   4. Master chain controls from the human's recipe: `set_plugin_param_by_name` or `apply_param_recipe` on the limiter and any other master plugins.
6. Render and measure again after each change. Stop when every limit passes, or when the iteration cap is reached.
7. Loudness-matched A/B for the human: `build_ab_package` (it matches both files to the same loudness so louder does not sound better).
8. Write a short report with `write_report_file`: before and after numbers for each limit, and what changed.

## Rules

- The ceiling is true peak (`measure_true_peak`), not sample peak.
- Judge loudness with `measure_integrated_loudness`, not by ear or by peak.
- Compare to a reference only at matched loudness.
- When the targets and the reference disagree, say so and ask which wins. Do not average them.
- Never chase a number by wrecking dynamics: check `measure_crest_factor` and `measure_loudness_range` against the targets file after every loudness change.
- The master chain recipe is the human's. If none exists, ask; do not invent a plugin chain.
- Stop at the iteration cap and ask.

## Check the targets against each other first

Loudness is roughly peak minus crest factor plus an offset that depends on the spectrum: K-weighting counts mids and highs more than bass, so a dark mix reads about 0.6 LU above its RMS and a bright one 2 to 3 LU above (measured 2026-10-24: our tech-house master 0.6, the Future House reference about 2.1 in its drop). Measure that offset on the first render (`build_measure_report` gives LUFS and RMS), then work out what the ceiling and crest allow. For our darker mix, -2 dBTP and crest 8 capped it near -11.5 LUFS; a brighter balance moves the cap up without more limiting. Ask which target gives way before rendering passes. A soft-clipping limiter such as Maximus also leaves true peak about 1.7 dB above sample peak.

## Section contrast against integrated loudness (measured 2026-10-25)

A limiter at its ceiling pins the loudest sections: on the tech-house remix the drops read about -12 LUFS whatever went in (raising the whole mix 1.5 dB before the master moved them 0.1 LU), so the master had squashed the drops more than the sparse breaks and the breaks ended up 1.5 LU louder. Contrast therefore comes from lowering builds and breaks before the master (`apply_section_gains`, see `mix-engineer`), and that lowers the integrated value, not the drops: 3.4 to 3.8 LU of drop over build cost 1.3 LU of integrated loudness. Measure `measure_section_levels` on the mastered render, report drop over build and drop over break next to the integrated value, and ask which gives way. The person chose contrast at -13.0 LUFS for that song.

## Stock Maximus on the master (measured 2026-10-24)

Find its slot with `list_effect_slots`, read knob text with `get_plugin_param_by_name`, set with `set_plugin_param_by_name`. It loads neutral. "Master pre gain" runs about 37.5 dB per unit above 0.5 (0.655 is +5.9 dB, 0.73 is +8.6 dB) and the loudness gained is far less than the dB added, because the soft saturation absorbs it. "Master post gain" is about 40 dB per unit (0.48 is -0.8 dB) and moves true peak one for one. "Low band stereo separation" above 0.5 narrows (0.7 reads "40% merged"), below 0.5 widens; the low band covers below 200 Hz. Put the limiter last in the chain (Move up on the slot before it, in the slot menu). Render each pass from a copy of the saved project.

## Club master from the person's references (2026-10-25)

`apply_club_master` is the delivery stage after the mix: DC removal and a silent-tail cut, then (with a profile) a broad linear-phase EQ toward the references, then a soft clipper into a look-ahead true-peak limiter, iterated to the targets' loudness and stopped by the crest floor. Build the profile with `build_reference_profile` from the tracks the person chose (WAV, FLAC, MP3, AIFF, OGG; others go through ffmpeg): it writes the per-track numbers, the mean and spread per third-octave band, and with targets_out a targets file measured from them. The true-peak ceiling stays the base file's, because the master must survive MP3 and AAC encoding. The match follows match-EQ practice: compare at equal level, act broadly, leave the band under 35 Hz alone (the references are in other keys) and fade the top octave out of the match ([iZotope, Match EQ](https://www.izotope.com/en/learn/how-to-use-match-eq-in-ozone-9); [iZotope, Tonal Balance Control](https://www.izotope.com/en/learn/leveling-up-your-mastering-workflow-with-tonal-balance-control)). A reference profile is the person's choice of target; a single reference has no spread, so ask for three or more per genre.

## Ask when

- The targets file is missing, incomplete, or conflicts with the reference.
- Reaching the target needs more compression or limiting than the human's recipe allows.
- The A/B is ready: this is a V1 gate. The human decides if it is done.
