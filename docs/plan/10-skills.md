# 10. Workstream B: Skills

Skills are the teaching layer. They explain the system to local models and to you: when to use a module, why, and what a good result looks like. Code and manifests say exactly what a module does; skills say when and why. The two must never disagree, so skills point to generated catalog files instead of restating module details.

## 1. Rules for every skill

1. **Written new for this system.** No skill is copied from elsewhere.
2. **Procedural and short.** Local models follow numbered steps and checklists better than long prose. Each `SKILL.md` stays under about 300 lines; detail lives in `references/`.
3. **Progressive disclosure.** Frontmatter (name and description) is always visible. The body loads when the skill triggers. References load when the body points to them.
4. **Generated references.** Files under `references/catalog/` are produced by `gen_catalog.py` from the manifests. A skill MUST NOT hand-copy module signatures.
5. **No hardcoded numbers that belong to you.** Loudness, true peak, balance, and genre values live in the targets file, genre profiles, and recipes (file 09, section 1). A skill tells the agent where to read them, never what they are.
6. **Say what to measure.** Any claim like "the bass is muddy" is tied to a measure module and a comparison, so it can be verified.
7. **Say when to ask.** Each skill names its V1 gates and A1 steps.
8. **No em dashes** in any skill text.

## 2. Skill layout

```
skills/<name>/
  SKILL.md                 frontmatter + body
  references/
    catalog/L2.md ...      generated from manifests
    checklists.md          hand written, short
  evals/
    prompts.json           eval prompts and assertions
```

## 3. How each skill is built and tested

Each skill goes through the skill-creator loop:

1. Draft the skill from the spec below.
2. Write three realistic prompts (file section per skill below).
3. Run each prompt with the skill and without it (baseline), using the target local model, and save transcripts.
4. Review the outputs against the assertions and with your eyes. Revise the skill.
5. Repeat until the with-skill runs beat the baseline on the assertions.
6. Tune the description so the skill triggers on the right prompts and stays quiet on the wrong ones.

Assertions are checked against the ledger and the tool-call transcript, not against the model's own claims.

## 4. The eleven skills (as built there are twelve: `track-creation` was added, see file 15)

### 4.1 `module-authoring`

- **Used by:** the local coding model during the card build loop.
- **Description (draft):** Use when writing, fixing, or reviewing one module for the FL co-producer from a task card: producing the .py file, module.toml, and tests, and reading lint failures. Use even when the user just says "build this card".
- **Teaches:** the eight module rules, the Result type, import classes, how to read a lint report line by line, how to fix only what the report lists, the card fields, and the out-of-scope discipline.
- **Body outline:** (1) read the card fields in order; (2) write the signature and the failure branches first; (3) write the tests from the card's acceptance cases; (4) fill the manifest; (5) self-check against LM-001 to LM-015; (6) respond with exactly three files.
- **References:** `catalog/rules.md` (generated from the linter), the card template, two worked examples (cards 01 and 04 from file 06 with their accepted code).
- **Eval prompts:**
  1. "Here is a task card for `split_frames`. Write the module." Assertions: three files; one public function; no raise; every acceptance case has a test.
  2. "The linter says LM-005 and LM-008 on this module. Fix it." Assertions: only the flagged lines change; no new features.
  3. Should not trigger: "How should I EQ a kick drum?"

### 4.2 `orchestrator-guide`

- **Used by:** the agent brain in every phase.
- **Description (draft):** Use when running or planning a co-producer session: reading the tool slice, writing a plan file, choosing verifiers, respecting autonomy levels and sandbox rules, handling failed verifications, and deciding when to ask the human.
- **Teaches:** phases P0 to P7, plan file schema, `$step.path` references, the autonomy table, what to do after `verified: false`, the ask budget, never calling A3.
- **Body outline:** (1) check the phase and slice; (2) read the spec digest; (3) write or load the plan; (4) one step at a time: call, read the Result, name the verifier; (5) failure ladder; (6) ask rules.
- **References:** `catalog/index.md`, plan file examples from file 07.
- **Eval prompts:**
  1. "Restyle my track from techno to dubstep." Assertions: plan starts with session start; includes a human review of melody MIDI; no A3 step; every write step has a verifier.
  2. A transcript where `set_track_volume_verified` returned `E_NOT_VERIFIED`. Assertion: the agent does not repeat the same call; it reads state or asks.
  3. Should not trigger: "Explain what a limiter does."

### 4.3 `studio-ops`

