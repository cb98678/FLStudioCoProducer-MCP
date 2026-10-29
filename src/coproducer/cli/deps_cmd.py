"""coproducer deps: record, check and install the exact versions this project runs on.

The lock (src/coproducer/data/deps.lock.json plus requirements.lock) is written from a machine where everything works, by
`coproducer deps --freeze`. running it with no flag compares this machine against it, `--docs` regenerates docs/DEPENDENCIES.md, and
`install-host` installs the pinned host packages. Model environments stay pinned in stacks.py; their installed versions are recorded here too.
"""
from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

LOCK_NAME = "deps.lock.json"
REQ_NAME = "requirements.lock"
SKIP = {"coproducer"}
TOOLS = {"uv": ["uv", "--version"], "git": ["git", "--version"], "ffmpeg": ["ffmpeg", "-version"], "ollama": ["ollama", "--version"],
         "nvidia-smi": ["nvidia-smi", "--query-gpu=driver_version,name", "--format=csv,noheader"]}
ENV_SCRIPT = ("import importlib.metadata as m, json, sys; "
              "print(json.dumps({'python': sys.version.split()[0], 'packages': {d.metadata['Name'].lower().replace('_', '-'): d.version for d in m.distributions() if d.metadata['Name']}}))")

# Why each package is here. Anything not listed is a transitive pin of one of these.
WHY = {
    "numpy": "audio and measurement maths", "scipy": "filters, resampling, template matching (fftconvolve)", "soundfile": "read and write WAV/FLAC", "noisereduce": "vocal denoise before chopping (vocalfx)",
    "pyloudnorm": "LUFS loudness (ITU BS.1770)", "mido": "MIDI messages for the FL bridge", "jsonschema": "module input and output schemas",
    "mcp": "Model Context Protocol servers", "python-rtmidi": "real MIDI ports to loopMIDI", "mss": "screenshots", "pillow": "image crops and templates",
    "pyautogui": "mouse and keyboard input", "pytest": "tests", "hypothesis": "property tests", "fl-studio-api-stubs": "FL API type stubs for tests",
}


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def direct_dependencies(home: Path) -> list:
    """Names the project asks for itself (pyproject.toml), normalised, extras included."""
    f = Path(home) / "pyproject.toml"
    if not f.is_file():
        return []
    proj = tomllib.loads(f.read_text(encoding="utf-8")).get("project", {})
    specs = list(proj.get("dependencies", [])) + [s for v in proj.get("optional-dependencies", {}).values() for s in v]
    return sorted({norm(re.split(r"[<>=!~\[; ]", s, maxsplit=1)[0]) for s in specs})


def host_packages() -> dict:
    import importlib.metadata as m
    return {norm(d.metadata["Name"]): d.version for d in m.distributions() if d.metadata["Name"] and norm(d.metadata["Name"]) not in SKIP}


def env_packages(python: str, runner=subprocess.run) -> dict:
    """{python, packages} of another interpreter, or {} when it cannot be run."""
    try:
        done = runner([python, "-I", "-c", ENV_SCRIPT], capture_output=True, text=True, timeout=60)
        return json.loads(done.stdout) if done.returncode == 0 else {}
    except (OSError, ValueError, subprocess.SubprocessError):
        return {}


def tool_versions(runner=subprocess.run) -> dict:
    out = {}
    for name, argv in TOOLS.items():
        try:
            done = runner(argv, capture_output=True, text=True, timeout=30)
            text = (done.stdout or done.stderr or "").strip().splitlines()
            out[name] = text[0] if done.returncode == 0 and text else None
        except (OSError, subprocess.SubprocessError):
            out[name] = None
    return out


