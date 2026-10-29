"""Load and check module.toml manifests."""
from __future__ import annotations

import json
from pathlib import Path

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

LAYERS = ("L0", "L1", "L2", "L3", "L4", "L5", "L6")
SIDE_EFFECTS = ("pure", "reads_fl", "writes_fl_sandbox", "reads_files", "writes_files", "system", "gui")
AUTONOMY = ("A0", "A1", "A2", "A3")
COSTS = ("instant", "seconds", "minutes", "gpu")
VERIFIERS = ("readback", "screenshot", "measure", "none")

REQUIRED = {
    "module": ("name", "layer", "summary", "version"),
    "io": ("input", "output"),
    "policy": ("side_effect", "autonomy", "cost", "idempotent", "verifier"),
    "deps": ("min_api", "calls", "models", "binaries", "packages"),
    "tests": ("golden", "failure"),
}


def load_manifest(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def manifest_problems(m: dict) -> list[str]:
    """Return a list of human-readable problems; empty means the manifest is complete."""
    out: list[str] = []
    for section, keys in REQUIRED.items():
        sec = m.get(section)
        if not isinstance(sec, dict):
            out.append(f"missing section [{section}]")
            continue
        for k in keys:
            if k not in sec:
                out.append(f"missing key {section}.{k}")
    if out:
        return out
    mod, io, pol = m["module"], m["io"], m["policy"]
    if mod["layer"] not in LAYERS:
        out.append(f"layer {mod['layer']!r} not in {LAYERS}")
    summary = mod["summary"]
    if "\n" in summary or not summary.strip().endswith("."):
        out.append("summary must be one sentence on one line ending with a period")
    for key in ("input", "output"):
        try:
            json.loads(io[key])
        except Exception as e:  # noqa: BLE001
            out.append(f"io.{key} is not valid JSON: {e}")
    if pol["side_effect"] not in SIDE_EFFECTS:
        out.append(f"side_effect {pol['side_effect']!r} unknown")
    if pol["autonomy"] not in AUTONOMY:
        out.append(f"autonomy {pol['autonomy']!r} unknown")
    if pol["cost"] not in COSTS:
        out.append(f"cost {pol['cost']!r} unknown")
    if pol["verifier"] not in VERIFIERS:
        out.append(f"verifier {pol['verifier']!r} unknown")
    return out
