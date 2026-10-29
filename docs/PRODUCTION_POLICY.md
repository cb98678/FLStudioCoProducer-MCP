# Production policy: editable first

This is the standing rule for every build and remix the co-producer does. It comes from the user's instruction
during the DTP remix and is encoded in the `editable-first` skill, the `co-producer-protocol` skill and the tools
named below.

## The rule

1. Drums are sampler channels in the channel rack plus patterns. The sounds may be generated one-shots (kick, snare,
   clap, hats, shaker, rim, tom, crash), existing samples, or the user's own. The beat itself is notes in patterns.
2. Bass, chords, leads and arps are plugin channels (a synth the user owns) plus piano-roll notes. If a generated sound
   is the target, find or build a patch that matches its tonality and frequency, then play it with notes.
3. Generated or recorded audio clips are the exception. Use them when editable parts are not conducive, or when audio
   has a clear advantage.
4. Generating sounds, samples and vocals is allowed, except a clone of a real person's recorded voice (see Vocals below). The rule is about where the result lives in the project.

Why: the user can change a note, a velocity, a pattern, a sample or a patch afterwards without asking for a re-render,
the model can diff and verify notes, and the mix stays workable (faders, EQ and sidechain per part).

## When audio is justified

| Case | Why audio wins |
| --- | --- |
| Vocals, vocal chops, spoken or sung lines | The performance is the asset; a synth cannot recreate it |
| Risers, downlifters, reverse crashes, sweeps, impacts | One-shot FX with long evolving noise; a synth patch gains nothing and a sampler hit is awkward |
| Long evolving textures and pads recorded from a source | Not note-based |
| Resampled material (bounce of a processed part, a chopped loop the user likes) | Processing is baked in on purpose |
| The user's own recording they want kept as is | Keep their audio; do not rebuild it |
| A sound with no available synth or sample that can reach it | Say so, then use the generated audio and note the gap |

Anything outside the table is a build with channels and notes. When in doubt, build editable and keep the audio only
as a reference sketch.

## Record the reason

Whenever a part is delivered as audio, write one line in the spec sheet (`record_decision`) naming the case from the
table. A part delivered as audio with no case is a bug in the plan.

## Practices learned on the DTP remix

- **Grid first.** Measure where the reference (the user's target remix) sits against the project grid and shift generated
  parts to match. DTP: 140 BPM, 96 PPQ, 384 ticks per bar, remix content about 2 sixteenth steps later than the project
  grid, so drums and bass were shifted by 2 steps.
- **Sections as data.** Write the section map (intro, kick in, groove, break, build, drop, main, dip, outro) as a list
  and generate the drum plan from it (`coproducer.drumplan`). Review the plan as data before touching the project.
- **Tension recipe.** Break: pedal swell with velocity ramp, octave layer joins late. Build: kick thins then drops out,
  snare roll density steps 4th, 8th, 16th, 32nd across the build, hats open up, a rising arp on a pluck, a gated sub,
  then a held low note and a one-beat silence of kick before the drop. Drop: impact, reverse crash into the downbeat,
  crash on 1, then a lean first phrase before the full groove.
- **Fills and crashes.** A fill in the last bar of each 8 or 16 bars, a crash on section starts and every fourth bar of
  long sections, rotating fill kinds so no two neighbors match.
- **Sidechain-free ducking.** The API has no sidechain routing, so cut bass notes where the next kick lands
  (`coproducer.tension.truncate_at_kicks`). Pre-ducked audio is a last resort.
- **FX stay audio.** Impacts, risers and downlifters live on one FX channel as an audio clip (`FX Risers`), built from
  `fx_cues` and the `oneshots` voices.
- **One clone per synth part.** Clone an existing synth channel so its patch comes with it, give it its own mixer track,
  and mute the audio version it replaces instead of deleting it.
- **Compare like with like.** Match reference and render bar by bar (`tools/spec_match.py`) before judging a band. Whole-file band shares move whenever the highs change.
- **Measure, then mix.** After the build, render and measure (sub, bass, mid, air bands, crest, LUFS, true peak) against
  the reference numbers before touching faders.

## Vocals

- **Edit the recording that is there.** Clean it (`coproducer.vocalfx`), trim lead-ins and put onsets on the grid (`coproducer.vocalclips`), then set its level in the mix.
  Keep each file at the level it had so the balance the producer set between clips survives.
- **Keep the length of any stretched sample.** See `docs/FLP_FORMAT.md`.
- **Do not clone or synthesize a real person's voice from a recording of them.** A sample of a speaker (a speech, a voice note, an interview) is theirs;
  a cloned voice saying new words would put words in their mouth. Offer the user's own voice, a clearly generic synthetic voice, or more editing of the original.
- **Check the source before you process it.** Transcribe it (`tools/transcribe_vocals.py`) so you know what the material is and who it is likely to be.

## Modes

- **Remix or build.** Full editable-first flow above.
- **Mix and master only.** Do not rebuild or replace parts. Gain stage, EQ, bus compression and limiting only, using
  the gain-staging, mix-engineer and mastering skills.

## Tools that implement this

| Need | Tool |
| --- | --- |
| Sample kit | `coproducer.oneshots.write_kit`, `python tools/flp_tool.py kit DIR` |
| Drum plan from sections | `coproducer.drumplan.plan_drums`, `fx_cues`, `to_note_bytes` |
| Tension and bass notes | `coproducer.tension` |
| Patch the sandbox FLP | `coproducer.flpfile.Flp`, `python tools/flp_tool.py` (format in `FLP_FORMAT.md`) |
| Channel inventory and parameters | `tools/chan_global.py`, `tools/gen_params.py`, `tools/dump_gen.py` |
| Measure a render | `tools/quick_measure.py`, `tools/stem_report.py` |