def ollama_models(runner=subprocess.run, only: list | None = None) -> dict:
    """{name: id} from `ollama list` (just the names in only, when given), or {} when Ollama is absent."""
    try:
        done = runner(["ollama", "list"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return {}
    rows = [ln.split() for ln in (done.stdout or "").splitlines()[1:] if ln.strip()]
    found = {r[0]: r[1] for r in rows if len(r) >= 2} if done.returncode == 0 else {}
    return {k: v for k, v in found.items() if only is None or k in only}


def external_versions(home: Path) -> dict:
    """FL Studio build, API level and FL's embedded Python from the last probe report, when there is one."""
    f = Path(home) / "sandbox" / "probe_report.json"
    try:
        v = json.loads(f.read_text(encoding="utf-8"))["versions"]["value"]
    except (OSError, ValueError, KeyError, TypeError):
        return {}
    return {"fl_studio": v.get("ui_getVersion"), "fl_api_level": v.get("general_getVersion"), "fl_embedded_python": str(v.get("python", "")).split()[0] or None}


def collect(home: Path, cfg: dict, runner=subprocess.run) -> dict:
    envs = {name: env_packages(py, runner) for name, py in sorted((cfg.get("envs") or {}).items())}
    return {"generated": datetime.date.today().isoformat(), "platform": sys.platform, "python": sys.version.split()[0],
            "direct": direct_dependencies(home), "host": host_packages(), "tools": tool_versions(runner), "ollama": ollama_models(runner, [cfg.get("llm", {}).get("model")]),
            "external": external_versions(home), "envs": {k: v for k, v in envs.items() if v}}


def lock_path(home: Path) -> Path:
    return Path(home) / "src" / "coproducer" / "data" / LOCK_NAME


def requirements_text(lock: dict) -> str:
    lines = ["# Exact host packages, written by `coproducer deps --freeze` on %s (%s, Python %s)." % (lock["generated"], lock["platform"], lock["python"]),
             "# Install with `coproducer install-host`. Do not edit by hand."]
    return "\n".join(lines + ["%s==%s" % (k, v) for k, v in sorted(lock["host"].items())]) + "\n"


def freeze(home: Path, cfg: dict, runner=subprocess.run) -> dict:
    lock = collect(home, cfg, runner)
    lp = lock_path(home)
    lp.parent.mkdir(parents=True, exist_ok=True)
    lp.write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (Path(home) / REQ_NAME).write_text(requirements_text(lock), encoding="utf-8", newline="\n")
    return lock


def load_lock(home: Path) -> dict | None:
    try:
        return json.loads(lock_path(home).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _row(name: str, status: str, detail: str = "") -> dict:
    return {"name": name, "status": status, "detail": detail}


def check(home: Path, cfg: dict, runner=subprocess.run) -> list:
    """Compare this machine with the lock. fail: a locked package is missing or differs; warn: tools, extras, model envs."""
    lock = load_lock(home)
    if lock is None:
        return [_row("lock file", "fail", "missing; run coproducer deps --freeze on a working machine")]
    rows, have = [], host_packages()
    if lock["python"].split(".")[:2] != sys.version.split(".")[:2]:
        rows.append(_row("python", "fail", "locked %s, running %s" % (lock["python"], sys.version.split()[0])))
    for name in sorted(lock["host"]):
        want = lock["host"][name]
        if name not in have:
            rows.append(_row("package " + name, "fail" if name in lock["direct"] else "warn", "missing (locked %s)" % want))
        elif have[name] != want:
            rows.append(_row("package " + name, "fail" if name in lock["direct"] else "warn", "locked %s, installed %s" % (want, have[name])))
    extra = sorted(set(have) - set(lock["host"]))
    if extra:
        rows.append(_row("unlocked packages", "warn", ", ".join(extra[:12]) + (" ..." if len(extra) > 12 else "")))
    now = tool_versions(runner)
    for name, want in lock["tools"].items():
        if want and now.get(name) != want:
            rows.append(_row("tool " + name, "warn", "locked %r, found %r" % (want, now.get(name))))
    models = ollama_models(runner, list(lock.get("ollama", {})))
    for name, ident in lock.get("ollama", {}).items():
        if name not in models:
            rows.append(_row("ollama " + name, "warn", "model not pulled"))
        elif models[name] != ident:
            rows.append(_row("ollama " + name, "warn", "id locked %s, found %s (the model was updated)" % (ident, models[name])))
    from .stacks import STACKS
    for stack, py in sorted((cfg.get("envs") or {}).items()):
        want = STACKS.get(stack, {})
        got = env_packages(py, runner).get("packages", {})
        pins = [[p.split("==")[0].split("[")[0], p.split("==")[1]] for p in want.get("packages", []) if "==" in p]  # extras such as [gpu] are not part of the name
        for lib in ("torch", "torchaudio"):
            if want.get(lib):
                pins.append([lib, want[lib]])
        bad = ["%s %s!=%s" % (n, got.get(norm(n)), v) for n, v in pins if (got.get(norm(n)) or "").split("+")[0] != v]
        rows.append(_row("env " + stack, "warn" if bad else "ok", "; ".join(bad) if bad else "matches stacks.py"))
    return rows or [_row("host packages", "ok", "%d packages match the lock" % len(lock["host"]))]


def host_install_plan(home: Path) -> list:
    """The commands that build the host environment from the lock: venv with the locked Python, packages, then this project without dependencies."""
    lock = load_lock(home)
    if lock is None:
        return []
    py = ".".join(lock["python"].split(".")[:2])
    venv = Path(home) / ".venv"
    exe = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    return [(["uv", "venv", "--allow-existing", "--python", py, str(venv)], None),
            (["uv", "pip", "install", "--python", str(exe), "-r", str(Path(home) / REQ_NAME)], None),
            (["uv", "pip", "install", "--python", str(exe), "--no-deps", "-e", str(home)], None)]


def _short(text) -> str:
    """The first version number in a tool's banner line, or the line itself when it has none (nvidia-smi: driver and card)."""
    m = re.search(r"\d+(?:\.\d+)+", text or "")
    return (text if not m or "," in (text or "") else m.group(0)) if text else "not found"


def render_docs(lock: dict) -> str:
    """docs/DEPENDENCIES.md from the lock and stacks.py, so the document cannot drift from what is pinned."""
    from .stacks import ACESTEP_COMMIT, ACESTEP_REPO, STACKS, WHISPER_REVISION
    out = ["# Dependencies", "",
           "Generated by `coproducer deps --docs` from `src/coproducer/data/deps.lock.json` and `cli/stacks.py`. Do not edit by hand.",
           "Locked on %s on %s with Python %s." % (lock["generated"], lock["platform"], lock["python"]), "",
           "## How to install", "",
           "On Windows the installer does every step below, with these pins: unzip the release and run `install.cmd` (see `docs/INSTALL.md`). By hand:", "",
           "1. Install uv and git (see Tools; Ollama only for the local brain model), then `uv venv` plus `coproducer install-host` for the pinned host packages.",
           "2. `coproducer setup`, then `coproducer doctor`.",
           "3. `coproducer install-models` for the model environments (pins below), then `ollama pull` for each brain model.",
           "4. `coproducer deps` shows any drift from this lock.", "",
           "## Host packages (`requirements.lock`)", "", "| Package | Version | Role |", "| --- | --- | --- |"]
    direct = set(lock["direct"])
    for name, ver in sorted(lock["host"].items()):
        if name in direct:
            out.append("| %s | %s | %s |" % (name, ver, WHY.get(name, "direct dependency")))
    out += ["", "%d further packages are transitive pins, all listed in `requirements.lock`." % (len(lock["host"]) - len(direct & set(lock["host"]))),
            "The editable install builds with `setuptools==80.10.2` (pyproject `[build-system]`, exact like the rest).",
            "ACE-Step downloads its own weights into its checkpoints folder on first use; they are not pinned by revision here.", "",
            "## Tools", "", "| Tool | Version found when locked |", "| --- | --- |"]
    out += ["| %s | %s |" % (k, _short(v)) for k, v in sorted(lock["tools"].items())]
    out += ["", "## Brain and critic models (Ollama)", "", "| Model | Id when locked |", "| --- | --- |"]
    out += ["| %s | %s |" % (k, v) for k, v in sorted(lock.get("ollama", {}).items())] or ["| none recorded | |"]
    out += ["", "Pull with `ollama pull <name>`; the id changes when the publisher updates a tag, and `coproducer deps` warns about that."]
    out += ["", "## External programs", ""]
    for k, v in sorted((lock.get("external") or {}).items()):
        out.append("- %s: %s" % (k.replace("_", " "), v))
    out += ["- loopMIDI 1.0.16.27: two virtual ports named in `config.toml` ([midi] out and in); install from https://www.tobias-erichsen.de/software/loopmidi.html",
            "- FL Studio: the build this was measured on is above; the FL-side script is generated by `coproducer gen`. FL 2024 (24.2.2) and 21 (21.2.0)"
            " are also installed on the development machine; nothing here uses them.",
            "- Plugins the builds load: Xfer Serum 1.368 and Serum 2 2.1.5 (the person's own presets); every other plugin is FL's own. Trial-only"
            " plugins on this edition are listed in config `fl.not_owned` (Transient Processor).", "",
            "## Model environments (`cli/stacks.py`, exact pins)", ""]
    for name, d in sorted(STACKS.items()):
        out.append("### %s" % name)
        if "clone" in d:
            out += ["- source: %s at commit `%s`" % (ACESTEP_REPO, ACESTEP_COMMIT), "- dependencies fixed by its own `uv.lock` (`uv sync --locked`)", ""]
            continue
        out.append("- python %s%s" % (d["python"], "" if not d["torch"] else ", torch %s, torchaudio %s" % (d["torch"], d["torchaudio"])))
        out += ["- `%s`" % p for p in d["packages"]]
        if d.get("weights"):
            out.append("- weights: %s at revision `%s` (%d files)" % (d["weights"]["repo"], d["weights"].get("revision"), len(d["weights"]["files"])))
        for repo, rev in sorted((d.get("hf_snapshots") or {}).items()):
            out.append("- Hugging Face snapshot %s at `%s` (read offline from the cache)" % (repo, rev))
        for key, f in sorted((d.get("separator_models") or {}).items()):
            out.append("- separator model %s: %d bytes, sha256 `%s`, kept at models/%s" % (key, f["bytes"], f["sha256"], d["model_dir"]))
        for key, f in sorted((d.get("files") or {}).items()):
            out.append("- file %s: %s, %d bytes, sha256 `%s`, kept at %s" % (key, f["url"], f.get("bytes", 0), f["sha256"],
                                                                                 f["dest"] if f["dest"].startswith("~") else "models/" + f["dest"]))
        if name == "critique":
            out.append("- also runs Whisper for word times: openai/whisper-large-v3 at revision `%s` (tools/transcribe_vocals.py)" % WHISPER_REVISION)
        out.append("- whole environment frozen in `models/locks/%s.txt`; installs use it" % name)
        out.append("")
    for name, versions in sorted((lock.get("envs") or {}).items()):
        out.append("Installed %s on the locking machine: Python %s, %d packages." % (name, versions.get("python"), len(versions.get("packages", {}))))
    return "\n".join(out).rstrip() + "\n"


def render_check(rows: list) -> str:
    mark = {"ok": "PASS", "warn": "WARN", "fail": "FAIL"}
    return "\n".join("%s  %-28s %s" % (mark[r["status"]], r["name"], r["detail"]) for r in rows)
