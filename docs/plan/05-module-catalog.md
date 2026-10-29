# 05. Module Catalog

Every planned module, by layer, with its one job. Each row starts with the module name in backticks. A script counts those rows, so the counts quoted elsewhere are exact for this file.

Columns: **Module** (name), **Job** (one sentence, one job), **Auto** (autonomy level from file 01), **Cost** (instant, seconds, minutes, gpu).

Notes:

1. **Names in L1 are planning names.** L1 names follow `op_<fl_module>_<function>` and are derived from the module sections of the official reference. The Gate 0 API inventory probe decides which functions exist on your build. A planned op the probe cannot find is dropped, and a function the probe finds that is not listed is added by the generator.
2. **Counts are exact for this file and will move.** After Gate 0, the generator replaces the L1 list with the real inventory.
3. **Every L2 to L6 module is exposed as an MCP tool** unless its manifest says otherwise. L0 and L1 are internal.
4. **Autonomy.** A0 observe, A1 propose, A2 act in sandbox, A3 promote (file 01).

## L0. Transport (host side, pure)

These implement the bridge protocol from file 03, section 4. All are pure except the last three, which touch MIDI ports.

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `encode_sysex` | Pack bytes into 7-bit form for SysEx | A0 | instant |
| `decode_sysex` | Unpack 7-bit SysEx data back to bytes | A0 | instant |
| `split_frames` | Split a byte string into frames of at most N bytes | A0 | instant |
| `join_frames` | Reassemble ordered frames into one message | A0 | instant |
| `build_frame` | Build one complete SysEx frame with header and checksum | A0 | instant |
| `parse_frame` | Validate and parse one SysEx frame into fields | A0 | instant |
| `match_reply` | Pair a reply frame group with its request id | A0 | instant |
| `find_midi_ports` | Find the bridge's virtual input and output port names | A0 | instant |
| `send_request` | Send one framed request on the bridge output port | A0 | instant |
| `wait_for_reply` | Wait for the matching reply or time out | A0 | seconds |

## L1. FL ops (run inside FL; generated)

One FL API call with argument validation, per function. Grouped by official module. All are internal and run only in the dispatcher.

### transport

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_transport_start` | Toggle play or pause | A2 | instant |
| `op_transport_stop` | Stop playback | A2 | instant |
| `op_transport_record` | Toggle recording | A2 | instant |
| `op_transport_is_playing` | Report whether the transport is playing | A0 | instant |
| `op_transport_get_song_pos` | Get the song position | A0 | instant |
| `op_transport_set_song_pos` | Set the song position | A2 | instant |
| `op_transport_get_loop_mode` | Get the loop mode | A0 | instant |
| `op_transport_set_loop_mode` | Toggle the loop mode | A2 | instant |

### mixer

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_mixer_track_count` | Get the number of mixer tracks | A0 | instant |
| `op_mixer_get_track_name` | Get a track's name | A0 | instant |
| `op_mixer_set_track_name` | Set a track's name | A2 | instant |
| `op_mixer_get_track_volume` | Get a track's volume | A0 | instant |
| `op_mixer_set_track_volume` | Set a track's volume | A2 | instant |
| `op_mixer_get_track_pan` | Get a track's pan | A0 | instant |
| `op_mixer_set_track_pan` | Set a track's pan | A2 | instant |
| `op_mixer_get_track_stereo_sep` | Get a track's stereo separation | A0 | instant |
| `op_mixer_set_track_stereo_sep` | Set a track's stereo separation | A2 | instant |
| `op_mixer_is_track_muted` | Report whether a track is muted | A0 | instant |
| `op_mixer_mute_track` | Toggle a track's mute | A2 | instant |
| `op_mixer_is_track_solo` | Report whether a track is soloed | A0 | instant |
| `op_mixer_solo_track` | Toggle a track's solo | A2 | instant |
| `op_mixer_get_track_peaks` | Get a track's current peak level | A0 | instant |
| `op_mixer_get_track_color` | Get a track's color | A0 | instant |
| `op_mixer_set_track_color` | Set a track's color | A2 | instant |
| `op_mixer_get_route_to_level` | Get the send level from one track to another | A0 | instant |
| `op_mixer_set_route_to_level` | Set the send level from one track to another | A2 | instant |
| `op_mixer_set_route_to` | Enable or disable routing between two tracks | A2 | instant |
| `op_mixer_get_route_send_active` | Report whether a route is active | A0 | instant |
| `op_mixer_get_eq_gain` | Get a mixer EQ band gain | A0 | instant |
| `op_mixer_set_eq_gain` | Set a mixer EQ band gain | A2 | instant |
| `op_mixer_get_eq_frequency` | Get a mixer EQ band frequency | A0 | instant |
| `op_mixer_set_eq_frequency` | Set a mixer EQ band frequency | A2 | instant |
| `op_mixer_get_eq_bandwidth` | Get a mixer EQ band bandwidth | A0 | instant |
| `op_mixer_set_eq_bandwidth` | Set a mixer EQ band bandwidth | A2 | instant |
| `op_mixer_get_current_tempo` | Get the project tempo | A0 | instant |
| `op_mixer_set_tempo` | Set the project tempo (API level dependent) | A2 | instant |

