# 03. Architecture

## 1. Shape of the system

Four MCP servers sit between the agent brain (a local tool-calling model) and the world. Measurement and transformation are kept apart from generative models. Every path that touches FL Studio ends in the sandbox copy.

```
                          +-----------------------------+
                          |  Agent brain (local LLM)    |
                          |  sees only the tool slice   |
                          |  for the current phase      |
                          +--------------+--------------+
                                         |  MCP (stdio)
                          +--------------v--------------+
                          |  Orchestrator (coproducer)  |
                          |  registry, planner,         |
                          |  executor, scheduler,       |
                          |  ledger, spec sheet         |
                          +--+------+--------+-------+--+
                             |      |        |       |
              +--------------v+  +--v-------+ +-----v----+ +v---------------+
              | fl-bridge     |  | studio-  | | studio-  | | desktop-       |
              | state in FL   |  | audio    | | ml       | | control        |
              | (L0,L1,L2,L3) |  | (L4)     | | (L5)     | | (L6)           |
              +------+--------+  +----+-----+ +----+-----+ +-------+--------+
                     | SysEx          |            |               | screenshots,
                     | over loopMIDI  |            |               | mouse, keys
              +------v--------+       |            |               |
              | FL Studio     |<------+-- files ---+  render CLI   |
              | dispatcher    |   (bounces, stems, MIDI)          |
              | script +      |<----------------------------------+
              | piano roll    |        GUI recipes (load plugin, import MIDI, export stems)
              | script        |
              +---------------+
```

File flows are shown as `files` in the diagram: bounces and stems flow from FL to `studio-audio`, and generated audio and MIDI flow from `studio-ml` into the sandbox folder.

### The four servers

| Server | Job | Layers it hosts | Runs where |
| --- | --- | --- | --- |
| `fl-bridge` | Read and write project state inside FL, with verification and rollback | L0 transport, L1 FL ops (as remote calls), L2 verified wrappers, L3 recipes | Host Python, talks to FL over SysEx |
| `studio-audio` | Measure and transform audio and note data | L4 measures | Host Python, CPU only |
| `studio-ml` | Run generative, transcription, separation, critique, and vision models | L5 model adapters | One isolated environment per model stack, started on demand |
| `desktop-control` | Operate the FL interface when the API cannot | L6 primitives and recipes | Host Python on the interactive Windows session |

Why four and not one: failures, dependencies, and permissions differ. `studio-audio` is deterministic and cheap. `studio-ml` is heavy and optional. `desktop-control` is the only server that can act outside FL's data model, so it has its own guardrails and can be disabled alone. `fl-bridge` is the only server that writes project state.

## 2. Process boundaries

| Process | Environment | Why separate |
| --- | --- | --- |
| FL Studio | FL's embedded Python (about 3.9) | Cannot be changed. Only the dispatcher and the piano roll script run here. |
| Orchestrator and `fl-bridge`, `studio-audio`, `desktop-control` | One host venv, Python 3.10+ | Share the module registry and the Result type |
| `studio-ml` model stacks | One venv each: ACE-Step (3.11 to 3.12), Demucs, Basic Pitch, critique model, vision model, LLM runtime | Conflicting pins (ACE-Step requires 3.11 to 3.12); isolation keeps one broken install from breaking the rest |
| Local LLM runtime | A separate server process exposing an OpenAI-compatible endpoint | The runtime is swappable. The orchestrator only needs an endpoint. |

