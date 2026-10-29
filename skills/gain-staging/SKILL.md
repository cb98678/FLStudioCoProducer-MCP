---
name: gain-staging
description: Use when setting levels in an FL project: headroom per track and bus, trims before processing, polling peaks, sending to buses, and keeping the master chain input clean. Use for "my mix clips", "levels are all over", or "set up gain staging".
---

# Gain staging

Goal: every stage has clean headroom, so later processing behaves and nothing clips. Level is fixed at the source, not on the master fader.

## Order of work

1. Snapshot: `snapshot_state`. Note the id in the ledger.
2. Read the layout: `list_tracks_summary`, then `get_track_peak_db` for each track while audio plays (`ensure_playing`).
3. Start at the sources. Work up: sources, then buses (the house Drums, Vocals and FX buses from `build_family_buses`, or `build_bus` and `create_send_route` for others; a send keeps the level its insert had to the master, 0.8 in FL, so a new bus starts neutral), then the master chain input.
4. Trim with `stage_gain_chain`: give it the stages in signal order with a target peak for each. It holds the meter, then moves each fader toward its target within `max_delta_db`. Silent stages are skipped and reported, not changed.
5. Fine changes: `apply_gain_trim` (capped dB change) or `set_track_volume_db_verified`.
6. Stop playback (`ensure_stopped`), then render (`prepare_for_render`, `render_via_cli`, `restore_after_render`) and measure with `build_measure_report`.
7. Compare with the targets file (`load_targets_file`, `check_report_limits`). Report what moved, by how much, and whether the render agrees.

## Part levels from solo renders (balance between parts)

Peaks keep headroom; the balance between parts comes from loudness measured on renders, against a profile the person approved. Do not set part levels from numbers in a plan file.

1. Take a mix the person has approved and build the profile once: `python tools/part_levels.py split PROJECT.flp SOLO_DIR`, render the folder with `render_folder_via_cli` (one FL launch for every part), then `python tools/part_levels.py measure SOLO_DIR RENDER_DIR --save-profile profile.json`. The profile holds each role's loudness relative to the kick.
2. On a new build: split, render, then `python tools/part_levels.py plan PROJECT.flp SOLO_DIR RENDER_DIR profile.json OUT.flp`. It writes the fader changes (at most 12 dB a pass, the kick and the master never move), then split and render again to confirm every part is within 1 dB.
3. The roles come from channel names; check them in the printout. A part with no role is left alone and reported. A solo keeps the Layer channel that triggers the part, controller channels (an Envelope Controller pump) and automation clips on, so the part sounds as in the mix. With a limiter on the master, split with `--bypass-master` (module `split_part_projects`, option bypass master) and use the same setting for the profile and every build compared with it.
4. FL's command line renders only while FL is closed. The render modules refuse while it runs; ask the person (`ask_human`) to save and close it, or use `render_with_restart` (A1, it asks before closing and reopening FL).
5. A part that is loud only in some sections (a sub that swells in the breaks) shows as a whole-part average. Check `measure_section_levels` on the render before accepting; fix a section problem in the notes or an automation clip, not with the fader.

## Target peak levels

Per-stage peak targets are not hardcoded here. Read them from the project's spec sheet (`spec_get`) or ask the human (`ask_human`) and record the answer with `record_decision`. Never invent one.

## Rules

- Peaks are not loudness. A peak target keeps headroom; loudness is judged on the render.
- Never fix a level problem with the master fader. If the master clips, go back to the sources and buses.
- Change the loudest offender first; re-poll before the next change.
- Stay inside `max_delta_db` per step. Many small steps beat one big one.
- Every trim must be verified. If a trim reports `verified: false`, stop and read the fader back; do not stack more changes on it.
- Check the master chain with `list_effect_slots` before trusting it: bypassed slots do nothing, and a limiter with large input gain turns every fader move into a smaller one.
- Gain staging precedes EQ and compression. If a processed track clips after a plugin, use the plugin's own output control (`set_plugin_param_by_name`) rather than the fader.

## Ask when

- A track has no audio during polling and it is not obvious why.
- The only way to avoid clipping is to change a creative balance (for example dropping a lead by a large amount).
- The iteration cap is reached with clipping remaining.
