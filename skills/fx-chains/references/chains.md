# Chain recipes (from the Future House reference, 2026-10-25)

Entries are in `plugins/library/`; list them with `list_effect_library`. Order is the slot order the reference uses. Settings are in each entry's
`params` (read in FL when the entry was saved). Why each chain works is in `docs/REFERENCE_FUTURE_HOUSE.md`.

| Part | Chain (library entry names) | What it does |
| --- | --- | --- |
| Vocal chops | fh Vocal Chop Fruity WaveShaper → fh Vocal Chop Fruity Parametric EQ 2 → fh Vocal Chop Fruity Reeverb 2 → fh Vocal Chop Fruity Compressor → fh Vocal Chop Fruity Multiband Compressor → fh Vocal Chop Soundgoodizer → fh Vocal Chop Fruity Parametric EQ 2 7 → fh Vocal Chop Gross Beat → fh Vocal Chop Fruity Love Philter | Light shaping, high-pass 126 Hz with cuts at 300 Hz, 1 kHz and 2.8 kHz and a 5.4 kHz shelf, a 1 s reverb at 25%, compression 5.8:1 then multiband, a second cleanup EQ, then the stutter (Gross Beat) and filter or pump (Love Philter) |
| Kick | fh Grv Kick 18_2 Fruity Parametric EQ 2 → fh Grv Kick 18_2 Fruity Multiband Compressor | High-pass 35 Hz, cuts at 147 and 396 Hz, a 9.8 kHz lift, gentle three-band control |
| Clap | fh Attack Clap 12 Fruity Parametric EQ 2 → fh Attack Clap 12 Fruity Reeverb 2 → fh Attack Clap 12 Soundgoodizer | High-pass 140 Hz, cuts, a 0.4 s room at 32% |
| Hats | fh Attack Hat 06 Fruity Parametric EQ 2 → fh Attack Hat 06 Fruity Reeverb 2 | Small cuts, a 0.2 s reverb at 40% |
| Crash and rides | fh Crash Fruity Parametric EQ 2 → fh Crash Fruity Delay 2 → fh Crash Fruity Reeverb 2 | High-pass 306 Hz, ping-pong delay, 2.1 s reverb |
| Drum bus | fh Drum Group Fruity Multiband Compressor (→ fh Drum Group Fruity Flanger for transitions only) | Three-band glue at 2:1 |
| Keys and chords | fh FL Keys Fruity Parametric EQ 2 → fh FL Keys Maximus (a -10 dB trim) → fh FL Keys Fruity Compressor → fh FL Keys Fruity Multiband Compressor → fh FL Keys Fruity Reeverb 2 → fh FL Keys Soundgoodizer → fh FL Keys Fruity Parametric EQ 2 7 → fh FL Keys Fruity Love Philter | Cut the low mids, squash hard (22.6:1), a wide 1.5 s reverb at 82%, then a cleanup EQ and the pump |
| Mid bass | fh FutureBass Fruity Compressor → fh FutureBass Fruity Fast Dist → fh FutureBass Fruity Parametric EQ 2 → fh FutureBass Fruity Reeverb 2 → fh FutureBass Soundgoodizer → fh FutureBass Fruity Love Philter → fh FutureBass Gross Beat → fh FutureBass Fruity Balance | Compression 12.7:1, distortion at 71% mix, high-pass 82 Hz, a short room, saturation, then filter, reverse and level automation targets |
| Sub | fh FutureSub Fruity Love Philter → fh FutureSub Fruity Parametric EQ 2 → fh FutureSub Fruity Compressor → fh FutureSub Fruity Multiband Compressor | Pump first, +6.4 dB at 66 Hz, -9.6 dB at 163 Hz, low-pass 2.4 kHz, heavy compression with makeup |
| Music bus (pumped) | fh Sidechain Fruity Filter → fh Sidechain Fruity Reeverb 2 → fh Sidechain Fruity Love Philter | The sweepable filter, a 3.2 s reverb for throws (wet automated), the pump target |
| FX, risers | fh Sidechain FX Fruity Parametric EQ 2 → fh Sidechain FX Fruity Reeverb 2 → fh Sidechain FX Soundgoodizer → fh Sidechain FX Fruity Love Philter | Bright EQ, a 4.1 s reverb at 75%, pumped |
| Crash wash | fh Sidechain FX Crash Fruity Reeverb 2 → fh Sidechain FX Crash Fruity Love Philter | An 8 s reverb, pumped |
| Low hits | fh Low Hit Fruity Parametric EQ 2 → fh Low Hit Fruity Reeverb 2 | Low-pass 479 Hz, a 2.8 s tail |
| Lead synth | fh Wow Synth Fruity Parametric EQ 2 → fh Wow Synth Fruity Reeverb 2 → fh Wow Synth Soundgoodizer | Cuts at 171 Hz and up, a short reverb with 98 ms predelay |
| Outro synth | fh Outro Synth Effector → fh Outro Synth Soundgoodizer → fh Outro Synth Fruity Parametric EQ 2 | Lo-fi colour, saturation, cleanup |

The Love Philter entries are the pump targets: they duck only when an Envelope Controller drives them (see the pumping work in
`docs/PLAN_FROM_REFERENCE.md`, item 10). Without that link they pass the sound through.
