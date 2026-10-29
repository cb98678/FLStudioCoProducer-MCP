# Mix guide from the breakdowns

General guidance the breakdowns give, set against this project's own measured targets. Where they differ, the project's targets (the style pack's targets file and the evaluation panel) win unless the person asks otherwise.

## Frequency lanes

| Band | Who owns it | How |
| --- | --- | --- |
| 20 to 60 Hz | the sub alone, a sine, mono, centred | low-pass the sub near 90 Hz; nothing else under 60 Hz |
| 60 to 250 Hz | the mid bass, gritty, pumped hard by the kick | high-pass the mid bass near 90 Hz so it does not fight the sub; the kick's body sits here too, so the pump makes room |
| 250 to 500 Hz | kick body, the voice's warmth, snare body | the crowded band: dip the pads and chords here (the Red Lights breakdown dips 150 to 300 Hz by about 1.5 dB on the master) |
| 500 Hz to 2 kHz | the lead's core, the voice's words | one lead at a time with the voice: duck or thin the lead under sung lines |
| 2 to 6 kHz | the voice's presence, synth bite, the kick's click | keep the voice on top here; de-ess before brightening |
| 6 to 20 kHz | noise sweeps, open hats, air | high-passed white noise lifts a drop; keep it under the hats |

The chords and pads go wide (panned or unison-spread) so the centre stays open for the voice and the bass; everything under about 150 Hz stays mono (mix.mono_low_hard_pump measures that on a club mix).

## Gain staging starting points (the breakdown's, as peaks on the channel)

kick about -6 dBFS, sub about -12, mid bass about -14, lead stack about -10, lead voice about -10, percussion and hats about -18. These are where to start a static mix; this project's part-level loop (tools/part_levels.py) and the section contrast loop set the real levels from renders, and the panel checks the voice sits where it should.

## The pump

- Depth: synths and mid bass fully down on the kick, the sub ducked too (mix.pump_deep, mix.mono_low_hard_pump).
- Shape: this project's pump holds 0.1 beat and is back by 0.3 beat (the Future House reference, measured); at 125 bpm that is the breakdown's 48 ms and 144 ms. mix.exp_recovery_pump makes the recovery a curve (fast at first, easing in) instead of a straight line.
- Without a kick: mix.ghost_trigger_pulse keeps the pump through breakdowns.

## Master targets

| | The breakdowns | This project |
| --- | --- | --- |
| Loudness | -6 to -4.5 LUFS in the loudest drop (modern); -11 to -9 LUFS (the 1993 record, by the breakdown) | the style's targets, about -8 LUFS for the club master |
| True peak | -1 dBTP | the panel's ceiling (club master at about -0.5 dBTP); for streaming files -1 dBTP is the safer ceiling |
| Drop dynamics | PLR 4 to 6 dB | the panel's loudness-range and contrast checks |

A 90s blueprint can be mastered quieter on purpose so the kick stands 6 to 8 dB over the mix; ask the person before going louder than the targets.
