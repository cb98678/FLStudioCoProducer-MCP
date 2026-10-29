# Stem remix pipeline (requested 2026-10-22)

Goal: take an MP3 dropped into the playlist, split it into stems with FL Studio's own stem separation, chop the vocals, turn the instruments into piano roll
parts and the drums into channel rack patterns, and finish a techno remix. Vocal chops, stretching, pitching, auto-tune with Newtone and sample editing
with Edison are part of it. This follows the editable-first rule in `PRODUCTION_POLICY.md`.

| Step | How | Status |
| --- | --- | --- |
| 1. MP3 on the playlist | `import_audio_clip_gui`, `add_audio_clip_to_playlist_gui` | Modules exist, GUI recipes not yet run on this machine |
| 2. Stems | FL's clip menu "Extract stems from sample" (drums, bass, instruments, vocals, each on its own playlist track), per [Slooply](https://slooply.com/blog/how-to-separate-vocals-instruments-in-fl-studio-no-plugins-needed/); the local fallback is `separate_stems` (a model on the GPU) | FL route needs a GUI recipe (`gui-fallback`); the local model route exists and is unit tested only |
| 3. Vocal chops | `coproducer.vocalclips` (onset search, trim, grid snap), `tools/vocal_patch.py`; chops are audio clips or sampler channels | Built and run on the DTP vocals; a chop generator that makes a pattern of slices is not built |
| 4. Instruments to piano roll | `transcribe_to_midi`, `clean_midi_notes`, `quantize_notes`, `import_midi_gui` or `write_notes_via_script` | Modules exist; quality of the transcription is unmeasured |
| 5. Drums to channel rack | Detect hits per stem, match to a sampler kit (`coproducer.oneshots`, `drumplan`), write patterns with `coproducer.flpfile` | Kit and pattern writer built; hit detection from a drum stem is not built |
| 6. Stretch and pitch | Audio clip stretch fields (`coproducer.vocalclips`, `docs/FLP_FORMAT.md`) and the clip menu in FL | Stretch fields are patched on the DTP project; pitch is not |
| 7. Auto-tune | Newtone: load the vocal, global Center, Variation and Transition knobs, per note snap, Advanced Edit for formant and vibrato; Save sample or Send to Playlist as audio clip, per the [Newtone manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Newtone.htm). Live pitch is Pitcher, not Newtone | No API. Needs GUI recipes (`gui-fallback`), then a pitch measure to verify |
| 8. Sample editing | Edison: region and slice, loop, Send sample to Playlist or to a channel, per the [Edison manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/Edison.htm). Edison also runs Python scripts, per [Run command and script editor](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/editortool_run.htm): a script is a `.pyscript` file in `Documents\Image-Line\FL Studio\Settings\Audio scripts`, listed in Tools > Scripting the next time the menu opens, with globals `Editor` and `EditorSample`, `ProgressMsg` and `ShowMessage`, and `CreateScriptDialog` for inputs. The `Sample` class covers normalize, amplify, silence, add sine or noise, center, reverse, reverse polarity, swap channels, insert silence, delete, trim, load from file or clipboard, regions and format matching; `Editor` has `SelectionStartS` and `SelectionEndS`. Reference.txt in the script folder lists the full API. The manual lists no stretch or pitch call there | Same shape as the piano roll script route (`write_notes_via_script`): write a `.pyscript`, then run it from the menu with a GUI recipe. Script generators are built (`coproducer.edison`: `probe_script`, `regions_script`, `gain_script`) and unit tested against a fake `Editor`; the GUI recipe that runs them is not built. Stretch and pitch stay on the clip fields and NewTone, or offline with `coproducer.dsp` |
| 9. Techno remix | `drumplan`, `tension`, `fxbed`, `automation`, mix tools | Built and run on the DTP remix |

Order of work: write the FL stem extraction recipe and run it on one MP3, then the drum hit detector, then the chop generator, then Newtone and Edison recipes.
Each step is proven by a render and a measure, not by the tool reporting success.


## Edison scripting notes (read from the installed Reference.txt and demo scripts, FL 26.1.7)

