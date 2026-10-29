# FLP layout used by the editable-first tools (FL Studio 2026, v26.1.7)

Why this exists: the FL Python API can set tempo, mixer and plugin parameters, but pattern notes and playlist clips are
written either through the piano roll script route (GUI driven) or by patching the saved project file. The file route
is deterministic, scriptable and verifiable, so the remix builder uses it on a sandbox copy. The original project is
never written. Numeric ids below were measured on this build; symbolic names for channel and pattern events match the
community reference at https://pyflp.readthedocs.io/en/stable/reference/events.html (ChannelID.New, ChannelID.SamplePath,
PatternID.New, PatternID.Name, PatternID.Notes). The reference lists names but not numeric ids, so treat the table below as
measured, not documented.

Library: `coproducer.flpfile`. CLI: `tools/flp_tool.py`. Tests: `tests/test_flpfile.py`.

## Container

`FLhd` (length 6: format, channel count, PPQ) then `FLdt` (length, events). The channel count is the u16 at byte 10 of the
file and must be raised when a channel is added. Events are `id byte`, then a value whose size depends on the id:
under 64 one byte, 64 to 127 two bytes, 128 to 191 four bytes, 192 and above a varlen length then bytes.
Text is UTF-16 little endian with a trailing null.

## Events used

| Id | Meaning | Value |
| --- | --- | --- |
| 64 | channel block start | u16 channel id (global channel index) |
| 0 | first byte event in a channel block | enabled flag (1 on, 0 off) |
| 203 | channel name | UTF-16 |
| 196 | sample file path | UTF-16, the path as the host FL sees it |
| 104 | channel's mixer track | u16 |
| 213 | plugin or channel data | opaque; copied unchanged when a channel is cloned |
| 99 | first event after the last channel block | used as the end of the final block |
| 65 | new pattern | u16 pattern id |
| 193 | pattern name | UTF-16 |
| 224 | pattern notes | 24-byte records |
| 233 | playlist | 88-byte items |

A channel block runs from its 64 event to the next 64 event, or to event 99 for the last one.

## Note record (24 bytes)

`pos u32` (ticks from the pattern start), `0x4000 u16`, `channel u16`, `length u32` (ticks, 0 for one-shots), `key u16`,
`0 u16`, then bytes `0x78 0x00 0x40 0x00 pan vel 0x80 0x80` (pan 0 to 128 with 64 centered, velocity 1 to 127).
96 ticks per beat, 384 per 4/4 bar, 24 per sixteenth step.

## Playlist item (88 bytes)

`pos u32` at 0 (ticks), pattern reference u16 at 6 (20480 plus the pattern id), `length u32` at 8, track u16 at 12
(499 minus the 1-based playlist track), unique item id u32 at 32. New items are copies of an existing pattern clip with those
fields changed, then the list is sorted by position. A project with no pattern clip has no template; place one in FL first.

## Audio clip items

For an audio clip the pattern reference at 6 is the channel index (below 20480). Byte 24 is a float32 start offset and byte 28 a
float32 end offset into the source file, in milliseconds of the source (checked on the DTP project: (end minus start) divided by
(length ticks times 4.464 ms) is 1.000 for unstretched clips and 1.33, 0.72, 0.97 for the stretched ones). Sliding start and end
together moves the content under the clip without changing its speed; changing only one changes the speed. Moving `pos` slides the
clip on the grid. `coproducer.vocalclips` reads and writes these fields and `tools/vocal_patch.py` applies them.

## Automation clips

Read from projects FL Studio 26.1.7 saved after "Create automation clip" on a mixer knob, a mixer EQ knob and a plugin knob, then proven by
rendering (2026-10-22). `coproducer.automation` writes them. Three pieces:

1. **Channel block of type 5.** Event 21 holds `05`, event 203 the name (UTF-16), event 128 the colour, event 234 the points.
2. **Event 227, 20 bytes, `<HHIIII>`** = 0, clip channel id, 0, link, 8, 469. FL writes every controller event (226, then 227) together,
   just before the first channel block, so new links go there.
3. **A playlist item** (88 bytes as above) whose channel field is the clip channel id. Length is the last point in beats times 96; track is
   499 minus the 1-based playlist track. FL itself places new clips at tick 0 with the song length.

