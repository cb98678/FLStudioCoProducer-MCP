---
name: orchestrator-guide
description: Use when running or planning a co-producer session: reading the tool slice, writing a plan file, choosing verifiers, respecting autonomy levels and sandbox rules, handling failed verifications, and deciding when to ask the human.
---

# Orchestrator guide

You drive a run through phases P0 to P7. Tools are limited to the current phase. Plans are data. Every write has a verifier. You never act outside the sandbox copy.

## Phases

| Phase | Name | Leave it when |
| --- | --- | --- |
| P0 | Intake | The spec sheet has project, mode, source, and the original's hash is recorded |
| P1 | Analyze | Analysis steps are verified; invariants drafted for a restyle |
| P2 | Plan | A plan is stored and validated |
| P3 | Produce | All P3 steps verified |
| P4 | Mix | All P4 steps verified |
| P5 | Listen | Capture, measure, compare, critique done |
| P6 | Master | Targets met or flagged |
| P7 | Deliver | A/B package, change log, and the human's approval recorded |

P5 can send work back to P4; P6 to P4 or P5. After the iteration cap in the spec sheet, stop and ask.

## Every turn

1. Call `run_status`: phase, budgets, halt flag, tool slice. If `halted` is true, stop.
2. Call `spec_get` once per phase to see goals and targets.
3. If you need a tool that is not in the slice, call `request_tool` with a reason. Do not look for a way around the slice.
4. Write or load the plan (`plan_set`), then `plan_run`. Steps run in order and stop at the first failure.
5. After each phase's steps, call `phase_advance`. It refuses until the exit check passes.

## Writing a plan

A plan is `{plan_id, steps: [...]}`. Each step has:

- `id`: unique, like `s01`.
- `phase`: P0 to P7.
- `module`: a registered tool name.
- `args`: its arguments. A whole-string value like `"$s02.value.path"` is replaced by that earlier step's result.
- `verifier`: one of `none` (reads only), `readback`, `file_nonempty`, `measure_within`, `stems_not_silent`, `key_match`, `bpm_match`, `melody_similarity`, `screenshot_post`, `original_untouched`, `human_review`.
- `verify`: the verifier's own arguments (see `references/verifiers.md`).
- `risky: true`: take a snapshot first. Use it before anything hard to undo.
- `autonomy`: only to make a step stricter (for example A1). Never looser than the module's own level.

Plans that build or remix parts put drums in sampler channels and patterns and synths in plugin channels and notes (`editable-first`); a part delivered as audio needs a recorded reason.

A plan with a write step and verifier `none`, an unknown tool, or autonomy A3 is rejected with every problem listed. Fix them all in one edit.

## Autonomy

- A0 read or measure: just do it.
- A1 propose: the step waits for the human's approval.
- A2 act in the sandbox copy, with a verifier.
- A3 touch a real project: never. Only the human runs `coproducer promote`.

## When a step fails

1. Read the error code and message in the Result. Do not repeat the same call with the same arguments.
2. `E_NOT_VERIFIED`: FL accepted the call but the readback differs (or a measure is out of range). Read the state again, then either change the approach or ask. Writes are never retried automatically.
3. `E_UNSUPPORTED_API`: the build lacks that call. Look for another tool, then the GUI route (see the `gui-fallback` skill).
4. `E_PENDING_HUMAN`: a person must answer. Stop; the question is in the pending-decisions file.
5. `E_HALTED` or `E_AUTONOMY`: stop and report. Do not try again.
6. After any failure the executor offers a rollback to the last snapshot through `ask_human`. Prefer rolling back to leaving a half-applied change.

## Ask the human when

- The spec sheet has a gap you cannot fill from a file.
- A V1 gate is reached (see `references/gates.md`).
- A choice is about taste, risk, or cost. Offer 2 to 4 options, recommended one first, using `ask_human`; record the answer with `record_decision`.

The ask budget is limited. Batch questions. See the `co-producer-protocol` skill.

## Never

- Call a tool outside the slice, edit the original project, or loop on a failing step.
- Invent a target. Targets come from the targets file the human filled in.
- Mark a phase done without `phase_advance` passing.
