# 07. The Orchestration Layer

The orchestrator holds no music logic. It loads the module registry, gives the local model a short catalog slice, and runs the plan, act, verify, record loop. Changing behavior means adding or changing a module or a skill, never editing the orchestrator.

## 1. Responsibilities

| The orchestrator does | The orchestrator does not |
| --- | --- |
| Load and validate the registry | Contain mixing, mastering, or style knowledge |
| Expose tools to the agent, sliced by phase | Call FL directly (it calls `fl-bridge`) |
| Turn a goal into a plan file of module calls | Decide what sounds good |
| Execute steps with verifiers, retries, and rollback | Promote results to a real project |
| Schedule GPU models | Hide a failed verification |
| Keep the ledger and the spec sheet | Run unbounded loops |
| Run the collaboration protocol with you | |

## 2. Components

| Component | File | Job |
| --- | --- | --- |
| Registry loader | `registry.py` | Walk `modules/`, run the linter, load passing modules, write `catalog/rejected.md` |
| Tool exposure | `tools.py` | Generate MCP tool definitions from manifests; group by server and phase slice |
| Planner | `planner.py` | Ask the agent LLM for a plan file; validate it against the registry and the autonomy table |
| Executor | `executor.py` | Run plan steps, call verifiers, retry within limits, roll back on failure |
| Verifiers | `verifiers.py` | Map manifest `verifier` names and plan-step verifier names to modules |
| GPU scheduler | `scheduler.py` | Load and unload models by phase; refuse loads that will not fit |
| Ledger | `ledger.py` | Append-only run log as JSON lines |
| Spec sheet | `spec_sheet.py` | Read and write the per-project spec; record decisions |
| Collaboration | `collab.py` | Ask questions, present options, deliver A/B, record approvals |

## 3. Phases

A run moves through phases. Each phase has its own tool slice, its own entry check, and its own exit check.

| Phase | Name | Entry check | Work | Exit check |
| --- | --- | --- | --- | --- |
| P0 | Intake | None | Read your direction. Confirm or fill the spec sheet. Create the sandbox copy. Record the original's hash. | Spec sheet complete; sandbox exists; `ping_fl` ok |
| P1 | Analyze | P0 passed | Capture or locate the source audio. Measure it. Estimate BPM, key, sections. For restyle, separate stems and transcribe. | Analysis report written; invariants file drafted (restyle) |
| P2 | Plan | P1 passed | Produce the plan file. Present it for approval if any step is V1 or A1. | Plan validated; approvals recorded |
| P3 | Build | Plan approved | Create or rebuild the arrangement in the sandbox: notes, patterns, channels, routing, plugin loads. | All write steps verified; snapshot taken |
| P4 | Produce | P3 passed | Sound design, balance, EQ, dynamics, buses, stereo. | Targets for balance met or flagged |
| P5 | Listen | P4 passed | Capture, measure, compare with targets, critique. | Measurement report; critique written |
| P6 | Master | P5 passed | Gain staging chain, loudness, true peak, final render. | Master targets met or flagged |
| P7 | Deliver | P6 passed | A/B package, change log, invariants check, promotion proposal. | Your approval recorded |

Loops: P4, P5, and P6 repeat until targets are met or the iteration cap in the spec sheet is hit. After the cap the orchestrator stops and asks you.

## 4. Tool slices

The agent sees only the tools for the current phase, to keep schemas short for a small context window. Slice size target: at most 25 tools.

| Phase | Tool slice (module names) |
| --- | --- |
| P0 | `ping_fl`, `get_fl_versions`, `read_project_summary`, `list_tracks_summary`, `list_channels_summary`, `save_project_copy`, `snapshot_state`, plus meta tools |
| P1 | `render_via_cli`, `build_measure_report`, `estimate_bpm_dsp`, `estimate_key_dsp`, `detect_sections_dsp`, `separate_stems`, `detect_silence`, `detect_leakage`, `transcribe_to_midi`, `clean_midi_notes`, `quantize_notes`, `extract_melody_contour`, `detect_chord_loop`, `write_midi_file`, `estimate_key_bpm_ml`, plus meta tools |
| P2 | `read_project_summary`, plus meta tools (planning is mostly reasoning over the spec and analysis) |
| P3 | `write_notes_via_script`, `import_midi_into_channel`, `set_tempo_and_swing`, `set_pattern_length_verified`, `clear_pattern_verified`, `select_pattern_verified`, `route_channel_to_track_verified`, `set_channel_volume_verified`, `set_track_name_verified`, `build_bus`, `load_plugin_gui`, `load_sample_gui`, `import_midi_gui`, `generate_audio`, plus meta tools |
| P4 | `set_rough_balance`, `set_track_volume_verified`, `set_track_pan_verified`, `apply_eq_recipe`, `set_eq_gain_verified`, `list_plugin_params`, `set_plugin_param_by_name`, `apply_param_recipe`, `create_send_route`, `setup_sidechain_route`, `solo_group`, `mute_track_verified`, plus meta tools |
| P5 | `prepare_for_render`, `render_via_cli`, `restore_after_render`, `build_measure_report`, `compare_to_reference`, `measure_masking_overlap`, `align_bounces`, `critique_audio`, `diff_state_snapshots`, plus meta tools |
| P6 | `stage_gain_chain`, `apply_gain_trim`, `get_track_peak_db`, `set_track_volume_verified`, `render_via_cli`, `measure_integrated_loudness`, `measure_true_peak`, `measure_loudness_range`, `count_clipped_samples`, `compare_to_reference`, `rollback_to`, plus meta tools |
| P7 | `write_report_file`, `diff_state_snapshots`, `compare_note_sequences`, `estimate_key_dsp`, plus meta tools |

