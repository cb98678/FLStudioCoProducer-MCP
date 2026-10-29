# The moves in FL Studio

How each move in moves.md is done by hand in FL Studio, and which coproducer option or tool does it. FL controls are named as the FL
Studio online manual names them (pages read 2026-10-28); the option ids are in src/coproducer/data/options.

## Tempo and the vocal

- **Stretch the vocal to the new tempo, pitch and formants kept.** Load the vocal stem in a Sampler channel or as an audio clip, set the
  project tempo, then in the channel settings' Time stretching: TIME, right-click, Project tempo (or the clip menu's Fit to tempo); Mode
  e3 Mono, the elastique mode for vocals and solo instruments with automatic formant preservation. It works offline and does not follow
  tempo automation; for a tempo change use Stretch pro, with F.Shift at 0 to keep the formants
  ([Sampler time stretching](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/chansettings_sampler.htm)).
  Check: the vocal's median note is unchanged (Freejak's Sorry: MIDI 63.1 before and after).
- **Tune to the record.** Measure first (pYIN on the vocal or bass stem). A channel's FINE knob tunes it in cents; Enable Main Pitch makes
  a channel follow the Main Pitch control
  ([Channel settings, Misc](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/chansettings_misc.htm)).
- Coproducer: the form option's tempo "standard" (form.whole_song_turned) picks the style's own tempo when the speed-up stays within
  x1.35; the build stretches the vocal clips itself.

## Form

- **Each pass a different job** (F11): in the playlist, the verse 1 clip over the full groove, the chorus 1 clip over the break's
  patterns (no bass pattern there), one bar with only the vocal's last words and the noise sweep, then the drop with the hook clips;
  verse 2 over a second break; chorus 2 over the drop patterns. Markers named Intro, Groove, Break, Stop, Drop. Coproducer:
  form.whole_song_turned (verse_as groove then break, chorus_as break then drop, drop_after 16, tail_break 2, gap_before_drop bar).
- **Drums that layer in**: two patterns, the kick alone and the full groove, eight bars each. Coproducer: drums.house_layer_in.

## Drops and transitions

- **The stop bar**: leave the bar before the drop empty of drum, bass and music clips (or gap the music bus for four beats), place a
  one-bar white-noise sweep that rises to the downbeat, and let the vocal clip run into it. Coproducer: fx.stop_bar_sweep (a one-bar noise
  riser cue and a four-beat gap on the music bus).
- **Drop halves**: automate the bass synth's filter cutoff open for the first 8 bars and closed for the second, add an off-beat chord
  stab pattern in the second 8, and lower the hook clips' volume there.

## Harmony

- **Two chords a bar, pushed**: in the chord channel's piano roll, the first chord from beat 1, the second from the 16th before beat 3
  (step 8 of 16); the bass follows the same roots. Coproducer: harmony.iii_IV_ii_V_pushed, locked (the engine keeps the record's chords
  otherwise); its loop is written in the major key and moves to the relative major under a minor song.

## Bass and mix

- **A dotted-8th bass**: notes on steps 1, 5, 8, 11 and 14 of each bar, two 16ths long, in the channel rack's step sequencer or the piano
  roll (the bass MIDI from `extract_song_loops` is the record's own line). Coproducer: bass.dotted_pump.
- **Ducked by the kick**: the kick on its own insert, "Sidechain to this track" from its send to the bass insert, Fruity Limiter's COMP
  tab with SIDECHAIN set to the kick, THRESH under the kick's peaks, RATIO up, REL and CURVE for how it swells back
  ([Fruity Limiter](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Fruity%20Limiter.htm)).
  Coproducer: the production recipe's pump (mix.pump_deep, mix.mono_low_hard_pump).
- **Mono low end**: keep the kick and bass inserts mono and narrow the music below about 150 Hz (a mid-side EQ or a stereo tool on the
  music bus). mix.mono_low_hard_pump carries the target (side 35 dB under mid below 150 Hz) for the panel to check.
