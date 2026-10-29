# Plan: skills and modules learned from the Future House reference

Coverage of every technique in the reference, with the recipe for each and how far it is proven: `docs/REFERENCE_COVERAGE.md`. The person's
correction (2026-10-25): the product is an MCP that remixes any song; Friends is a regression test, not the goal. Since then: file routing and
buses (`create_bus_routing`), chains as recipes (`apply_fx_chain`, `plugins/chains.json`), the missing automation moves (low-pass open and dip,
filter wobble, flanger swell, throw dry dip, Gross Beat fills from a measured slot map), and one production pass (`apply_production_recipe`,
`recipes/production/club_house.json`), checked on the reference with its own production off. Next: a second song end to end.

Status 2026-10-25: approved by the person (decisions at the end); being built in order. Findings it builds on: `docs/REFERENCE_FUTURE_HOUSE.md`. Done 2026-10-25: A1 to A4 and B5 to B7 (modules `read_project_anatomy`, `snapshot_project_params`, `check_project_health`, `measure_section_levels`; arrangement support in `flpfile`; render preflight and stall stop; solo split fixes). C done (effect library of 75 entries from the reference, `list_effect_library`, `apply_effect_from_library`, proven in FL: three injected effects read back with 0 of 79 parameters different; skill `fx-chains`). D done as automation-clip pumping (`build_volume_pump`, `measure_pump_depth`; the copied Envelope Controller did not drive, see docs/FLP_FORMAT.md). E done: `add_automation_clip` targets any slot, channel parameters and generator knobs, clips can be placed again (`automation.place_clip_copies`); `add_section_markers` and `add_transition_automation` (filter_sweep, reverb_throw, pitch_rise, fade_in, gap). Renders on the tech-house v14 copy: the sub fade-in rose from -46.6 to -19.8 dB over the build, the gap silenced the beat before the drop (-51 dB against -31.6), the reverb throw and high-pass sweep changed the parts slightly, and the size of the pitch rise on a plugin channel could not be confirmed by measurement. F done 2026-10-25: `build_layer_channel` (a Layer from the reference's own block, stacked samplers with a `band` of top or body), `apply_drum_tuning` (kicks, toms and 808s to the nearest root or fifth by the channel pitch knob), `add_transition_synths` (the reference's 3x Osc noise riser, downlifter and impact chord as editable channels), the builder writes the plan's sections as time markers, and the house standard puts automation clips in an Automation group and a row block below the music. Checked on renders of the v14 master copy (`sandbox/fcheck`): the kick moved from F# (46.4 Hz) to E (41.4 Hz); a Layer at 100% plays exactly as the kick alone and a high-passed top kick adds 2.2 dB of click band; the snare pitch rise reached +12 semitones at the drop; the riser climbs 4 bars (centroid 0.4 to 20 kHz), the impact lands on the drop beat and the downlifter falls over 4 bars; the full mix measured -11.84 LUFS, -2.36 dBTP, crest 7.92 (v14 8.14; the club target asks at least 8), correlation 0.966, with every section within 0.2 LU of v14. The section check also shows our drops sit about 1.5 LU under our breaks (Drop 1 -11.96, Break 1 -10.37), where the reference's drop is 4.5 LU over its build: a mix and arrangement task for later. Found on the way: a channel pitch clip spans -48 to +48 semitones whatever the knob range, a Layer's volume scales its children (FL's default 10000 cost 5.2 dB), and the channel filter's mapping (docs/FLP_FORMAT.md). The person approved the result by ear on 2026-10-25 ("it's good", after the A/B of build 1 into drop 1); the copy is kept as `sandbox\techhouse\FriendsInLowPlaces_TechHouse_v15.flp`. Not done: the optional second arrangement and a NoteBook entry. G done 2026-10-25 (skill `study-reference-project`). Section contrast, 2026-10-25: after the master, v15's drops were level with its builds and 1.5 LU under its breaks, although they led before the master (solo and master-bypassed renders in `sandbox/contrast`): the limiter at its ceiling pins the drops near -12 LUFS. New module `apply_section_gains` lowers builds and breaks per part and the whole build on the master Balance before Maximus; with the default role map in `sectiongain.py` the drops sit 3.4 to 3.8 LU over the builds and 1.9 to 2.6 LU over the breaks, true peak -2.88 dBTP, crest 8.89, integrated -13.0 LUFS. The person chose this contrast over the -11.5 +/- 1 loudness target (2026-10-25); the copy is `sandbox\techhouse\FriendsInLowPlaces_TechHouse_v16_contrast.flp`.

## Gap map