- **Used by:** the agent brain in P0, P3, and P4 for any change inside FL.
- **Description (draft):** Use for reading or changing FL Studio project state through the fl-bridge tools: sandbox rules, snapshots, verified writes, rollback, reading a failed verification, naming tracks, routing, tempo, patterns, and plugin parameters by name.
- **Teaches:** read before write; use `*_verified` tools; the sandbox rule; snapshot before risky steps; what `verified: false` means and why FL can ignore writes; plugin parameter maps; that API calls are toggles for play and loop.
- **References:** `catalog/L2.md`, `catalog/L3.md`.
- **Eval prompts:**
  1. "Pull the bass down a little and pan the hats left." Assertions: reads state first; uses verified tools; change within delta caps; reports verified.
  2. "Set the tempo to 140 and confirm." Assertion: checks API level support; confirms by readback.
  3. Edge: "Delete the kick channel." Assertion: asks, because deletion is not a supported A2 action and is not reversible by value restore.

### 4.4 `listen-and-measure`

- **Used by:** the agent brain in P1 and P5.
- **Description (draft):** Use when the user wants the project analyzed, listened to, or measured: capturing a render, choosing which measurement answers which question, reading a measure report, comparing to a reference, and cross-checking key and tempo.
- **Teaches:** capture routes C1 to C3; peaks are not loudness; what each measure means and what question it answers; stale-capture danger (snapshot id and project hash); DSP-first, model second; how to write findings as numbers with units.
- **References:** `catalog/L4.md`, measure glossary.
- **Eval prompts:**
  1. "Why does my drop feel weak?" Assertions: captures; measures crest factor, loudness, band energy; compares with a reference; avoids claiming feel without numbers.
  2. "Is this too loud?" Assertion: asks for or reads the targets file; does not invent a number.
  3. Should not trigger: "Write a bassline in A minor."

### 4.5 `gain-staging`

- **Used by:** the agent brain in P4 and P6.
- **Description (draft):** Use when setting levels in an FL project: headroom per track and bus, trims before processing, polling peaks, sending to buses, and keeping the master chain input clean. Use for "my mix clips", "levels are all over", or "set up gain staging".
- **Teaches:** order of operations (sources to buses to master chain); polling peaks inside FL with `stage_gain_chain`; peaks versus loudness; delta caps; never fixing level problems with the master fader; verifying with a render.
- **References:** `catalog/L2.md`, `catalog/L3.md`, `catalog/L4.md`.
- **Eval prompts:**
  1. "Gain stage this project." Assertions: snapshot; starts at sources; uses `stage_gain_chain`; ends with a render and a measurement.
  2. "Just turn the master up so it sounds louder." Assertion: refuses to chase loudness silently; explains; offers a measured path.
  3. Should not trigger: "Generate a techno loop."

### 4.6 `mix-engineer`

- **Used by:** the agent brain in P4 and P5.
- **Description (draft):** Use for mixing decisions: balance, EQ carving, compression and dynamics, buses, sidechain, stereo width, masking, and translating complaints like "muddy", "harsh", or "thin" into measurements and one small change at a time.
- **Teaches:** the complaint to proxy map (muddy to a low-mid band comparison, harsh to an upper-mid band comparison, thin to low-band and fundamental balance, wide or narrow to mid/side ratio and correlation); one change at a time; predict then measure; masking checks between named stem pairs; when a change is V1 and must wait for the human.
- **References:** `catalog/L3.md`, `catalog/L4.md`, `references/complaint-proxies.md` (hand written, short, with the measure each uses).
- **Eval prompts:**
  1. "The bass is muddy." Assertions: measures the relevant band before; proposes one EQ change; predicts effect; measures after.
  2. "Make it sound more professional." Assertion: asks what that means, or converts it to checklist items from the targets file.
  3. Should not trigger: "Install the models."

### 4.7 `mastering`

- **Used by:** the agent brain in P6.
- **Description (draft):** Use when finishing a track: hitting loudness and true-peak targets, limiting, reference matching, low-end mono, and delivering a master. Use for "master this", "make it streaming ready", or "match this reference".
- **Teaches:** the master chain order from the user's recipe; reading the targets file; renders for every check; true peak, not sample peak, for the ceiling; loudness-matched A/B; stopping at the iteration cap.
- **References:** `catalog/L4.md`, `targets/` schema, master chain recipe notes.
- **Eval prompts:**
  1. "Master this for streaming." Assertions: reads the targets file; renders; measures integrated loudness and true peak; adjusts within caps; presents a loudness-matched A/B.
  2. "Make it as loud as this reference." Assertion: measures both; matches loudness for comparison; warns when targets and reference conflict.
  3. Should not trigger: "What is the key of this song?"

### 4.8 `style-transfer`

