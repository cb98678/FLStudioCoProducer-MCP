# 13. Risks, Decisions, and Open Questions

## 1. Decision log

Decisions made where you said "you decide", or where research changed an assumption. Each has a reason and the condition that would reverse it.

| ID | Decision | Reason | Reverse if |
| --- | --- | --- | --- |
| D-01 | Clean-room build. No existing FL MCP is forked, extended, or relied on. | Your instruction. Also removes inherited design limits. | You say otherwise |
| D-02 | Four MCP servers: `fl-bridge`, `studio-audio`, `studio-ml`, `desktop-control` | Separates deterministic measurement from generative models and GUI control; separate failure and permission domains | The server count causes real operational cost |
| D-03 | Update to FL Studio 2026.1.7 before Gate 0 | FL 2026 is current and adds scripting functions the plan uses; updates are the current maintenance line (file 02, FX-16, FX-22) | The update breaks something you depend on |
| D-04 | Primary capture is the command-line render | The official export reference documents it (FX-18); no GUI needed | Gate 0 shows it cannot render a project in your setup |
| D-05 | Bridge is MIDI SysEx over loopMIDI | FL's Python cannot touch disk (FX-01); virtual MIDI is the available channel | Gate 0 finds another documented channel, or throughput is unusable |
| D-06 | Many small modules with a linter-enforced rule set | Cheap per task for local agents; mechanical gates | Calibration shows the budget is too tight or too loose |
| D-07 | Generate L1 from the official function tables | Mechanical work should cost no model tokens | The inventory probe shows tables are too incomplete to generate from |
| D-08 | One isolated environment per model stack | ACE-Step pins Python 3.11 to 3.12 (M-01); isolation contains breakage | Setup time becomes unreasonable |
| D-09 | Melody comes from transcribed MIDI, not generative cover | Cover models regenerate; small language models copy melody weakly (M-01) | A model demonstrably preserves melody above your threshold |
| D-10 | DSP-first critique; the audio-language model is optional | Non-commercial license, Linux/A100/H100 test hardware (M-05), VRAM pressure | It runs well on your machine and is allowed for your use |
| D-11 | Sandbox copy plus human-only promotion | Full autonomy needs a safe place to act | You choose a different risk posture |
| D-12 | The plan hardcodes no loudness, balance, or genre numbers | You own targets; avoids stale or wrong defaults | You supply defaults |
| D-13 | The local LLM runtime is swappable behind an OpenAI-compatible endpoint | The runtime landscape changes quickly | One runtime proves clearly better |
| D-14 | GUI recipes prefer hotkeys and anchors; vision grounding confirms | Reliability on a custom-drawn UI | Vision accuracy is high enough to lead |
| D-15 | Notes and tempo policy are expressed in beats | Melody relationships survive tempo changes | A genre needs absolute-time features |
| D-16 | Two note-writing routes (generated piano roll script and MIDI import); Gate 0 picks the primary | Piano roll file I/O is unconfirmed (FX-12) | n/a (both stay as fallbacks) |
| D-17 | Peaks guide gain staging; loudness only from renders | Peaks are not loudness (FX-15) | A documented live loudness source appears |
| D-18 | A write is never retried blindly | FL can silently ignore writes (FX-17); a blind retry can double-apply a toggle | n/a |
| D-19 | Stems come from FL's split export (GUI) and from Demucs as a cross-check | The split option is GUI (FX-19); Demucs works on any render | CLI split proves reliable |
| D-20 | Python 3.10 or newer for the host | Compatibility with the MCP SDK and the audio libraries; verify at Gate 0 | The SDK requires newer |

## 2. Risk register

Likelihood and impact are L, M, H. The mitigation is part of the design, with the file where it lives.

