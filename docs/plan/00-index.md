# FL Studio AI Co-Producer: Full-Scope Plan

Owner: Mark ("Meeps"). Status as of October 18, 2026. Version 1.0 of the plan.

This is a clean-room build plan for a local-first AI co-producer for FL Studio. Nothing here forks, extends, or depends on any existing FL Studio MCP. Existing public projects are read only as prior art for pitfalls, and each is named as such where it appears.

The system has three workstreams that ship together on one shared foundation:

| Workstream | What it is | Main files |
| --- | --- | --- |
| A. MCP servers | Four new MCP servers that give a local model hands inside FL Studio, ears on the audio, access to local generative models, and a screen-control fallback | 03, 04, 05, 07 |
| B. Skills | Twelve skills as built (eleven planned) that teach local models how to produce, mix, gain stage, master, and restyle, and how to build the system's own modules | 10 |
| C. Python layer | Installers, environments, GPU scheduler, model registry, and the orchestration loop that drives plan, act, listen, measure, critique | 07, 08, 09 |

## How to read this plan

Read in this order if you are new to it: 01, 02, 03, 04. Then read 12 (roadmap) and 13 (risks and decisions). Files 05 and 06 are the build inventory. Files 07 to 11 are the detailed designs. File 14 lists every source with its verification status.

| File | Contents |
| --- | --- |
| [01-vision-and-spec.md](01-vision-and-spec.md) | Vision, spec sheet, success criteria, verifiability classes, autonomy table, failure modes |
| [02-official-findings.md](02-official-findings.md) | What the official Image-Line documentation says, as a numbered fact register, and the design consequence of each fact |
| [03-architecture.md](03-architecture.md) | Servers, process boundaries, data flows, the SysEx bridge protocol, sandbox, capture routes, repository layout |
| [04-module-system.md](04-module-system.md) | The module rules, the Result type, the manifest, the linter, side-effect classes, generated documentation |
| [05-module-catalog.md](05-module-catalog.md) | Every planned module by layer, with one job each |
| [06-task-cards.md](06-task-cards.md) | The task card template, the build loop, and the ten calibration cards in full |
| [07-orchestrator.md](07-orchestrator.md) | Registry loader, tool exposure, planner, executor, verifiers, ledger, collaboration protocol |
| [08-python-layer-and-models.md](08-python-layer-and-models.md) | Installers, isolated environments, model registry, GPU scheduler, benchmarks, Windows specifics |
| [09-workflows.md](09-workflows.md) | Module-by-module sequences for new tracks, style transfer, mixing, gain staging, mastering, and GUI fallback |
| [10-skills.md](10-skills.md) | Specification and eval prompts for each of the eleven skills |
| [11-testing.md](11-testing.md) | Test pyramid, fake FL harness, synthetic audio, contract tests, gate acceptance tests |
| [12-roadmap.md](12-roadmap.md) | Phases, gates, work packages, parallel lanes |
| [13-risks-and-decisions.md](13-risks-and-decisions.md) | Decision log, risk register, open questions, assumptions to confirm |
| [14-sources.md](14-sources.md) | Sources with links and a status for each: opened and read, or seen in search results only |
| [15-as-built.md](15-as-built.md) | Where the build differs from the plan, the counts as built, and what is not built |

A single combined file, `PLAN-full.md`, contains all of the above in order, including file 15. The module count quoted across the plan (about 230) comes from file 05; the as-built count is 250 (file 15).

## Conventions

1. **Requirement language.** The words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY follow RFC 2119. Anything written as a plain statement of fact is either cited or marked as an assumption.
2. **Fact status tags.** Every external claim carries one of three tags in file 02 and file 14:
   - **READ**: the page was opened and read for this plan.
   - **SEEN**: the claim appeared in a search result and has not been opened. Verify before relying on it.
   - **PROBE**: the claim can only be settled on your machine. Gate 0 contains a probe for it.
3. **Decisions.** Where you said "you decide", the decision is in the decision log in file 13 with its reason and the condition that would reverse it.
4. **Numbers.** Module counts, line budgets, and VRAM figures are planning estimates unless tagged READ. Gate 0 replaces the estimates with measured values.
5. **Style.** No em dashes in any delivered document. Ranges use the word "to".
6. **Dates.** All "latest version" statements are as of October 18, 2026. Re-check any version-dependent fact before building on it.

## Glossary

| Term | Meaning |
| --- | --- |
| Sandbox copy | A duplicate of your FL project in a dedicated folder. The agent writes only here. |
| Promotion | The human-approved act of copying results from the sandbox into a real project. Never automatic. |
| Module | One function with one job, with a manifest and tests. The unit of build, test, and exposure. |
| Registry | The set of modules that passed the linter. The orchestrator sees only registered modules. |
| Task card | A one-page work order for a local coding model to produce one module. |
| Gate | A checkpoint with executable acceptance tests. Work does not move past a gate without passing them. |
| Invariants file | The written definition of what "preserving the spirit" means for one track: key, melodic contour, rhythm motif, harmonic loop, section order, energy arc. |
| Genre profile | A data file describing a target genre's tempo range, drum templates, bass family, structure, and mix targets. |
| Spec sheet | The per-project source of truth for goals, targets, and decisions. Updated before behavior changes. |
| Ledger | The append-only run log from which any run can be audited or resumed. |
| Bridge | The MIDI SysEx channel over virtual ports that carries requests into FL Studio and replies out of it. |
| Capture | Producing an audio file of the project so that it can be measured. |

## Method note

The plan follows the Spec, Verifier, Environment, Loop method from your agentic prompt architect file. File 01 is the spec sheet. Verifiers are named for every requirement. The environment is the sandbox. The loop is plan, act, capture, measure, critique, reconcile, and it runs under the autonomy table in file 01.