Servers use the official [MCP Python SDK](https://py.sdk.modelcontextprotocol.io/) over stdio. Tool definitions are generated from module manifests, not written by hand.

## 3. The FL-side footprint

Only two files live inside FL's data folders. Both are generated.

| File | Location | Job |
| --- | --- | --- |
| `device_coproducer.py` | `Documents\Image-Line\FL Studio\Settings\Hardware\coproducer\` | Controller script. First line `# name=Coproducer`. Receives SysEx, dispatches to L1 ops, replies with SysEx. |
| `coproducer_notes.pyscript` | `Documents\Image-Line\FL Studio\Settings\Piano roll scripts\` | Writes notes into the piano roll. Body is generated per call (route N1) or reads a staged file if Gate 0 proves that is allowed (route N2a). |

The dispatcher MUST be small and dumb. It contains: a SysEx receiver, a frame reassembler, a table mapping op names to L1 functions, a reply sender, and an idle-time work queue. It MUST NOT contain any music logic, retries, or policy. All judgment lives in the host.

The controller script is selected as the controller type in MIDI Settings, as the [MIDI scripting manual](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/midi_scripting.htm) describes. Setup prints exact click-path instructions and then verifies by calling `ping_fl`.

## 4. The bridge protocol (SysEx over virtual MIDI)

This is the contract between `fl-bridge` and the dispatcher. It is frozen at Gate 0.

### 4.1 Transport

1. Two virtual MIDI ports from [loopMIDI](https://www.tobias-erichsen.de/software/loopmidi.html): `coproducer-in` (host to FL) and `coproducer-out` (FL to host).
2. The host sends SysEx on `coproducer-in`. FL's controller script receives it in its SysEx handler and replies with the `device` module's SysEx output function on `coproducer-out`. Gate 0 confirms the exact handler and function names against the live API inventory.
3. Port names are discovered by `find_midi_ports`, never hardcoded.

### 4.2 Frame format

All bytes inside a SysEx message MUST be 7-bit (0x00 to 0x7F).

```
F0 7D 43 50  VV  TT  RR RR  SS SS  NN NN  <payload bytes, 7-bit packed>  CC  F7
|  |  |  |   |   |   |      |      |
|  |  |  |   |   |   |      |      +-- total frame count (14 bit, big-endian 7-bit pair)
|  |  |  |   |   |   |      +--------- sequence number of this frame (14 bit)
|  |  |  |   |   |   +---------------- request id (14 bit)
|  |  |  |   |   +-------------------- message type (see below)
|  |  |  |   +------------------------ protocol version (starts at 0x01)
|  +--+--+---------------------------- 0x7D (non-commercial id) then ASCII 'C','P'
+------------------------------------- SysEx start
```

1. Manufacturer byte 0x7D is the MIDI reserved id for non-commercial and experimental use. Then the two ASCII bytes `C` (0x43) and `P` (0x50) tag the stream so other SysEx traffic is ignored.
2. `CC` is a checksum: the sum of all bytes from `VV` through the last payload byte, masked to 7 bits.
3. Payload size per frame is `max_payload`, default 200 bytes after packing, a conservative value below the 240 and 256 byte truncation points seen in the reports in file 02 (M-10). Gate 0 measures the real limit and may raise it.
4. A message larger than `max_payload` is split by `split_frames` and rebuilt by `join_frames`.

### 4.3 Message types

| TT | Name | Direction | Meaning |
| --- | --- | --- | --- |
| 0x01 | REQUEST | host to FL | Call one op |
| 0x02 | REPLY | FL to host | Result of a request |
| 0x03 | ERROR | FL to host | The op raised or the arguments failed validation |
| 0x04 | PING | host to FL | Liveness |
| 0x05 | PONG | FL to host | Liveness reply with FL and API versions |
| 0x06 | ACK | either | Frame group received |
| 0x07 | EVENT | FL to host | Unsolicited state change (play state, peak batch) |

### 4.4 Payload encoding

1. The body is bytes. Bytes are converted to 7-bit form by `encode_sysex` in groups of 7: for each group of up to 7 input bytes, emit one header byte whose bit `i` holds the top bit of input byte `i`, followed by the input bytes with their top bit cleared. A partial final group of `n` bytes emits `n + 1` bytes.
2. Request body: UTF-8 text `op_name` then a unit separator (0x1F) then each argument as a JSON scalar or small JSON value, separated by 0x1F. If Gate 0 shows `json` is not importable inside FL, arguments are restricted to integers, floats, booleans, and strings, using a tiny parser that the generator emits into the dispatcher.
3. Reply body: the same encoding for the return value.
4. Floats are sent as decimal text with at least 9 significant digits, so a 0 to 1 parameter value round-trips.

### 4.5 Behavior rules

1. The host assigns request ids. A reply carries the same id. `match_reply` pairs them.
2. `wait_for_reply` enforces a timeout (default 2 seconds for reads, 5 for writes). On timeout the result is `E_TIMEOUT`.
3. Reads MAY be retried up to 2 times. Writes MUST NOT be retried blindly. After a write timeout the host reads state to learn whether it landed.
4. The dispatcher processes at most one request at a time and does its work in the idle handler to keep FL responsive.
5. Large replies (for example a plugin parameter map of up to 4096 entries) are paged: the op takes `offset` and `count` arguments.
6. The dispatcher ignores any SysEx that lacks the `7D 43 50` prefix.
7. A sandbox guard exists host-side: write ops are refused unless the sandbox flag is set for the session and the active project path matches the sandbox folder. The dispatcher also reports the active project name in every PONG so the host can check it.

### 4.6 What Gate 0 proves for the bridge

1. A PING round trip works through loopMIDI and returns FL and API versions.
2. A 4 KB payload round-trips intact, and the largest safe frame size is measured.
3. Sustained throughput is measured for 4096-entry parameter dumps.
4. Whether `json` imports inside FL is recorded.
5. Behavior when FL is busy (for example during render) is recorded.

## 5. Capture routes (how the system gets ears)

FL's scripting API exposes no live audio buffers. The official docs describe a command-line render, so capture has three routes, in priority order.

| Route | How | Use | Notes |
| --- | --- | --- | --- |
| C1 Command-line render | Save the sandbox copy, then run FL with `/R /E<format> /F<folder> /O<outfolder> project.flp` per the [export reference](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_save_export.htm) | Every measurement pass | No GUI. PROBE: executable path, output location, behavior if FL is already running. |
| C2 Live peak polling | Inside FL, poll each mixer track's peak level | Gain staging during playback | Peaks are not loudness. |
| C3 Split stems | Export dialog "Split mixer tracks" through a GUI recipe, or Demucs on a full render | Per-track analysis, restyle input | Dialog options are GUI recipes. |

Capture records the snapshot id and project file hash with the file, so a measurement can never be attributed to the wrong state (failure mode F-14).

Open item: whether the API can save the project. If it cannot, the save is a GUI recipe (`save_project_copy`) or a hotkey sent by `desktop-control`. Gate 0 decides.

## 6. Sandbox design

1. **Sandbox folder.** `<workspace>\sandbox\<project-name>\`. Setup creates it. The path is in the config file.
2. **Copy on start.** Starting a session copies your `.flp` and its sample references into the sandbox. The original is read once and never opened for write.
3. **Original hash.** The SHA-256 of the original is recorded at start and re-checked at promotion.
4. **Path checks.** Every module with side-effect class "writes FL" or "writes files" or "GUI" validates that its target is under the sandbox folder. A violation returns `E_SANDBOX_VIOLATION`.
5. **Snapshots.** Before each phase the orchestrator takes a state snapshot (a JSON dump of all tracked mixer, channel, pattern, and plugin parameters) and a project file copy. Rollback restores state by replaying the snapshot through verified writes, or by reopening the saved copy (GUI recipe) when parameters alone cannot restore it.
6. **Promotion.** A human action. It produces a report and a diff of the ledger, and then copies the chosen artifacts into a destination you name. It is autonomy level A3 and the orchestrator never invokes it on its own.

## 7. GPU and process scheduling

1. At 12 to 16 GB VRAM, at most one heavy model is resident at a time. Heavy means a generative audio model, an audio-language critique model, or a large vision model.
2. The agent-brain LLM needs VRAM too. Two supported modes: (a) brain on GPU with the other models run on demand after the brain is paused or offloaded, or (b) a smaller brain that stays resident with generative models loaded in the remaining space. The scheduler's model registry declares each model's VRAM footprint and the scheduler picks.
3. The scheduler tracks loaded models, evicts before loading, refuses loads that will not fit, and logs every load and unload to the ledger.
4. Analysis prefers DSP first (key, BPM, sections, loudness) and uses a model only for what DSP cannot do.

## 8. Repository layout

```
coproducer/
  pyproject.toml
  config.toml                       # paths, ports, sandbox, targets file locations
  modules/
    l0_transport/<module>/{<module>.py, module.toml, test_<module>.py}
    l1_fl_ops/    (generated)
    l2_verified/
    l3_recipes/
    l4_measures/
    l5_models/
    l6_gui/
  fl_side/                          # generated artifacts installed into FL
    device_coproducer.py
    coproducer_notes.pyscript
  servers/
    fl_bridge/server.py
    studio_audio/server.py
    studio_ml/server.py
    desktop_control/server.py
  orchestrator/
    registry.py  tools.py  planner.py  executor.py  verifiers.py
    scheduler.py  ledger.py  spec_sheet.py  collab.py
  models/
    registry.toml                   # per-model role, VRAM, license, load command, endpoint
    installers/<stack>.py
    envs/<stack>/                   # created by setup
  skills/<skill-name>/SKILL.md      # plus references/ generated from manifests
  catalog/                          # generated reference docs per layer
  genre_profiles/<genre>.toml
  targets/<name>.toml               # loudness and balance targets you set
  specs/<project>/spec.md           # per-project spec sheet
  specs/<project>/invariants.yaml
  tools/
    lint_modules.py  gen_l1.py  gen_fl_side.py  gen_catalog.py
    probe_api.py  bench_llm.py  bench_vision.py
  tests/
    fake_fl/  fixtures/audio/  integration/  e2e/
  runs/<run-id>/ledger.jsonl        # append-only run logs
  sandbox/                          # sandbox project copies
```

## 9. Error taxonomy

All modules return the same error codes so the executor can decide what to do without reading messages.

| Code | Meaning | Executor default |
| --- | --- | --- |
| E_ARG | Invalid argument | Return to the agent with the schema; no retry without a change |
| E_NOT_FOUND | Name or id does not exist | Return nearest valid names |
| E_UNSUPPORTED_API | FL build lacks the function | Stop; suggest the GUI recipe if one exists |
| E_TIMEOUT | No reply in time | Retry if read; verify state if write |
| E_NOT_VERIFIED | Write read back differently | Do not proceed; log; offer rollback |
| E_SANDBOX_VIOLATION | Target outside sandbox | Halt the step; always logged |
| E_GPU_BUDGET | Model will not fit | Evict or choose a smaller variant |
| E_MODEL | Model call failed | Retry once; then fall back (for example DSP critique) |
| E_GUI_MISMATCH | Screenshot check failed | Reverse the action if possible; halt on repeat |
| E_BLOCKED_BY_DIALOG | Unexpected dialog | Halt; ask the human |
| E_IO | File read or write failed | Surface path and cause |
| E_HALTED | Halt hotkey or budget reached | Stop the run; ledger final entry |
| E_INTERNAL | A module raised an unexpected error (caught) | Log; do not retry; report as a bug |
| E_AUTONOMY | A step is above its allowed level or was not approved | Stop; ask the human |
| E_PENDING_HUMAN | A person must answer and none is present | Write the pending decision; stop |
