"""install.ps1, install.cmd and tools/make_release.py: pins agree with the dependency lock, every command the installer runs exists and
parses, the script stays plain ASCII for Windows PowerShell 5.1, and a release zip carries what a fresh machine needs and nothing of this one."""
import re
import runpy
import zipfile
from pathlib import Path

import pytest

from coproducer.cli import COMMANDS, build_parser, deps_cmd, stacks
from coproducer.models.spec import load_registry

ROOT = Path(__file__).resolve().parents[1]
PS1 = (ROOT / "install.ps1").read_text(encoding="utf-8")


def _pin(name: str) -> str:
    m = re.search(r'^\$%s = "([^"]*)"' % name, PS1, re.M)
    assert m, name
    return m.group(1)


def test_script_is_ascii_without_em_dashes():
    """Windows PowerShell 5.1 reads a file without a byte order mark as the ANSI code page: any non-ASCII character would come out garbled."""
    for f in ("install.ps1", "install.cmd", "docs/INSTALL.md"):
        text = (ROOT / f).read_bytes()
        assert b"\xe2\x80\x94" not in text, f
        if f != "docs/INSTALL.md":
            text.decode("ascii")
    assert b"\r\n" in (ROOT / "install.cmd").read_bytes()               # batch files want CRLF


def test_pins_match_the_dependency_lock():
    lock = deps_cmd.load_lock(ROOT)
    assert _pin("HostPython") == lock["python"]
    assert lock["tools"]["uv"].startswith("uv %s " % _pin("UvVersion"))
    assert lock["tools"]["ffmpeg"].startswith("ffmpeg version %s-full_build" % _pin("FfmpegVersion"))
    assert _pin("UvVersion") in _pin("UvUrl") and _pin("FfmpegVersion") in _pin("FfmpegUrl")
    for sha in ("UvSha256", "FfmpegSha256"):
        assert re.fullmatch(r"[0-9a-f]{64}", _pin(sha))
    assert _pin("UvUrl").startswith("https://github.com/astral-sh/uv/releases/download/")
    assert _pin("FfmpegUrl").startswith("https://github.com/GyanD/codexffmpeg/releases/download/")


def test_standard_models_are_every_registry_model_that_is_not_optional():
    std = set(re.search(r'^\$StandardStacks = @\(([^)]*)\)', PS1, re.M).group(1).replace('"', "").replace(" ", "").split(","))
    serum = set(re.search(r'^\$SerumStacks = @\(([^)]*)\)', PS1, re.M).group(1).replace('"', "").replace(" ", "").split(","))
    full = set(re.search(r'^\$FullOnlyStacks = @\(([^)]*)\)', PS1, re.M).group(1).replace('"', "").replace(" ", "").split(","))
    reg = load_registry(ROOT / "models" / "registry.toml")
    needed = {s.stack for s in reg.values() if not s.optional and s.stack in stacks.STACKS}
    # plus sep: optional in the registry because separate_stems (Demucs alone) can stand in, but the remix pipeline's vocals come from it
    assert std == needed | {"sep"} and reg["roformer"].fallback == "separate_stems" and full == {"acestep"} and reg["acestep"].optional and serum == {"serum", "serummcp"} and (std | serum | full) <= set(stacks.STACKS)


def test_every_coproducer_call_in_the_script_parses():
    calls = re.findall(r'Invoke-Tool \$Cop (?:\$\w+|@\(([^)]*)\))', PS1)
    assert len(calls) >= 5
    for body in [c for c in calls if c]:
        argv = [x.strip().strip('"') for x in body.split(",")]
        assert argv[0] in COMMANDS
        build_parser().parse_args(argv)
    p = build_parser()
    p.parse_args(["setup", "--no-desktop", "--data-dir", "C:/x", "--torch-index=", "--models-dir", "D:/m"])
    p.parse_args(["install-desktop", "--with-serum", "--serum-presets", "C:/p"])
    p.parse_args(["install-models", "demucs", "acestep", "--with-optional"])
    for flag in ("--torch-index=", "--allow-existing", "--no-desktop", "check-servers", "setup-midi", "doctor"):
        assert flag in PS1, flag


def test_never_stops_or_kills_fl_studio():
    low = PS1.lower()
    assert "stop-process" not in low and "taskkill" not in low and not re.search(r"\bkill\b", re.sub(r"#.*", "", low))


def test_release_packs_the_program_and_nothing_of_this_machine(tmp_path):
    mr = runpy.run_path(str(ROOT / "tools" / "make_release.py"))
    root = tmp_path / "repo"
    for rel in mr["REQUIRED"] + ["src/coproducer/x.py", "modules/a/a.py", "docs/HANDOFF.md"]:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("x")
    (root / "pyproject.toml").write_text('[project]\nname = "coproducer"\nversion = "9.9.9"\n')
    for junk in ("config.toml", ".mcp.json", "sandbox/song/a.wav", "runs/r1/l.json", "models/envs/demucs/python.exe", "models/weights/w.th",
                 "runtime/uv/uv.exe", ".venv/Scripts/python.exe", ".git/HEAD", "src/coproducer/__pycache__/a.pyc", "logs/install.log",
                 "dist/old.zip", "docs/x.json.coproducer-20261026-212334.bak", "savepoints/sp.zip", "checkpoints/vae/m.safetensors",
                 "Settings/Hardware/coproducer/device_coproducer.py", "coproducer_update.zip", "models/acestep/checkpoints/a.safetensors"):
        (root / junk).parent.mkdir(parents=True, exist_ok=True)
        (root / junk).write_text("x")
    out = mr["build"](root)
    names = set(zipfile.ZipFile(out).namelist())
    assert out.name == "coproducer-9.9.9.zip" and set(mr["REQUIRED"]) <= names and "modules/a/a.py" in names
    assert not [n for n in names if n.split("/")[0] in ("sandbox", "runs", "runtime", ".venv", ".git", "logs", "dist", "savepoints", "checkpoints", "Settings")]
    assert "coproducer_update.zip" not in names and not [n for n in names if n.endswith((".bak", ".safetensors"))]
    assert not {"config.toml", ".mcp.json"} & names and not [n for n in names if "__pycache__" in n or "models/" in n and "envs" in n]
    (root / "install.ps1").unlink()
    with pytest.raises(SystemExit, match="install.ps1"):
        mr["build"](root)


def test_the_real_tree_is_a_complete_release():
    mr = runpy.run_path(str(ROOT / "tools" / "make_release.py"))
    names = mr["files"](ROOT)
    assert not [r for r in mr["REQUIRED"] if r not in names]
    assert "config.toml" not in names and not [n for n in names if n.startswith(("sandbox/", "models/envs/", "runtime/"))]
    tops = {n.split("/")[0] for n in names}
    assert {"src", "modules", "tools", "skills", "docs", "fl_side", "models", "assets", "styles", "recipes", "tests"} <= tops


def test_array_lines_that_join_strings_are_in_parentheses():
    """In PowerShell the comma binds tighter than +: in @("a" + $x + "b", "c") the pieces become separate elements. The first installer wrote
    its coproducer.cmd that way, a line of its own ran a bare python.exe, and the install hung at a Python prompt (2026-10-27)."""
    bad, inside = [], False
    for n, line in enumerate(PS1.splitlines(), 1):
        t = line.strip()
        if re.search(r"= @\($", t):
            inside = True
            continue
        if inside and t.startswith(")"):
            inside = False
        elif inside and " + " in t and not t.startswith("("):
            bad.append(n)
    assert not bad, bad
