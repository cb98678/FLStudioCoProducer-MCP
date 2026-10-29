# Serum 2, the Serum MCP and generated sounds

Status 2026-10-28 (wavetables and the sampler added; the route below dates from 2026-10-26). The person's rule: "when we use Serum we do not stick to specific presets. We generate our own sounds that sonically match the original song: same tone, key, attack, decay ... we musically match what exists and then do interesting and unique things." This file records how a sound goes from the original record to a Serum 2 channel in the remix project, what was proved on rtxclub, and what is still open.

## The route, step by step

| Step | Tool | Proved |
| --- | --- | --- |
| 1. Read the part in the original | `measure_part_sound` on the stem that carries it (a stretch where it plays clearly) | Synthetic tests; Curse of Curves bass and other, Girls other read 2026-10-26 |
| 2. Design the sound | serum-mcp `generate_preset`, starting from the draft step 1 returns, written to subfolder `sandbox/<song>` of `Presets\User` | serum-mcp's own tests; its presets load in Serum (2026-10-24) |
| 3. Hear it without FL | `render_serum_sound` (Serum 2 under pedalboard, the `serum` model) on the audition notes step 1 returns | 2026-10-26, see below |
| 4. Compare with the original | `compare_part_sound` (original stretch against the render), then serum-mcp `edit_preset`, at most three rounds | Synthetic tests |
| 5. Put it on a channel | `build_remix_project` option `serum_states` (`tools/remix_song.py --serum-state stab=FILE`): the state Serum saved in step 3 goes into a Serum 2 channel cloned from `sandbox\serum\serum_sounds.flp` | Offline (file rebuilt byte for byte); an FL load is the open check |
| 6. Judge it in the mix | Render the remix in FL, the person listens | Every remix |

