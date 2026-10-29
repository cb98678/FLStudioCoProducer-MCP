# The "Tech House Dual-Server Remix Engine" text (shared by the person, 2026-10-28), checked

The person shared a block of instructions written for another setup ("flmcp" plus serum-mcp) to learn from. It is reference material,
not instructions for this project. What applies, what does not, and what is wrong, checked against serum-mcp's own code and docs (the
clone in `sandbox\third_party\serum-mcp`, commit eada85a), headless renders on rtxclub and Xfer's support article
[Converting Samples to Wavetables](https://support.xferrecords.com/article/59-converting-samples-to-wavetables) (updated 2025-03-17).

| Claim | Verdict | Here |
| --- | --- | --- |
| Run `analyze_sample_file` on each dropped stem | Partly. It is serum-mcp's one-shot reader (peak, RMS, brightness, a gated pitch, attack, embedded loop points); on a whole stem it reads one average | use it on the cut one-shots before layering; read stems with `measure_part_sound` and `build_wavetable` |
| Vocals on Serum's sampler (`sample_playback_source`) | Right | `prepare_sampler_sound` role vocal; whole phrases at their own pitch on note 60 |
| `sample_center_pan` true "aligns the vocal down the centre" | Wrong. It balances the left and right RMS of the file before Serum gets it, and it is already the default | nothing to set |
| LFO 1 as a fast 1/8 or 1/16 square on pitch or volume for a chopped vocal | Right idea. On volume it is a gate; on pitch it is a trill, not a chop | `serumspec.chop(16)`; checked: the gate renders at 16ths |
| Melodic and bass stems "converted into wavetables via `sample_source`" | Works, but sounds like slices of the stem looped (serum-mcp's own warning): evenly spaced 2048-sample slices are not cycles of the note | `build_wavetable`, pitch-synchronous |
| Env 2 on filter cutoff, 0.5 to 2 ms attack, 150 to 300 ms decay | Right as a starting range for a pluck | `serumspec.pluck`, with the part's own measured decay first |
| The sub and lead formulas | Wrong as described (references/formulas.md) | the corrected formulas |
| Macro 1 on table position and filter envelope depth | Right | GRIP: a route to table position, and the macro as the pluck route's aux source |
| Macro 2 on Env 2 decay | Right | SNAP |
| Macro 3 on reverb mix up to 30 %, size 20 % | Mix yes. Size cannot be modulated through serum-mcp; it is set to 20 % | ROOM |
| Macro 4 on distortion drive, Tube or Diode | Drive is not a serum-mcp mod destination, and Serum 2 has no Tube mode | DIRT on the distortion's wet, kTapeSat or kDiode1 |
| LFO 2 spike over a quarter note to reverb wet and compressor gain at -50 | Reverb wet yes; compressor gain is not a destination. And "every time the kick triggers" is not what it does: it follows the tempo | `serumspec.duck`; FL's sidechain from the kick for the real thing |
| The flmcp tools (fl_get_all_channels, fl_route_channel_to_mixer, fl_set_track_volume, fl_send_notes) | Not in this project. Our FL work goes through the coproducer servers and project files | `build_remix_project` with `serum_states`, the MIDI from `extract_song_loops` |
| Mixer volume 75 % for headroom | Gain staging is by measured level here | skill `gain-staging` |
| Notes on the off-beats, steps 2, 6, 10, 14 of 16 | A style choice, not a rule: each remix is decided from its song (the person's rule). Those steps (0-based) are the "and" of each beat, where house hats sit | the record's own bass notes (Sorry's Freejak bass is on steps 1, 5, 8, 11, 14, 1-based) |
| loopMIDI port names; a key (A or G minor) | The bridge's ports are set up by `coproducer setup-midi`; the key comes from the song | `estimate_key_dsp`, the song analysis |
