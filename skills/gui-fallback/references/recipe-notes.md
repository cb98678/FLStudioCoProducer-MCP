# GUI recipe notes

Recipes live in `src/coproducer/data/gui_recipes/*.json` (or `gui_recipes/` in the project home, which wins). Each lists parameters and steps, and marks itself `verified: false` until a human confirms it on their machine with `coproducer calibrate`.

Step kinds: `hotkey`, `type`, `click` (a recorded anchor), `click_row`, `click_col`, `template_click`, `click_in_window` (an offset from a window found by title; optional `clicks` and `modifiers`), `knob_in_window` (turn a knob to a value 0..1 of its travel, read back from its arc after each drag), `locate_click` (vision), `wait`, `expect_dialog`, `expect_no_dialog`, `expect_title`, `expect_file`. A recipe that works inside an editor window lists it in `allow_open`.

Post-conditions the engine checks:

| Recipe | After it runs |
| --- | --- |
| `save_project_copy` | The file exists, is not empty, and the Save dialog is gone |
| `open_project_copy` | No dialog is open and the title shows the project |
| `export_split_stems_gui` | The Export dialog is gone and no dialog is blocking |
| `load_plugin_gui`, `load_sample_gui`, `import_midi_gui`, `add_mixer_insert_gui` | No dialog is blocking |
| `arm_piano_roll_script_gui`, `open_plugin_ui_gui` | The expected window appears (checked by `screenshot_verify`) |

Shortcuts used come from the FL manual's shortcut reference: Save As Ctrl+Shift+S, Open Ctrl+O, Export wave Ctrl+R, Import MIDI Ctrl+M (piano roll), F5 to F10 windows.

## Newtime and Newtone (measured on FL 26.1.7, 2560 x 1440, 2026-10-29)

Both open from the clip menu of the audio clip at the start of playlist track 1 (anchors `playlist_clip1_menu`, `clip_menu_time_warp`,
`clip_menu_pitch_correct`); both load another file with Ctrl+O. Newtime's window title reads WarpCorrectionTrack. Offsets in the recipes
are from each window's top-left corner at its default size (Newtime 741 x 617).

- Newtone's knobs scale every note: CENTER 0 leaves a note's pitch centre, 1 puts it on the semitone; VARIATION's reset (noon, 0.5) is the
  voice as sung, 0 flattens it, 1 doubles it; TRANS's reset (1) keeps the glides between notes, 0 jumps. Knob drags are not linear in
  pixels (105 px moved VARIATION 57 % up and 36 % down), so `knob_in_window` reads the arc back and drags again.
- Newtime: Edit > Delete all markers asks first (dialog "Delete all markers", Yes at 247, 153 from its corner); Marker detection asks
  "Auto-detect markers" only when markers exist. Snap Off before Shift+clicking markers (Snap 1/4 beat to quantize to 16ths).
- A Shift+click within about 25 px of Newtime's editor edge scrolls the view 15 px: keep clicks 50 px inside.
- Newtime's grid sat at 1.85034 s a bar for 130 bpm on this machine's samples (as if 44200 Hz): `quantize_vocal_gui` slows the vocal by
  442/441 first and speeds the result back.
- Both editors close with the X at the top right without asking. FL asks "Save changes to ...?" (Confirm: Yes, No, Cancel) when it is
  closed with an edited project.

## Extract stems from sample (measured on FL 26.1.7, 2026-10-29)

The clip menu of an audio clip opens from the icon at the left of the clip's header. The recipe finds things by picture, not fixed points
(a fixed point missed the clip by 18 px on a second project): the header picture `playlist_song_clip_header` (icon and the name Song, which
`prepare_stems_project` gives the clip) clicked 17 px left of its centre, then the entry Extract stems from sample and the dialog's Extract
button. The menu is drawn in the clip's colour; matching ignores colour. The dialog is drawn inside FL's window, not as a separate window. Defaults kept: all four stems, mute the source
track when done, group the playlist tracks, new mixer tracks. FL is unresponsive while it separates (under 80 s for a 2:37 song here),
then writes `<sample>_drums.wav`, `_bass`, `_instruments` and `_vocals` (32-bit float, the song's length) to the project's data folder's
Audio subfolder: `prepare_stems_project` points the data folder at the work folder, so the files land next to the bench project. On
Girlish Type Men the four stems summed back to the mix within -37 dB, the vocal stem correlated 0.96 with RoFormer's, the drums 0.996 with Demucs'.
The split is deterministic: the GUI run and the hand run wrote bit-identical files. A template project saved after an extraction carries a muted
first row and grouped, named stem rows; `prepare_stems_project` resets every row (`Flp.reset_playlist_tracks`).
Closing FL afterwards without saving asks Save changes (No), then whether to keep or delete the sample files it created ("Keep these files
or delete them?", listing the four stems): answer Keep.