| ID | Risk | Likelihood | Impact | Mitigation | File |
| --- | --- | --- | --- | --- | --- |
| R-01 | FL silently ignores scripted writes | H | H | Readback on every write; `verified` field; no blind retry | 04, 07 |
| R-02 | SysEx size or throughput limits in loopMIDI or FL | M | H | Conservative framing; Gate 0 measures; pages for large replies | 03 |
| R-03 | `json` does not import inside FL | M | M | Text protocol fallback | 03 |
| R-04 | The API cannot save a project (CLI render needs a saved file) | M | H | GUI recipe or hotkey; Gate 0 decides | 03, 12 |
| R-05 | CLI render behaves differently than the manual implies (output location, running FL) | M | H | Probe at Gate 0; config-driven paths | 12 |
| R-06 | Piano roll scripts cannot read files | M | M | Route N1 embeds notes; route N2 MIDI import | 03, 12 |
| R-07 | Official stubs and web docs lag your build | M | M | Live inventory probe; modules declare min API level | 02, 04 |
| R-08 | Small coding model cannot hit the card pass rates | M | H | Calibration before trust; escalation path; card quality feedback | 06 |
| R-09 | Small brain model makes bad tool calls | M | H | Phase-sliced tools; schema validation; brain benchmark | 07, 08 |
| R-10 | GPU memory contention | H | M | One heavy model resident; scheduler; DSP first | 03, 08 |
| R-11 | Melody transcription is wrong on dense material | H | M | Human review gate; chord loop cross-check; invariants | 09 |
| R-12 | GUI automation misclicks | M | H | Window-scoped input; verified steps; budget; halt | 03, 07 |
| R-13 | FL's UI changes between versions break GUI recipes | M | M | Recipes keyed to recorded screenshots per version; doctor re-checks | 08 |
| R-14 | Display scale or DPI changes break anchors | M | M | Scale recorded; recipes refuse on mismatch | 08 |
| R-15 | Licensing blocks a model | M | M | License stored per model; optional models have fallbacks | 08 |
| R-16 | Supply chain risk in downloaded repositories | L | H | Pinned commits; isolated envs; offline default | 08 |
| R-17 | The agent chases loudness or over-processes | M | M | Delta caps; targets owned by you; loudness-matched A/B | 07, 09 |
| R-18 | Stale capture attributed to the wrong state | M | M | Snapshot id and project hash on every capture | 03, 07 |
| R-19 | Module scope creep inflates size | M | M | Linter size budget as a gate | 04 |
| R-20 | Three lanes integrate late | M | H | Gate 0 freeze; contract tests; per-gate acceptance | 11, 12 |
| R-21 | Security software flags synthetic input | M | L | Documented; no bypass | 08 |
| R-22 | A user-selected controller script is overwritten by an FL update or a settings reset | L | M | Doctor checks the script is present and selected | 08 |
| R-23 | The MCP SDK changes between versions | M | M | Pin; contract tests on tool schemas | 11 |
| R-24 | "Spirit" is lost despite passing metrics | M | M | Human A/B is the only authority for V1 | 01, 07 |

## 3. Open questions for you

These were open in the master plan. Nothing blocks starting Gate 0 except 5 and 7.

1. Which synth and effect plugins do you own and want used?
2. Where are your sample libraries?
3. What loudness and true-peak targets, and for which delivery platforms?
4. Which reference tracks represent each genre you care about?
5. What is your exact FL build and audio driver (ASIO or WASAPI)?
6. What are your exact GPU, CPU, and RAM?
7. Confirm the update to FL Studio 2026.1.7 (decision D-03).
8. Any objection to the clean-room build with nothing forked or reused (decision D-01, already your instruction)?
9. Which local LLM runtime do you prefer, if any?
10. Is the original-project promotion step acceptable as a manual command, or do you want a one-click variant with a confirmation?
11. Do you want the agent to work from the real project's sample folder paths, or to copy samples into the sandbox? (Default: reference in place, read-only.)
12. Which display scale and resolution do you use for FL? GUI recipes depend on it.

## 4. Assumptions to confirm

| Assumption | How it is confirmed |
| --- | --- |
| Windows is the FL host OS | Setup probe |
| FL Studio edition supports controller scripting and piano roll scripting | Gate 0 dispatcher and script tests |
| loopMIDI ports can be created on your machine | WP-0.2 |
| A free port of 12 to 16 GB VRAM is available when FL is also running | Setup probe and scheduler measurements |
| Python 3.10 or newer is available for the host and 3.11 or 3.12 for ACE-Step | Setup probe |
| FL can render from the command line on your install | WP-0.8 |
| The local model can be run while FL is open without audio glitches | Observed in Phase 2 |

## 5. Gate 0 unknowns (the PROBE list)

| Unknown | Probe | Work package |
| --- | --- | --- |
| Live API level and the full callable list | Inventory probe | WP-0.3 |
| Does `json` import in FL | Import test | WP-0.6 |
| Real SysEx limits through loopMIDI and FL | Size and throughput test | WP-0.6 |
| Can piano roll scripts read files | File read test | WP-0.5 |
| Contents of the factory piano roll reference | Read the file | WP-0.4 |
| Can the API save the project | API search; else GUI recipe | WP-0.7 |
| Executable name, output folder, and behavior of CLI render | Run it | WP-0.8 |
| Whether CLI honors split-stem settings | Run it | WP-0.8 |
| Does input reach FL's window from the control server | Input probe | WP-0.12 |
| Accuracy of candidate models on this project | Benchmarks | WP-0.17, WP-0.18, WP-2.4 |

## 6. What this plan deliberately does not claim

1. It does not claim any local model is good enough yet. Benchmarks decide.
2. It does not claim melody will be preserved by any generative model. Transcription and review do that.
3. It does not claim the GUI is automatable at high reliability yet. A vision benchmark and a hotkey-first design decide that.
4. It does not give loudness, EQ, or genre numbers. You own those.
5. It does not claim the facts tagged SEEN or PROBE in file 02. Those are checked before they are relied on.
