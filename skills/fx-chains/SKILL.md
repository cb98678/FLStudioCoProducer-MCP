---
name: fx-chains
description: Use when adding or upgrading effect chains on parts and buses (EQ, insert reverb, compression, saturation, filters, pumping targets) from the effect library, or when asked to "make the vocals sit", "glue the drums", "give the bass grit", or "use the reference's effects".
---

# FX chains

Effects go into mixer slots as whole saved settings from the effect library, one part at a time, and every change is checked in FL and on a render.

## Order of work

1. Read the project: `read_project_anatomy` (which inserts hold which parts, what is already in each slot, which slots are free) and `check_project_health`.
2. Whole chains are recipes: `plugins/chains.json` names, per role (chops, vocal, kick, clap, hats, perc, stab, bass and reese, sub, arp and synth, fx) and for the music bus, the library entries in the reference's slot order, and why. `apply_fx_chain` puts them in by role in one step (or `chains` for chosen inserts), after what each insert already holds; an insert without room is listed, not changed. `references/chains.md` is the same table for reading.
3. For a single effect, find it with `list_effect_library` (filter by plugin or by text such as "vocal chop"; with the parameters option it shows the settings) and place it with `apply_effect_from_library`. Either way the source must be a project derived from an FL save.
4. Ask the person to open the copy (or open it after asking). Read each placed slot back with `get_plugin_param_by_name` or `snapshot_project_params` and compare with the entry's params; a mismatch means the injection failed, so stop.
5. Render before and after (`render_via_cli` with the person's permission) and measure what the chain was meant to change: `measure_band_energy` for EQ, `measure_section_levels` for level and section contrast, `measure_crest_factor` for compression, `measure_stereo_correlation` for width.
6. Compressors, distortion and saturation change level: rerun the part levels (`gain-staging`) after a chain goes in.

## Rules

- One part per pass; say which entries went where and what the measures did.
- Start from the recipe, then adjust single parameters with `set_plugin_param_by_name`, never by swapping whole chains blindly.
- Do not copy the reference master chain as a master: its limiter ceiling is +4 dB and it clips. Master with the `mastering` skill.
- Soundgoodizer settings cannot be read through FL's API; treat a Soundgoodizer entry as fixed and check it by ear and on a render.
- Skip entries for plugins this FL edition does not own (config `fl.not_owned`); `check_project_health` names them.
- Reverb goes in as an insert effect with its own low and high cut, as in the reference; long reverbs belong on FX and transition parts, short ones on drums.

## Ask when

- The part has no free slot, or the chain would replace effects the person put there.
- A chain changes the character of a part (distortion on a vocal, a flanger on the drums): that is the person's call.
