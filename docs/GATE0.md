# Gate 0 run sheet

Everything below needs FL Studio on your Windows machine. Each step says what it settles and what to send back. Do them in order. Use a throwaway or copied project for anything marked WRITES.

Before you start: update FL Studio, install loopMIDI, install the repo (see README), run `coproducer doctor`, run `coproducer setup` and do its steps A and B.

| # | Command | Settles | Pass means |
| --- | --- | --- | --- |
| G0-1 | `coproducer probe ping` | The bridge works through loopMIDI | Five round trips, each under 2 seconds, with the FL version |
| G0-6 | `coproducer probe throughput` | The safe SysEx size | `passed: true`. Put `safe_frame_size` (or lower) in `config.toml` as `[bridge] max_payload` |
| G0-2, G0-7, G0-9 | `coproducer probe install-fl`, then in FL choose controller type `Coproducer Probe (user)`, open View > Script output and wait for "probe done", then `coproducer probe report` | The real API inventory, whether `json` imports, whether a script can write files, tempo and song position units, save and tempo setter names | The report lists which planned functions are missing on your build. Send me the report |
| G0-3 | `coproducer probe install-fl --mutating` on a COPY of a project, same steps as above | WRITES. Fader law (0 to 1 value versus dB), whether `general.undo()` reverses a script write, marker readback | The `fader_law`, `undo` and `markers` entries are filled in |
| G0-5 | Save a sandbox copy, set `[fl] exe` in `config.toml`, then `coproducer probe render --project sandbox\yourcopy.flp` | The command-line render | A WAV exists and loudness is a number |
| G0-8 | `coproducer probe desktop`, then run the `save_project_copy` recipe with `[desktop] allow_unverified = true` | A route to save the project | A file appears in the sandbox |
| G0-9 | Piano roll: run `write_notes_via_script` for 4 notes, `arm_piano_roll_script_gui`, `run_piano_roll_script_gui`, `check_notes_written` | The note-writing route (the script structure `createDialog` and `apply` is the one the factory scripts use; this confirms it on your build) | `check_notes_written` returns verified |
| G0-10 | `coproducer install-models`, then `coproducer probe models` | Each model loads and passes a smoke test | Every installed model is `passed` (Flamingo may show `fallback`) |
| G0-S | `coproducer probe stress`, then `coproducer probe stress --only desktop` | The bridge and desktop checks survive abuse (read-only; the desktop run briefly minimizes FL and opens Notepad) | Every scenario PASS. Results and the last measured numbers: `docs/STRESS_REPORT.md` |

After each GUI recipe step, `coproducer calibrate <anchor>` records any click points a recipe asks for (the export recipe needs `export_split_checkbox` and `export_start`). Recipes stay marked draft (`verified: false`) until you confirm them; flip a recipe's flag in `gui_recipes/<name>.json` after you have watched it work.

## What to send back

1. The `probe report` output (all of it).
2. The `ping`, `throughput`, `render`, `desktop` and `models` JSON.
3. Any recipe that failed, with the screenshot it saved in `sandbox/screens/`.

With those I can freeze the interfaces: fader law, tempo and position units, pattern and playlist numbering, the save route, the note route, and the safe SysEx size.

## Troubleshooting: "cannot find MIDI port"

Windows reports loopMIDI ports with an index after the name, for example `coproducer-in 1`. The tool now matches `coproducer-in` to that name, and the error lists every port the system can see. If the list does not show your two ports:

1. Make sure loopMIDI is running (tray icon) and lists `coproducer-in` and `coproducer-out`.
2. Close any other program holding them (a DAW, a MIDI monitor). Windows MIDI ports are often single-client.
3. See what Python sees: `python -c "import mido; print(mido.get_output_names(), mido.get_input_names())"`. If the names differ from the config, set `[midi] out` and `in` in `config.toml` to the real names, or to the part before the index.

## Troubleshooting: ping prints "no complete reply"

The ports opened, so the host side works. Open FL's View > Script output, run `coproducer probe ping` again, and read the Script output.

| What Script output shows | Meaning | Fix |
| --- | --- | --- |
| Nothing at all, not even "bridge ready" | The script is not loaded | MIDI Settings: pick the `coproducer-in` input, set Controller type to `Coproducer (user)`, then click Reload in Script output. Check the file is `Documents\Image-Line\FL Studio\Settings\Hardware\Coproducer\device_coproducer.py` (run `coproducer setup` again to copy it) |
| "bridge ready" but no "sysex in" lines during the ping | FL is not receiving from the port | The input `coproducer-in` is not enabled, or a different FL input has the script. Tick Enable on `coproducer-in` |
| "sysex in ... ours=False" | FL receives something else | The bytes are not our frames; send me the line |
| "sysex in ... ours=True" and "sysex out" but the probe still times out | FL answers but the reply never reaches the host | The output `coproducer-out` is not enabled, or its port number differs from the input's. Give the input `coproducer-in` and the output `coproducer-out` the same Port number |
| "sysex in ... ours=True" but no "sysex out" | The script failed while building a reply | Send me the lines around it |

Reload the script (or restart FL) after every change to the input, output or port numbers.
