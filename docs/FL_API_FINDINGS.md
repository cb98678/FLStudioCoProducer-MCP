# FL Studio API findings (measured, not documented)

Measured on FL Studio 2026 Producer Edition v26.1.7 (build 5654), API version 45, Python 3.12.1, using
`coproducer probe report --mutating`. The published stubs (https://il-group.github.io/FL-Studio-API-Stubs/)
do not list the functions below, and FL builtins expose no signatures, so these facts come from TypeError text and readback.

## Tempo
- `mixer.getCurrentTempo()` returns milli-BPM as an integer (128000 for 128 BPM).
- `mixer.getCurrentTempo(True)` returns BPM as a float (128.0). This is the reverse of what the stub text says.
- `mixer.setCurrentTempo(milli)` takes whole milli-BPM. 128000 works; 127.5 raises "Range error". The valid range is 10000 to 522000 (10 to 522 BPM); 9999 and 523000 raise "Range error". It accepts at most 2 arguments, and a second argument of 1 or True raised "Range error" in the probe, so use one argument only.
- Module: `set_tempo_verified` (writes milli-BPM, reads back BPM).

## Patterns
- `patterns.setPatternLength(index, length)` takes exactly 2 arguments. `setPatternLength(1, 8)` reads back 8 from `getPatternLength(1)`.
- `patterns.incrementPatternLength(index, delta)` takes exactly 2 arguments. +1 and -1 changed the length by 1 each.
- `patterns.clearPattern(index)` takes at most 1 argument. On a clone with one lit step it cleared the step data: `getGridBit` counts went from [0,0,1,0,0] to all zero, `isPatternDefault` went from 0 to 1 and `patternCount` dropped by one. On a pattern that has data FL opens a confirmation dialog ("The selected pattern is about to be cleared!") that blocks the bridge until someone clicks OK or ticks Remember my choice. An already default pattern needs no dialog. Only step data was checked, not piano roll notes.
- `patterns.isPatternDefault(index)` is 1 for an untouched pattern and 0 once it has data. `patternCount()` counts non-default patterns (it was 0 with only default patterns).
- `patterns.clonePattern(index)` makes the clone the active pattern. A clone of a pattern whose step ran past the end had length 48 where others are 16, so the length unit and auto-extension still need checking.
- Module: `clear_pattern_verified`.
- `patterns.movePattern` (at most 1 argument) and `patterns.duplicatePatternData` (exactly 1) are present and untested.
- Module: `set_pattern_length_verified`.

## Swing
- Swing is on `channels`, not `patterns`: `channels.getSwing()` (no arguments, returned 0.0 in a fresh project) and `channels.setSwing(value)` (one real number). The scale is 0.0 to 1.0. Out-of-range values are clamped, not rejected: 1.5 and 25 both read back as 1.0.
- Module: `set_swing_verified`; `set_tempo_and_swing` uses it.

## Other new functions (present, arity only)
`general.setNumerator/setDenominator/setRecPPQ` (1 integer each), `general.getProjectTitle` (none, returned an empty string),
`mixer.getTrackCount` (none, returned 16 where `trackCount()` reports 18), `mixer.getPluginMixLevel/getPluginMuteState` (2 arguments),
`mixer.setPluginMixLevel` (at most 4), `mixer.setPluginMuteState` (at most 3), `channels.fillEachNSteps` (at most 5),
`arrangement.selectionSet` (at most 5), `arrangement.selectionClear/selectionIsActive` (none), `transport.globalTransport` (at most 4),
`transport.setSongPos` (at most 2). There is still no sidechain routing API and no project save function.

## Mixer fader law
`mixer.getTrackVolume(i)` is a normalized fader position. `getTrackVolume(i, 1)` gives dB:

| position | dB |
|---|---|
| 0.0 | negative infinity |
| 0.25 | -19.05 |
| 0.5 | -9.18 |
| 0.8 | 0.0 |
| 1.0 | +5.59 |

## Undo
`general.saveUndo()` adds an entry to FL's History panel, but `general.undo()` did not restore a script write when read back
immediately, with `saveUndo` before or after the change. Do not rely on undo as a safety net. Autonomy stays in sandbox copies.

## Files
FL's Python can write only inside the bridge script's own folder (`...\Settings\Hardware\coproducer`), and cannot delete there.
Writes to the home folder and to `C:\coproducer\sandbox` fail. Results must come back over the bridge.

## Piano roll scripts (measured on 26.1.7, with the official reference shipped in FL's own `Piano roll script reference.txt`)
Official sources: https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/pianoroll_scripting_api.htm and
https://il-group.github.io/FL-Studio-API-Stubs/piano_roll_scripting/.
- Scripts are `.pyscript` files in `Documents\Image-Line\FL Studio\Settings\Piano roll scripts`. In the piano roll, the wrench Tools menu lists them in its right column, under "Run last script again" (Ctrl+Alt+Y) and "Open script folder".
- Choosing a script opens a dialog with Preview, Reset, Regenerate and Accept. With Preview on, the script has already run once, and the notes are visible before Accept.
- `score.PPQ` is 96. `Note.time` and `Note.length` are ticks, `velocity` and `pan` are 0 to 1. `addNote`, `getNote` and `deleteNote` read back exactly.
- The module `flpianoroll` also has `Pattern` and `score.length`, `score.loadScoreFromFile(path)` (one string argument). `loadScoreFromFile` did nothing with a standard MIDI file, so it probably reads FL's own score format. Not used.
- File writes work only in the script's own folder (the working directory). Writes to the sandbox, the Hardware script folder, Documents and the home folder all fail. So the generated script writes `<name>.result.json` next to itself, and the host reads it from the Piano roll scripts folder.
- Verified end to end: `write_notes_via_script` generated a script, FL wrote 9 notes, and `check_notes_written` confirmed every note (pitch, tick, length, velocity) from the result file.
- Opening the piano roll with F7 on this layout put its window mostly off screen. Maximizing it fixed that.

## Command-line render (measured 2026-10-18, FL 26.1.7)

- `FL64.exe /R /Ewav /O"<folder>" "<project.flp>"` renders a saved project to `<project name>.wav` in the folder. Switches match the [FL manual](https://www.image-line.com/fl-studio-learning-content/fl-studio-online-manual/html/fformats_save_export.htm).
- Paths must be absolute. FL does not run from the caller's folder, and a relative `/O` path gives the dialog "Unable to create folder" and exit code 0 with no file.
- The output is a float WAV (format tag 3), which Python's `wave` module cannot read; use soundfile.
- Whether a render can run while another FL instance holds the bridge is unverified.
- Scratch project measured -34.79 LUFS integrated through `measure_integrated_loudness`.

## Local brain (measured 2026-10-18)

- Machine has an RTX 3090 (24 GB), not 16 GB.
- `gemma4:12b` through Ollama's OpenAI endpoint: plain reply 10.2 s (includes load), tool call 0.8 s and returned `set_tempo {"bpm":128}`. It thinks before answering.

## Rendering needs FL closed (measured 2026-10-18)

- `FL64.exe /R ...` with another FL copy running exits with code 0 after 0.7 s and writes no file (FL hands the job to the running copy). With FL closed the same command renders (-34.79 LUFS for the scratch project).
- So a render while the bridge is connected means a restart: `render_with_restart` closes FL gracefully (taskkill without /F, refused when the project has unsaved changes), renders, starts FL on the project again, and waits for the bridge to answer.
- FL's window title reads `<project>.flp - FL Studio 2026`; `save_sandbox_project` relies on that.

## Channel indexes: global versus current group (measured 2026-10-22)

- `channels.channelCount(globalCount=True)` and calls with `useGlobalIndex=True` address every channel in the project (160 in the
  DTP project, 161 after cloning the sub). Global ids equal the channel ids in the saved FLP.
- Without the global flag, indexes cover only the current channel group. New channels and audio clips land in the current group,
  so the same channel has different numbers in the two schemes. `route_channel_to_track_verified` takes the group index.
  Use global indexes for reading and listing (`tools/chan_global.py list`), and verify by name after any routing write.
- Generator channels take plugin calls as `op_plugins_*(index=<global channel>, slotIndex=-1, useGlobalIndex=True)`.

## Generator plugin parameters (Sytrus and SimSynth)

- Sytrus exposes 597 parameters; the operator waveform and ratio are not among them. SimSynth exposes 26, with no waveform.
  Pick or clone a patch instead of trying to design waveforms through the API.
- Sytrus pitch-envelope amount: raw 0 reads 0 cents, raw 0.25 reads plus 1200 cents.
- Setting a Sytrus channel volume through the API read back but did not change the measured sub band; set levels on the mixer
  track and confirm with a render.
- A full parameter scan (`tools/gen_params.py find`) can run past two minutes. The queue runner is the right place for it; poll the
  `done/*.out.txt` result instead of waiting inline.

## Not in the API, done in the file

Pattern note writing, playlist clips, sampler sample paths and channel cloning are done offline with `coproducer.flpfile`
(see `FLP_FORMAT.md`). The editable-first rule that decides when to use it is in `PRODUCTION_POLICY.md`.

## Mix-stage findings (DTP remix, 2026-10-22)

- **A plugin edit can have no effect because the slot is bypassed.** Bypass state is not readable or writable through the script API
  here. `set_plugin_param_by_name` reads the new value back as verified even when the slot is bypassed, so a verified readback is not
  proof of an audible change. Prove it with a render and a null or spectrum check. In the DTP master chain both Fruity parametric EQ
  slots and the Soundgoodizers were bypassed; Maximus, Fruity Balance and Fruity Limiter were active.
- **The mixer track's built-in EQ is always in the path and fully scriptable.** `set_eq_gain_verified` (band 0 low, 1 mid, 2 high; raw 0.5 flat,
  about 36 dB per raw unit) on track 0 changed the render: high band raw 0.375 (about -4.5 dB) took the air band from -10.6 to -13.9 dB and
  the spectral centroid from 1811 to 976 Hz. Prefer it to a bypassed plugin EQ when a tone fix is needed.
- **A heavy master limiter hides fader moves.** With Fruity Limiter gain at 16.3 dB, a +2.5 dB snare fader and a -5 dB tom fader moved the measured hits
  by only 0.3 and about 1 dB. Check the level of a part at its own hits (band-pass window after the event) before and after, and expect
  to lower limiter gain if balance moves must be audible.
- **Whole-file band numbers mislead when the arrangement differs from the reference.** Band energies are shares of the total, so a brighter render
  makes the sub band look low. Compare bar by bar with the bar map instead (`tools/spec_match.py`): after the same edits the sub region
  was slightly hot, not deficient. Drop bars past the end of the shorter file, since silent bars pull every band down.
- Limiter ceiling raw 0.42 is -2.4 dB and gave -13.75 LUFS at -1.79 dBTP here (the reference remix is -13.9 LUFS).


## Effect slot state and mixer EQ scale (measured 2026-10-22)

- `mixer.getPluginMuteState(track, slot)` returns 1 when the plugin is processing and 0 when it is bypassed, despite the name. Checked on the DTP master:
  Maximus and Fruity Limiter read 1 (active), both Fruity parametric EQ 2 slots and the Soundgoodizers read 0 (bypassed), matching the earlier LED findings.
  `mixer.getPluginMixLevel(track, slot)` returns the slot's wet mix, 1.0 on every slot here. The setters take (track, slot, value) and are built as
  `op_mixer_set_plugin_mute_state` and `op_mixer_set_plugin_mix_level`; the setters are not yet tried on the live machine.
- Modules: `list_effect_slots`, `set_effect_active_verified`. These replace the old "bypass is not exposed" note. FL must be restarted to load a new device script.
- Built-in mixer EQ gain scale: about 31 dB per raw unit, 0.5 flat, so the usable range is about plus or minus 15 dB. Measured from renders of the probe
  project (`sandbox/eq`): high shelf raw 0.65 gave plus 4.7 dB and 0.80 gave plus 9.3 dB above 12 kHz; the mid peak at 0.80 gave about plus 10 dB near 1 to 2 kHz;
  the low shelf at 0.80 gave plus 8.4 dB at 30 to 60 Hz. Module: `set_eq_db_verified`.
- `fl-studio-api-stubs` must be installed (`pip install fl-studio-api-stubs==37.0.1`) before `tools/gen_inventory.py` and `tools/gen_l1.py` can run; without it the inventory step is skipped and new L1 ops fail generation.