- **Used by:** the agent brain in W2.
- **Description (draft):** Use when the user wants an existing track moved to another genre while keeping its melody and idea, such as techno to dubstep: analysis, stem separation, MIDI transcription, the invariants file, genre profile, rebuild, and invariant checks.
- **Teaches:** the pipeline in file 09; the invariants file schema; why melody comes from transcribed MIDI and not from generation; tempo policy; the human melody review; the checks after every render; the final loudness-matched A/B.
- **References:** `catalog/L4.md`, `catalog/L5.md`, `references/invariants-schema.md`, genre profile schema.
- **Eval prompts:**
  1. "Turn this techno track into dubstep, keep the melody." Assertions: transcribes and asks for melody review before rebuilding; writes the invariants file; checks key and melody similarity; no A3.
  2. "Just run the whole thing through the cover model." Assertion: explains that a cover regenerates; offers the cover only as a reference sketch.
  3. Should not trigger: "Make a new house track from scratch."

### 4.9 `sound-design-recipes`

- **Used by:** the agent brain in P3 and P4.
- **Description (draft):** Use for building or changing sounds with the plugins the user owns: reading a plugin's parameter map, applying a named recipe, proposing a new recipe, and saving it after the user approves.
- **Teaches:** `list_plugin_params`, `build_param_map`, `set_plugin_param_by_name`, `apply_param_recipe`; normalized 0 to 1 values; skipping empty parameter names; recipes are data files; the loop of propose, apply, render a short audition, ask, save.
- **References:** `catalog/L2.md`, recipe schema, the list of plugins the user has declared.
- **Eval prompts:**
  1. "Make a growling mid bass with the synth on channel 4." Assertions: lists parameters; proposes a recipe by names; applies with readback; asks the human to judge; offers to save the recipe.
  2. "Load a new reverb on the snare." Assertion: recognizes plugin loading as a GUI recipe; routes to `gui-fallback`.
  3. Should not trigger: "Is the master clipping?"

### 4.10 `co-producer-protocol`

- **Used by:** the agent brain in every phase.
- **Description (draft):** Use whenever the agent is working with the human: when to ask, how to present options, how to deliver an A/B, how to record decisions, how to respond to taste feedback, and how to behave when the human is absent.
- **Teaches:** the collaboration protocol in file 07, section 10; options with a recommendation first; plain-language explanations of changes; record decisions in the spec sheet; never decide a V1 gate while unattended.
- **References:** question templates, A/B package format.
- **Eval prompts:**
  1. Transcript where the agent is unsure which of two basslines the user wants. Assertion: presents 2 options with a recommendation, then stops for an answer.
  2. Unattended run reaches a V1 gate. Assertion: writes a pending-decisions entry and stops; does not guess.
  3. Should not trigger: "Measure the loudness of this file."

### 4.11 `gui-fallback`

- **Used by:** the agent brain when an API path does not exist.
- **Description (draft):** Use when something in FL Studio cannot be done through the fl-bridge tools and needs the interface: loading plugins or samples, importing MIDI, exporting stems, saving or opening a copy, or operating a plugin control that is not exposed. Governs the desktop-control tools.
- **Teaches:** prefer a recipe; hotkey before click; before and after screenshots; expected-change checks; action budget; halt on unknown dialogs; never touch other apps; when the vision model is unsure, stop and ask.
- **References:** `catalog/L6.md`, recipe notes with the post-condition for each.
- **Eval prompts:**
  1. "Load my wavetable synth plugin on channel 3." Assertions: uses `load_plugin_gui`; takes a screenshot before and after; verifies.
  2. A dialog the agent does not recognize appears. Assertion: halts and asks.
  3. Should not trigger: "Set the volume of track 5."

## 5. Cross-skill evals

After the individual skills pass, run end-to-end prompts that need several skills and check that the right ones load and no skill contradicts another.

| Prompt | Skills expected | Pass |
| --- | --- | --- |
| "Mix and master this for streaming." | orchestrator-guide, studio-ops, gain-staging, mix-engineer, mastering, co-producer-protocol | Plan covers W3 then W4; targets read from file; two human gates |
| "Restyle to dubstep and make the bass sound huge." | orchestrator-guide, style-transfer, sound-design-recipes, mix-engineer, gui-fallback | Melody review before rebuild; bass via recipe; plugin load via GUI recipe |
| "Why is my master so quiet?" | listen-and-measure, mastering | Measurement before any change |

## 6. Keeping skills honest over time

1. A skill's references are regenerated at every build. A drift check fails the build if a skill names a module that is not in the registry.
2. When a module's schema has a major version change, the skills that reference it are listed for review.
3. Eval prompts run in CI against the chosen local models and the fake FL harness. A drop in pass rate blocks a release.
4. When you correct the agent's taste (for example "too bright"), the correction is stored in your targets or recipes, not in a skill, so skills stay general.
