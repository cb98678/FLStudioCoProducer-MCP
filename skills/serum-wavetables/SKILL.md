---
name: serum-wavetables
description: Use when the person wants a song's own sounds (a vocal phrase, drum hits, a bass, a melodic part, cut from stems or from extract_song_loops) turned into Serum 2 wavetables or sampler sounds and used in the remix, wants a wavetable from a Serum formula, or asks how to use the Serum MCP (serum-mcp) for wavetables, the sample oscillator, LFO chops, macros or in-synth ducking. Covers build_wavetable, prepare_sampler_sound, tools/serum_tables.py, serum-mcp's sample_source and sample_playback_source fields, and getting the result onto an FL channel.
---

# Serum 2 wavetables and sampler sounds from the song

The person (2026-10-28): "make skills on how to use the MCP Serum 2 for Wave tables. we want to be able to extract sounds or vocal or
even drum sounds and basses and use them in the song using serum 2." The standing rules hold: generate sounds that match the original's
tone, attack and decay; vocal phrases stay whole at their own pitch; editable first; never write the person's originals.

## Pick the route by what the sound has to stay

| The sound must | Route | Tool | serum-mcp field |
| --- | --- | --- | --- |
| stay recognizably itself (a vocal phrase, the kit's kick or clap, a bass note) | Serum's sample oscillator | `prepare_sampler_sound` | `sample_playback_source` |
| become a playable synth with the part's own timbre (a bass, a riff, a held vocal vowel) | pitch-synchronous table | `build_wavetable` (path) | `wavetable` (installed) or `sample_source` |
| become a texture from unpitched audio (drums, noise, breaths) | evenly sliced table, buzzy by design | none: serum-mcp slices it | `sample_source` with `sample_frames` |
| become a cloud or a pad from a phrase | granular engine | none | `granular_source` |
| be designed from math | formula table | `build_wavetable` (formula) | `wavetable` or `sample_source` |

Why a table needs `build_wavetable`: a wavetable frame is one cycle of 2048 samples. serum-mcp's `sample_source` cuts evenly spaced
2048-sample slices, which are not one period of the note, fades 64 samples in and out of each and normalizes each, so a pitched stem
comes back as a buzzy loop of slices (its own docs say so). `build_wavetable` tracks the note's fundamental, fits every harmonic over a few
whole periods (bleed that does not repeat averages out, as in `extract_song_loops`), rebuilds each cycle band-limited at exactly 2048
samples, aligns the frames' phase so they morph without cancelling, and turns the table so its wrap is the quietest point.

## Steps

1. **Get clean material.** `extract_song_loops` (skill `loops-and-kits`) gives averaged bass and music loops, a kit averaged from many
   hits and the hook cut. A stem stretch where the part plays alone also works: give its start and end in seconds.
2. **Make the tables and sampler cuts.** For a whole song: `python tools/serum_tables.py --loops sandbox\loops\SONG --section drop_a
   --install-tables`. It writes, under sandbox\wavetables\SONG: the bass table (longest held note of the section's bass loop), the music
   table when that loop holds a pitch, two formula tables (references/formulas.md), sampler plans for the kit and the hook, a
   serum-mcp spec per sound (spec_ROLE.json) built from those readings, tables.json and a README. One sound at a time: the two MCP tools.
3. **Read the numbers before designing.**
   - `edge_loss_db`: what serum-mcp's edge fade would change if the table goes in through `sample_source`. Under about -30 dB it does
     not matter. Above it, install the table (`--install-tables` copies it to Serum's Tables\User\sandbox\SONG and the spec names it with
     `wavetable`, which Serum plays exactly; serum-mcp resolves a Tables-relative path).
   - Pitch: a table plays its fundamental at the note's pitch, so a bass table read from F1 plays G1 on G1. The measured note and cents
     are only a check that the right note was read.
   - The sampler plan: `play_note` is 60 (FL's C5): Serum's sample oscillator plays a file at its own pitch and speed on note 60, pitch
     and length coupled (an octave down is twice as long). A vocal and a drum are not transposed; a bass or melodic sample gets the
     octave, semitone and fine that make each note play as itself, and a sustain loop on rising zero crossings.
   - A bass stem whose attack reads slower than 40 ms carries the record's sidechain pump: the spec holds the note and the pump stays
     FL's job (skill `mix-engineer`).
4. **Design with serum-mcp.** Read its skill (`sandbox\third_party\serum-mcp\skill\serum-sound-design\SKILL.md`). Generate each spec with
   `generate_preset`, subfolder `sandbox/SONG`, name `CP - SONG ROLE`, and read it back with `describe_preset`. Then the one creative
   move for this remix, said out loud (references/moves.md: pluck, 16th chop, in-synth duck, the four macros, dirt, room). Match first:
   the envelope and the filter come from `measure_part_sound` readings (soundbrief), not from a genre template.
5. **Hear it without FL.** `render_serum_sound` on notes chosen per sound (the bass line's MIDI from `extract_song_loops`, the hook on
   note 60 at its bar). Compare with the source: `compare_part_sound` for a synth part; for a sampler sound the render on note 60
   should correlate with the source near 1.0. Three rounds of `edit_preset` at most, then the person's ear.
6. **Into the song, editable.** The state Serum saved in step 5 goes onto a Serum 2 channel with `build_remix_project` option
   `serum_states` (`tools/remix_song.py --serum-state bass=FILE.serumstate`). Notes: the section's bass MIDI into that channel's piano
   roll; a vocal chop is one note on 60 per phrase, at the phrase's bar, the phrase already at the remix tempo (stretched with its pitch
   kept, at most 6 % slower); drums stay channel-rack samplers with patterns (skill `editable-first`), a Serum sampler drum is for
   layering or pitching a hit. Name the tables' folder when the project is shared: a preset that uses a table or a sample needs that file.

## Worked example: Sorry, the Freejak remix (2026-10-28)

From sandbox\loops\sorry_freejak, section drop_a, 16 frames, run on rtxclub:

| Sound | Reading | Headless render (Serum 2.1.5 under pedalboard) |
| --- | --- | --- |
| Bass table | F1 -3 cents, 43.6 Hz; 3rd harmonic strongest (fundamental 0.55, 2nd 0.65, 6th 1.0); edge loss -29 dB, installed | G1 on note 31, F1 on 29; levels 0.51, 0.63, 1.0 against the table's 0.55, 0.65, 1.0 (the low-pass takes the 6th to 0.63) |
| Music table | D#4 +18 cents, edge loss -35 dB | D#4 on note 63 |
| PM sub | formula, edge loss -33 dB | a pure sine on G1 with Macro 1 at 0 |
| Morph stab | formula, edge loss -27 dB, installed | G4 and G#4 on notes 67 and 68 |
| Kick | 0.44 s, peak -1 dBFS | on note 60: correlation 0.9994 with the kit kick (lag 0.09 ms); on 48: 1.96 times as long |
| Hook | 3.75 s, whole bars 1 to 2 | its own pitch on note 60 (76.6 against 76.8 MIDI); the 16th gate at 8.0 Hz (16ths at pedalboard's 120 bpm; 8.53 Hz at 128 in FL) |

The person has not heard these yet. The bass dropped to sustain 0.8 with a 3 ms attack: the stem read a 124 ms attack, the remix's pump.

## Limits and what is not verified

- serum-mcp writes into Serum's own folders: presets under Presets\User\sandbox\SONG, samples it copies under Samples\User\serum-mcp,
  tables under Tables\User\serum-mcp (sample_source) or Tables\User\sandbox\SONG (`--install-tables`). Nothing else of the person's.
- Macro scaling through `aux_source` is written but `describe_preset` does not show it; check the macro moves the pluck once in Serum.
- The duck and chop LFOs follow the tempo, not the kick, and restart on each note (Retrig): notes must start on the grid.
- Serum 2's formula parser is taken from Serum 1's documented variables (references/formulas.md); the Serum 2 guide PDF could not be
  read here. The formula is evaluated by `build_wavetable`, never sent to Serum.
- The attachment the person shared (2026-10-28) is reviewed in references/attachment-review.md: what applies here, what is wrong.
- A singer's voice is not cloned: the vocal is the record's own phrase on the sampler, or a vowel's cycles as an instrument timbre.
