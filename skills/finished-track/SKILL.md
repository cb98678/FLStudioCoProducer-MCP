---
name: finished-track
description: Use before calling a remix or a track done, when the person hands back their own edit or final of a build ("compare what I did with what you did", "this is the finished version", "look at what I changed"), and when deciding levels, vocal depth, synth layers, echoes and what to leave switched off. What a finished track looks like in the person's own projects, how to compare a build with their edit, and the checklist.
---

# What a finished track looks like

The person (2026-11-16, their Hello Toni tech house final against the build): "Compare this meticulously vs what you did and lets update
the recipes and understanding of what a finished track looks like. Note the vocal timings and syllables dropping on the metronome. Notice
the layers of Serum synths, the sound design and the bass design. Notice the plugins, echoes, what's turned off and what's turned down
and changed compared from what I produced and what you produced."

Guidelines, not guardrails. Every song still chooses or makes its own sounds (skill creative-variety): what follows is a way of looking
and one finished song's numbers, never a preset sheet. Full study: docs/remix_studies/hellotoni_person_final.md.

## When the person hands back an edit

1. Copy their project into the sandbox beside the build; their file is only read. A project zipped from FL points at a Temp folder, so
   put its samples beside the copy.
2. Find the file they started from before reading any difference as their decision (they opened the produced project, not the contrast
   pass after it, and its missing Section Gain clips were nobody's deletion).
3. `diff_flp_projects` with that file as before and theirs as after: tempo, channels, fader levels, routes, effects added, removed,
   switched off, mix knobs, settings, slot order, FL stretch, channel knobs, Serum 2 parameters, notes and clips.
4. Settings need FL: with their project open, `snapshot_project_params` on the changed inserts, a few per call, and `list_tracks_summary`
   for the faders in FL's own dB. Read only. A render waits until FL is closed; never close their session for it.
5. The voice: `python tools/align_vocal_clips.py THEIR.flp ...` without `--out` prints every phrase's phase against the singer's own beat
   and its syllable weights (skill vocal-slice-align). Compare with the build's placement phrase by phrase.
6. Write the study (docs/remix_studies), the lessons, and change the default the finding points at. Keep their effect settings in the
   library with the source named. Say what could not be read (a Serum 1 state, a loudness without a render) and what is one song's
   evidence.

## What the person's final shows

| Area | The build did | The person's final | Carry over |
| --- | --- | --- | --- |
| Tempo | 119 bpm | 114 | they will change tempo after the build: every sample that carries time is on FL's Stretch with TIME in beats (`tempo_proof` in the build) |
| Vocal phrases | her strummed beats on the project's beats, a lead added | choruses and verse 3 left there; verse 1 an 8th off, one passage a 16th early, the outro an 8th off | the 16th a phrase sits on is the person's choice; a passage sung a 16th behind the guitar goes onto the clicks (`syllable_slots`, `phase_advice`) |
| Vocal slices | 18 long clips | 34 clips cut at phrase ends, nudged within 30 ms by ear | cut at phrase ends so a line can be re-phased; never inside a held word |
| Vocal level and tone | fader 1.5 dB over the kick's; a chop EQ that thinned it | 2.8 dB under the kick's; low shelf +3.7 dB at 103 Hz, mid cuts eased, Subtle stereo enhancer | the voice sits inside the track with its body; chain "vocal" in plugins/chains.json |
| Vocal depth | reverb on the insert only | every clip copied to a second insert: shelves, a dark 1.3 s reverb with 26 ms pre-delay, enhancer, 3.5 dB under the dry fader | chain `vocal_wet` |
| Echoes | chops rendered with an echo tail | those notes removed; the last word copied onto the next beats (some copies in Resample mode, pitched up) into a quarter-note delay | chain `vocal_throw`; echoes stay clips the person can move |
| Chops | on the Music Bus at -1.6 dB | straight to the Master at -6.7 dB, low mids lifted, soft clipper | chops are not ducked with the music; they sit with the voice |
| Lead synth | one Serum 2 patch | three synths on the same notes: the patch, a copy an octave down with a slow filter LFO, a third synth; silent where the hook loops | a drop's lead gets an octave layer with its own movement; parts leave the bars where the voice does something special |
| Bass | sample, chain, its own pump | pump off (the bus pump stays), reverb mix 34 %, -14 dB shelf at 9.7 kHz, a limiter last | one pump is enough; the bass stays dry and dark on top |
| Sub | Serum at -6.2 dB | -14.6 dB and Serum's volume at 0.066 | under a bass sample with low end the sub is a trace |
| Drums | made snare and clap | pack samples (909 Snare, Grv Snareclap 05); kick, hats, perc and all drum faders kept | choose snare and clap by ear of the song from the packs first |
| Transitions | stutter fill, tape stop, risers, filter moves | both Gross Beats off; risers and impacts 4 dB down; filter and reverb throws kept | an effect move has to earn its place; loud FX are not excitement |
| Master | Emphasizer, fader -3.1 dB | Emphasizer off, a little Soundgoodizer, fader -5.4 dB, meters off | the project is a mix with headroom; the master is a later step (skill mastering) |
| Notes | bass, sub, stab ends a tick short of the grid | ends on the grid | starts and ends of bass, sub and chords on the 16th grid (`grid_length`) |

## As a style

The person asked for this finish as a style (2026-11-16): pack meeps_dance_remix on production recipe meeps_dance. It sets their faders, the
master with headroom and the Emphasizer off, one pump on the music bus, the wet double of the voice as a build step, and leaves out the
stutter fill and the tape stop. It does not choose sounds, lines or phrasing: those stay per song. The throw and the octave lead layer
are listed in the pack as moves to offer.

## Before calling it done

* Play it against the click: do the stressed syllables of every phrase drop on the beats or the ands? A phrase with its weight on the e
  and a is moved a 16th; an 8th either way is a choice to offer, with the weights, not to make silently.
* Solo the voice with its double and its throws: is there depth without washing the words, and is every echo a clip?
* Vocal fader against the kick's: over it is a demo, a few dB under is a record. Then chops and FX against the voice.
* Mute each effect move in turn: if nothing is missed, it goes.
* Low end: kick and bass carry it; bring the sub up only until it is felt.
* Lead in the drop: one layer or a stack? Octave, movement, and room for the voice.
* Change the tempo by 5 bpm and back: does everything follow?
* The master: headroom, nothing limiting, analysis tools off.
* Say what was measured and what was only read from the file.
