"""coproducer doctor: one function per check, each returns {name, status: ok|warn|fail, detail, fix}."""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

from ..config import load_config
from ..lint import lint_tree
from . import detect


def _row(name: str, status: str, detail: str = "", fix: str = "") -> dict:
    return {"name": name, "status": status, "detail": detail, "fix": fix}


def check_python() -> dict:
    ok = sys.version_info >= (3, 11)
    return _row("python", "ok" if ok else "fail", sys.version.split()[0], "" if ok else "use Python 3.11 or newer for the host")


def check_packages() -> list:
    out = []
    for mod, required in (("numpy", 1), ("scipy", 1), ("soundfile", 1), ("pyloudnorm", 1), ("mido", 1), ("jsonschema", 1), ("mcp", 1), ("rtmidi", 0), ("mss", 0), ("PIL", 0), ("pyautogui", 0)):
        try:
            importlib.import_module(mod)
            out.append(_row("package " + mod, "ok"))
        except ImportError:
            out.append(_row("package " + mod, "fail" if required else "warn", "missing", "coproducer install-host  (or pip install -e .[midi,gui])"))
    return out


def check_modules(home: Path) -> dict:
    problems = lint_tree(home / "modules")
    return _row("module lint", "ok" if not problems else "fail", "%d module(s) with problems" % len(problems), "coproducer lint")


def check_fl_side(home: Path, data_dir: Path) -> dict:
    src, dst = home / "fl_side" / "device_coproducer.py", detect.hardware_dir(data_dir) / "device_coproducer.py"
    if not src.is_file():
        return _row("FL-side script", "fail", "not generated", "coproducer gen")
    try:
        ast.parse(src.read_text(encoding="utf-8"), feature_version=(3, 9))
    except SyntaxError as e:
        return _row("FL-side script", "fail", "does not parse as Python 3.9: %s" % e, "coproducer gen")
    if not dst.is_file():
        return _row("FL-side script installed", "warn", "not in FL's Hardware folder", "coproducer setup")
    same = dst.read_bytes() == src.read_bytes()
    return _row("FL-side script installed", "ok" if same else "warn", "up to date" if same else "differs from the repo copy", "" if same else "coproducer setup")


def check_midi(cfg: dict) -> list:
    ports, out = detect.midi_ports(), []
    for key, name, label in (("out", cfg["midi"]["out"], "host to FL"), ("in", cfg["midi"]["in"], "FL to host")):
        if "error" in ports:
            out.append(_row("MIDI port " + name, "warn", ports["error"], "pip install python-rtmidi"))
        elif any(name in p for p in ports[key]):
            out.append(_row("MIDI port " + name, "ok", label))
        else:
            out.append(_row("MIDI port " + name, "fail", "not found (%s)" % label, "create it in loopMIDI (see coproducer setup)"))
    return out


def check_fl(cfg: dict) -> dict:
    exe = cfg["fl"].get("exe") or ""
    if exe and Path(exe).is_file():
        return _row("FL executable", "ok", exe)
    newest = detect.newest_fl_exe()
    return _row("FL executable", "warn", "not set in config.toml (newest found is used)", "set [fl] exe, found: %s" % (newest or "nothing under Program Files"))


def check_gpu() -> dict:
    from ..models.vram import query_vram
    got = query_vram()
    return _row("GPU", "ok" if got else "warn", "%d MB free of %d MB" % got if got else "nvidia-smi not found", "" if got else "install the NVIDIA driver")


def check_envs(cfg: dict, home: Path) -> list:
    from ..models.spec import load_registry
    reg_file = home / "models" / "registry.toml"
    out = []
    for name, spec in (load_registry(reg_file).items() if reg_file.is_file() else []):
        py = cfg["envs"].get(spec.stack)
        good = bool(py) and Path(py).is_file()
        out.append(_row("model env " + name, "ok" if good else ("warn" if spec.optional else "fail"),
                        py or "no environment", "coproducer install-models " + spec.stack))
    return out


def check_tools() -> list:
    return [_row("tool " + t, "ok" if detect.tool_path(t) else "warn", detect.tool_path(t) or "not on PATH", "install " + t)
            for t in ("uv", "git", "ffmpeg")]