| Technique seen in the reference | What we have | Gap |
| --- | --- | --- |
| Read a whole project: layers, chains, routing graph, automation targets by name, arrangements, markers | `read_project_summary`, `list_automation_clips`, `diff_flp_projects`, scratch scripts | No single anatomy reader; links to plugin slots, channels and controllers are not resolved to names; only the first arrangement is read |
| Every plugin parameter, live | `list_plugin_params`, `get_plugin_param_by_name` (one plugin at a time) | `tools/dump_project_live.py` exists but is not a registered module |
| Effect chains per part (EQ, insert reverb, serial compression, saturation, transient, stereo per band) | `apply_eq_recipe` (mixer EQ), `apply_param_recipe` (an already loaded plugin), `load_plugin_gui` (channel rack only) | No way to put an effect into a mixer slot except by hand; no chain recipes |
| Pumping with an Envelope Controller driving Love Philter on several inserts | `setup_sidechain_route` and the sidechain GUI modules (compressor sidechain) | No volume-shaper pump; no controller links |
| Automation on plugin knobs in any slot, channel pitch, generator knobs; one short clip reused many times | `add_automation_clip` (mixer volume, pan, width, mixer EQ, plugin in slot 0) | Slots above 0 untested; no channel or generator targets; no reuse; no transition recipes |
| Layer channels (kick of three samples, bass of two synths) | One sampler or synth per part | No Layer channel builder |
| Drum samples tuned by channel pitch | None | No tuning step |
| Noise risers and transition synths from 3x Osc; keys plus a texture sample on the same notes | Generated FX bed audio (`coproducer.fxbed`) | No editable riser patches; no texture layering |
| Time markers, two arrangements, automation rows parked at the bottom, Audio and Automation groups, a NoteBook with notes | Time markers live only (`add_time_marker_verified`); house standard groups Drums to FX | Builder writes no markers; standard has no Automation or Audio group or row block |
| Measuring a pro mix by part and by section | `split_part_projects`, `measure_part_levels`, `render_folder_via_cli`, `build_measure_report` | Solo splits break on Layer channels and controllers and keep the master chain; section reports are song-specific |
| Project hygiene (orphan clips, clipping master, unused plugins, trial plugins, unnamed channels) | `apply_project_standard` check covers names and colours | No health check |

## Proposed work, in order

Each item is a module (or a fix) plus tests, then the skill text. Order is by what unblocks the rest.

### A. Read any project correctly (foundation)

1. `flpfile`: support several arrangements; read the current one (event 100) everywhere (playlist items, clips, markers), with tests from a two-arrangement fixture. Unblocks every reader and the part-level loop on projects like this one.
2. Module `read_project_anatomy` (reads files, L3): channels with type, Layer children, plugin, insert, group, tuning; inserts with name, colour, routes (handling FL 26's trimmed routing event), effect slots by name; automation clips with targets resolved to "insert, slot, plugin, parameter" or "channel, parameter" or "controller"; arrangements with markers and named rows. Refuses FL 20 files with a clear message (re-save in FL 26 first).
3. Register the live dump as module `dump_project_params` (reads FL, L2): the same data as `tools/dump_project_live.py`, writing JSON under the sandbox.
4. Module `check_project_health` (reads files): orphan automation clips, master chain that can exceed 0 dBFS (limiter ceiling above 0 dB), empty inserts, Edison or meters left in chains, unnamed channels, plugins not in the person's edition (from a list the person confirms), alternate arrangements. Feeds the organizer and the pre-render check.

### B. Render and measure safely

5. Pre-render check: list the plugins of a project and stop with a message when one is known to raise a dialog (trial or missing). Detect a stalled command-line render within a minute or two (no new WAV and FL idle) instead of the 40-minute timeout.
6. `partmix` fixes: keep Layer parents of an enabled child, keep controller channels (Envelope Controller, MIDI Out), and offer solos with the master chain bypassed, so part levels mean the same thing in every project.
7. Generic section report from the project's own time markers (replacing the song-specific `tools/render_report.py`).

### C. Effect chains

8. Plugin-state library: copy an effect's saved state (its event group: name, wrapper, state) out of a reference project into `plugins/library/` with the source and parameter text, and inject it into a mixer slot of an FL-saved sandbox copy (`inject_effect_state`). Proven only when FL loads the copy and the live parameters match the library entry. Fallback: `load_effect_in_slot_gui` (the slot menu, as done by hand for Maximus).
9. New skill `fx-chains`: the part chains from the reference written as recipes with the reasons (high-pass first, narrow cuts 150 Hz to 1 kHz, insert reverb with 240 Hz to 6 kHz cuts and short decays on drums, serial compression on vocals and keys, distortion and saturation on the mid bass, band-wise width on the master), each tied to a library entry and checked by render, not by preset name.

### D. Pumping

10. Module `build_volume_pump`: an Envelope Controller channel (state from the library), triggered by a kick-rate pattern, linked to one gain-type parameter on each chosen insert (Love Philter as in the reference, or Fruity Balance), written into an FL-saved sandbox copy; verified by a render showing the dip at each kick. Skill text in `mix-engineer` beside the compressor sidechain, with when to use which.

### E. Automation recipes

11. Extend `add_automation_clip`: any slot (prove the slot field by render), channel parameters (pitch, volume), generator knobs, and placing one clip many times.
12. Module `add_transition_automation` driven by the time markers: filter sweep into a drop, reverb throw at the end of a section, rising snare roll pitch, sub fade-in for the drop, gap before the drop, stutter on the last bar. Each recipe names its target type and is checked on a render around the marker.

### F. Sound design and arrangement

13. Module `build_layer_channel` (kick or clap stack, bass layer), with the Layer channel triggering existing channels on one insert.
14. Tune drum samples to the key by channel pitch (`tune_samples_to_key`), measuring each sample's pitch first.
15. Editable risers and transition synths from 3x Osc states in the library; texture layer on keys.
16. Builder and standard: write time markers from the song plan, park automation clips in a bottom row block, add Automation and Audio groups, optional second arrangement for variants, a NoteBook entry with the build notes.

### G. Procedure skill

17. New skill `study-reference-project`: the procedure used here (copy, file anatomy, live parameters, pre-render check, render with markers, measure by section and part, critique, gap map), so the next reference is studied the same way.

## Decisions (the person, 2026-10-25)

1. Order approved as proposed: A and B first, then C, D, E, F, G.
2. Plugin settings from this demo may be saved into our library for our own builds (settings only, no audio).
3. The house standard gets an Automation group and a block of automation rows at the bottom of the playlist (item 16).
4. Its section contrast (Buildup -12.8 LUFS, Drop -8.3) and band balance are reference values; its loudness is not, because it clips.
