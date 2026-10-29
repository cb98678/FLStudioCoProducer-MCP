# 04. The Module System

The entire design hangs on one idea: every unit of code is one function with one job, small enough for a 12 to 16 GB local model to write in one pass and for a machine to verify. A rule a machine can check is a rule a small model cannot quietly break. So each rule below is enforced by the linter, not left to convention.

## 1. The eight module rules

1. **One public function per file.** The file name is the function name, written verb then noun (`measure_true_peak`, `set_track_volume_verified`). Private helpers MAY exist in the same file only if they are named with a leading underscore and the whole file stays within the size budget.
2. **A size budget.** The function body is at most 40 lines, nesting depth at most 3, at most 6 parameters. These are starting values, tuned after the calibration set at Gate 0.
3. **A typed signature that returns a `Result`.** Arguments and return value are JSON friendly. Errors never cross the module boundary as exceptions.
4. **A declared side-effect class.** One of: `pure`, `reads_fl`, `writes_fl_sandbox`, `reads_files`, `writes_files`, `gui`. Imports MUST match the class, so a pure module cannot import MIDI, subprocess, or screen libraries.
5. **Declared dependencies.** Minimum FL API version, models, binaries, Python packages.
6. **A manifest, `module.toml`,** with summary, input and output schemas, side-effect class, autonomy level, and cost class.
7. **Tests ship with the module.** At least one golden case and one failure case, run against the fake FL harness or synthetic audio.
8. **Composition only through the registry.** A module calls other modules by name through the registry. It never imports another module's file. Layer rule: a module MAY call modules in the same or lower layers only.

## 2. The Result type

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Error:
    code: str                      # one of the E_* codes in file 03, section 9
    message: str                   # short, human readable, no stack traces
    retryable: bool = False
    detail: dict = field(default_factory=dict)

@dataclass(frozen=True)
class Result:
    ok: bool
    value: Any = None              # JSON friendly
    error: Error | None = None
    meta: dict = field(default_factory=dict)   # verified, snapshot_id, elapsed_ms, cost

def ok(value=None, **meta) -> Result: ...
def fail(code, message, retryable=False, **detail) -> Result: ...
```

The `ok` and `fail` helpers are the only way modules construct a Result. A write module's `meta` MUST contain `verified: bool`. A capture or measure module's `meta` MUST contain `snapshot_id` and `project_hash` when a project is involved.

## 3. The manifest

Every module has a `module.toml`. The registry, the tool generator, the skills reference generator, and the linter all read it.

```toml
[module]
name = "set_track_volume_verified"
layer = "L2"
summary = "Set a mixer track's volume, read it back, and report whether it took effect."
version = "1.0.0"

[io]
input = '''
{"type":"object","required":["track","value"],
 "properties":{"track":{"type":"integer","minimum":0},
               "value":{"type":"number","minimum":0,"maximum":1}}}
'''
output = '''
{"type":"object","properties":{"before":{"type":"number"},"after":{"type":"number"}}}
'''

[policy]
side_effect = "writes_fl_sandbox"
autonomy = "A2"
cost = "instant"                # instant | seconds | minutes | gpu
idempotent = true
verifier = "readback"           # readback | screenshot | measure | none

[deps]
min_api = 36
calls = ["op_mixer_get_track_volume", "op_mixer_set_track_volume"]
models = []
binaries = []
packages = []

