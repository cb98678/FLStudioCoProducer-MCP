# 08. The Python Layer and the Local Models

Workstream C. One Python project, `coproducer`, installs the models, isolates their environments, schedules the GPU, and runs the loop. This file also covers how the local agent brain and the vision model are chosen, because the plan deliberately does not fix them.

## 1. Commands

All through one command-line entry point.

| Command | Job |
| --- | --- |
| `coproducer setup` | Probe the machine, create environments, install models, install FL-side files, write `config.toml`, run smoke tests |
| `coproducer doctor` | Re-run the probes and smoke tests; report what is wrong in plain terms |
| `coproducer probe-api` | Run the API inventory probe inside FL and save the result |
| `coproducer lint` | Run the module linter |
| `coproducer gen` | Regenerate L1 ops, the FL-side files, catalog docs, and tool definitions |
| `coproducer build-cards` | Run the local-agent build loop over cards |
| `coproducer bench-llm` | Benchmark candidate agent models on tool-calling tasks |
| `coproducer bench-vision` | Benchmark candidate GUI-grounding models on FL screenshots |
| `coproducer serve` | Start the four MCP servers and the orchestrator |
| `coproducer run <spec>` | Start a run from a spec sheet |
| `coproducer resume <run-id>` | Resume an interrupted run |
| `coproducer promote <run-id>` | The human promotion step (A3) |

## 2. What `setup` does

Setup is idempotent. Running it twice changes nothing the second time.

1. **Probe the machine.** Windows version, GPU name, VRAM, driver version, CUDA runtime, free disk space, Python versions available, ffmpeg presence, FL Studio install path and version, user data folder, audio driver in FL (ASIO or WASAPI, informational), loopMIDI ports.
2. **Check the plan's assumptions.** FL Studio 2026.1.7 or newer; Python 3.10 or newer for the host; 3.11 or 3.12 available for ACE-Step. Report any that fail and stop with an exact fix.
3. **Create environments.** One per stack under `models/envs/<stack>/`, using the Python version the stack needs.
4. **Install stacks.** Each installer pins a repository commit or package version and records it in `models/registry.toml`.
5. **Download weights** to a models folder named in the config, with a size estimate shown first and checksum verification after.
6. **Install FL-side files.** Generate and copy the dispatcher and the piano roll script. Print the click-path to select the controller type in MIDI Settings.
7. **Create virtual MIDI ports** instructions for loopMIDI, then verify they appear.
8. **Smoke test each model** (section 6) and the bridge (`ping_fl`).
9. **Write `config.toml`** and a setup report.

Setup MUST NOT change anything outside the workspace, the models folder, and the two FL-side files. It MUST NOT install drivers. If a driver is out of date it says so and stops.

## 3. Isolated environments

