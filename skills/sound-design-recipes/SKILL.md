---
name: sound-design-recipes
description: Use for building or changing sounds with the plugins the user owns: reading a plugin's parameter map, applying a named recipe, proposing a new recipe, and saving it after the user approves.
---

# Sound design with recipes

A recipe is a named set of plugin parameters for a plugin the human owns. Recipes are data files, stored in `recipes/<name>.toml`. Whether a sound is good is the human's call (a V1 gate).

## Steps

1. Find the plugin: `find_channel_by_name` or `find_track_by_name` for the index. Plugins on the channel rack and in mixer slots are addressed by `index` and `slot_index`.
2. Learn the controls: `list_plugin_params` then `build_param_map`. Parameter names can be empty or repeated; skip empty names and use `get_plugin_param_by_name` to read a value.
3. Read an existing recipe if one fits (a file under `recipes/`). If none, propose one: a short list of `name: value` pairs with a sentence on why each moves the sound toward the request.
4. Snapshot: `snapshot_state`.
5. Apply with `apply_param_recipe` (many) or `set_plugin_param_by_name` (one). Values are normalized 0 to 1. Each write is read back; stop on the first `verified: false`.
6. Audition: render a short section (`prepare_for_render`, `render_via_cli`, `restore_after_render`) and measure the relevant band or dynamics (`measure_band_energy`, `measure_crest_factor`) so the change has numbers.
7. Ask the human to listen and decide: keep, adjust, undo (`rollback_to`). Use `ask_human` with options.
8. When approved, offer to save the recipe. Write it with `write_report_file` into `recipes/` only if the human agrees, using plugin parameter names so it survives index changes.

## Choosing the sound for a synth part (stab, arp, sub, lead)

The person, 2026-10-26: "when we use Serum we do not stick to specific presets. We generate our own sounds that sonically match the original song: same tone, key, attack, sustain... we musically match what exists and then do interesting and unique things." Order:

1. **Measure what the original's part sounds like**: `measure_part_sound` on the stem that carries it ("other" for keys and guitars, the bass stem, the vocal for a sung bass), over a stretch where the part plays clearly, with its `role`. It returns the note envelope (attack, hold, decay, sustain, release; notes cut off by their length are told apart from notes that die away), brightness and how it moves after the attack, the harmonic series of the clearest notes, noise, width, register, plain words for the creative brief, the measured notes for an audition, and a first serum-mcp draft. A chord part has no single harmonic series: choose the table by ear from the shape and brightness, or cut one clear note as a sample source. Read the draft's notes (the octave check, the cutoff starting point).
2. **Design the sound with the Serum MCP**: read its own skill first (`sandbox\third_party\serum-mcp\skill\serum-sound-design\SKILL.md`), then `generate_preset` from the draft, named `CP - <Song> <Part>`, with `subfolder` `sandbox/<song>`, and `describe_preset` to read it back. Then one creative change that suits the remix (a little more bite for a drop, a filter that opens with the build), said out loud.
3. **Hear it and compare, before FL**: `render_serum_sound` (Serum 2 headless) on the draft's audition notes, then `compare_part_sound` (the original stretch against the render). Change what its list says with `edit_preset` and render again; three rounds at most, then the person's ear decides. Width on a near-sine part comes from chorus or reverb, not unison: two detuned voices on a sine beat (the Girls hook, 2026-10-26). A sound is judged in the mix, never alone: the numbers make the base sound belong to the record, the mix decides the rest.
3a. **The record's own cycles as the table** (skill `serum-wavetables`): when the stem holds a clean held note, `build_wavetable` reads it
   pitch-synchronously into a real table (phases kept, bleed averaged out) instead of harmonic levels only; a sound that must stay itself
   (a vocal phrase, a kit hit) goes on Serum's sample oscillator through `prepare_sampler_sound`.
