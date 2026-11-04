---
name: vocal-slice-align
description: Use when a vocal in an FL project sounds off the beat, when the person has sliced a vocal into pieces and moved them by hand, when vocal clips need to lay in line with the grid, be quantized as clips or positioned across the grid without cutting a word, or when piano, chords and bass need quantizing in a remix. The measured rule, the tool, the checks and the guideline on quantizing.
---

# Vocal slices in line with the grid

The person (2026-11-02, Hello Toni): "Quantize the piano and bass and make the vocals all lay in line. I did slices and aligned some, but
they are not perfect. If you need to slice audio of the main vocals like I did, let's create the skill to slice vocals that do not fall
directly on beat in chunks like I did and position them across the grid." And: "we should always when possible keep piano and bass
quantized unless it's counter to the creative purpose of the note specifically. These are not rules but suggestions."

Guidelines, not guardrails: break any of this when the song asks for it, say so in the plan, and judge by ear.

## What was measured (Hello Toni, 2026-11-02)

* Her syllables cluster just before her own beats and half beats (the onset phase histogram over one of her beats: 45 of 135 onsets in the
  last eighth before the beat, 34 just before the half beat). With a 25 ms lead added, her onsets sit on her 16th grid (median 13 ms off).
* Dragging a slice by eye until its first syllable hits a grid line puts a pickup syllable on the beat and the stressed one a 16th early:
  the person's "of time" sat with its pickup on the bar and the phrase a quarter beat late; verse 1 sat 0.56 beat before her bar.
* A held word sliced in the middle and nudged by 0.05 beat clicks; a slice under which the unsliced copy still plays doubles (+6 dB) and flams.

## The rule (coproducer.vocalalign, tools/align_vocal_clips.py)

1. The vocal file plays at its own speed on FL's Stretch (skill remix-from-stems): one of the singer's beats is one project beat, her beat
   grid is `warp_to_grid`'s steady grid (source bpm, origin), clip windows are the file's own milliseconds.
2. Collect every clip of the vocal file and of its slice files (FL's "NAME - Part_n.wav", located in the long file by cross-correlation).
3. Identical clips on one mixer track play once; a shorter clip whose material already plays at the same time on the same mixer track
   (within a beat) is a flam or a forgotten copy, and goes. Clips of one channel whose windows touch in the file and continue in the
   playlist are one clip again.
4. A phrase (3 of her beats or longer) moves by the smallest amount that puts her beats on the project's beats, plus her lead
   (`newtimeview.best_lead`); from 8 beats on her even beats go to beats 1 and 3 of the bar, so her two-beat chord changes agree with the
   stabs. A riff (shorter) keeps the feel the person chose: its first onset snaps to the nearest 16th. A throw (a clip on another mixer
   track cut from inside a phrase) follows its phrase.
5. Rewrite the clips on one channel and one playlist row per mixer track (Vocal, Vocal FX); remove the clone channels and the slice
   files (`flpfile.remove_channel`, `renumber_channels`); point the samples next to the saved project.
6. Check: `tools/check_vocal_coverage.py --flp PROJECT --words ... --vocals ...` (every word once, gaps silent), the measurement script's
   `her_grid_offset` (0 plus the lead for phrases) and `to_16th` (0 for riffs), then render and listen.

    python tools/align_vocal_clips.py PROJECT.flp --vocal-file VOCAL.wav --source-bpm 86 --origin 0.0755 --samples-dir FOLDER
        --mixer-rows 10=1,16=2 --mixer-channels 10=24,16=30 --out ALIGNED.flp --report align.json

Without `--out` it only prints the plan. Example: sandbox/remix/hellotoni_tech_house_aligned_v1/build_aligned.py (alignment, quantize,
tidy, samples, render, master, checks on the person's own project; their file is only read).

## Quantizing the parts

`flpfile.quantize_notes(channels, ppq // 4)` moves note starts to the 16th grid and leaves lengths (a pluck's short gate is on purpose).
Piano, chords, stabs and bass stay quantized unless a note is off the grid for a reason (a hat or shaker humanized by 4 ticks is a
groove, not a mistake; the voice-lead synth that follows her Newtone melody is quantized once the voice is in line). Report what moved.
