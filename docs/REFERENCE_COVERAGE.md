# What we learned from the Future House reference, and the recipe for each

Every technique found in the reference (`docs/REFERENCE_FUTURE_HOUSE.md`), the module or recipe that does it in any project, and how far it is
proven. "Render" means checked on a render of a project; "tests" means unit tests only. Updated 2026-10-25.

The whole set runs in one step with `apply_production_recipe` (recipe `recipes/production/club_house.json`), on any FL-saved arrangement with
time markers and parts named by role. First checked off the remix on the reference itself with its own automation and pump switched off
(`sandbox/offsong/fh`, `fh2`): every move applied, FL rendered it, and the pump on the new music bus deepened the beat dip from 7.0 to 10.9 dB.
Section gains are not applied blind (the same map moved two songs' builds 3.7 and 6.2 LU): the contrast loop renders, reads
`measure_section_levels`' contrast and scales the map. On the demo one turn took the drop from 2.5 to 4.9 LU over its buildup (target 4.5).

## Routing

| Reference | Recipe | Proven |
| --- | --- | --- |
| Drum Group bus for kick, clap, hats | `create_bus_routing` kind drums (Drum Bus), skipped when the family Drums Bus exists | read back; FL renders the result |
| One music bus (Sidechain) for vocal chops, keys, mid bass, outro synth, carrying filter, throw reverb and pump | `create_bus_routing` kind music (Music Bus); chain `music_bus` puts the reference's filter and reverb on it | read back; the pump on it measured on a render |
| Sub, fills and FX skip both buses | the music kind takes chops, vocal, stab, arp, reese, bass and synth only | tests |
| Every reverb an insert effect with its own cuts, no send buses | the chains place reverbs as insert effects | tests (FL readback of 3 effects earlier) |

## Pumping (the "sidechain")

| Reference | Recipe | Proven |
| --- | --- | --- |
| One Envelope Controller, triggered by the kick pattern, linked to Love Philter on the music bus, sub and three FX inserts | `build_volume_pump`: a clip on a Fruity Balance per insert, dipping on every kick (the controller itself cannot be copied: a byte-identical copy did not drive) | render (Friends and the off-song pass) |

## Automation (all 18 clips)

| Reference clip | Recipe | Proven |
| --- | --- | --- |
| Fruity Filter cutoff on the music bus (high-pass rise into the drop) | `filter_sweep` | render (small effect) |
| Reeverb 2 wet and dry on the music bus (throws) | `reverb_throw` (wet swell, dry dips to 82%) | render (the dry dip measured 2 to 3 dB on the last beat) |
| LP on the mid bass opening over the build | `lowpass_open` (the reference's Love Philter) | render (noise centroid 0.1 to 5.2 kHz over 4 bars) |
| Vocal chop low-pass and output volume rides | `lowpass_dip`; levels by `apply_section_gains` | dip: tests (same plugin and knob as lowpass_open); section gains: render |
| Sub fades in for the drop | `fade_in` | render |
| Mid bass output volume rides | `apply_section_gains` | render |
| Gross Beat time slot on the vocal chops (stutter and halftime patterns) | `stutter_fill`, `reverse_fill`, `tape_stop`: what every slot of the reference's bank does was measured (`plugins/grossbeat_vc_bank.json`) | render (each fill did what its slot was measured to do) |
| Gross Beat "Bass Reverse" on the mid bass | measured: that Gross Beat's time mix is 0%, it changes nothing; `reverse_fill` does the move | render |
| Balance on the mid bass (a short gap) | `gap` | render |
| Balance on the master (a small dip before the drop) | `apply_section_gains` on the master, before its limiter | render |
| Snare channel pitch over the build | `pitch_rise` (a pitch clip spans -48 to +48 semitones, measured) | render (+12 semitones reached) |
| Harmless filter: one one-beat clip placed 64 times | `filter_wobble` (one clip, placed every `period` beats) | render (centroid 0.5 to 6.4 kHz each beat, open after the last copy) |
| Lead synth filter in the outro | `lowpass_dip` or `lowpass_open` on its insert; a generator knob directly with `add_automation_clip` | tests |
| Control Surface macro switching drum-bus Multiband and Flanger in | `fx_swell` (the reference's flanger faded in on the drum bus, held neutral from the song start) | renders; the flanging itself not separated by measurement |
| Two orphan clips linked to nothing | `check_project_health` reports them | tests |

Two things the renders taught (2026-10-25, `sandbox/offsong/moves`): FL holds a knob at a clip's last value, so a wobble clip that ended closed
left the part filtered after it (it now ends open); and before its first clip a plugin plays as saved, so the reference's flanger (saved at wet
-7 dB) flanged everything until its first swell (an init clip now holds it neutral). The transition instances on one insert cost about 1 dB
together on noise; gain staging takes it back.

## Effect chains

All 15 part chains (vocal chops, kick, clap, hats, crash, drum bus, keys, mid bass, sub, music bus, FX, crash wash, low hits, lead, outro synth)
are in the effect library (75 entries); the tone chains are recipes by role in `plugins/chains.json`, put in with `apply_fx_chain`. Left out on
purpose: the master chain (its limiter sits above 0 dB and clips) and automation targets, meters and Edison. Three injected effects read back
in FL with 0 of 79 parameters different; whole chains on a new song: tests, to be heard.

## Sound design

| Reference | Recipe | Proven |
| --- | --- | --- |
| Kick: Layer of three samples on one insert, pitched down, different filters | `build_layer_channel` with `stack` (band top or body, pitch, pan, level) | render |
| Claps stacked, two panned and pitched up; hats and shakers stacked | `build_layer_channel` stacks with pan and pitch | tests |
| Bass: Layer of a sub and a mid bass on two inserts | `build_layer_channel` | tests |
| Keys with a texture sample on the same notes | `build_layer_channel` | tests |
| Drum samples tuned by channel pitch | `apply_drum_tuning` | render (kick F# to E) |
| 3x Osc noise risers, downlifter, Wow Synth impact | `add_transition_synths` (the reference's patches) | render (shapes) |
| Vocal chops played as a melody | the chop recipe (`editable-first`) | render (Friends) |
| Snare build pattern | the drum plan | render (Friends) |
| One-shot FX audio around transitions | the generated FX bed; editable synth risers above | partial |

## Organization

Channel groups including Automation, the automation row block, names and colours: `apply_project_standard` (FL readback). Not done: a second
arrangement for variants, a NoteBook entry and the project metadata fields.

## Not yet proven on a new song

The production pass has run on the reference itself (own production off) and on synthetic projects. A second song from the person, end to end
(plan, build, production pass, gain staging, master), is the real test.