Steps 1 to 4 are one tool for a part, `match_part_sound` (generating through `generate_serum_preset`, which runs serum-mcp's own code in its own environment, the `serummcp` model), and one flag for a whole remix, `tools/remix_song.py --match-sounds` (the stab and arp from the other stem, the sub from the bass stem). The revision between rounds is by rule: envelope times scaled by the measured ratios, the sustain set to the original's, the cutoff moved along serum-mcp's calibration by the brightness ratio, chorus for width, the octave for register; the harmonic shape is reported, not changed.

The draft is where the design starts. The creative move for the remix (a little more bite for a drop, a filter that opens with the build) is added on purpose in step 2 and said out loud; step 4 is there so the base sound belongs to the record before that move.

## What was proved on rtxclub, 2026-10-26

- **Serum 2 runs headless.** pedalboard 0.9.26 (in its own environment, `coproducer install-models serum`) loads Serum 2.1.5 from the binary inside the bundle, `C:\Program Files\Common Files\VST3\Serum2.vst3\Contents\x86_64-win\Serum2.vst3`, with `plugin_name="Serum 2"` (the file also holds "Serum 2 FX"). The bundle folder itself does not scan. It plays MIDI notes and returns audio.
- **The state format.** pedalboard keeps a VST3 state as JUCE binary XML (magic `VC2!`, a length, `<VST3PluginState>` with the IComponent and IEditController streams in JUCE's own base64, a null byte). Rebuilt byte for byte from its parts. FL keeps the same two streams in the Serum channel's plugin event (chunk 53, records 3 and 2); the layout is written up in `src/coproducer/serumstate.py`.
- **A preset file becomes a working state.** The serum-mcp preset "CP - Deep Sub", split into the two streams by `serumstate.inject_preset`, rendered the same audio as the state Serum itself wrote for that preset in FL: difference -73 dB, correlation 1.00000 (`sandbox\diag\serum_pedal_probe.py`, output in `sandbox\diag\serum_probe`). Serum then re-saved it in its own format version (11.0); that re-saved state is what step 5 writes into the project.
- **The whole route on a real part.** The Girls hook synth ("other" stem, 30 to 90 s): read as a near-sine C5 bleep, 6 ms attack, plucked (time to -20 dB 0.33 s), a burst of 4th, 6th and 8th harmonics on the attack, narrow. serum-mcp wrote "CP - Girls Hook" (`Presets\User\sandbox\girls`) from the draft: the measured body and attack frames as its wavetable, an envelope moving the table from the attack frame to the body, TONE and BITE macros, chorus and reverb. Three rounds of render and compare (`sandbox\diag\sound_match\girls`): attack 0.9x, decay 0.83x, brightness 0.99x, same register; the upper harmonics still fall about 5 dB per octave faster and it is narrower than the record. Round 2 tried two unison voices for the width and was worse: two detuned voices on a near-sine beat, which read as a slow attack and a held level. Not yet heard by the person.
- **FL loads them.** FL's command-line render opened `girls_nu_disco_v2` and `friends_deep_house_v2` (2026-10-26), whose stab, arp and sub channels hold states written this way, and rendered both to the end without an error. Whether each channel played its generated sound was not isolated (no solo render of those parts yet).
- **Still to look at with the person:** FL opening a project whose Serum channel holds a state written this way. FL passes the state to the plugin unchanged and every other byte of the channel is kept, so the risk is low, but it is checked once with the person present, as for any generated preset (serum-mcp's own notes say an early preset of theirs crashed FL): open `sandbox\serum\serum_inject_test.flp` (a copy of `serum_sounds.flp` with one more channel, "Girls Hook (generated)", written from the state above), play a few notes on that channel, and check that Serum shows "CP - Girls Hook".

## Wavetables and the sampler, from the song's own material (2026-10-28)

The person: "make skills on how to use the MCP Serum 2 for Wave tables. we want to be able to extract sounds or vocal or even drum sounds
and basses and use them in the song using serum 2". Skill `serum-wavetables` has the steps; this is what was built and proved.

| Need | Tool | serum-mcp field |
| --- | --- | --- |
| A pitched part as a playable table (bass, riff, held note) | `build_wavetable` (path): the longest held note, every harmonic fitted over four whole periods per frame, each cycle rebuilt at 2048 samples, frames phase aligned, the wrap at the quietest point | `wavetable` (a path under Serum's Tables, exact) or `sample_source` with `sample_frames` (serum-mcp fades 64 samples at each frame edge; the tool reports that as edge_loss_db) |
| A table from math | `build_wavetable` (formula; Serum's x, w, y) | the same |
| A sound that stays itself (vocal phrase, kit hit, bass note) | `prepare_sampler_sound`: a 24-bit WAV cut, its pitch, level, balance, transposition and sustain loop | `sample_playback_source` |
| A whole loops folder | `tools/serum_tables.py --loops sandbox\loops\SONG --section S --install-tables`: tables, sampler plans and one spec per sound | |
| Spec parts | `src/coproducer/serumspec.py`: pluck, chop, duck, macros, room, dirt, assemble | envelopes, lfos (curve), macros, mod_routes with aux_source, fx_chain |

Facts found in serum-mcp's own code (commit eada85a) and used:

- `sample_source` slices evenly: starts at linspace(0, length - 2048, frames), each slice faded over 64 samples and normalised to 0.9
  (`preset/wavetable.py`). A file of exactly frames times 2048 samples at 44.1 kHz is sliced on its frame starts.
- `wavetable` accepts any WAV path relative to Serum's Tables folder (`preset/mapping.py`, `_resolve_wavetable`); serum-mcp reads the
  frame count from the file. That is how an installed table is named.
- The sample oscillator plays a file at its recorded pitch and speed on MIDI note 60, pitch and length coupled (docs/PARAMETER_SCHEMA.md).
  `sample_center_pan` balances the channels' RMS; it does not centre or mono anything.
- Mod destinations are a confirmed list (`preset/schema.py` MOD_DEST_TARGETS): oscillator volume, pan, pitch, table position, filter
  cutoff and more, envelope times, LFO rate, an effect's wet, FXUtils level_out and width. Not a distortion's drive, a reverb's size or a
  compressor's gain.
- An LFO with its rate unset runs at Serum's default, a quarter note synced; a value for 1/16 is not confirmed (10.66 reads as 1/8). The
  chop draws 16ths as steps inside the quarter note.
- Distortion modes are kAsym, kDiode1, kDiode2, kDownsample, kHardClip, kLinFold, kOverdrive, kRectify, kSinFold, kSineShaper, kSoftClip,
  kSoftSat, kStompBox, kTapeSat, kXShaper, kXShaperAsym, kZeroSquare: no Tube.

Proved on rtxclub, 2026-10-28, from sandbox\loops\sorry_freejak (section drop_a): seven presets written by serum-mcp's generate_preset
into Presets\User\sandbox\sorry_freejak (bass table, music table, PM sub, morph stab, kick, hook chop; describe_preset reads them back),
four tables in Tables\User\sandbox\sorry_freejak, and headless renders (Serum 2.1.5 under pedalboard, `sandbox\diag\wavetables`,
measured by `sandbox\diag\wavetable_check.py`):

| Sound | Render |
| --- | --- |
| Bass table (read from F1, 43.6 Hz) | G1 on note 31, F1 on 29; harmonic levels 0.51, 0.63, 1.0, 0.03, 0.02, 0.63 against the table's 0.55, 0.65, 1.0, 0.03, 0.02, 1.0 (the low-pass at 0.45 takes the 6th down) |
| PM sub | a pure sine on G1 with Macro 1 at 0 |
| Morph stab, music table | G4, G#4 and D#4 on notes 67, 68 and 63 |
| Kick on the sampler | note 60: correlation 0.9994 with the kit kick (lag 0.09 ms), 8.6 dB under it at master 0.5 and osc 0.75; note 48: 1.96 times as long |
| Hook on the sampler with the 16th chop | its own pitch on note 60 (MIDI 76.8 against 76.6 in the cut); the gate at 8.0 Hz, 16ths at pedalboard's 120 bpm (it sends no tempo of the remix; FL at 128 gives 8.53 Hz) |

Still open: the person's ear; one FL load of a project whose Serum channel plays an installed table and a sampled hook; whether a macro
used as an aux source scales the pluck (written, not shown by describe_preset); the Serum 2 guide's own formula-parser page (its PDF is
behind a signed link this session cannot fetch; Serum 1's documented variables are used).

## Installing

- serum-mcp: cloned at `sandbox\third_party\serum-mcp` (commit `eada85a`, MIT, [Celian-mrc/serum-mcp](https://github.com/Celian-mrc/serum-mcp)), environment made with `uv sync --frozen`. Register it with Claude Desktop together with the co-producer servers: `coproducer install-desktop --with-serum` (entry `coproducer-serum`: `uv run --frozen --directory <clone> serum-mcp`, with `SERUM_PRESETS_PATH` at `Documents\Xfer\Serum 2 Presets\Presets\User` and its `Tables` and `Samples` beside it). The presets path stays at `Presets\User` because the server finds the Factory presets from it; generated presets go in the subfolder `sandbox/<song>` (the `subfolder` argument of `generate_preset`), so nothing of the person's library is touched.
- serum-mcp's generator for the pipeline (steps 2 and 4 without a chat): `coproducer install-models serummcp` (records the clone's environment; the clone stays at `sandbox\third_party\serum-mcp`, pinned to commit `eada85a`).
- The serum model (step 3): `coproducer install-models serum` (pedalboard 0.9.26, numpy, soundfile, zstandard, cbor2, all pinned in `src/coproducer/cli/stacks.py`). pedalboard is GPL-3.0 and runs as its own process; nothing of it is linked into the co-producer. Set `SERUM2_VST3` if Serum 2 is installed somewhere else.

## Serum 2 and serum-mcp facts

| Item | Value |
| --- | --- |
| Serum 2 | 2.1.5, user presets in `Documents\Xfer\Serum 2 Presets\Presets\User`, with `Tables` and `Samples` beside `Presets` |
| serum-mcp tools | `generate_preset`, `edit_preset`, `describe_preset`, `list_parameters`, `find_reference_presets`, `list_sample_files`, `analyze_sample_file` |
| serum-mcp skill | `sandbox\third_party\serum-mcp\skill\serum-sound-design\SKILL.md`: different tables per oscillator, macros that do something, loudness of sample-based presets, naming by role. Read it before designing. |
| Measured harmonics | serum-mcp's `custom_harmonics` builds a wavetable from a list of harmonic levels per frame; `measure_part_sound` writes the original part's levels there (attack frame, then body frame) |
| Cutoff | serum-mcp's cutoff is 0 to 1 on a calibrated curve (its `docs/PARAMETER_SCHEMA.md`, "Filter cutoff Hz curve"); `measure_part_sound` suggests a value from the part's roll-off |

## What still needs the person

- One FL load of a built project with a generated sound (above).
- Listening: a sound is judged in the mix, not alone and not by numbers.

## History

- 2026-10-24: Serum 2 installed and the serum-mcp audit done; the person's own presets won the first round ("PL Crusty Pluck [LCV]" for chords, "CP - Deep Sub" for the sub, "ARP - Jno Style" for the arp), cloned by preset name from `sandbox\serum\serum_sounds.flp`.
- 2026-10-26: the person asked for sounds generated to match each song instead of a fixed set. Steps 1 to 5 above built and tested; the offline Serum host proved.
- 2026-10-28: wavetables and the sampler from the song's own loops and kit (skill serum-wavetables), proved on the Sorry Freejak loops.
