# Playing loops and kits in FL Studio

From the FL Studio online manual (pages read 2026-10-28); the controls named are FL's own.

## A loop that follows the project tempo

Load the loop in a Sampler channel or drag it onto the playlist as an audio clip. In the channel settings, Time stretching:

- TIME: right-click it and choose Project tempo; this also locks the sample to the tempo, so later tempo changes stretch it. For an audio
  clip, the clip menu in the playlist has Fit to tempo with the project's tempo.
- Mode: e3 Generic (the default, any material) for full loops; e3 Mono for a vocal or a solo instrument (formants preserved); Slice
  stretch or Slice map for drum loops with slice markers on the hits (Slice stretch at a tempo equal to or lower than the project, Slice
  map equal or higher; the slices move, they are not stretched, so the transients stay); Stretch or Stretch pro (with F.Shift for the
  formants) when the tempo is automated, since the elastique modes do not follow tempo changes.
- PITCH shifts without changing the length; MUL multiplies the length (twice as long at the same TIME).

Source: [Sampler channel settings, Time stretching](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/chansettings_sampler.htm).

## A loop played as slices

- **Slicex** slices a loop by beat detection (or the WAV's own slice or region data) and plays each slice from a key, so the groove can
  be re-sequenced in the piano roll. A slice is given a key with its region marker's Trigger note. Tools > Time > Drum(loop) stretch
  stretches globally or per slice (it overwrites the sample data); Tools > Regions > Declick out all regions removes clicks between
  slices. [Slicex](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Slicex.htm)
- **Fruity Slicer** loads a loop (Open and slice a sample), takes its BPM and BEATS (Auto-fit matches the project tempo), slices it
  (Dull, Medium or Sharp auto-slicing, or even beat divisions), and Dump beat to piano roll writes one note per slice in the loop's
  rhythm, so changing the notes changes the groove. [Fruity Slicer](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Fruity%20Slicer.htm)

## A kit as channel-rack drums

Each one-shot on its own Sampler channel, the pattern typed into the step sequencer from the README's step strings (X a full step, x a
softer one), or the section's MIDI file dragged into a channel's piano roll. Kick on its own mixer insert, so it can be the sidechain
source: on the bass or music insert, Fruity Limiter's COMP tab, SIDECHAIN set to the kick's insert after "Sidechain to this track" on the
kick's send; THRESH below the kick's peaks, RATIO up, REL and CURVE for the swell back ([Fruity
Limiter](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Fruity%20Limiter.htm)). The coproducer's own
pump (a volume shaper following the kick) does the same from the production recipe.

## Tuning a loop or a sound to the record

Measure the record's tuning on a monophonic stem (the vocal or the bass) before retuning anything: Sorry and its remix both sit within 5
cents of A440. A channel's FINE knob (Misc settings) tunes it in cents; a channel responds to the Main Pitch control only when its Enable
Main Pitch box is ticked. [Channel settings, Misc](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/chansettings_misc.htm)
