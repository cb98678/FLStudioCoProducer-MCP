---
name: loops-and-kits
description: Use when the person wants clean drum loops, one-shots, a kit, bass lines or instrument loops cut from a song's stems or from a remix being studied, wants one note of a record's synth or bass sampled and played from the piano roll, wants a captured loop played in a remix, wants loops or kicks on this computer that match a groove (FL Studio's factory Packs), or wants a record's groove or bass copied into FL Studio as editable channel-rack patterns and MIDI. Covers extract_song_loops, find_matching_loops and how FL plays loops and kits (Sampler time stretching, Slicex, Fruity Slicer, the channel rack).
---

# Loops and kits

The person (2026-10-28, with Sorry and Freejak's remix): "Search for loops or create clear drum loops from the existing drums and
original instrumentation, note the bass." A stem separated from a finished master carries bleed (the vocal in the drums, the kick in the
bass), so a bar cut straight from it is not clean. A loop that repeats is: align every repetition and take the median, and what repeats
adds up while what does not (a sung line, a fill, a crash) averages out. The same holds for one drum hit, and a clap that always lands
on a kick comes back clean when that kick, averaged from the beats where it plays alone, is subtracted.

## Steps

1. **Analyse the song** with `build_song_analysis` (beat grid, stems, words). Loops need a steady grid; the report says when it is not.
2. **Choose the sections** from the form, where one pattern repeats: a groove before and after its claps come in, each half of a drop
   whose second half changes, a break. Bars are 1-based on the analysis grid, "name:first-last", comma separated. A study page's form
   table (skill `remix-craft`) gives them.
3. **Cut** with `extract_song_loops` (song_dir, sections, kit_from the cleanest groove, hook the vocal bars of a hook to keep as a cut).
   It writes under sandbox\loops\SONG: drums, bass, music (the other stem) and full loops of 1, 2 and 4 bars per section, the kit, MIDI
   files of the drum pattern and the bass line per section, patterns.json and a README with every number.
4. **Read the README before using anything.**
   - Residual: how loud the part that was left out was against the loop. -20 dB or lower is a clean, programmed loop (Freejak's drums
     -21 to -30 dB); -5 to -10 dB is a played or varied part (the original Sorry's percussion). A loop that does not repeat (residual
     above -3 dB) is skipped, and a stem that is silent in a section (the bass in a break) says so.
   - Bass loops are transcribed from the length that repeats best: notes that repeat every 2 bars with a sound that moves over 4 show a
     cleaner 4-bar loop.
   - Patterns read three bands: kick below 110 Hz, snare or clap 1.2 to 4 kHz, hats above 7 kHz. A band that only hits with the kick is
     the kick's own click (the README says so). Kit voices are named by measurement (a snare's body against its crack, a hat's decay):
     check them by ear before building on them.
5. **Search the computer** with `find_matching_loops` (patterns_path, section; kick_path the kit's kick). Without folders it reads FL
   Studio's factory Packs (Loops and Legacy\Loops; kicks in Drums\Kicks, Legacy\Drums\Dance and the FPC kicks). Loops rank by step
   profile in all three bands (tempo is not compared; FL stretches), kicks by pitch, decay and click. It only reads. FL's factory loops
   are Ogg Vorbis inside a WAV wrapper (format tag 0x674F, slice markers as chapters): the Ogg stream inside is read. A best score under
   about 0.8 means nothing there grooves the same: say so and use the cut loops and the kit. Ask before downloading anything from a loop
   site.
6. **Into FL Studio, editable first** (skill `editable-first`): the kit one-shots on channel-rack Samplers with the pattern in the step
   sequencer, or the MIDI file dragged into the channel's piano roll; the bass MIDI on a synth whose sound `measure_part_sound` drafts
   from the bass loop. Audio loops are for reference, layering and texture; references/fl-loops.md has FL's ways to play them.
7. **Into Serum 2** (skill `serum-wavetables`): the bass loop's held note as a wavetable (`build_wavetable`), the kit and the hook on Serum's
   sample oscillator (`prepare_sampler_sound`), or the whole folder at once with tools/serum_tables.py.

## In the remix: a captured loop, one bass note, one synth note

The person (2026-10-29, with Better Off Alone and the Pickle remix): "capture a perfect loop from the drum and use it in the song remix
... sample a note from that synth and use it in a piano roll". Three plan fields put what was captured into a remix build, each on its
own Sampler channel, editable in the piano roll:

- **drum_loops**: a one-bar loop (or 2, 4, 8) played by one note per loop in the sections it names (`remixplan.drum_loop_notes`).
  Stretch it to the remix tempo first (rubberband, pitch kept) and cut it to exactly one bar; high-pass it at about 150 Hz when the
  kit's kick plays under it, so one kick drives the sidechain. Let the kit play only the kick where a loop carries the claps and hats.
  A captured kick can carry a long low tail the record's bass hid (the Pickle kick: 42 to 46 Hz to 0.4 s); under a pedal bass it reads
  as a second bass note. Shelve it (about -3 dB at 60 Hz) and end it near 0.24 s before the bass goes under it.
- **bass_sample**: one note as the bass part's sample, {file, root_midi}; every bass note is transposed from it. Slice one beat from
  the *averaged* bass loop: it is clean and keeps the record's pump inside it. Tune it with `prepare_sampler_sound` options tune (cents
  measured over the whole stem; a short cut of a sub reads up to a quarter-tone off).
- **sampler_lead**: one note of a synth playing a melody, {sample, root_midi, notes [beat, length, MIDI, velocity], glide, scoop, fall}.
  Find a note with nothing bending into it (a repeated note, not one after a leap) and the quietest pad under it, then
  `prepare_sampler_sound` with options isolate (only that note's harmonics kept), pitch_midi (the note it is: over a chord the pitch
  search can land on the chord's root) and fade_out_s. Bends are slide notes: glide (from the last note while it rings, a constant
  time, the Pickle lead's 0.05 beat), scoop (a semitone up into a phrase start) and fall (down at the end of a long note).

FL's Sampler plays a one-shot sample to its end whatever the note length, so cut a note to the length it should ring. Slide notes work
on native FL instruments only, not on VSTs ([FL Studio manual, piano roll](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll.htm)):
a Serum layer of the same melody plays without the bends.

## Worked example: Sorry and the Freejak remix

Sections "intro:1-2, groove_a:5-12, groove_b:13-20, break:21-27, drop_a:29-36, drop_b:37-44, drop2:53-68" with kit_from groove_b and hook
1-2. The remix's groove reads kick `X...X...X...X...`, clap `....X.......X...`, open hat `..X...X...X...X.`; its bass G G A flat A flat
A flat | F F B flat B flat C on 16th steps 1, 5, 8, 11 and 14; the kick averaged from 16 hits (65 Hz, decay 138 ms), the clap from 16
hits with the kick taken out (its low band 27 dB down). The original's verse reads its dembow (kick on the beats with pickups, the perc on
4, 7, 12 and 15), its percussion varying too much bar to bar for a clean kit. docs/remix_studies/sorry_freejak.md has the full study.

## Worked example: Better Off Alone and the Pickle remix (2026-10-29)

Sections "drum_intro:1-8, bass_intro:9-15, drop:51-66" at 128 bpm. Kit: kick from 22 hits (residual -17.7 dB), clap, open hat; the drop
reads kick `X...X...X...X...`, hats `o.Xox.XoooXox.Xo`; the bass G#1 on every beat in the mix-in, A1 G#2 G#1 A1 at the end of every fourth
drop bar. The practice remix (sandbox\remix\boa_pickle_style_v1, make_sounds.py) plays the drum-intro and drop loops at 129 bpm high-passed,
one beat of the averaged bass loop tuned 22 cents up onto G#1, and the lead's B4 at 50.44 s lifted out of the pad (22 dB of pad removed).
docs/remix_studies/better_off_alone_pickle.md has the study.

## Limits

Averaging removes what does not repeat, never what does: a bass's bleed in the drum stem repeats with the pattern and stays. A section
must hold at least two repetitions of a loop; one is a plain cut and is labelled so. Tempos of found loops are read from their length
(a loop is a whole number of bars) and the onsets; odd-length files can read wrong. The person's originals and FL's Packs are never
written; everything new goes under the sandbox. Sounds captured from someone else's record are for study and private
practice; a release keeps the moves and replaces the sounds.