Any phase MAY request a one-off addition to its slice. Additions are logged. The `gui-fallback` skill is the only place that tells the agent when to ask for the `desktop-control` primitives, because those carry the most risk.

### Meta tools (orchestrator, not modules)

| Tool | Job |
| --- | --- |
| `plan_get` | Return the current plan file and step statuses |
| `plan_update` | Replace the remaining steps (validated) |
| `spec_get` | Return the spec sheet digest |
| `record_decision` | Add a decision with its reason to the spec sheet |
| `ask_human` | Ask a question with 2 to 4 options and wait |
| `present_ab` | Deliver an A/B comparison package and wait for a verdict. As built: the tool `build_ab_package` followed by `ask_human` (file 15) |
| `phase_advance` | Request a phase change; runs the exit check |
| `ledger_tail` | Return the last N ledger entries |
| `halt_run` | Stop the run cleanly |

## 5. The plan file

The planner writes a plan as data, not as free text. The executor runs the data.

```yaml
plan_id: restyle-0001
goal: "Restyle sandbox/track_a.flp from techno to dubstep, keep melody and key"
spec_ref: specs/track_a/spec.md
iteration_cap: 3
steps:
  - id: s01
    phase: P1
    module: render_via_cli
    args: {project_path: "sandbox/track_a/track_a.flp", out_dir: "sandbox/track_a/renders"}
    verifier: file_nonempty
    autonomy: A2
  - id: s02
    phase: P1
    module: separate_stems
    args: {input_path: "$s01.value.path", out_dir: "sandbox/track_a/stems", stems: 4}
    verifier: stems_not_silent
    autonomy: A2
  - id: s03
    phase: P1
    module: transcribe_to_midi
    args: {input_path: "$s02.value.stems.other"}
    verifier: human_review
    autonomy: A1
```

Rules:

1. Arguments reference earlier results with `$stepid.path` syntax.
2. Every step names a module in the registry, a verifier, and an autonomy level at least as strict as the module's own.
3. The planner's output is validated: unknown modules, missing verifiers, forward references, and any A3 step are rejected before anything runs.
4. A plan MAY contain at most one human-review step per V1 decision, so you are not asked redundant questions.

## 6. Executor semantics

```
for step in plan:
    check autonomy: A1 -> collab.ask_approval; A3 -> refuse unless explicit human action
    check sandbox guard for modules that write
    check halt flag and action budget
    result = registry.call(step.module, **resolve(step.args))
    ledger.append(step, result)
    if result.ok:
        verdict = verifiers.run(step.verifier, step, result)
        ledger.append(verdict)
        if verdict.pass: continue
    # failure path
    if result.error.retryable and attempts < step.max_attempts: retry
    else: offer rollback to the last snapshot; stop the phase; ask the human
```

Details:

1. **Retry policy.** Reads MAY be retried up to 2 times. Writes MUST NOT be retried blindly: the executor first reads state to learn whether the write landed. A verified-false write is never repeated without the agent changing something.
2. **Snapshot cadence.** A snapshot is taken before every phase and before any step marked `risky: true` in the plan.
3. **Rollback.** `rollback_to` restores values through verified writes. If a change cannot be restored by values (for example a loaded plugin), the saved project copy is reopened through the GUI recipe.
4. **Iteration cap.** The P4 to P6 loop stops at `iteration_cap` and asks you.
5. **Action budget.** GUI steps count against a per-run budget in the spec sheet (default 200 actions). On exhaustion the run halts with `E_HALTED`.
6. **Rate limit.** Writes to FL are paced so the dispatcher's idle queue never grows beyond a small bound.

## 7. Verifier registry

Verifiers are modules or small compositions named in plan steps.

| Verifier | Passes when | Implemented by |
| --- | --- | --- |
| `readback` | `result.meta.verified` is true | Built in |
| `file_nonempty` | The returned path exists and is larger than a minimal size | Built in |
| `measure_within` | A named metric is inside the target range from the targets file | `compare_to_reference` |
| `stems_not_silent` | No stem is flagged silent; leakage under limit | `detect_silence`, `detect_leakage` |
| `key_match` | Estimated keys match | `estimate_key_dsp` on both |
| `bpm_match` | Estimated tempo matches the requested value within tolerance | `estimate_bpm_dsp` |
| `melody_similarity` | Score at or above the invariants file's threshold | `compare_note_sequences` |
| `screenshot_post` | Post-condition screenshot check passes | `screenshot_verify` |
| `original_untouched` | Original project hash equals the recorded hash | Built in |
| `human_review` | You approved | `collab` |

