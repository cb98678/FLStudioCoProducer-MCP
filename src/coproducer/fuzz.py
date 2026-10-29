"""Registry-wide fuzzing: throw hostile arguments at every module and record how it holds up.

A module is judged on what the registry hands back, never on what the module promises:
  defect   a call raised past the registry, hung, came back as E_INTERNAL (the module raised or returned a non-Result), returned an
           error code that is not in ERROR_CODES, accepted an argument of the wrong type, or created a file outside the sandbox.
  fragile  a result that is not strict JSON (NaN or Infinity), a result over 1 MB, or a call slower than SLOW_S seconds.
Everything runs against the fake FL, fake desktop and fake processes, inside a throwaway folder, so it is safe on any machine.
"""
from __future__ import annotations

import json
import math
import os
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .result import ERROR_CODES, Result

TIMEOUT_S = 15.0
SLOW_S = 3.0
BIG_RESULT = 1_000_000
SEED = 20261021

STRINGS = ["", " ", "a", "A" * 300, "A" * 50_000, "\x00", "a\x00b", "../../escape.txt", "..\\..\\escape.txt", "C:\\Windows\\System32\\x",
           "CON", "NUL", "aux.txt", "con:", "trailing. ", "\\\\?\\C:\\x", "\\\\server\\share\\x", "日本語のパス🎹.wav", "\u202eevil.wav", "\ud83d",
           "%s%d{0}{}", "{x}", "'; DROP TABLE x;--", "\n\r\t", "\u0301" * 50, "é" * 200, "~", "~/x", "$HOME", "%USERPROFILE%", "a/b/c/d/" * 40,
           "http://127.0.0.1:9/x", "file:///etc/passwd", "-rf", "--help", "null", "NaN", "0", "-1", "1e999"]
INTS = [0, 1, -1, 2, 127, 128, 255, 256, 65535, 65536, 2 ** 31 - 1, 2 ** 31, -2 ** 31, 2 ** 53, 2 ** 63 - 1, 2 ** 63, 2 ** 64, 10 ** 30, -10 ** 30, 1.0]
NUMS = [0.0, -0.0, 0.5, -0.5, 1.0, 1e-320, 5e-324, 1e308, -1e308, float("nan"), float("inf"), float("-inf"), 2 ** 63, 0.1 + 0.2, 1e15, 123456789.123456789]
BOOLS = [True, False]
WRONG = [None, "x", "1", 1.5, 7, True, [], {}, [1], {"a": 1}]
WINDOWS_ONLY = ("CON", "NUL", "aux.txt", "con:", "\\\\?\\C:\\x", "\\\\server\\share\\x")


@dataclass
class Case:
    label: str
    args: dict
    expect_arg_error: bool = False


@dataclass
class Outcome:
    module: str
    label: str
    status: str = "ok"                  # ok | refused | defect | fragile
    code: str = ""
    note: str = ""
    seconds: float = 0.0
    args_text: str = ""


@dataclass
class World:
    reg: Any
    root: Path
    fake: Any = None
    handles: list = field(default_factory=list)


def _types(schema: dict) -> list:
    t = schema.get("type")
    return [t] if isinstance(t, str) else list(t or [])


def base_value(schema: dict, name: str = "", paths: dict | None = None) -> Any:
    """A plausible valid value for a schema, so a case can vary one argument while the rest are sensible."""
    paths = paths or {}
    if "enum" in schema:
        return schema["enum"][0]
    types = [t for t in _types(schema) if t != "null"] or ["string"]
    t = types[0]
    lo, hi = schema.get("minimum"), schema.get("maximum")
    if schema.get("exclusiveMinimum") is not None:
        lo = schema["exclusiveMinimum"] + (1 if t == "integer" else 0.5)
    if t == "integer":
        v = 0 if lo is None else int(math.ceil(lo))
        return min(v, int(hi)) if hi is not None else v
    if t == "number":
        v = 0.5 if lo is None else float(lo)
        return min(v, float(hi)) if hi is not None else v
    if t == "boolean":
        return False
    if t == "string":
        for key, val in paths.items():
            if name == key or name.endswith("_" + key):
                return val
        return "x" * max(1, schema.get("minLength", 0))
    if t == "array":
        item = schema.get("items", {})
        return [base_value(item, name, paths) for _ in range(schema.get("minItems", 0))]
    return {}


