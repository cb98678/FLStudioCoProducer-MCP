---
name: studio-ops
description: Use for reading or changing FL Studio project state through the fl-bridge tools: sandbox rules, snapshots, verified writes, rollback, reading a failed verification, naming tracks, routing, tempo, patterns, and plugin parameters by name.
---

# Studio ops

You work on a sandbox copy of the project, through verified tools. Tool details are in `references/catalog/L2.md` and `L3.md`; this file says when and why.

## Rules

1. Read before you write. Start with `read_project_summary`, then `list_tracks_summary` or `list_channels_summary`. Use `find_track_by_name` and `find_channel_by_name` instead of guessing indexes.
2. Use the `*_verified` tools for every change. They read the value back. Only `verified: true` counts as done.
3. Work only on the sandbox copy. `copy_project_to_sandbox` makes it; the original is never written. If `ping_fl` shows the open project is not the sandbox copy, stop and fix that first.
4. Snapshot before anything risky: `snapshot_state` (tracks, channels, tempo). Restore with `rollback_to`. For one kind of value, `snapshot_tracks` and `restore_track_values` (or the channel and state variants) are smaller.
5. One change at a time, then read it back. Stay inside the delta caps in the spec sheet.
6. Deleting things in the open session is not supported. If asked to delete a channel, track or pattern, ask the human; do not look for a trick. The one exception is a sandbox copy of a file: `apply_project_standard` can drop channels that play nothing and sit on no mixer insert, and it lists silent channels that do sit on an insert without removing them.

## What `verified: false` means

FL accepted the call but the value did not change (or changed to something else). This happens: some writes are ignored while FL is busy or when a control is locked. Do this:

1. Do not repeat the same write in a loop.
2. Read the current value with the matching read tool.
3. If it is unchanged, check `undo_last_verified` has not undone it, and check you addressed the right index.
4. If it still fails, use the GUI route (`gui-fallback`) or ask.

## Common jobs

| Job | Tools |
| --- | --- |
| Levels in dB | `set_track_volume_db_verified`, `get_track_peak_db`, `apply_gain_trim` (capped), `set_rough_balance` (many at once) |
| Pan and width | `set_track_pan_verified`, `set_track_stereo_sep_verified`, `set_channel_pan_verified` |
| Mute and solo | `mute_track_verified`, `solo_track_verified`, `solo_group` then `restore_solo_group` |
| Names | `set_track_name_verified`, `set_playlist_track_name_verified` |
| Routing | `route_channel_to_track_verified`, `create_send_route`, `set_route_level_verified`, `build_bus` |
| Tempo | `set_tempo_verified`, `set_tempo_and_swing`; confirm by readback |
| Transport | `ensure_playing`, `ensure_stopped`, `ensure_loop_mode`, `set_song_position_verified` (the API only toggles play and loop, so these check state first) |
| Markers | `add_time_marker_verified` |
| Plugin parameters | see the `sound-design-recipes` skill |
| Notes in the piano roll | `write_notes_via_script`, then run the script (GUI recipes), then `check_notes_written` |

## Reading a project you did not build

1. `read_project_anatomy` on a sandbox copy first: channels with Layer children, inserts with routes and effect slots, automation and controller links by name, every arrangement (the current one is the one FL plays), markers. Its summary lines say which buses take which inserts and what drives what.
2. `check_project_health` next: orphan automation, meters and recorders left in chains, unnamed channels, empty inserts, plugins not in this FL edition (config `fl.not_owned`), and with a parameter snapshot a master that can pass 0 dBFS.
3. `snapshot_project_params` reads every effect parameter live (about 80 ms a call; pass only the inserts you need). `tools/dump_project_live.py` writes it to a JSON file for `check_project_health`.
4. Renders refuse a project that uses a plugin in `fl.not_owned` (FL would wait on a trial dialog) and stop FL when no WAV appears for a few minutes (the stall limit). Remove or replace such a plugin in a sandbox copy before rendering, and say so in the report.

## Organizing and buses

1. `apply_project_standard` writes a sandbox copy with house names, colours and groups (`docs/PROJECT_STANDARD.md`). The person opens that copy.
2. `build_family_buses` then works in the open session: `list_family_inserts` reads the saved copy, `check_open_project` confirms FL has that project open by comparing insert names, `route_tracks_through_bus` sends the family through its bus and turns the direct master route off, `set_track_color_verified` colours the bus. It stops without writing if the open project differs.
3. FL has no save call. Ask the person to Save As a new name, then read the saved file back: FL rewrites it, and it is the only proof of what FL keeps.
4. Facts that cost a cycle: a send defaults to 0.8 in FL (not 1.0); FL returns colours as signed integers with an alpha byte; an insert, channel or playlist-row colour is shown only when the appearance flag in the file is set; channel rack group names are sorted by FL, so stored indices must follow the sorted order.

## Sidechain

There is no documented API for sidechain routing. Treat a sidechain as a GUI task or ask the human. Do not claim it is set.

## Ask when

- The target track or channel is ambiguous (two names match).
- A change is larger than the delta cap, or is irreversible by value restore.
- Verification keeps failing after one different attempt.
