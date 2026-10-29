# L1 generation report

Generated 319 ops from the FL API stubs 37.0.1 inventory plus the observed live additions.

## Left out on purpose

- ui keystroke functions (closeActivePopupMenu, closeAllMenu, copy, cut, delete, down, enter, escape, insert, jog, jog2, left, moveJog, next, nextWindow, no, paste, previous, right, strip, stripHold, stripJog, up, yes): they act on whatever has focus in the person's session; GUI recipes with guards do that work
- device functions the dispatcher uses itself (baseTrackSelect, createRefreshThread, destroyRefreshThread, directFeedback, dispatch, dispatchGetReceiverPortNumber, dispatchReceiverCount, forwardMIDICC, fullRefresh, hardwareRefreshMixerTrack, midiOutMsg, midiOutNewMsg, midiOutSysex, processMIDICC, repeatMidiEvent, sendMsgGeneric, setHasMeters, setMasterSync, stopRepeatMidiEvent)
- functions with parameter types the generator does not map (lists, constants objects)

## Planned names not generated

- `op_device_midi_out_sysex`: internal to the dispatcher, not exposed as an op
- `op_mixer_set_tempo`: built as op_mixer_set_current_tempo (milli-BPM integer, observed on build 26.1.7)
- `op_patterns_get_swing`: swing is on channels: built as op_channels_get_swing
- `op_patterns_set_swing`: swing is on channels: built as op_channels_set_swing
- `op_ui_get_program_title`: renamed: the real function is ui.getProgTitle, generated as op_ui_get_prog_title

## Wrapper and recipe modules not built

- `import_midi_into_channel`: replaced by import_midi_gui and write_notes_via_script (score.loadScoreFromFile did nothing with a standard MIDI file)
- `save project`: FL 26.1.7 has no save function in general; only midi.FPT_Save and FPT_SaveNew constants exist (untested), so saving goes through save_project_copy (GUI)
- `setup_sidechain_route`: FL 26.1.7 has no sidechain routing function (only getRouteSendActive, getRouteToLevel, setRouteTo, setRouteToLevel); needs a recorded GUI recipe or the human
