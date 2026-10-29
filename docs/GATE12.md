# Gate 1 and Gate 2 acceptance matrix

Status on 2026-10-22. "Proven" means a repeatable test or measured run exists and passed. Test counts: 825 tests, all passing in the cloud workspace; the Windows clean install passed its full suite.

## Gate 1: ears and generators

| ID | Test | Status | Evidence |
| --- | --- | --- | --- |
| G1-1 | Measure report on every fixture | Proven | `tools/gate1_bench.py`, `tests/test_gate1.py`: 19 fixtures, 108 checks against maths, ffmpeg EBU R128 and pyloudnorm, 0 failed. See `docs/GATE1.md` |
| G1-2 | Clean install, then doctor | Proven on your machine | Fresh folder `C:\cp_clean`, fresh venv, `requirements.lock` (56 packages match the lock), `setup`, `lint`, full test suite and the Gate 1 bench all passed. Doctor passes every host check; the three model environments report "no environment" there by design (multi-GB, not reinstalled in a scratch folder), and `install-models --dry-run` covers them. Found and fixed: `setup` picked "FL Studio 21BETA" over FL Studio 2026 |
| G1-3 | Fake-FL suite | Proven | 825 tests, fuzz of 269 modules (`docs/STRESS_REPORT.md`) |
| G1-4 | Generated L1 | Proven | `tests/test_fakefl_matches_inventory.py`, generated dispatcher has 104 ops, each with a module test; `docs/l1_missing.md` lists names not generated and why |
| G1-5 | DSP accuracy | Proven: passes the rules you accepted on 2026-10-22 | `docs/GATE1.md`. Blind tempo is a shortlist (74 percent exact, 97 percent exact or octave, true value always listed, never wrong without the ambiguous flag); with the genre range or project tempo it is 100 percent. The key set is synthetic |

## Gate 2: mix loop and GUI

| ID | Test | Status | Evidence or what is missing |
| --- | --- | --- | --- |
| G2-1 | Rough mix to targets | Waiting for your approval of targets | Your three references are measured and proposed targets are in `docs/TARGETS_PROPOSAL.md`. One conflict to settle (references are about -14 LUFS, you chose about -9). Then run on a deliberately bad test project (scenario E1) |
| G2-2 | `load_plugin_gui` with before and after screenshots | Proven live (stock plugin) | On FL Studio 2026 in the sandbox scratch project: F8, typed "Fruity Limiter", Enter, and the plugin's own window opened. Screenshots `sandbox/screens/g2_before.png` and `g2_after.png`. The recipe's last step was wrong (it demanded no open window, but the plugin's own window is the success); it now waits for a window titled with the plugin name. The recipe is marked verified for stock plugins; try it once on a third-party plugin you own before relying on it there |
| G2-3 | Sandbox safety | Proven | `tests/test_sandbox_safety.py`: 14 file-writing modules x 3 escape attempts (absolute path, `..`, `sandbox/../`) all return `E_SANDBOX_VIOLATION` and nothing is created outside. A new writing module that is not on the list fails the test |
| G2-4 | Resume after a kill | Proven | `tests/test_resume_kill.py`: the run process is killed hard (no cleanup) partway through 24 verified writes, restarted, and only unverified steps are written again |
| G2-5 | Halt hotkey stops a GUI recipe | Proven live | The hotkey did not exist; built: `coproducer halt --key` watches Ctrl+Alt+F12 and writes `runs/HALT`, which every input action and the orchestrator check. Live run on your machine: a 16-action recipe in FL, key pressed after about 5 actions, the next action was refused, result `E_HALTED`, 0 actions sent after the halt file appeared. `coproducer halt` stops by hand and `coproducer halt --clear` clears it. `tests/test_halt_key.py`, `tools/halt_live_test.py` |

## End-to-end scenarios

| ID | Scenario | Status |
| --- | --- | --- |
| E1 | Rough mix of a deliberately bad mix | Needs a test project and G2-1 targets |
| E2 | Master a mixed project | Needs targets and a mixed project |
| E3 | Restyle a short techno loop | Gate 3 work |
| E4 | New project from a brief | Needs the brief-to-plan path; not yet exercised end to end |
| E5 | Dispatcher stops answering mid-run | Proven (new): the run pauses in `waiting_for_fl` with instructions, resume does nothing while FL is silent, and continues cleanly when FL returns without repeating verified steps. A write that may or may not have happened asks before it is repeated. `tests/test_fault_run.py`. This was in the plan but not implemented until now |
| E6 | Unattended run reaching a human gate | Proven | `test_a1_step_needs_approval_and_unattended_runs_write_pending_file` |

## Defects found by this pass

1. `setup` and `doctor` chose the last FL install by name, so `FL Studio 21BETA` beat `FL Studio 2026` (setup would have written the old beta into `config.toml`). Fixed with one shared ranking.
2. Blind tempo reads 124 to 135 BPM techno as half tempo, and the result was not flagged. `estimate_bpm_dsp` now flags ambiguity and lists the 2:1 and 3:2 relatives.
3. The planned `waiting_for_fl` pause did not exist. Built and tested (E5).
4. The planned global halt hotkey did not exist. Built and run live (G2-5).
5. `load_plugin_gui` ended by demanding that no window be open, which fails exactly when it succeeds. Fixed and confirmed live (G2-2).
