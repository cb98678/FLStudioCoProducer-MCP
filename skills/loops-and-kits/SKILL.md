---
name: loops-and-kits
description: Use when the person wants clean drum loops, one-shots, a kit, bass lines or instrument loops cut from a song's stems or from a remix being studied, wants loops or kicks on this computer that match a groove (FL Studio's factory Packs), or wants a record's groove or bass copied into FL Studio as editable channel-rack patterns and MIDI. Covers extract_song_loops, find_matching_loops and how FL plays loops and kits (Sampler time stretching, Slicex, Fruity Slicer, the channel rack).
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

## Worked example: Sorry and the Freejak remix

Sections "intro:1-2, groove_a:5-12, groove_b:13-20, break:21-27, drop_a:29-36, drop_b:37-44, drop2:53-68" with kit_from groove_b and hook
1-2. The remix's groove reads kick `X...X...X...X...`, clap `....X.......X...`, open hat `..X...X...X...X.`; its bass G G A flat A flat
A flat | F F B flat B flat C on 16th steps 1, 5, 8, 11 and 14; the kick averaged from 16 hits (65 Hz, decay 138 ms), the clap from 16
hits with the kick taken out (its low band 27 dB down). The original's verse reads its dembow (kick on the beats with pickups, the perc on
4, 7, 12 and 15), its percussion varying too much bar to bar for a clean kit. docs/remix_studies/sorry_freejak.md has the full study.

## Limits

Averaging removes what does not repeat, never what does: a bass's bleed in the drum stem repeats with the pattern and stays. A section
must hold at least two repetitions of a loop; one is a plain cut and is labelled so. Tempos of found loops are read from their length
(a loop is a whole number of bars) and the onsets; odd-length files can read wrong. The person's originals and FL's Packs are never
written; everything new goes under the sandbox.