def check_desktop(home: Path, config: Path | None = None) -> dict:
    """The co-producer servers are in the config file Claude Desktop actually reads (the Store build reads its own packaged copy)."""
    import shutil
    from . import desktop_cmd as D
    path = config or D.config_path()
    fix = "coproducer install-desktop, then fully quit and restart Claude Desktop"
    try:
        data = D.load_config_file(path)
    except ValueError as e:
        return _row("Claude Desktop servers", "fail", str(e), "fix the JSON or move the file aside, then " + fix)
    ours = {k: v for k, v in (data.get("mcpServers") or {}).items() if k.startswith(D.PREFIX)}
    missing = [n for n in D.build_entries(home) if n not in ours]
    if missing:
        where = "no config file at %s" % path if not path.is_file() else "%s is missing %s" % (path, ", ".join(missing))
        return _row("Claude Desktop servers", "warn", where, fix)
    want = str(home.resolve())
    for name, e in sorted(ours.items()):
        cmd = str(e.get("command") or "")
        if not (Path(cmd).is_file() or shutil.which(cmd)):
            return _row("Claude Desktop servers", "fail", "%s starts %s, which does not exist" % (name, cmd or "nothing"), fix)
        args = [str(a) for a in e.get("args") or []]
        if "--home" in args and args.index("--home") + 1 < len(args) and args[args.index("--home") + 1] != want:
            return _row("Claude Desktop servers", "fail", "%s points at %s, not this install (%s)" % (name, args[args.index("--home") + 1], want), fix)
    return _row("Claude Desktop servers", "ok", "%d in %s" % (len(ours), path))


def _reg_value(key: str, name: str):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError:
        return None


def check_midi_settings(read=None, fl_versions=None) -> list:
    """loopMIDI's two ports and FL's MIDI device settings for the bridge, read from the registry (what coproducer setup-midi writes)."""
    from . import midi_setup as M
    if read is None:
        if not sys.platform.startswith("win"):
            return []
        read = _reg_value
    fix = "close FL Studio, then coproducer setup-midi"
    missing = [p for p in M.PORTS if read(M.LOOPMIDI_KEY + "\\Ports", p) is None]
    rows = [_row("loopMIDI ports", "fail" if missing else "ok", ("missing " + ", ".join(missing)) if missing else ", ".join(M.PORTS), fix)]
    vers = M.fl_version_keys() if fl_versions is None else fl_versions
    if not vers:
        return rows + [_row("FL MIDI settings", "warn", "FL Studio has not been started on this account yet", "start FL once, close it, then coproducer setup-midi")]
    base = "%s\\%s\\Devices" % (M.FL_KEY, vers[0])
    inp = {k: read(base + "\\MIDI input\\" + M.PORTS[0], k) for k in M.INPUT}
    out = read(base + "\\MIDI output\\" + M.PORTS[1], "Port")
    bad = [k for k, v in M.INPUT.items() if k != "IDString" and str(inp[k]) != v]
    if bad or str(out) != M.OUTPUT["Port"]:
        what = ("input %s: %s" % (M.PORTS[0], ", ".join(bad))) if bad else "output %s has no port" % M.PORTS[1]
        return rows + [_row("FL MIDI settings", "fail", "%s (%s)" % (what, vers[0]), fix)]
    return rows + [_row("FL MIDI settings", "ok", "%s: %s enabled with the Coproducer script, %s on port 1" % (vers[0], M.PORTS[0], M.PORTS[1]))]


def run_checks(home: Path) -> list:
    cfg = load_config(home)
    data_dir = Path(cfg["fl"].get("data_dir") or detect.fl_data_dir())
    rows = [check_python(), *check_packages(), check_modules(home), check_fl_side(home, data_dir), *check_midi(cfg), check_fl(cfg),
            check_gpu(), *check_tools(), *check_envs(cfg, home), *check_midi_settings(), check_desktop(home)]
    return rows


def render(rows: list) -> str:
    mark = {"ok": "PASS", "warn": "WARN", "fail": "FAIL"}
    lines = ["%s  %-28s %s%s" % (mark[r["status"]], r["name"], r["detail"], ("   -> " + r["fix"]) if r["fix"] and r["status"] != "ok" else "") for r in rows]
    counts = {k: sum(r["status"] == k for r in rows) for k in mark}
    return "\n".join(lines + ["", "%d passed, %d warnings, %d failures" % (counts["ok"], counts["warn"], counts["fail"])])
