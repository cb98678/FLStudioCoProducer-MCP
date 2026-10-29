---
name: gui-fallback
description: Use when something in FL Studio cannot be done through the fl-bridge tools and needs the interface: loading plugins or samples, importing MIDI, exporting stems, saving or opening a copy, or operating a plugin control that is not exposed. Governs the desktop-control tools.
---

# GUI fallback

Use the interface only when no API tool exists. Prefer a recipe over free-form clicking. Every action is scoped to the FL Studio window, counts against an action budget, and stops when anything unexpected appears.

## Before you start

1. `check_desktop_ready`: the FL window exists, is the right one, and can take input. If not, stop and report.
2. `list_open_dialogs`: if a dialog is open, deal with it first (see Dialogs).
3. Check the recipe exists and whether it is confirmed. Draft recipes (marked `verified: false`) only run if the human has allowed unverified recipes in config. If refused, say so and ask the human to run `coproducer calibrate`.

## Recipes (use these first)

| Need | Tool |
| --- | --- |
| Save the open project as a sandbox copy | `save_project_copy` |
| Open a sandbox copy | `open_project_copy` |
| Add a plugin to the channel rack | `load_plugin_gui` |
| Load a sample | `load_sample_gui` |
| Import a MIDI file into the piano roll | `import_midi_gui` |
| Export one WAV per mixer track | `export_split_stems_gui` |
| Add a plugin to a mixer slot | `add_mixer_insert_gui` |
| Open a plugin's window | `open_plugin_ui_gui` |
| Pick a piano roll script, then run it | `arm_piano_roll_script_gui`, `run_piano_roll_script_gui` |
| Render with the command line | `render_via_cli` (no clicks) |
| Split a song into stems with FL's own Extract stems from sample | `extract_stems_gui` (`prepare_stems_project`, recipe `extract_stems_gui`) |
| Fit a vocal to the beat in Newtime (warp markers on its syllables, quantized) | `quantize_vocal_gui` (`detect_warp_markers`, `add_warp_markers_gui`, recipes `newtime_load_gui`, `newtime_quantize_save_gui`) |
| Auto-tune a vocal in Newtone and save its notes as MIDI | `apply_vocal_tuning_gui` (styles robotic, middle, smooth, natural; recipe `newtone_tune_save_gui`) |

Paths a recipe writes or opens must be inside the sandbox folder. A path outside it is refused.

## Free-form control (only when no recipe fits)

The primitives `take_screenshot`, `click_at`, `type_text`, `press_hotkey`, `drag_between`, `wait_for_change`, `locate_element`, `screenshot_verify` are on demand: ask for each with `request_tool` and a reason.

1. Prefer a hotkey (`press_hotkey`) to a click. FL's documented shortcuts are in the manual.
2. `take_screenshot` before and after every action.
3. To click something, `locate_element` first. If its confidence is low, stop and ask. Never click on a guess.
4. After the action, `screenshot_verify` the expected change: a window title, a dialog appearing or gone, or an element visible. No change within the wait means failure.
5. On mismatch: reverse if you can, retry once with a different locating method, then `halt_input` and ask.

## Dialogs

`dismiss_dialog_gui` closes a dialog only if its title is on the allow list the human confirmed. Any other dialog halts the run (`E_BLOCKED_BY_DIALOG`). Do not click through an unknown dialog.

## Rules

- Never touch another application. Every input checks the FL window first.
- The action budget is limited. When it is used up the run halts; do not look for a way around.
- `halt_input` is always available. Use it the moment anything looks wrong.
- A failed recipe saves a screenshot of the failure; show it to the human.
- Input is a last resort. If an API tool exists, use that.

## Ask when

- The vision model is unsure where something is.
- A recipe is still a draft on this machine.
- An unknown dialog appears, or the window title is not what you expected.
