"""Build src/coproducer/data/api_inventory.json from the installed FL API stubs.

One job: read stub source files (AST only, nothing imported) and write name, signature and since-version
for every public function. Run: python tools/gen_inventory.py
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

MODULES = ("transport", "mixer", "channels", "patterns", "plugins", "playlist",
           "arrangement", "general", "ui", "device", "midi", "screenshot")
SINCE = re.compile(r"[Ii]ncluded since API [Vv]ersion (\d+)")


# Functions the live FL Studio 2026 build (26.1.7, API 45) has that the published stubs lack.
# Shapes come from probe reports (arity from TypeError text, behaviour from readback), not from documentation.
# Parameter names are ours; the real functions take these positionally.
OBSERVED_SINCE = 45
OBSERVED = {
    "mixer.setCurrentTempo": ([("tempo", "int")], "None"),  # milli-BPM: 128000 is 128 BPM
    "patterns.setPatternLength": ([("index", "int"), ("length", "int")], "None"),
    "patterns.incrementPatternLength": ([("index", "int"), ("delta", "int")], "None"),
    "patterns.clearPattern": ([("index", "int")], "None"),
    "channels.getSwing": ([], "float"),
    # per-slot effect state on a mixer track; arity from TypeError text (get takes exactly 2, set takes at most 3 and 4)
    "mixer.getPluginMuteState": ([("index", "int"), ("slotIndex", "int")], "int"),
    "mixer.getPluginMixLevel": ([("index", "int"), ("slotIndex", "int")], "float"),
    "mixer.setPluginMuteState": ([("index", "int"), ("slotIndex", "int"), ("value", "int")], "None"),
    "mixer.setPluginMixLevel": ([("index", "int"), ("slotIndex", "int"), ("value", "float")], "None"),
    "channels.setSwing": ([("value", "float")], "None"),
}


# Stub signatures the live build contradicts. Each entry names parameters to drop; the evidence is the TypeError text.
CORRECTIONS = {
    # live: "function takes at most 4 arguments (5 given)"; the stub lists pickupMode, the build does not take it
    "plugins.getParamValueString": ("pickupMode",),
}


def apply_observed(inv: dict) -> dict:
    for full, drop in CORRECTIONS.items():
        if full in inv:
            inv[full]["params"] = [q for q in inv[full]["params"] if q["name"] not in drop]
            inv[full]["corrected"] = True
    for full, (params, ret) in OBSERVED.items():
        inv[full] = {"since": OBSERVED_SINCE, "observed": True, "file": "probe_report",
                     "params": [{"name": n, "type": t, "default": None} for n, t in params], "returns": ret}
    return inv


def stub_root() -> Path:
    import importlib.util
    spec = importlib.util.find_spec("mixer")
    if spec is None or not spec.submodule_search_locations:
        raise SystemExit("fl-studio-api-stubs is not installed")
    return Path(list(spec.submodule_search_locations)[0]).parent


def params_of(fn: ast.FunctionDef) -> list[dict]:
    a = fn.args
    pos = a.posonlyargs + a.args
    defaults = [None] * (len(pos) - len(a.defaults)) + list(a.defaults)
    out = []
    for arg, d in zip(pos, defaults):
        out.append({"name": arg.arg,
                    "type": ast.unparse(arg.annotation) if arg.annotation else "",
                    "default": ast.unparse(d) if d is not None else None})
    return out


def scan(root: Path) -> dict:
    inv: dict[str, dict] = {}
    for mod in MODULES:
        d = root / mod
        if not d.is_dir():
            continue
        for py in sorted(d.glob("*.py")):
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    doc = ast.get_docstring(node) or ""
                    m = SINCE.search(doc)
                    inv[f"{mod}.{node.name}"] = {
                        "since": int(m.group(1)) if m else 1,
                        "params": params_of(node),
                        "returns": ast.unparse(node.returns) if node.returns else "",
                        "file": py.name,
                    }
    return inv


def main() -> int:
    inv = apply_observed(scan(stub_root()))
    out = Path(__file__).resolve().parent.parent / "src" / "coproducer" / "data" / "api_inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inv, indent=1, sort_keys=True), encoding="utf-8")
    (out.parent / "__init__.py").touch()
    print(f"{len(inv)} functions -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
