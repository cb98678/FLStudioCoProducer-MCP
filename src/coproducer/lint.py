"""Module linter: rules LM-001 to LM-015 from the plan (file 04).

A module that fails any rule is not registered. The linter reads the file's syntax
tree and its manifest; it never imports the module.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from .manifest import LAYERS, load_manifest, manifest_problems

DEFAULT_BUDGET = {"lines": 40, "depth": 3, "params": 6}
HARD_BUDGET = {"lines": 60, "depth": 4, "params": 8}

VERBS = {
    "get", "set", "list", "find", "ensure", "measure", "count", "detect", "estimate", "compare",
    "extract", "transpose", "quantize", "clean", "encode", "decode", "split", "join", "build",
    "parse", "match", "wait", "send", "apply", "create", "solo", "snapshot", "rollback", "diff",
    "restore", "prepare", "write", "read", "import", "load", "unload", "separate", "transcribe",
    "generate", "repaint", "critique", "ground", "check", "render", "export", "open", "save",
    "arm", "run", "take", "click", "type", "press", "drag", "locate", "screenshot", "halt",
    "align", "call", "copy", "stage", "setup", "mute", "route", "select", "clear", "add", "remove", "dismiss", "ping", "undo",
}

_BASE = ["__future__", "typing", "dataclasses", "math", "json", "re", "coproducer.call", "coproducer.result", "coproducer.dsp"]
_PURE = _BASE + ["numpy", "scipy.signal", "itertools", "functools", "collections", "statistics", "bisect", "coproducer.beatgrid", "coproducer.melody", "coproducer.tonal"]
_FILES_R = _PURE + ["pathlib", "soundfile", "pyloudnorm", "hashlib", "scipy.fft", "scipy.stats", "mido", "coproducer.services", "tomllib", "coproducer.datafiles", "coproducer.flpfile", "coproducer.automation", "coproducer.vocalchops", "coproducer.cutrefine", "coproducer.projdiff", "coproducer.parttiming", "coproducer.remixbuild", "coproducer.songplan", "coproducer.partmix", "coproducer.songanalysis", "coproducer.flporg", "coproducer.projorg", "coproducer.anatomy", "coproducer.fxlib", "coproducer.pump", "coproducer.transitions", "coproducer.layers", "coproducer.drumtune", "coproducer.fxsynth", "coproducer.sectiongain", "coproducer.mixroute", "coproducer.fxchains", "coproducer.production", "coproducer.midiref", "coproducer.songform", "coproducer.soundbrief", "coproducer.variety", "coproducer.loopsets", "coproducer.wavetables", "coproducer.serumspec", "coproducer.newtimeview"]
_FILES_W = _FILES_R + ["subprocess", "time", "shutil", "tempfile", "coproducer.services", "coproducer.pianoroll_template", "coproducer.remixaudio", "coproducer.stylepack", "coproducer.mastering"]
_FL = _PURE + ["time"]
ALLOWED_IMPORTS = {
    "pure": _PURE,
    "reads_files": _FILES_R,
    "writes_files": _FILES_W,
    "reads_fl": _FL,
    "writes_fl_sandbox": _FL,
    "system": _PURE + ["mido", "rtmidi", "platform", "time", "pathlib", "coproducer.services", "urllib.request", "urllib.error", "subprocess", "shlex", "coproducer.renderwatch",
               "shutil", "coproducer.intake", "coproducer.panel", "coproducer.stylepack", "json", "coproducer.flpfile", "coproducer.serumstate", "coproducer.soundbrief"],
    "gui": _PURE + ["time", "mss", "PIL", "pyautogui", "ctypes", "pathlib", "coproducer.services", "coproducer.newtimeview", "coproducer.knobread"],
}
FL_MODULES = ["__future__", "typing", "mixer", "channels", "patterns", "plugins", "playlist",
              "arrangement", "transport", "general", "ui", "device", "midi", "launchMapPages", "screen"]

_ABS_PATH = re.compile(r"^([A-Za-z]:[\\/]|/(usr|home|etc|tmp|var|opt|mnt|root)/)")
_NAME = re.compile(r"^[a-z]+(_[a-z0-9]+)+$")


@dataclass(frozen=True)
class Violation:
    rule: str
    message: str
    line: int = 0

    def __str__(self) -> str:
        return f"{self.rule} line {self.line}: {self.message}"


def _imports(tree: ast.AST) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out += [(a.name, n.lineno) for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            for a in n.names:
                out.append((f"{mod}.{a.name}" if mod else a.name, n.lineno))
            if not n.names:
                out.append((mod, n.lineno))
    return out


def _import_ok(full: str, allowed: list[str]) -> bool:
    return any(full == a or full.startswith(a + ".") for a in allowed)


def _depth(node: ast.AST, cur: int = 0) -> int:
    best = cur
    for ch in ast.iter_child_nodes(node):
        nxt = cur + 1 if isinstance(ch, (ast.If, ast.For, ast.While, ast.Try, ast.With)) else cur
        best = max(best, _depth(ch, nxt))
    return best


def _public_funcs(tree: ast.Module) -> list[ast.FunctionDef]:
    return [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not n.name.startswith("_")]


def _calls(tree: ast.AST) -> list[tuple[ast.Call, str | None]]:
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            is_call = (isinstance(f, ast.Name) and f.id == "call") or \
                      (isinstance(f, ast.Attribute) and f.attr == "call")
            if is_call:
                a0 = n.args[0] if n.args else None
                out.append((n, a0.value if isinstance(a0, ast.Constant) and isinstance(a0.value, str) else None))
    return out


def lint_module(mod_dir: Path, known: dict[str, str] | None = None) -> list[Violation]:
    """Lint one module directory. `known` maps module name to layer for call checks."""
    v: list[Violation] = []
    mpath = mod_dir / "module.toml"
    if not mpath.exists():
        return [Violation("LM-009", "module.toml missing")]
    try:
        m = load_manifest(mpath)
    except Exception as e:  # noqa: BLE001
        return [Violation("LM-009", f"module.toml unreadable: {e}")]
    probs = manifest_problems(m)
    if probs:
        return [Violation("LM-009", p) for p in probs]
    name, layer = m["module"]["name"], m["module"]["layer"]
    pol, deps = m["policy"], m["deps"]
    src_path = mod_dir / f"{name}.py"
    if not src_path.exists():
        return [Violation("LM-001", f"{name}.py not found next to module.toml")]
    src = src_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [Violation("LM-001", f"syntax error: {e}", e.lineno or 0)]

    # LM-001 / LM-002
    pubs = _public_funcs(tree)
    if len(pubs) != 1:
        v.append(Violation("LM-001", f"expected exactly one public function, found {len(pubs)}"))
        return v
    fn = pubs[0]
    if fn.name != name or mod_dir.name != name:
        v.append(Violation("LM-001", f"function {fn.name!r}, file {name!r}, dir {mod_dir.name!r} must all match"))
    if layer == "L1":
        if not fn.name.startswith("op_"):
            v.append(Violation("LM-002", "L1 names must start with op_"))
    else:
        if not _NAME.match(fn.name) or fn.name.split("_")[0] not in VERBS:
            v.append(Violation("LM-002", f"{fn.name!r} must be verb_noun with an allowed verb"))

    # LM-003 size budget
    budget = dict(DEFAULT_BUDGET)
    for k, val in (m.get("budget") or {}).items():
        if k in budget and isinstance(val, int):
            budget[k] = min(max(val, 1), HARD_BUDGET[k])
    body = fn.body
    has_doc = bool(body) and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
        and isinstance(body[0].value.value, str)
    first = body[1].lineno if has_doc and len(body) > 1 else body[0].lineno
    nlines = (fn.end_lineno or first) - first + 1
    if nlines > budget["lines"]:
        v.append(Violation("LM-003", f"body is {nlines} lines, budget {budget['lines']}", fn.lineno))
    d = _depth(fn)
    if d > budget["depth"]:
        v.append(Violation("LM-003", f"nesting depth {d}, budget {budget['depth']}", fn.lineno))
    nparams = len(fn.args.args) + len(fn.args.kwonlyargs)
    if nparams > budget["params"]:
        v.append(Violation("LM-003", f"{nparams} parameters, budget {budget['params']}", fn.lineno))

    # LM-004 annotations
    for a in fn.args.args + fn.args.kwonlyargs:
        if a.annotation is None:
            v.append(Violation("LM-004", f"parameter {a.arg!r} lacks an annotation", fn.lineno))
    want = "dict" if layer == "L1" else "Result"
    ret = ast.unparse(fn.returns) if fn.returns is not None else ""
    if ret != want:
        v.append(Violation("LM-004", f"return annotation must be {want}, found {ret or 'none'}", fn.lineno))

    # LM-005 imports
    allowed = FL_MODULES if layer == "L1" else ALLOWED_IMPORTS.get(pol["side_effect"], _PURE)
    if layer == "L1":
        pass
    for full, line in _imports(tree):
        if not _import_ok(full, allowed):
            v.append(Violation("LM-005", f"import {full!r} not allowed for {pol['side_effect']}/{layer}", line))

    # LM-006 no raise, no bare except
    for n in ast.walk(tree):
        if isinstance(n, ast.Raise):
            v.append(Violation("LM-006", "raise is not allowed; return fail(...)", n.lineno))
        if isinstance(n, ast.ExceptHandler) and n.type is None:
            v.append(Violation("LM-006", "bare except is not allowed", n.lineno))

    # LM-007 / LM-008 composition through the registry only
    declared = list(deps["calls"])
    for node, lit in _calls(tree):
        if lit is None:
            v.append(Violation("LM-008", "call() needs a string-literal module name", node.lineno))
            continue
        if lit not in declared:
            v.append(Violation("LM-008", f"call({lit!r}) not listed in deps.calls", node.lineno))
        elif known is not None:
            if lit not in known:
                v.append(Violation("LM-008", f"call({lit!r}) names an unknown module", node.lineno))
            elif LAYERS.index(known[lit]) > LAYERS.index(layer):
                v.append(Violation("LM-007", f"call({lit!r}) goes up from {layer} to {known[lit]}", node.lineno))

    # LM-010 consistency
    if pol["autonomy"] == "A2" and pol["verifier"] == "none" and pol["side_effect"] != "pure" and layer != "L1" \
            and pol["side_effect"] not in ("reads_files", "reads_fl", "system"):
        v.append(Violation("LM-010", "A2 modules that change state need a verifier other than none"))
    if pol["side_effect"] == "gui" and pol["autonomy"] != "A0" and pol["verifier"] != "screenshot":
        v.append(Violation("LM-010", "gui modules that send input require verifier = screenshot"))

    # LM-011 tests present
    tpath = mod_dir / f"test_{name}.py"
    tsrc = tpath.read_text(encoding="utf-8") if tpath.exists() else ""
    if not tpath.exists():
        v.append(Violation("LM-011", f"test_{name}.py missing"))
    else:
        tnames = {n.name for n in ast.walk(ast.parse(tsrc)) if isinstance(n, ast.FunctionDef)}
        for key in ("golden", "failure"):
            ref = m["tests"][key].split("::")[-1]
            if ref not in tnames:
                v.append(Violation("LM-011", f"tests.{key} names {ref!r} which is not defined in the test file"))

    # LM-012 write modules report verified
    if pol["side_effect"] == "writes_fl_sandbox" and layer != "L1":
        if "verified" not in src:
            v.append(Violation("LM-012", "write module must set meta.verified"))
        if tsrc and "verified" not in tsrc:
            v.append(Violation("LM-012", "golden test must assert verified"))

    # LM-013 no absolute paths
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and _ABS_PATH.match(n.value):
            v.append(Violation("LM-013", f"hardcoded absolute path {n.value!r}", n.lineno))

    # LM-014 no em dash anywhere in the module or manifest text
    for label, text in (("module", src), ("manifest", mpath.read_text(encoding="utf-8"))):
        if "—" in text:
            v.append(Violation("LM-014", f"em dash in {label}"))

    # LM-015 docstring
    doc = ast.get_docstring(fn)
    if not doc:
        v.append(Violation("LM-015", "function needs a docstring", fn.lineno))
    elif len(doc.strip().splitlines()) > 6:
        v.append(Violation("LM-015", "docstring longer than 6 lines", fn.lineno))
    return v


def lint_tree(root: Path) -> dict[str, list[Violation]]:
    """Lint every module under root. Returns {module_name: violations} for failing modules only."""
    dirs = sorted(p.parent for p in root.rglob("module.toml"))
    known: dict[str, str] = {}
    for d in dirs:
        try:
            mm = load_manifest(d / "module.toml")
            known[mm["module"]["name"]] = mm["module"]["layer"]
        except Exception:  # noqa: BLE001
            continue
    bad: dict[str, list[Violation]] = {}
    for d in dirs:
        vs = lint_module(d, known)
        if vs:
            bad[d.name] = vs
    return bad