### channels

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_channels_channel_count` | Get the number of channels | A0 | instant |
| `op_channels_get_channel_name` | Get a channel's name | A0 | instant |
| `op_channels_set_channel_name` | Set a channel's name | A2 | instant |
| `op_channels_get_channel_volume` | Get a channel's volume | A0 | instant |
| `op_channels_set_channel_volume` | Set a channel's volume | A2 | instant |
| `op_channels_get_channel_pan` | Get a channel's pan | A0 | instant |
| `op_channels_set_channel_pan` | Set a channel's pan | A2 | instant |
| `op_channels_is_channel_muted` | Report whether a channel is muted | A0 | instant |
| `op_channels_mute_channel` | Toggle a channel's mute | A2 | instant |
| `op_channels_is_channel_solo` | Report whether a channel is soloed | A0 | instant |
| `op_channels_solo_channel` | Toggle a channel's solo | A2 | instant |
| `op_channels_get_channel_color` | Get a channel's color | A0 | instant |
| `op_channels_set_channel_color` | Set a channel's color | A2 | instant |
| `op_channels_get_target_fx_track` | Get the mixer track a channel feeds | A0 | instant |
| `op_channels_set_target_fx_track` | Route a channel to a mixer track | A2 | instant |
| `op_channels_get_channel_type` | Get a channel's type | A0 | instant |
| `op_channels_select_one_channel` | Select exactly one channel | A2 | instant |
| `op_channels_midi_note_on` | Play a live note on a channel (audition only) | A2 | instant |

### patterns

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_patterns_pattern_count` | Get the number of patterns | A0 | instant |
| `op_patterns_pattern_number` | Get the current pattern number | A0 | instant |
| `op_patterns_get_pattern_name` | Get a pattern's name | A0 | instant |
| `op_patterns_set_pattern_name` | Set a pattern's name | A2 | instant |
| `op_patterns_get_pattern_length` | Get a pattern's length | A0 | instant |
| `op_patterns_set_pattern_length` | Set a pattern's length (FL 2026) | A2 | instant |
| `op_patterns_jump_to_pattern` | Make a pattern current | A2 | instant |
| `op_patterns_select_pattern` | Select a pattern | A2 | instant |
| `op_patterns_find_first_next_empty_pat` | Find the first empty pattern | A0 | instant |
| `op_patterns_clear_pattern` | Clear a pattern (FL 2026) | A2 | instant |
| `op_patterns_get_swing` | Get the swing amount (FL 2026) | A0 | instant |
| `op_patterns_set_swing` | Set the swing amount (FL 2026) | A2 | instant |

### plugins

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_plugins_is_valid` | Report whether a plugin exists at a channel or mixer slot | A0 | instant |
| `op_plugins_get_plugin_name` | Get the plugin's name | A0 | instant |
| `op_plugins_get_param_count` | Get the plugin's parameter count | A0 | instant |
| `op_plugins_get_param_name` | Get one parameter's name | A0 | instant |
| `op_plugins_get_param_value` | Get one parameter's value | A0 | instant |
| `op_plugins_set_param_value` | Set one parameter's value | A2 | instant |
| `op_plugins_get_param_value_string` | Get one parameter's display text | A0 | instant |
| `op_plugins_get_color` | Get the plugin's color | A0 | instant |

### playlist

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_playlist_track_count` | Get the number of playlist tracks | A0 | instant |
| `op_playlist_get_track_name` | Get a playlist track's name | A0 | instant |
| `op_playlist_set_track_name` | Set a playlist track's name | A2 | instant |
| `op_playlist_is_track_muted` | Report whether a playlist track is muted | A0 | instant |
| `op_playlist_mute_track` | Toggle a playlist track's mute | A2 | instant |
| `op_playlist_is_track_solo` | Report whether a playlist track is soloed | A0 | instant |
| `op_playlist_solo_track` | Toggle a playlist track's solo | A2 | instant |
| `op_playlist_get_track_color` | Get a playlist track's color | A0 | instant |
| `op_playlist_set_track_color` | Set a playlist track's color | A2 | instant |