[tests]
golden = "test_set_track_volume_verified.py::test_sets_and_reads_back"
failure = "test_set_track_volume_verified.py::test_ignored_write_reports_unverified"
```

Field rules:

1. `calls` lists every registry module this one invokes. The linter checks each exists in the same or a lower layer.
2. `min_api` is the minimum FL API level. The registry refuses to load the module if the probe-recorded API level is lower.
3. `cost` decides scheduling: `gpu` modules go through the scheduler.
4. `autonomy` is one of A0 to A3 per file 01.
5. `verifier` names how the module's effect is checked. A2 modules with `verifier = "none"` are rejected by the linter.

## 4. Side-effect classes and allowed imports

| Class | May import | MUST NOT import | Example |
| --- | --- | --- | --- |
| `pure` | `math`, `json`, `dataclasses`, `typing`, `re`, `numpy`, `scipy.signal` | `mido`, `rtmidi`, `subprocess`, `os`, `socket`, `pyautogui`, any file I/O | `encode_sysex`, `compare_note_sequences` |
| `reads_files` | pure set plus `pathlib` read-only use, `soundfile`, `librosa`, `pyloudnorm` | write modes, `subprocess`, MIDI, screen | `measure_integrated_loudness` |
| `writes_files` | `reads_files` set plus write-mode `pathlib` use | MIDI, screen | `write_report_file` |
| `reads_fl` | pure set plus `time` and the bridge client (via the registry call only) | file writes, screen | `list_tracks_summary` |
| `writes_fl_sandbox` | `reads_fl` set | file writes outside sandbox helper, screen | `set_track_volume_verified` |
| `gui` | screen and input libraries, screenshot libraries | MIDI bridge direct use | `load_plugin_gui` |

L1 ops run inside FL, so they are checked against a different rule set: only FL's own scripting modules are allowed, plus nothing else.

## 5. Linter rules

The linter, `tools/lint_modules.py`, reads each file's syntax tree and manifest. A module that fails any rule is not registered, so the orchestrator never sees it.

| Rule | Check |
| --- | --- |
| LM-001 | Exactly one public top-level function; its name equals the file stem |
| LM-002 | Name matches `^[a-z]+(_[a-z0-9]+)+$` and begins with an allowed verb (see section 6) |
| LM-003 | Function body at most the line budget; nesting depth at most the budget; parameter count at most the budget |
| LM-004 | All parameters and the return are annotated; return annotation is `Result` |
| LM-005 | Imports are a subset of the allowed list for the declared side-effect class |
| LM-006 | No bare `except:` and no `raise` that escapes the function body (errors become `fail(...)`) |
| LM-007 | No import of another module file; cross-module calls go through `registry.call("name", ...)` only |
| LM-008 | Every name passed to `registry.call` appears in `calls` in the manifest, and sits in the same or a lower layer |
| LM-009 | Manifest present and complete; schemas parse as JSON Schema; summary is one sentence |
| LM-010 | `module.toml` side-effect class, autonomy, and verifier are consistent (A2 requires a verifier other than `none`; `gui` requires `screenshot`) |
| LM-011 | Test file exists with the golden and failure tests named in the manifest; both exist and are collected by pytest |
| LM-012 | Write modules return `meta.verified`; the golden test asserts it |
| LM-013 | No hardcoded absolute paths; no network access unless the manifest declares it |
| LM-014 | No em dash in any docstring or summary |
| LM-015 | Docstring present, at most 6 lines: purpose, args, returns, errors |

A lint run produces a machine-readable report that the build loop feeds back to the local agent verbatim on a failure.

## 6. Naming

Allowed leading verbs, so the catalog sorts and the agent can guess names:

`get`, `set`, `list`, `find`, `ensure`, `measure`, `count`, `detect`, `estimate`, `compare`, `extract`, `transpose`, `quantize`, `clean`, `encode`, `decode`, `split`, `join`, `build`, `parse`, `match`, `wait`, `send`, `apply`, `create`, `solo`, `snapshot`, `rollback`, `diff`, `restore`, `prepare`, `write`, `read`, `import`, `load`, `unload`, `separate`, `transcribe`, `generate`, `repaint`, `critique`, `ground`, `check`, `render`, `export`, `open`, `save`, `arm`, `run`, `take`, `click`, `type`, `press`, `drag`, `locate`, `screenshot`, `halt`, `align`, `stage`, `setup`, `restore`, `op`.

L1 ops are named `op_<fl_module>_<function>` and are exempt from the verb list.

Suffix `_verified` marks an L2 wrapper that reads back. Suffix `_gui` marks a GUI recipe.

## 7. Layers and the allowed call direction

```
L6  GUI primitives and recipes      may call L0 to L5 where listed in calls
L5  Model adapters                  may call L4 and below
L4  Audio and note measures         may call L4 and below (pure/files only)
L3  Recipes                         may call L2 and below
L2  Verified wrappers               may call L1 and L0
L1  FL ops (inside FL)              call FL's own API only
L0  Transport                       call nothing in the registry
```

An orchestrator-level planner MAY call any layer. A module MUST NOT call upward.

## 8. Registration and exposure

1. The registry loader walks `modules/`, runs the linter, and loads each passing module. Failing modules are listed in `catalog/rejected.md` with their rule ids.
2. The tool exposure step generates one MCP tool per module that has `expose = true` (default true for L2 to L6; L0 and L1 are internal). A module MAY set `expose = false` in its manifest.
3. A tool's description is the manifest summary plus the input schema. Descriptions are short on purpose, so small context windows are not flooded.
4. Tools are grouped into server slices and phase slices. The agent sees only the slice for the current phase (file 07, section 4).

## 9. Generated artifacts

| Artifact | Generator | From | Used by |
| --- | --- | --- | --- |
| `fl_side/device_coproducer.py` | `gen_fl_side.py` | L1 op source files and the protocol constants | Installed in FL |
| L1 op files, manifests, tests | `gen_l1.py` | Official function tables plus the API inventory probe output | The registry |
| `catalog/L*.md` | `gen_catalog.py` | Manifests | Skills references, human reading |
| MCP tool definitions | `tools.py` | Manifests | The servers |
| `catalog/rejected.md` | Registry loader | Lint reports | Human debugging |

The generator `gen_l1.py` works from the function tables on the official reference pages. For each function it emits the op, a manifest, and a golden test against the fake FL. Local agents only write what the generator cannot: toggle functions, functions needing flags the manual leaves unexplained, and anything the inventory probe finds that the manual does not list.

Every generated file carries a header naming its generator and the input hash, so a stale file is detectable.

## 10. Versioning and change control

1. Each module has a semantic version in its manifest. A change to an input or output schema is a major version change and requires regenerating dependent skills references.
2. Tool schemas exposed by servers are frozen at Gate 0 and changes after that go through a change note in the decision log.
3. The registry records the content hash of each loaded module in the ledger at run start, so a run can be reproduced.

## 11. Why this is cheap for local agents

1. The agent never needs to see the whole system. A task card carries exactly what the module needs (file 06).
2. The gate is mechanical: lint, tests, size. Retries are driven by exact error text, which small models handle better than vague review.
3. The largest layer is generated, so most modules cost no model tokens.
4. A failing module affects only itself. It is not registered, and the orchestrator works with what passed.