Source: [Run command and script editor](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/plugins/editortool_run.htm) and the files in `C:\Program Files (x86)\Image-Line\FL Studio 2026\System\Config\Audio scripts`.

- A script starts with `from enveditor import *`. Two shapes exist: a preview style with `createDialog()` returning a `ScriptDialog(title, description)` plus `apply(form)`, and a simple style that builds the form at top level and calls `form.Execute()`.
- The web page names the dialog class `CreateScriptDialog`; the installed Reference.txt names it `ScriptDialog`. The demo scripts use CapitalCase methods (`AddInputKnob`, `GetInputValue`, `Execute`) while Reference.txt lists lowerCamel (`addInputKnob`, `getInputValue`, `execute`). Treat the installed files as the truth for this build and test on the machine before relying on either.
- Positions are sample indexes (`Editor.SelectionStartS`, `Editor.SelectionEndS`). Per-sample Python loops are slow and need `Utils.ProgressMsg`; prefer the range methods (`AmpFromTo`, `NormalizeFromTo`, `AddRegion`) as `coproducer.edison` does.
- Measured on this machine (2026-10-22): `EditorSample.Length`, `NumChans`, `SampleRate`, `RegionCount` and `GetRegion` work. `open()` for writing succeeds only inside the Audio scripts folder (the working directory); `C:\\coproducer\\sandbox` and `C:\\Windows\\Temp` both raise `SystemError: FileIO returned NULL`. Scripts therefore write results beside themselves, and a host job copies them out.
- No stretch or pitch call exists in the API.
- The user Audio scripts folder is empty on this machine. Nothing has been written there yet; ask before writing.

### Edison job runner (built 2026-10-22)

One fixed script, `coproducer run.pyscript`, reads `coproducer_job.json` from the Audio scripts folder, applies a list of ops to the open sample and writes `coproducer_result.json` (lengths, per-op log, regions) next to it. To change what Edison does, change the job file, not the script. `tools/edison_job.py JOB.json --install` validates and writes both. Ops (`coproducer.edison.OPS`): `grid` (regions every N beats at a bpm and offset), `regions` (regions at chosen ms times), `gain`, `normalize`, `fade_in`, `fade_out`, `reverse`, `silence`, `delete`, `insert_silence`, `trim`, `trim_to_bars`, `fit_length` (pad with silence or cut to an exact number of bars), `mono`. Ranges default to the whole sample; `from_ms`/`to_ms` narrow them and `"selection": true` uses the Edison selection.

Tempo alignment splits across tools because Edison has no stretch call: `coproducer.dsp.estimate_tempo` finds the source bpm, `grid` and `trim_to_bars` cut it on that grid, `fit_length` makes it an exact bar count, and FL's own tempo-sync stretch on the channel or playlist clip (or NewTone for pitch) does the stretching.

Fades: the preferred way is volume automation on the playlist clip or mixer track (`add_automation_clip` with a `ramp` curve), which stays editable. The Edison `fade_in` and `fade_out` ops are stepped (48 gain steps) and kept as an optional extra, not part of the default flow. Untested ops are not relied on until they have run once in Edison.

### First stem test (stemstest, 2026-10-22)

FL's "Extract stems from sample" wrote four stereo float WAVs (bass, drums, instruments, vocals, about 264 s each) into `sandbox\\stemstest\\Audio`. `tools/stem_report.py` measured them (loudness, bands, tempo, key). `tools/drum_hits.py` (library `coproducer.drumhits`) found 569 hits in the drum stem: 374 kick, 190 snare, 5 hat, tempo 108.48 bpm, mean distance from the 16th grid 12.8 ms (random would be about 35 ms), 105 bars. The most repeated bars are kick on steps 0, 8, 10 or 0, 6, 8 with snare on 4 and 12. The drum stem holds almost no hat energy (hat-band share at the 90th percentile of hits is 0.11), so hats must come from the drum generator or another stem; lowering the detection threshold only doubles the kick count with bleed. Beat 0 is the first detected hit, not a verified downbeat.

### Editable drums from the stem (2026-10-23)