**Event 234.** Header `<IIIBII>` = 1, 64, flags, 0, 3, point count. Flags are 0x400, or 0x401 for centred knobs (pan, stereo separation).
Then 24 bytes per point, `<ddfBBBB>`: **delta in beats from the previous point** (0 for the first, NOT an absolute position; writing
absolute beats made ramps run 2x to 3x slow), value 0..1 (the knob position), tension float32 (0 is a straight line), three zero bytes,
and a flag byte (0 for the first point, 2 for the rest). Then a constant 112 byte tail. The encoder reproduces FL's own bytes exactly.

**Link** = `0x70000000 | track << 22 | sub << 16 | param`, track 0 is the master.

| Target | sub | param |
| --- | --- | --- |
| Track volume, pan, stereo separation | 0 | 0x1FC0, 0x1FC1, 0x1FC2 |
| Built-in track EQ gain, frequency, Q (band 0 to 2) | 9 | 0x1FD0+band, 0x1FD8+band, 0x1FE0+band |
| Plugin parameter k in the first effect slot | 0 | 0x8000 + k |

Slots above the first are assumed to use `sub` = slot (not yet tested). The ids agree with the REC constants in
[FL-Studio-API-Stubs](https://il-group.github.io/FL-Studio-API-Stubs/midi_controller_scripting/midi/__rec_events/): `REC_Mixer_Vol = 0x20001FC0`,
`REC_PluginBase = 0x8000`, `REC_ItemRange = 0x10000`.

**Values are knob positions, not units.** Volume: 0.8 is 0 dB, 0.3 about -15.4 dB, 1.0 about +5.6 dB (`automation.db_to_fader`). Built-in
EQ gain: 0.5 is flat, 1.0 about +12.9 dB. Plugin parameters differ per plugin: read the normalised value with `plugins.getParamValue` first
(a Fruity Limiter gain of 0.0 is silence, 1.0 about +5 dB).

**Links can carry a formula (event 230).** A crossfade clip written by FL has two 227 links, each followed by an event 230 holding UTF-16 text such
as `0.5*Tension(`. A link and its formula are one unit and must stay adjacent. Moving the 227 events without their 230 events made FL's command line
render hang on a real project (the DTP project, 2026-10-22; even a flat two point clip hung it, the same clip rendered after the fix).
`automation.add_automation_clip` keeps the pairs together and `remove_automation_clip` drops a formula with its link.

**Only inject into a project FL itself saved.** Adding any automation clip to the old-format scratch base (`probe_scratch.flp`, which
carries legacy events) made FL's command line render hang or crash, while the same clip in an FL-saved copy rendered correctly. Open the
project in FL, save it, then patch the saved copy. (Older notes here blamed the scratch base alone; the formula pairing above caused the DTP hang.) Render-checked: track volume dip (silence where the value is 0), master volume,
track EQ high gain, Fruity Limiter gain.

## Arrangements, mixer inserts and links (read from the FL demo "Future House", 2026-10-25)

- **Several arrangements.** Each starts with event 99 (u16 id), then 241 (name), 233 (playlist), 500 track records (238, each followed by its flag
  event 43, and 239 for a named row), and its time markers (148 position, 205 name). Event 100 after the last arrangement holds the id of the current
  one, which FL plays and renders. `Flp.current_arrangement()` follows it; edits that change channel ids touch every arrangement's playlist.
- **Insert blocks.** An insert's colour (149), appearance flag (42), icon (95) and name (204) come just before its flags event 236; its effect slots
  follow (per slot: 201 internal name, 212 wrapper with insert u32 and slot u32, optional 203 name the person gave, 155, 128, 41, 213 state, then 98
  slot index; an empty slot is only the 98), then routing 235, 165, 166, 49, input 154 and output 147. The master is the first block and has no name.
- **Routing 235** is one byte per destination insert (0 is the master). FL 26 trims the trailing zeros (1, 3 or 104 bytes); FL 20 wrote all 127.
- **Mixer records 225** (12 bytes): u32, id byte, group byte, u16 insert << 6 | slot, i32 value. The master's insert field is 448 in FL 26 saves
  and 128 in FL 20 saves. Group 31: id 192 volume, 193 pan, 194 width, 208 to 226 the insert EQ, id 0 slot on (1) or off (0), id 1 slot mix
  (12800 is 100%). Group 32: a send level, the id byte is the destination; FL writes only sends away from the default. Switching master slots off
  through the id 0 records is honoured by FL's command-line render (a split with the master bypassed stopped every solo hitting 0 dBFS).
- **Links 227** (20 bytes): u16 output (0x8000 set for a controller output, low bits the output number), u16 source (automation clip or controller
  channel id; 0x8900 for a Control Surface on insert 100), u32, u32 target, u32 8, u32 469. Mixer target: 0x70000000 | insert << 22 | slot << 16 |
  param, param 0x8000 + k for plugin parameter k. Channel target: channel << 16 | param (4 is pitch; 0x8000 + k a generator parameter).
- **The legacy-event guard was too strict.** FL 26.1.7 itself writes events 67, 80, 94 and 192 (seen in its saves of the Future House demo and of
  our tech-house master), so `automation.LEGACY_EVENTS` no longer lists them. The old scratch base carries only those, so the guard no longer
  tells it apart; the render stall stop (`stall_s`) is the safety net if a patched file makes FL hang.
- **A copied Envelope Controller does not drive.** The reference's Envelope Controller (channel 1) pumps five inserts in FL's command-line render,
  and removing its five links stops it. A byte-identical copy of its channel block as a new channel, with byte-identical links that name the new
  channel id (also tried: link sources 0, 2, 9, 29 and 31, links moved first or last), drove nothing (2026-10-25, `sandbox/pumpcheck` to
  `pumpcheck5`). The cause is not in the events we can see. Our pump uses automation clips on a Fruity Balance instead (`build_volume_pump`).
- **Automation in any slot works.** A clip on Fruity Balance volume in slot 9 (link sub 9) rendered at the level it asked for: a flat clip at the
  knob for -8 dB measured -7.9 dB. Fruity Balance volume follows the mixer fader law (0.8 is 0 dB).
- **Time markers** (current arrangement, right after its playlist event 233): 148 position (ticks), 33 and 34 (time signature 4 and 4), 46, 45,
  168 (u32), 101 (u16), then 205 name. `Flp.add_time_marker` writes that group in position order.
- **Channel automation targets**: channel << 16 | code (4 is pitch, centred at 0.5 like FL's own snare-pitch clip) and channel << 16 | (0x8000 + k)
  for generator parameter k. A flat clip at 0.5 on a plugin channel's pitch left its sound unchanged (2026-10-25). For the size of a rise see
  "A channel pitch clip spans" below.
- **The reference's filter is high-pass.** Its Fruity Filter (library entry "fh Sidechain Fruity Filter") has High pass at 1 and Low pass at 0:
  cutoff 0 passes everything, and its clip sweeps 0 to 0.42 into a transition and back to 0 on the drop.
- **Layer channels** are type 3 (event 21) with one event 94 (u16 channel id) per child, written right after the mixer track event 104, and an
  event 50 of 1; they have no plugin state. The notes are on the Layer, so a solo must keep it on. `layers.add_layer` builds one from the
  reference's KICK block (library entry "fh layer"), sets the children and moves the part's notes onto it.
- **Channel levels 219** (24 bytes, six i32): pan (0 to 12800, 6400 centred), volume (0 to 12800, 10000 is FL's default 78%), pitch knob in cents,
  filter mod x, filter mod y, filter type. **Pitch knob range** is the i32 at byte 112 of the channel's event 215, in semitones (2 by default). Read
  from the reference: every channel's pitch fits its range (277 cents with range 7, 800 with 8), and `Flp.set_channel_pitch` widens the range
  when a value needs more. FL's command-line render honours the stored cents: a kick set to -201 cents rendered 2 semitones lower (46.4 Hz to
  41.4 Hz, 2026-10-25).
- **A channel pitch clip spans -48 to +48 semitones, whatever the knob range.** Measured 2026-10-25 (`sandbox/fcheck/pitchcal`): the same snare
  clip from 0.5 to 1.0 over 16 beats rose about 3 semitones a beat and reached +47 at the end with the knob range at 2, 12 and 24 alike. So a rise
  of N semitones runs from 0.5 to 0.5 + N / 96 (`transitions.pitch_rise`), and the reference's own 0.5 to 1.0 clip asks for four octaves. The
  first pitch-rise check, on a plugin channel, could not be confirmed by measurement and the reason is not known; on a sampler the rise is clear.
- **Channel filter** (levels bytes 12 to 24: cutoff 0..256, resonance 0..256, type in FL's order Fast LP, LP, BP, HP, BS, LPx2, SVF LP, SVF
  LPx2). Measured on white noise through a sampler (2026-10-25, `sandbox/fcheck/filtercal`): LP at 64 has its corner near 100 Hz, 128 near 320 Hz,
  193 near 1 kHz, and Fast LP at 256 is open; HP is steep in the other direction: at 32 the corner is near 4 kHz (-10 dB at 1.3 kHz, -36 dB at
  80 Hz), at 64 near 8 kHz, and at 193 (the reference's top kick) everything is 17 dB or more down. HP at 0 passes everything.
- **A Layer's volume scales what it plays.** A Layer at 12800 (100%) over one kick rendered exactly as the kick alone; at FL's default 10000 it
  was 5.2 dB quieter. Two kicks tuned to the same note summed in phase (+2.1 dB over the louder alone), no cancellation. The channel volume knob is
  close to a square law: 5000 against 10000 measured -11 dB.
- **Renumbering channels** must also remap the children of Layer channels (94) and the source and channel target of links (227); a mixer target
  (0x70000000 and up) and a source of 0x8000 and up are not channels. `Flp.renumber_channels` does both since 2026-10-25.

## Pitfalls found the hard way

- **Do not shorten a stretched sample's file.** Pointing 17 clips of a stretched 11 minute mp3 (rate 0.97) at a 9 second cut of it,
  with the offsets moved to match, made FL render 400 s instead of 139 s and those clips came out 6 dB quieter or silent. The cause
  was not isolated (bisecting by channel group pinned it to that one channel); a cleaned copy as long as the source fixed it
  (`tools/vocal_clean.py --region A,B --keep-length` keeps the original audio outside the cleaned region).
- **Sliced-audio copies are one file.** `audio_..._2.ogg` to `_9.ogg` in a Sliced audio folder were byte identical (same md5). Clean
  one and point every channel at it.
- **Decoder delay did not shift the clips.** Cleaned wavs made from Opus and mp3 sources lined up with the original decode to
  within 0.1 ms in the rendered vocal stems, so offsets carry over unchanged when the length is kept.
- **Pattern id collisions merge patterns silently.** Two parts given overlapping id ranges (arp 150 to 153 against sub
  100 to 153) played each other's notes. `Flp.add_pattern` refuses a reused id; use `next_pattern_id(floor)`.
- **A 64 event directly before a 65 event is not a channel.** FL 2026 writes a current-item marker there (value 3303 in the
  DTP project). Counting every 64 gave 162 channels against a header of 161. `channel_ids()` skips it.
- **Strip drum notes by channel, not by position.** `strip_notes` filters the 24-byte records of every pattern before the
  playlist by their channel field.
- **Rebuild from a fresh save.** FL rewrites layout details when it re-saves. A scan of one re-saved file assumed an old
  layout and produced a corrupt project. Always start from a fresh save of the sandbox copy (`save_sandbox_project`),
  patch, re-parse, then reopen in FL.
- **Reopen and verify.** `Flp.save` proves the bytes re-parse and round trip. It does not prove FL accepts the file. After
  patching, open it, list channels with `tools/chan_global.py list`, confirm the new channels and pattern count, render
  with `render_with_restart` and measure.
- **Closing FL matters.** `render_with_restart` closes FL and refuses a project with unsaved changes. Never patch a file FL
  has open.

## Raw pitch keys

FL's raw piano-roll key is MIDI minus 12 (raw 48 is MIDI 60). A patch can shift it further: the Deep
Sytrus patch applies minus 19 semitones, so raw 36 sounds as F1 (43.65 Hz), raw 43 as C2 and raw 48 as F2. Find a patch's
offset by playing a note and measuring the render, not by reading the key name.

## FL 26.1.7 start-of-file quirk (found 2026-10-23)

A project begins with events 199 (version), 159 (build), 169, 28, then 172 followed by the title text event (id 192, "FL Studio 26.1.7.5654.5654"). Event 172 holds 3 bytes here, not the 4 that its id range (128 to 191) implies; its fourth "byte" is the id 0xC0 of the title text. Reading it as a dword made every following event desynchronize. Older projects such as the DTP file happened to resynchronize a few events later, so the bug stayed hidden until a project made fresh from FL's template (stemstest) showed "no playlist event". `parse` now reads 3 bytes when the byte after the three is 0xC0, and a test pins it. A project with no pattern clip yet is handled with a built-in 88-byte pattern clip layout (`PATTERN_CLIP_TEMPLATE`), copied from a real project with id and position zeroed.