def weird_values(schema: dict, name: str = "", paths: dict | None = None) -> list:
    """Values of the right type chosen to hurt: boundaries, extremes, hostile text, nesting."""
    types = [t for t in _types(schema) if t != "null"] or ["string"]
    out: list = []
    for t in types:
        if t == "integer":
            out += INTS
            for k in ("minimum", "maximum"):
                if k in schema:
                    out += [int(schema[k]), int(schema[k]) - 1, int(schema[k]) + 1]
        elif t == "number":
            out += NUMS
            for k in ("minimum", "maximum"):
                if k in schema:
                    out += [float(schema[k]), float(schema[k]) - 1e-9, float(schema[k]) + 1e-9]
        elif t == "boolean":
            out += BOOLS
        elif t == "string":
            out += STRINGS
            out += [(paths or {}).get("outside", "/nonexistent/outside")] if "path" in name or name.endswith("dir") else []
        elif t == "array":
            item = base_value(schema.get("items", {}), name, paths)
            deep: Any = []
            for _ in range(60):
                deep = [deep]
            out += [[], [None], [item] * 1000, deep, [item, item], [[]], [{}], list(range(300))]
        elif t == "object":
            out += [{}, {"a": {"b": {"c": {}}}}, {"__proto__": 1}, {"": ""}, {str(i): i for i in range(500)}, {"a" * 2000: 1}, {"\x00": "\x00"}]
    if "null" in _types(schema):
        out.append(None)
    if "timeout" in name or name.endswith("_wait_s"):      # a call that waits as long as it is told is not hanging; keep the waits short
        out = [v for v in out if not (isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and v > 5)]
    seen, uniq = [], []
    for v in out:
        key = repr(v)[:200]
        if key not in seen:
            seen.append(key)
            uniq.append(v)
    return uniq


def _valid_type(value: Any, schema: dict) -> bool:
    from jsonschema import Draft202012Validator
    return Draft202012Validator({"type": schema.get("type")} if "type" in schema else {}).is_valid(value)


def cases_for(schema: dict, rng: random.Random, paths: dict | None = None, chaos: int = 25) -> list:
    """Every case for one module: the sensible call, each argument made weird in turn, each made the wrong type, each left out, chaos."""
    props = schema.get("properties") or {}
    required = list(schema.get("required") or [])
    base = {k: base_value(props.get(k, {}), k, paths) for k in required}
    out = [Case("baseline", dict(base)), Case("every argument present", {k: base_value(v, k, paths) for k, v in props.items()})]
    for k, s in props.items():
        for w in weird_values(s, k, paths):
            out.append(Case("%s=%s" % (k, repr(w)[:60]), {**base, k: w}))
        for w in WRONG:
            if not _valid_type(w, s) and "enum" not in s:
                out.append(Case("%s wrong type %s" % (k, repr(w)[:30]), {**base, k: w}, expect_arg_error=True))
    for k in required:
        out.append(Case("missing %s" % k, {a: v for a, v in base.items() if a != k}, expect_arg_error=True))
    if schema.get("additionalProperties") is False:
        out.append(Case("unknown argument", {**base, "zzz_unknown": 1}, expect_arg_error=True))
    pools = {k: weird_values(s, k, paths) or [None] for k, s in props.items()}
    for _ in range(chaos if props else 0):
        out.append(Case("chaos", {k: rng.choice(pool) for k, pool in pools.items() if k in required or rng.random() < 0.6}))
    return out


def _call_with_timeout(reg, name: str, args: dict, timeout: float):
    box: dict = {}

    def go() -> None:
        try:
            box["res"] = reg.call(name, **args)
        except BaseException as e:  # noqa: BLE001 - the whole point is to catch what escapes the registry
            box["exc"] = e

    th = threading.Thread(target=go, daemon=True)
    t0 = time.perf_counter()
    th.start()
    th.join(timeout)
    return box, th.is_alive(), time.perf_counter() - t0


def judge(module: str, case: Case, box: dict, hung: bool, seconds: float, strict_json: bool = True) -> Outcome:
    o = Outcome(module, case.label, seconds=round(seconds, 3), args_text=repr(case.args)[:300])
    if hung:
        return _mark(o, "defect", "HANG", "no answer in %.0f s" % TIMEOUT_S)
    if "exc" in box:
        e = box["exc"]
        return _mark(o, "defect", "ESCAPED", "%s: %s" % (type(e).__name__, str(e)[:200]))
    res = box["res"]
    if not isinstance(res, Result):
        return _mark(o, "defect", "NOT_A_RESULT", type(res).__name__)
    if not res.ok:
        o.code = res.error.code
        if res.error.code not in ERROR_CODES:
            return _mark(o, "defect", res.error.code, "error code is not in ERROR_CODES")
        if res.error.code == "E_INTERNAL":
            return _mark(o, "defect", "E_INTERNAL", res.error.message[:200])
        o.status = "refused"
    if case.expect_arg_error and (res.ok or res.error.code != "E_ARG"):
        return _mark(o, "defect", "ARG_ACCEPTED", "a wrong-typed or missing argument was not refused with E_ARG (got %s)" % (res.error.code if not res.ok else "ok"))
    if not strict_json:                 # internal modules may hand back arrays; only what a client can see must be strict JSON
        return o
    try:
        text = json.dumps(res.to_dict(), allow_nan=False)
    except (ValueError, TypeError) as e:
        return _mark(o, "fragile", "NOT_STRICT_JSON", str(e)[:150])
    if len(text) > BIG_RESULT:
        return _mark(o, "fragile", "HUGE_RESULT", "%d bytes" % len(text))
    if seconds > SLOW_S:
        return _mark(o, "fragile", "SLOW", "%.1f s" % seconds)
    return o