`python tools/stem_drums.py stemstest.flp stemstest_drums.flp drum_hits.json --kick 0 --snare 3 --mute-ch 6 --set-tempo` writes a sandbox copy with the project tempo set to the fitted 108.478 bpm, the stem's drum channel muted, and kick and snare as notes on the 808 Kick and 808 Snare sampler channels: 60 distinct one-bar patterns over 106 bars (velocities in three buckets so repeated bars share a pattern), on playlist track 44. Notes are shifted by the first hit's time (27.31 s) so they land on the recorded hits. `tools/flp_note_times.py` checks the file without FL: all 374 kick and 190 snare hits have a placed note within 80 ms, mean absolute error 13.8 ms (kick) and 11.6 ms (snare), the error being the 16th-note quantization of live playing. The file has not been opened in FL yet; listen against the stem before trusting it.


## Status after the first full remix (Friends in Low Places v12, 2026-10-23)

All nine steps ran end to end on one song; see `WORKED_EXAMPLE_FRIENDS.md` for the result and `HANDOFF.md` for the commands.

| Step | Where it ended up |
| --- | --- |
| 2. Stems | FL's menu, run by hand (the user), four WAVs. The GUI recipe is still not built |
| 3. Vocal chops | Built: `cutrefine`, `vocalchops`, `tools/refine_cuts.py`; chops are sampler channels triggered by patterns, long phrases are audio clips. Rules: `VOCAL_CHOP_RECIPE.md` |
| 5. Drums | Built for this song: hit detection (`drumhits`) found the groove, but the remix drums are generated (`remixplan.drums`), not copied from the stem |
| 4, 6, 7, 8 | Instruments to piano roll, Newtone auto-tune and Edison were not needed for this remix; the stretch is done offline (`coproducer.dsp`) and pitch by playing the chop at another key |
| 9. Remix | `remixplan` + `tools/build_techhouse.py`, rendered by `render_via_cli` |

### Generalising to a second song (status 2026-10-24)

Built and tested on the first song, not yet run on a second: `songplan` (everything song specific as one JSON file), `remixbuild` (module `build_remix_project`), `songanalysis` (module `build_song_plan`: verified downbeat from kick, snare and drum entrances, hook and chop planner from the lyrics with word times, chop roles, three vocal clip windows, chord loop from bass roots, arrangement and FX cues). Regression on the first song: downbeat 27.3086 s against the hand-set 27.3085 s; hook window 133.8 to 137.0 s against 133.55 to 137.05 s; chorus clip 132.9 to 147.6 s against 132.9 to 148.2 s; the planner finds friends, low places, whiskey, blues away and okay. What is still open: hands-off stems (FL's menu recipe or Demucs), the section map is a template rather than the song's own (`sections_from_bars` exists but is not wired to a tool that measures bar levels), chord loop from the bass stem is a noisy estimate, and the second song itself needs the person's audio. The numbered list below is the original plan.

Everything song specific lives in `src/coproducer/remixplan.py` (tempo, key, chord roots, section map, chop table with the sung words, clip hints) and in the origin constant 27.3085 s. For another song the work to do, in order:

1. Song analysis: tempo (`estimate_bpm_dsp`), key (`estimate_key_dsp`), a verified downbeat (today the first detected drum hit is assumed), sections (`detect_sections_dsp`), word-level lyrics from the vocal stem.
2. Automatic chop planning: pick the most repeated, most singable lines and words from the lyrics, with the word before and after each (the data `CHOPS` holds by hand).
3. A hands-off stem recipe (FL menu through `gui-fallback`, or Demucs on the GPU as the fallback). Done 2026-10-29: `extract_stems_gui`, the local models as the fallback.
4. Chord and bass plan from the instruments stem instead of the fixed `ROOTS8`.
5. A regression set: this song's hand-fixed clips (`..._v3e_userfix.flp`) and the measures `check_vocal_edges` and `find_final_s_end`, so a recipe change cannot make an old cut worse.
6. Hat detection (the drum stem holds almost none; hats come from the generator).

### Sound design

The stabs, arp and sub are Sytrus patches cloned from the DTP project and sound cartoonish; the replacement route through Serum 2 is in `SERUM_MCP.md`.
