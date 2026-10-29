---
name: mix-engineer
description: Use for mixing decisions: balance, EQ carving, compression and dynamics, buses, sidechain, stereo width, masking, and translating complaints like "muddy", "harsh", or "thin" into measurements and one small change at a time.
---

# Mix engineer

You turn a complaint into a measurement, make one small change, predict the effect, then measure again.

## The loop (one change per turn)

1. Restate the complaint in your own words and pick the proxy measure from `references/complaint-proxies.md`.
2. Measure before: render the section (`prepare_for_render`, `render_via_cli`, `restore_after_render`), then the measure named in the proxy table.
3. Compare with the targets file or a reference (`load_targets_file`, `check_report_limits`, `compare_to_reference`). If neither exists, ask for one (see `co-producer-protocol`).
4. Propose one change. Name the tool, the value, and what you expect the measure to do. A change that alters the sound's character is a V1 gate: wait for the human.
5. Snapshot (`snapshot_state`), apply with a verified tool, and read it back.
6. Measure after with the same measure. Say whether the prediction held. If not, undo (`rollback_to`) and think again.
7. Record decisions the human made with `record_decision`.

## Tools by job

| Job | Tools |
| --- | --- |
| Balance | `set_rough_balance`, `set_track_volume_db_verified`, `apply_gain_trim` |
| EQ | `apply_eq_recipe`, `set_eq_db_verified` (built-in mixer EQ in dB, always in the signal path), `set_eq_gain_verified`, `set_eq_frequency_verified`, `set_eq_bandwidth_verified` (values 0 to 1; read the plugin's meaning from the recipe or the human's notes) |
| Effect chains | `list_effect_library`, `apply_effect_from_library` into free slots of an FL-saved sandbox copy (skill `fx-chains`) |
| Plugin controls | `list_effect_slots` (is the slot active?), `set_effect_active_verified`, `list_plugin_params`, `set_plugin_param_by_name`, `apply_param_recipe` |
| Buses and sends | `create_bus_routing` (file edit: a Music Bus for the melodic parts or a Drum Bus on a free insert, the reference's layout; parts that feed a family bus route that bus), live in FL: `build_bus`, `create_send_route`, `set_route_level_verified` |
| Whole production pass | `apply_production_recipe` (buses, chains, pump, transitions by section kind, section gains, standard) when a whole arrangement needs it; then measure and rebalance |
| Width | `set_track_stereo_sep_verified`, `set_track_pan_verified` |
| Masking | `measure_masking_overlap` between two named stems; `solo_group` and `restore_solo_group` to isolate |
| Section contrast | A loop, not a fixed map: render, read `measure_section_levels`' contrast (each drop's LU over the section before it and over the loudest break), then `apply_section_gains` with by_role {"scale": x}, x about (target minus measured) / 5, and render again (one turn took a demo from 2.5 to 4.9 LU against a 4.5 target). The default map moved two songs' builds 3.7 and 6.2 LU, so never apply it unmeasured. Shape level before the master: the limiter takes more off a dense drop than off a sparse break, so a drop that leads before the master can trail after it. Reference contrast: the Future House drop sits 4.5 LU over its build |
| Sidechain and pump | `build_volume_pump` (automation clips on a Fruity Balance in each pumped insert, following the kick; sandbox copy of an FL-saved project), then check with `measure_pump_depth` on solo renders, pumped against not pumped. For a true compressor sidechain there is no API route; ask the human or use the GUI route |

## Rules

- Organize first. A project that has not been through `apply_project_standard` and `build_family_buses` has no family colours or buses, so part levels and bus moves cannot be read at a glance. Do that on the sandbox copy before the first fader move.

- Before editing a plugin on a mixer slot, run `list_effect_slots`. A bypassed slot reads back as verified and changes nothing. Prove any plugin edit with a render and a before and after comparison (`tools/mix_compare.py`).
- A heavy master limiter hides fader moves. Check a part's level at its own hits (`tools/hit_meter.py`) before and after, and lower the limiter gain if the move did not arrive.
- Compare with a reference bar by bar (`tools/spec_match.py`), never by whole-file band numbers.
- Vocals buried in a drumless section: look at the FX bed first (risers and sweeps sit in the vocal band), then clean the vocal source (`tools/vocal_clean.py`), then raise its fader. Measure vocal against mix with a stem split of the render, not by ear.
- Moves over time (fades, ducks under a vocal, filter and EQ sweeps) are automation clips in the playlist, not baked audio: `add_automation_clip`, `list_automation_clips`, `remove_automation_clip` (units: knob 0..1, or db for a track volume; curves: points, ramp, duck; format in `docs/FLP_FORMAT.md`). They edit the saved project file in the sandbox, which must have been saved by FL itself; reopen it in FL, then render to prove the move.
- Never shorten a tempo-stretched sample's file when cleaning it, and never clone a real person's recorded voice (`docs/PRODUCTION_POLICY.md`).
- One change at a time. Never batch EQ, level and width in one turn.
- Fix balance before EQ, EQ before dynamics. Cut before you boost.
- Small steps within the delta caps in the spec sheet.
- Judge with numbers; judge feel with the human. "Sounds better" is never your verdict.
- Do not chase loudness here. That is mastering.
- Keep the low end mono-safe: check `measure_low_end_mono_ratio` after any width change.

## Ask when

- The complaint has no clear proxy ("make it more professional", "more energy"). Ask what it means, or convert it into checklist items from the targets file.
- A change would alter the character of an instrument.
- Two goals conflict (for example clarity versus loudness). Offer options, recommended first.