def _mark(o: Outcome, status: str, code: str, note: str) -> Outcome:
    o.status, o.code, o.note = status, o.code if o.code and status == "fragile" else code, note
    return o


# ------------------------------------------------------------------------------------------------ the fake world
def build_world(root: Path, fully: bool = True) -> World:
    """A registry wired to a fake FL over the real bridge. fully=False leaves every service unset (the unconfigured machine)."""
    from .bridge import BridgeClient
    from .fakefl import FakeFL
    from .loopback import LoopbackTransport, load_device_script
    from .registry import Registry
    from .services import clear_services, set_service
    from . import testrig

    root = Path(root)
    for d in ("sandbox", "scripts", "cwd", "canary"):
        (root / d).mkdir(parents=True, exist_ok=True)
    clear_services()
    modules = Path(os.environ.get("COPRODUCER_MODULES") or testrig.MODULES)
    reg = Registry(modules, ceiling="A2", approver=lambda n, a: True).load()
    fake = FakeFL()
    script = load_device_script(fake)
    BridgeClient(reg, LoopbackTransport(fake, script)).attach(reg)
    reg.activate()
    w = World(reg, root, fake)
    if fully:
        w.handles += [testrig.build_desk(root / "sandbox"), testrig.build_ml()]
        from .fakeprocs import FakeProcs
        set_service("procs", FakeProcs())
        set_service("fl_exe", str(root / "canary" / "no_such_fl.exe"))
        set_service("piano_roll_scripts_dir", str(root / "scripts"))
        set_service("llm", {"endpoint": "http://127.0.0.1:9/v1", "model": "none", "timeout_s": 1})
        set_service("sandbox_root", str(root / "sandbox"))
        import wave
        with wave.open(str(root / "sandbox" / "tone.wav"), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            f.writeframes(b"\x00\x10" * 4410)
        (root / "sandbox" / "song.flp").write_bytes(b"FLhd" + b"\x00" * 64)
    return w


def close_world(w: World) -> None:
    from .services import clear_services
    try:
        w.fake.uninstall()
    finally:
        for h in w.handles:
            getattr(getattr(h, "sched", None), "unload_all", lambda: None)()
        clear_services()


def tree(root: Path, skip: tuple) -> set:
    out = set()
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if str(Path(dp, d).relative_to(root)) not in skip]
        out.update(str(Path(dp, f).relative_to(root)) for f in fn)
    return out


def fuzz_module(w: World, name: str, rng: random.Random | None = None, timeout: float = TIMEOUT_S, chaos: int = 25) -> list:
    """Every case against one module. Also reports any file created outside sandbox/ and scripts/."""
    global TIMEOUT_S
    rng = rng or random.Random(SEED)
    root = w.root
    paths = {"path": str(root / "sandbox" / "tone.wav"), "project": str(root / "sandbox" / "song.flp"), "out_dir": str(root / "sandbox" / "out"),
             "outside": str(root / "canary" / "outside")}
    paths.update({"src_path": paths["path"], "image_path": paths["path"], "input_path": paths["path"], "a_path": paths["path"],
                  "b_path": paths["path"], "path_a": paths["path"], "path_b": paths["path"], "result_path": paths["path"]})
    before = tree(root, ("sandbox", "scripts"))
    old, TIMEOUT_S = TIMEOUT_S, timeout
    outs = []
    try:
        for case in cases_for(w.reg.modules[name].input_schema, rng, paths, chaos):
            box, hung, secs = _call_with_timeout(w.reg, name, case.args, timeout)
            outs.append(judge(name, case, box, hung, secs, w.reg.modules[name].expose))
    finally:
        TIMEOUT_S = old
    made = sorted(tree(root, ("sandbox", "scripts")) - before)
    if made:
        outs.append(Outcome(name, "files outside the sandbox", "defect", "WROTE_OUTSIDE_SANDBOX", ", ".join(made)[:300]))
    return outs


def summarize(outcomes: list) -> dict:
    by_mod: dict = {}
    for o in outcomes:
        m = by_mod.setdefault(o.module, {"calls": 0, "ok": 0, "refused": 0, "defect": 0, "fragile": 0, "examples": []})
        m["calls"] += 1
        m[o.status] += 1
        if o.status in ("defect", "fragile") and len(m["examples"]) < 3:
            m["examples"].append({"status": o.status, "code": o.code, "case": o.label, "note": o.note, "args": o.args_text})
    return by_mod