## 8. The ledger

An append-only JSON-lines file per run, `runs/<run-id>/ledger.jsonl`. Every entry has an id, a timestamp, and a type.

| Field | Meaning |
| --- | --- |
| `seq` | Monotonic sequence number |
| `ts` | Timestamp |
| `type` | `run_start`, `phase_enter`, `step_start`, `step_result`, `verify`, `snapshot`, `rollback`, `ask`, `answer`, `model_load`, `model_unload`, `decision`, `halt`, `run_end` |
| `step_id` | Plan step id, when relevant |
| `module` | Module name and version hash |
| `args` | Resolved arguments (large blobs stored by path) |
| `result` | Result summary: ok, error code, meta |
| `verified` | For writes: true or false |
| `snapshot_id` | State snapshot active at the time |
| `project_hash` | Hash of the sandbox project file when relevant |

Uses:

1. **Audit.** You can see everything the agent did.
2. **Resume.** After a crash, the orchestrator replays the ledger to find the first step without a verified result and continues there.
3. **Promotion report.** The change log you review is generated from the ledger.
4. **Skill evals.** Transcript review uses ledger entries.

## 9. The spec sheet

A markdown file per project with a small machine-readable header. The agent reads a digest of it at the start of every phase.

```
---
project: track_a
mode: restyle                # new | restyle | mix | master
source: sandbox/track_a/track_a.flp
original_hash: sha256:...
targets: targets/streaming_default.toml
genre_profile: genre_profiles/dubstep.toml
invariants: specs/track_a/invariants.toml
iteration_cap: 3
action_budget: 200
tempo_policy: genre          # keep | genre | half_time
---
# Goals
# Decisions (each with date and reason)
# Open questions
# Approved by human (list)
```

Rules: a decision is added by `record_decision` before behavior changes. The orchestrator MUST refuse to start a phase if the spec sheet is missing a field that the phase needs.

## 10. Collaboration protocol

You are the co-producer. The protocol keeps the system useful without nagging.

1. **Ask only when it matters.** The orchestrator asks at: spec gaps in P0, plan approval in P2 when any step is A1 or V1, melody MIDI review in P1 (restyle), V1 judgments in P5 and P6, and the final A/B in P7. Everything else runs.
2. **Options, not essays.** A question offers 2 to 4 options, with the agent's recommendation first and one line of reasoning for each. Free-text answers are always allowed.
3. **A/B delivery.** `present_ab` produces two loudness-matched bounces (the original and the result, matched to the same integrated loudness so louder does not sound better), a short measurement diff, and the change list. You answer with approve, approve with notes, or reject with notes.
4. **Notes become spec.** Your notes are written to the spec sheet as decisions, then the plan is updated.
5. **Explain changes.** Every A2 change in P4 and P6 is described in one plain sentence in the change log, with the measured before and after.
6. **No silent loudness chasing.** The agent never raises overall level to make a comparison sound better. Gain moves are capped per step by the spec sheet.
7. **Ask budget.** A run has a maximum number of questions in the spec sheet (default 12). When the budget is used, the agent proceeds on its recommended option and logs it as an assumption, except for V1 gates and A3 steps, which always ask.
8. **Unattended runs.** If you are not present, the orchestrator does not guess V1 gates. It completes preparatory work, writes the question and its options to a pending-decisions file, and stops.

## 11. How the agent brain is prompted

1. The system prompt is fixed: role, autonomy rules, the Result and error vocabulary, the instruction to call tools rather than describe them, and the instruction to name which verifier proves each claim.
2. Each turn includes: the current phase, the spec sheet digest (under a size limit), the tool slice, the last N ledger entries, and the active plan step.
3. Skills are loaded by phase: the orchestrator-guide skill always, then the skills for the phase (for example `mix-engineer` and `gain-staging` for P4 and P6).
4. Generated catalog references are loaded on demand for the layer in use, so descriptions never drift from the code.
5. The agent LLM is reached through the local OpenAI-compatible endpoint described in file 08.

## 12. Crash and resume

1. The ledger is flushed after every entry.
2. On start, if an unfinished run exists, the orchestrator offers to resume.
3. Resume rebuilds the plan state from the ledger. A step with a verified-true result is not repeated. A step with an unknown outcome (crash mid-write) is handled by reading FL state first.
4. If FL is not running or the dispatcher does not answer `ping_fl`, the run pauses in `waiting_for_fl` and says what to do.

## 13. Safety enforcement points

| Rule (file 01) | Enforced by |
| --- | --- |
| Original project never written | Sandbox guard in every writing module; hash check in P7 |
| A3 never autonomous | Plan validator rejects A3 steps; executor refuses A3 without an explicit human action in the same session |
| Every write verified | LM-012; executor refuses to proceed after `verified: false` |
| Input only to FL windows | `desktop-control` primitives check the target window handle on every call |
| Halt | A global hotkey and `halt_input`; the executor checks the halt flag between steps and the primitives check it between actions |
| Unknown dialogs | `dismiss_dialog_gui` halts on anything not on its allow list |