One environment per stack because pins conflict. For example, ACE-Step 1.5 requires Python 3.11 to 3.12 per its [README](https://github.com/ace-step/ACE-Step-1.5), and the host project targets 3.10 or newer.

| Stack | Python | Contents | Started by |
| --- | --- | --- | --- |
| host | 3.10+ | Orchestrator, MCP SDK, registry, L0 to L4, desktop-control, numpy, scipy, soundfile, pyloudnorm | `coproducer serve` |
| acestep | 3.11 to 3.12 | ACE-Step 1.5 cloned from GitHub and installed with `uv sync` (no pip package) | Scheduler on demand |
| demucs | 3.10+ (3.12 used) | Demucs (`pip install -U demucs`) and torch | Scheduler on demand |
| basicpitch | 3.11 at most (3.11 used) | Basic Pitch (`pip install basic-pitch`) | Scheduler on demand |
| critique | pinned | Audio-language model stack (optional) | Scheduler on demand |
| vision | pinned | GUI-grounding model stack | Scheduler on demand |
| llm | none (binary server) | Local LLM runtime with an OpenAI-compatible endpoint | Started with `serve` |

Model stacks are driven by a thin runner in each environment that speaks a simple line-delimited JSON protocol over stdin and stdout, so the host never imports model libraries and a broken stack cannot crash the host.

The MCP servers use the official [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/). Pin the version at Gate 0 and re-check the current release before pinning, as the SDK is evolving.

## 4. The model registry

`models/registry.toml` is data. The scheduler and the adapters read it.

```toml
[models.acestep]
role = "generate"
stack = "acestep"
license = "MIT"
vram_gb = { min = 8, typical = 12 }
variants = ["2B-turbo+lm0.6B", "2B-sft+lm1.7B"]
default_variant = "2B-turbo+lm0.6B"
commit = "<pinned at setup>"
load = "runner acestep --variant {variant}"
smoke = "generate 5s prompt='four on the floor kick' -> nonempty wav"
optional = false

[models.demucs]
role = "separate"
stack = "demucs"
license = "<read from the repo at setup>"
vram_gb = { min = 2, typical = 4 }
commit = "<pinned at setup>"
smoke = "separate 5s synthetic mixture -> 4 nonempty stems"
optional = false

[models.basicpitch]
role = "transcribe"
stack = "basicpitch"
vram_gb = { min = 0, typical = 0 }     # runs on CPU
smoke = "transcribe a synthetic monophonic scale -> 8 notes within a semitone"
optional = false

[models.flamingo]
role = "critique"
stack = "critique"
license = "non-commercial"
vram_gb = { min = 10, typical = 14 }   # with quantization; to be measured
optional = true
fallback = "dsp_critique"

[models.agent]
role = "brain"
stack = "llm"
endpoint = "http://127.0.0.1:<port>/v1"
chosen_by = "bench-llm"

[models.vision]
role = "ground_gui"
stack = "vision"
chosen_by = "bench-vision"
```

Fields marked "to be measured" or "pinned at setup" are not facts in this plan. The numbers in the table above are planning ranges drawn from the ACE-Step tier description and the Music Flamingo model card in file 02, and setup replaces them with measured values.

### Licenses

Each model's license is stored at install. The registry marks non-commercial models. The orchestrator reads `optional` and `fallback`: if an optional model is absent, the corresponding DSP fallback is used and the ledger says so. [Music Flamingo's model card](https://huggingface.co/nvidia/music-flamingo-hf) lists a non-commercial license, so it is optional by design.

## 5. The GPU scheduler

Goals: never run out of memory, keep the loop moving, and be explicit.

```
request(model, phase):
    need = registry[model].vram_estimate(variant)
    free = query_free_vram()
    if need <= free: load
    else:
        for m in resident models sorted by (not needed in this phase, last used):
            unload(m); free = query_free_vram()
            if need <= free: break
        if need > free: try smaller variant; else fail E_GPU_BUDGET
    record in ledger: model_load with measured VRAM after load
```

Rules:

1. At most one heavy model is resident (a generator, the critique model, or the vision model). The agent brain is either resident (mode a) or paused (mode b).
2. **Mode a, resident brain.** A smaller brain stays loaded. Heavy models use the remainder. Choose this when the brain plus the heaviest needed model fit together.
3. **Mode b, swapped brain.** A larger brain is unloaded while a heavy model runs. The orchestrator persists state to the ledger first, so nothing is lost across the swap.
4. The scheduler measures VRAM after each load and updates the registry's observed footprint.
5. Phase hints: P1 prefers demucs and basicpitch; P3 may use acestep; P5 may use the critique model; GUI recipes need the vision model during their steps.
6. The scheduler never loads a model in a path that the sandbox guard has not cleared; model outputs go into the sandbox folder.

## 6. Smoke tests

A smoke test proves the model works on this machine. It uses a tiny synthetic input so it runs in seconds to a minute.

| Stack | Smoke test | Pass |
| --- | --- | --- |
| acestep | Generate 5 seconds from a short prompt | Non-empty WAV; duration within 0.5 s of request; not silent by `detect_silence` |
| demucs | Separate a 5 second synthetic mixture | Four non-empty stems; durations match |
| basicpitch | Transcribe a synthetic 8-note scale | 8 notes; pitches within 1 semitone |
| critique | Critique a 10 second synthetic clip | Non-empty text under a time limit |
| vision | Ground "play button" on a stored FL screenshot | Coordinates inside the labeled region |
| llm | Round trip of a tool call | Valid tool call JSON for a trivial tool |

## 7. Choosing the agent brain (benchmark `bench-llm`)

No model is fixed in this plan. The landscape moves monthly. The shortlist is taken from current roundups at Phase 0 (see [KDnuggets](https://www.kdnuggets.com/top-7-coding-models-you-can-run-locally-in-2026) and [Morph's ranking](https://www.morphllm.com/best-ollama-models) as starting points; both were seen in search results only) and every candidate is measured on this project's own tasks.

### Runtime

The runtime MUST expose an OpenAI-compatible endpoint with tool calling. Candidates: llama.cpp server and Ollama. The orchestrator talks to the endpoint only, so the runtime is swappable. Pick by whether it supports the model's tool-call format reliably on Windows.

### Benchmark design

1. **Set.** 40 tasks. Each gives a phase, a tool slice, a short ledger tail, and an instruction. The correct answer is a specific tool call with specific arguments (or a refusal where the autonomy rules require one).
2. **Mix.** 10 single-call reads, 10 verified writes, 10 multi-step plans (checked against a reference plan structure), 5 autonomy-refusal cases, 5 cases where a tool returns an error and the agent must recover correctly.
3. **Metrics.** Valid-JSON rate, correct-tool rate, correct-argument rate, correct-refusal rate, recovery rate, tokens per step, steps per second on the target GPU, VRAM at the context length used.
4. **Adoption.** The model must reach at least 95 percent valid JSON, at least 85 percent correct tool selection, and 5 of 5 correct refusals, with VRAM that fits the chosen scheduler mode. These are starting thresholds.
5. **Reuse.** The same benchmark also scores coding models for the module-authoring role through the calibration set in file 06. One model MAY serve both roles.

## 8. Choosing the vision model (benchmark `bench-vision`)

FL Studio's interface is custom drawn, so there is no accessibility tree to read. The `ground_gui_element` adapter needs a model that returns screen coordinates for a described element. Open candidates seen in search results include [UGround](https://github.com/OSU-NLP-Group/UGround), [GUI-Actor](https://microsoft.github.io/GUI-Actor/), and others listed in a [2026 survey](https://www.perea.ai/research/gui-grounding-models-2026). All are SEEN only.

Benchmark:

1. **Set.** 60 screenshots taken from your FL install at the resolution and scale you use: browser, channel rack, piano roll, mixer, plugin windows, export dialog, MIDI settings. Each has labeled target elements with bounding boxes.
2. **Metric.** Click accuracy: a predicted point inside the box. Report by window type.
3. **Adoption.** At least 90 percent on the windows the GUI recipes use (browser, channel rack, mixer, export dialog), measured at your actual display scale. Below that, the recipe falls back to hotkeys and fixed anchors, and the plan records which recipes are only semi-reliable.
4. **Hybrid.** Where a recipe can use a keyboard shortcut or a fixed anchor from a recorded reference screenshot, it does so first and uses the vision model only to confirm.

## 9. Local coding model for card building

Chosen with the calibration set in file 06, using the same candidates as the brain benchmark. Stronger models MAY be configured for escalations only.

## 10. Windows specifics

1. **loopMIDI.** Two ports named `coproducer-in` and `coproducer-out`. Setup checks for them and explains how to create them. Vendor page: [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html) (known vendor page, not opened for this plan).
2. **Python launcher.** Setup finds interpreters with the `py` launcher so it can select 3.10, 3.11, and 3.12 explicitly.
3. **Paths.** Use `pathlib`; long paths enabled; the workspace should not sit under a cloud-synced folder, because sync clients lock files during render.
4. **Documents folder.** FL's data folder is under the Documents folder by default. If it is redirected (for example by OneDrive), setup reads the real location.
5. **Permissions.** The desktop-control server needs to run in the interactive user session, not as a service. It does not need administrator rights. FL itself and the control server MUST run at the same integrity level, or input will be blocked.
6. **Display scale.** GUI recipes record the display scale in the config and refuse to run if it differs from the recorded value, because recorded anchors depend on it.
7. **Audio driver.** CLI render uses FL's own export path and does not need a live audio device, but playback-based gain staging does. Record the active driver and buffer size in the setup report.
8. **Disk.** Models and renders need space. Setup shows an estimate before downloading and refuses if free space is below the estimate plus a margin. Estimates are measured, not assumed.
9. **Antivirus.** Synthetic input from the control server can trip security software. Setup documents this and does not attempt to bypass it.

## 11. Supply chain hygiene

1. Every installer pins a version or commit and records it.
2. Weights are verified by checksum where the publisher provides one.
3. Installers use only the registries and repositories listed in the config.
4. Models run with no network access by default after install (offline mode flags set where supported).
5. Downloaded repositories are treated as untrusted code: they run only inside their own environment and never inside the host.

## 12. The analysis libraries (host side)

| Need | Candidate | Status |
| --- | --- | --- |
| Reading and writing audio | `soundfile` | Candidate; verify at Gate 0 |
| Loudness | `pyloudnorm` ([listing](https://pypi.org/project/pyloudnorm/0.0.1)) | SEEN; verify against reference signals |
| Resampling for true peak | `scipy.signal.resample_poly` | Candidate |
| Tempo, key, sections | `librosa` or similar DSP library | Candidate; accuracy measured on a small labeled set at Gate 1 |
| MIDI reading and writing | `mido` or `pretty_midi` | Candidate |
| Screenshots and input | A Windows screen capture library and an input library | Chosen in Phase 0 after checking that input reaches FL's window |

Every candidate is checked against its current official documentation at the time it is pinned, per your standing instruction. The plan records the version used in the setup report.