### arrangement

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_arrangement_add_auto_time_marker` | Add a time marker at a position | A2 | instant |
| `op_arrangement_jump_to_marker` | Jump to a marker | A2 | instant |
| `op_arrangement_current_time` | Get the current arrangement time | A0 | instant |
| `op_arrangement_get_marker_name` | Get a marker's name | A0 | instant |

### general, ui, device

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `op_general_get_version` | Get the scripting API version | A0 | instant |
| `op_general_undo` | Undo one step | A2 | instant |
| `op_general_save_undo` | Create an undo point with a label | A2 | instant |
| `op_general_get_changed_flag` | Report whether the project has unsaved changes | A0 | instant |
| `op_ui_get_version` | Get the FL Studio version string | A0 | instant |
| `op_ui_show_window` | Show a window | A2 | instant |
| `op_ui_hide_window` | Hide a window | A2 | instant |
| `op_ui_get_program_title` | Get the title of the active project | A0 | instant |
| `op_device_get_name` | Get the controller device name | A0 | instant |
| `op_device_is_assigned` | Report whether the device is assigned | A0 | instant |
| `op_device_midi_out_sysex` | Send a SysEx reply on the bridge output | A0 | instant |

## L2. Verified wrappers (host; read back every write)

One operation plus readback, returning a Result with `meta.verified`. Idempotent where the manual allows.

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `ping_fl` | Return FL's version, API level, and active project name | A0 | instant |
| `get_fl_versions` | Return the recorded FL version and API level from the last probe | A0 | instant |
| `get_config_value` | Return one value from `config.toml` by key | A0 | instant |
| `read_project_summary` | Return counts of tracks, channels, patterns with data, playlist tracks, tempo, and project name | A0 | seconds |
| `list_tracks_summary` | List mixer tracks with name, volume, pan, mute, solo | A0 | seconds |
| `find_track_by_name` | Find mixer track indexes whose name matches | A0 | instant |
| `get_track_peak_db` | Get a track's current peak in dB | A0 | instant |
| `set_track_volume_verified` | Set a track's volume and confirm by readback | A2 | instant |
| `set_track_pan_verified` | Set a track's pan and confirm by readback | A2 | instant |
| `set_track_name_verified` | Set a track's name and confirm by readback | A2 | instant |
| `mute_track_verified` | Set a track's mute state and confirm | A2 | instant |
| `solo_track_verified` | Set a track's solo state and confirm | A2 | instant |
| `set_route_level_verified` | Set a send level and confirm | A2 | instant |
| `set_eq_gain_verified` | Set a mixer EQ band gain and confirm | A2 | instant |
| `ensure_playing` | Make the transport play if it is not, then confirm | A2 | instant |
| `ensure_stopped` | Make the transport stop if it is not, then confirm | A2 | instant |
| `ensure_loop_mode` | Make loop mode match the request, then confirm | A2 | instant |
| `set_song_position_verified` | Set the song position and confirm | A2 | instant |
| `set_tempo_verified` | Set the tempo and confirm (API level dependent) | A2 | instant |
| `list_channels_summary` | List channels with name, type, volume, pan, target track | A0 | seconds |
| `find_channel_by_name` | Find channel indexes whose name matches | A0 | instant |
| `set_channel_volume_verified` | Set a channel's volume and confirm | A2 | instant |
| `set_channel_pan_verified` | Set a channel's pan and confirm | A2 | instant |
| `mute_channel_verified` | Set a channel's mute state and confirm | A2 | instant |
| `route_channel_to_track_verified` | Route a channel to a mixer track and confirm | A2 | instant |
| `list_plugin_params` | List a plugin's non-empty parameter names and indexes | A0 | seconds |
| `build_param_map` | Build and cache a name to index map for a plugin | A0 | seconds |
| `get_plugin_param_by_name` | Get a plugin parameter by name | A0 | instant |
| `set_plugin_param_by_name` | Set a plugin parameter by name and confirm | A2 | instant |
| `list_patterns_summary` | List patterns with name and length | A0 | seconds |
| `select_pattern_verified` | Select a pattern and confirm | A2 | instant |
| `set_pattern_length_verified` | Set a pattern's length and confirm (FL 2026) | A2 | instant |
| `clear_pattern_verified` | Clear a pattern and confirm it is empty (FL 2026) | A2 | instant |
| `list_playlist_tracks` | List playlist tracks with name and mute state | A0 | seconds |
| `mute_playlist_track_verified` | Set a playlist track's mute and confirm | A2 | instant |
| `set_playlist_track_name_verified` | Set a playlist track's name and confirm | A2 | instant |
| `add_time_marker_verified` | Add a time marker and confirm it exists | A2 | instant |
| `snapshot_state` | Capture tracked mixer, channel, pattern, and plugin parameters to a snapshot file | A0 | seconds |
| `diff_state_snapshots` | Compare two snapshots and list changed values | A0 | instant |
| `restore_state_values` | Replay a snapshot's values through verified writes | A2 | seconds |
| `undo_last_verified` | Undo one step and confirm the state changed back | A2 | instant |

## L3. Recipes (host; at most three L2 calls each, plus verification)

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `apply_gain_trim` | Adjust a track's level by a capped delta toward a target peak | A2 | seconds |
| `create_send_route` | Create a send from one track to a bus at a given level | A2 | seconds |
| `solo_group` | Solo a set of tracks and un-solo the rest, remembering prior state | A2 | seconds |
| `rollback_to` | Restore a named snapshot, falling back to a saved project copy if needed | A2 | seconds |
| `build_bus` | Route a set of tracks to one bus track and name it | A2 | seconds |
| `setup_sidechain_route` | Route a trigger track to a target track's sidechain input | A2 | seconds |
| `apply_eq_recipe` | Apply a named EQ recipe to a track's mixer EQ | A2 | seconds |
| `set_rough_balance` | Set starting levels across tracks from a balance target file | A2 | seconds |
| `stage_gain_chain` | Set levels stage by stage, polling peaks, to hold target headroom | A2 | seconds |
| `set_tempo_and_swing` | Set tempo and swing together and confirm | A2 | instant |
| `prepare_for_render` | Stop transport, set the range, and confirm the project is saved | A2 | seconds |
| `restore_after_render` | Restore transport and selection state after a render | A2 | seconds |
| `write_notes_via_script` | Write a list of notes to a pattern through the generated piano roll script | A2 | seconds |
| `import_midi_into_channel` | Bring a MIDI file into a channel through the chosen import route | A2 | seconds |
| `apply_param_recipe` | Apply a named set of plugin parameter values by name | A2 | seconds |

## L4. Measures (audio and note data; pure or reads files; CPU only)

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `read_audio_file` | Load an audio file to a sample array with its sample rate | A0 | seconds |
| `measure_integrated_loudness` | Measure integrated loudness in LUFS per ITU-R BS.1770 | A0 | seconds |
| `measure_short_term_loudness` | Measure short-term loudness over a sliding window | A0 | seconds |
| `measure_loudness_range` | Measure loudness range in LU | A0 | seconds |
| `measure_true_peak` | Measure true peak in dBTP using oversampling | A0 | seconds |
| `measure_sample_peak` | Measure sample peak in dBFS | A0 | instant |
| `measure_rms` | Measure RMS level in dBFS | A0 | instant |
| `measure_crest_factor` | Measure the peak to RMS ratio in dB | A0 | instant |
| `measure_band_energy` | Measure energy in named frequency bands | A0 | seconds |
| `measure_spectral_centroid` | Measure the spectral centroid in Hz | A0 | seconds |
| `measure_mid_side_ratio` | Measure the mid to side energy ratio | A0 | instant |
| `measure_low_end_mono_ratio` | Measure how mono the signal is below a cutoff frequency | A0 | seconds |
| `measure_stereo_correlation` | Measure the stereo correlation coefficient | A0 | instant |
| `count_clipped_samples` | Count samples at or beyond full scale | A0 | instant |
| `measure_masking_overlap` | Measure band-wise overlap between two audio files | A0 | seconds |
| `compare_to_reference` | Compare a measure report to a reference or target file | A0 | seconds |
| `detect_silence` | Find silent regions and report whether a file is mostly silent | A0 | seconds |
| `detect_leakage` | Estimate leakage of other sources into a stem | A0 | seconds |
| `estimate_bpm_dsp` | Estimate tempo from audio with DSP | A0 | seconds |
| `estimate_key_dsp` | Estimate musical key from audio with DSP | A0 | seconds |
| `detect_sections_dsp` | Estimate section boundaries from audio with DSP | A0 | seconds |
| `align_bounces` | Align two bounces by lag so they can be compared | A0 | seconds |
| `build_measure_report` | Run the standard measures on a file and assemble one report | A0 | seconds |
| `extract_melody_contour` | Reduce a note list to a pitch contour with rhythm positions | A0 | instant |
| `compare_note_sequences` | Score the similarity of two note lists | A0 | instant |
| `quantize_notes` | Snap note starts and lengths to a grid | A0 | instant |
| `clean_midi_notes` | Remove very short, very quiet, and overlapping duplicate notes | A0 | instant |
| `transpose_notes` | Shift a note list by semitones | A0 | instant |
| `detect_chord_loop` | Find the repeating chord progression in a note list | A0 | instant |
| `read_midi_file` | Read a MIDI file into a note list | A0 | seconds |
| `write_midi_file` | Write a note list to a MIDI file in the sandbox | A2 | seconds |
| `write_report_file` | Write a report to the sandbox as JSON and markdown | A2 | instant |

## L5. Model adapters (studio-ml; one model, one call)

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `check_gpu_budget` | Report free VRAM and whether a named model fits | A0 | instant |
| `load_model` | Load a registered model through the scheduler | A2 | gpu |
| `unload_model` | Unload a model and free its memory | A2 | gpu |
| `separate_stems` | Split an audio file into stems with Demucs | A2 | gpu |
| `transcribe_to_midi` | Transcribe audio to a note list with Basic Pitch | A2 | gpu |
| `estimate_key_bpm_ml` | Ask the audio-understanding model for key and tempo as a cross-check | A2 | gpu |
| `generate_audio` | Generate audio from a text prompt with the music model | A2 | gpu |
| `generate_cover` | Generate a cover of a reference audio with the music model | A2 | gpu |
| `repaint_section` | Regenerate a time range of an audio file | A2 | gpu |
| `critique_audio` | Ask the audio-language model for a critique of an audio file | A1 | gpu |
| `ground_gui_element` | Return screen coordinates of a described element from a screenshot | A0 | gpu |
| `call_agent_llm` | Call the local agent LLM endpoint with a prompt and tool slice | A0 | gpu |

## L6. Desktop control (primitives and recipes)

### Primitives

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `take_screenshot` | Capture the FL Studio window to an image file | A0 | instant |
| `locate_element` | Find a described element on a screenshot using the vision model | A0 | gpu |
| `click_at` | Click at screen coordinates inside the FL window | A2 | instant |
| `type_text` | Type text into the focused FL control | A2 | instant |
| `press_hotkey` | Send a key chord to the FL window | A2 | instant |
| `drag_between` | Drag from one point to another inside the FL window | A2 | instant |
| `wait_for_change` | Wait until the screenshot differs from a reference or time out | A0 | seconds |
| `halt_input` | Stop all pending input and set the halt flag | A0 | instant |

### Recipes

| Module | Job | Auto | Cost |
| --- | --- | --- | --- |
| `screenshot_verify` | Check a screenshot against an expected post-condition | A0 | gpu |
| `render_via_cli` | Render the saved sandbox project with FL's command-line options | A2 | minutes |
| `save_project_copy` | Save the open project to a path inside the sandbox | A2 | seconds |
| `open_project_copy` | Open a saved sandbox project in FL | A2 | seconds |
| `export_split_stems_gui` | Export one WAV per mixer track through the Export dialog | A2 | minutes |
| `load_plugin_gui` | Load a named plugin into a channel or mixer slot | A2 | seconds |
| `load_sample_gui` | Load an audio file into a new sampler channel | A2 | seconds |
| `import_midi_gui` | Import a MIDI file into the project | A2 | seconds |
| `add_mixer_insert_gui` | Add a plugin to a mixer track's insert slot | A2 | seconds |
| `open_plugin_ui_gui` | Open a plugin's window for GUI-only controls | A2 | seconds |
| `arm_piano_roll_script_gui` | Open the piano roll and select the generated script | A2 | seconds |
| `run_piano_roll_script_gui` | Run the selected piano roll script and confirm the notes appeared | A2 | seconds |
| `dismiss_dialog_gui` | Close a known, harmless dialog; halts on unknown dialogs | A2 | seconds |

## Layer totals

Counted from the tables above by script.

| Layer | Name | Modules |
| --- | --- | --- |
| L0 | Transport | 10 |
| L1 | FL ops (generated) | 98 |
| L2 | Verified wrappers | 41 |
| L3 | Recipes | 15 |
| L4 | Measures (audio and note data) | 32 |
| L5 | Model adapters | 12 |
| L6 | Desktop control | 21 |
| Total | | 229 |

As built the totals are L0 13, L1 97, L2 48, L3 16, L4 38, L5 13, L6 25, total 250, of which 136 are exposed as tools (file 15).

L1 is generated and its count will be replaced by the real inventory at Gate 0. Every other layer is written or card-built. Excluding L1, the hand-built total is 131.
