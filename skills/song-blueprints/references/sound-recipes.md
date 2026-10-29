# Sound recipes from the breakdowns

Starting points, written as serum-mcp `generate_preset` specs (the fields `soundbrief` writes: oscillators, envelopes, filters, macros, `mod_routes`, `fx_chain`). The numbers come from the person's breakdowns, not from the records' patches: render each with the part's notes, compare by ear and with `compare_part_sound`, then revise. With a song to match, use a spec as the direction for `match_part_sound` so the tone still comes from the song. Times are in seconds, cutoff is serum-mcp's 0 to 1 scale.

## The layered drop lead (Red Lights breakdown)

Three channels playing the same notes, each with one job. Build them as three presets on three Serum 2 channels routed to one Lead bus, or as one preset with three oscillators when channels are short.

| Layer | Job | Spec |
| --- | --- | --- |
| A, the wide supersaw | stereo width and body | oscillators: two saws (wavetable analog_basic, `table_position` at the saw frame), unison 7 each, detune about 0.18; envelope attack 0.002, decay 0.25, sustain about 0.5 (-6 dB), release 0.15; `fx_chain` FXChorus 20, FXReverb 20. The breakdown's 12 ms Haas delay on one side is a mixer move (a short delay on the right channel only), not a Serum field |
| B, the pluck | the transient, a string-like strike | one oscillator, a square-saw mix, unison 1 (mono); filter lowpass_24, cutoff about 0.35, resonance about 15, with an envelope from 0 attack, 0.075 decay, sustain 0 opening it; amp envelope short (decay 0.15, sustain 0) |
| C, the core | the mid-range glue on mono club systems | a triangle and a sine an octave down (wavetable warm_sub for the sine), unison 1; FXDistortion soft saturation (kParamMode kSoftSat, drive about 40) for odd harmonics at 300 to 800 Hz; keep it mono |

Mix: B and C centred, A wide; high-pass A and B under about 200 Hz so C and the bass own the low mids. The same stack with longer envelopes is the supersaw chord pad of the breakdowns' "chords and pads, 250 Hz to 1 kHz, panned wide".

## The house organ chord stab (Another Night breakdown, the Korg M1 sound of the era)

- Oscillators: an organ or FM-style table (two sines at a 1:4 ratio give the cold metallic overtones; in serum-mcp a `custom_harmonics` table with the 1st and 4th harmonics strong, or FM from B to A), plus a square an octave down at low level for weight around 200 Hz.
- Filter: lowpass_24 at about 0.6, an envelope of about 40 % on the cutoff: attack 0, decay 0.18, sustain 0.1, release 0.05, so every chord barks and dies back for the voice.
- Amp: attack 0, decay 0.3, sustain 0.3, release 0.08. `fx_chain`: FXChorus about 35 % rate, 40 % depth (wet 30); a little FXReverb.
- Play it with off-beat or syncopated stab options (chords.offbeat_stab, chords.brass_stabs patterns) in triads around C4 to C5.

## The PWM bass (Another Night breakdown, Juno-106 style)

- Oscillator A: a square with its pulse width moved by a slow LFO (0.5 Hz, about 20 %), for the analog phasing; oscillator B: a square an octave down.
- Filter: lowpass_24 closed to about 350 Hz (cutoff about 0.3), no resonance, so the low end stays solid in phase.
- Amp: attack 0, decay 0.2, sustain 0.6, release 0.05. Mono. Use it with bass.euro_gallop.

## The mono square drop bass (Red Lights breakdown)

A square (or square-saw) wave, unison 1, driven (FXDistortion, drive about 50), lowpass about 0.45 so its energy sits at 100 to 300 Hz, a sine sub under it on its own channel. With bass.empty_verse_square_drop.