3b. **The loop as one tool**: `match_part_sound` does steps 1 to 3 for a part (it generates with serum-mcp's own code through `generate_serum_preset`, renders, compares and revises the envelope, cutoff, width and octave for up to three rounds, and keeps the round nearest the original); `tools/remix_song.py --match-sounds` runs it for every synth part of a remix. It matches; the twist is still yours to add and to say.
4. **Put it on its channel**: `build_remix_project` option `serum_states` (`tools/remix_song.py --serum-state stab=FILE.serumstate`) writes the state Serum saved in step 3 into a Serum 2 channel; nothing is loaded by hand. Until the first FL load of such a project has been checked with the person present (`docs/SERUM_MCP.md`), say that it is the first one.
5. **The person's library is a reference, not the default.** Their presets ("PL Crusty Pluck [LCV]", "CP - Deep Sub", "ARP - Jno Style") show what they like; use them as a starting point for a design or as the fallback when generation fails, not as the sound of every song.
6. **Check timing before blaming it.** When a part "feels off", render it alone and run `measure_part_timing` against its notes. On-grid onsets mean the problem is the sound or the pattern, not the timing; say so instead of moving notes.
7. Serum plays at true pitch and does not change level with velocity: do not carry a Sytrus key offset over, and do not rely on velocity for soft passages.
8. **Serum 2 is the synth when it is installed** (chords: "PL Crusty Pluck [LCV]", the person's own swap on the techno remix, 3.5 dB under the old stab) (the person, 2026-10-25: "when available, you should use Serum 2 for high-quality synthesizers"). A part with a generated sound (steps 1 to 4) gets it; the other parts are cloned from `options.serum_project` (default `sandbox\serum\serum_sounds.flp`, a copy of the project where the person chose their sounds) by preset name, and Sytrus is the fallback only when no such project exists. The report says which sound each part got (its serum and serum generated lists).
9. **Recreate the song's instruments, never crowd them.** When the synth plays the song's chords (from a tested reference MIDI, `midiref`), it plays the chord the song plays over each bass root, voiced as a close triad between A3 and A4, or root and fifth when the file is unclear or several guitars stack up, in the song's own strum. Never copy a transcription's full piano and guitar parts: stacked voicings across the same register are what makes a remix muddy. Where the original's own instrumentation stem plays (`Original Instruments`), the synth chords rest, so the two never double.
10. **Transition effects are saved neutral.** A swell plugin (the drum-bus flanger) plays as saved wherever no clip drives it, which is every playback started mid-song: save it dry, and leave the flanger swell out unless asked (the person switched it off as too persistent, 2026-10-26).

## Instruments from the FL demo songs

The option bank's sound options (`src/coproducer/data/options/sound.json`, 51 of them, `docs/DEMO_STUDY.md`) are the demo songs' instruments as their designers left them: the plugin, the FLEX preset, the insert chain, the register, the channel to import, and from the solo renders the measured sound (attack, decay, sustain, brightness, width, words) with a Serum starting point.

1. **As a direction for Serum** (the default when Serum 2 is installed): `match_part_sound` with options.direction set to the option's measured sound. soundbrief.blend keeps the original part's harmonics, brightness and register and takes the demo instrument's envelope, gating, filter movement and width. The match converges on that blend: the record's tone, played the way the demo plays it.
2. **As the instrument itself** (no Serum, or the person asks for the demo patch): the plan's instruments entry makes `build_remix_project` import the channel (up to three layers of a stack) from the demo's render copy in sandbox/demo_study/render and move the part's notes into the instrument's own register.
3. Stacks are the lesson most demos teach: three kicks, three to six claps nudged a few milliseconds apart, eight synths of three kinds on one trance lead, four bass layers each covering a band. When one patch sounds thin, layer two plain ones before reaching for a bigger patch (`build_layer_channel`).
4. FLEX presets carry macros (Space, Metal, Plucked, OSCEX, TuneX): melodic techno moves them across a phrase; set and automate them with `set_plugin_param_by_name` and `add_automation_clip`.

## Layers, tuning and transition patches (from the Future House reference)

1. **Layer instead of hunting for one perfect sample.** The reference's kick is three samples under one Layer channel on one insert (two pitched 1 to 2 semitones down, different fade-outs), its bass a sub and a mid bass on separate inserts. `build_layer_channel` adds the Layer, copies a sampler for each extra file (`stack`, same insert and settings, its own level and pitch) and moves the part's notes onto the Layer. The Layer stays at 100% (its volume scales everything it plays); set the levels on the children. A layer's `band` splits the work: `top` high-passes it to its click (corner about 4 kHz), `body` low-passes it to its sub (about 120 Hz). Two full-range kicks tuned to the same note add in phase (measured +2 dB), so a stack is louder: rebalance with `gain-staging` and judge it on a solo render.
2. **Tune drums to the key.** `apply_drum_tuning` reads each kick, tom or 808 body pitch from its file and sets the channel pitch knob to the nearest root or fifth (it widens the knob's range when needed; FL's default range is 2 semitones). Hats, claps and noisy samples have no clear pitch and are left alone. A texture layer on keys (the reference plays a scrape sample on the keys' notes) is a Layer too.
3. **Editable risers.** `add_transition_synths` adds the reference's 3x Osc noise riser, noise downlifter and impact chord as channels with notes, so a riser can be retimed, retuned or filtered in FL instead of re-rendering an FX bed. Their envelopes were set at 126 BPM; check the shape on a render.

## Rules


- When a generated sound is the target, match it with a synth patch the human owns and play it with notes (see `editable-first`) instead of keeping the audio.

- Only plugins the human owns and has loaded. Loading a plugin is a GUI task: use `load_plugin_gui` (see `gui-fallback`), never guess.
- If a control is not exposed as a parameter, use `open_plugin_ui_gui` and the screenshot-verified GUI tools for that one control.
- Change few parameters per round. Name what each is expected to do.
- Never overwrite an existing recipe without asking.
- Taste goes to the human; numbers go to the log.

## Ask when

- The request is purely descriptive ("growly", "warm") with no reference. Offer 2 or 3 interpretations, recommended first.
- A parameter name is ambiguous (two match).
- The plugin has no exposed parameters.
