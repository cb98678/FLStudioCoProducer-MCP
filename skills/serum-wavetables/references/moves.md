# Moves for sounds made from the song (src/coproducer/serumspec.py)

Each move returns a part of a serum-mcp PresetSpec; `serumspec.assemble` merges them. Every field and destination below is one serum-mcp
lists as confirmed (its `generation/spec.py` and `preset/schema.py` MOD_DEST_TARGETS at commit eada85a, the clone in
`sandbox\third_party\serum-mcp`); call `list_parameters` when unsure.

## Indices: serum-mcp counts from 0

| Serum's panel | serum-mcp |
| --- | --- |
| Osc A, B, C, Noise, Sub | oscillator0 to oscillator4 (oscillators list positions 0 to 4) |
| Filter 1, 2 | filter0, filter1 |
| Env 1 (amp), Env 2, 3, 4 | env0 to env3 (envelopes list) |
| LFO 1 to 10 | lfo0 to lfo9 |
| Macro 1 to 8 | macro0 to macro7 |
| an effect | fx0, fx1 ... by its place in `fx_chain`, whatever rack it is in |

## The moves

| Move | What it writes | Notes |
| --- | --- | --- |
| amp | env0 attack, hold, decay, sustain, release | from `measure_part_sound` when there is a part to match |
| pluck | env1 fast attack, decay to 0, routed to filter0.cutoff; `aux_source` macro0 scales it | decay from the part's own decay; 0.5 to 2 ms attack and 150 to 300 ms decay is a starting range for a percussive pluck, not a rule |
| chop | an LFO whose curve is 4 (16ths) or 2 (8ths) on-off steps, Retrig, routed -100 to oscillator0.volume | the LFO's rate is left unset: Serum's default is a quarter note synced to the tempo, so the steps are 16ths. serum-mcp has a confirmed rate value for 1/8 only (10.66), none for 1/16 |
| duck | an LFO spike at each quarter note falling off over 35 % of it (three curve points: a falling two-point curve renders blank), routed negative to an effect's wet | an inverted sidechain inside the synth: the room clears on each beat. It follows the tempo, not the kick |
| macros | 1 GRIP: table position; 2 SNAP: Env 2 decay; 3 ROOM: the reverb's wet (up to 30 %); 4 DIRT: the distortion's wet | a macro adds to the destination: a reverb at wet 0 is dry until ROOM moves |
| room | FXReverb, size 20 %, wet 0 | kHall, kSpace, kVintage or kAbyss |
| dirt | FXDistortion at a fixed drive, wet 0 | Serum 2 has no mode called Tube: kTapeSat, kSoftSat, kOverdrive, kStompBox saturate; kDiode1 and kDiode2 clip. Put it before the room |
| table_osc | `sample_source` and `sample_frames` for a table in the sandbox | serum-mcp slices exactly the file's frames (evenly spaced starts land on multiples of 2048) |
| table_ref | `wavetable` as a path under Serum's Tables folder | exact frames, no edge fade |

Not available as modulation in serum-mcp: a distortion's drive, a reverb's size, a compressor's gain. The dirt and duck moves work
through the effect's wet instead. FXUtils level_out is a confirmed destination when a gain duck is needed.

## Sampler oscillator facts (serum-mcp docs/PARAMETER_SCHEMA.md and spec.py, eada85a; checked by render 2026-10-28)

- `sample_playback_source`: an absolute path to a WAV (only WAV), copied into Serum's Samples\User\serum-mcp. Plays at its recorded
  pitch and speed on MIDI note 60 (FL's C5). The kit kick rendered on 60 correlated 0.9994 with the file; on 48 it ran 1.96 times longer.
- `sample_loop`: off (a one-shot), forward, ping_pong, tailed; loop start and end in percent of the file.
- `sample_center_pan` (on by default) gain-balances the two channels to the same RMS. It does not make a sound mono or move it to the
  centre: a vocal is centred because it was recorded and mixed there.
- Table position does not apply on the sampler; warp does.
- Layering several samples: `analyze_sample_file` on each first (peak and RMS), since one-shots are not gain matched.
