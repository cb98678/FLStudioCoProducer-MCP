import json
import subprocess
from pathlib import Path

from coproducer.cli import deps_cmd


class Done:
    def __init__(self, out="", code=0):
        self.stdout, self.stderr, self.returncode = out, "", code


def runner(argv, **kw):
    if argv[0] == "uv":
        return Done("uv 0.9.9 (abc)")
    if argv[:2] == ["ollama", "list"]:
        return Done("NAME ID SIZE MODIFIED\ngemma4:12b abc123 8 GB 2 days ago\n")
    if argv[0] == "ollama":
        return Done("ollama version is 0.20.0")
    if "-I" in argv:
        return Done(json.dumps({"python": "3.12.1", "packages": {"demucs": "4.1.0", "numpy": "2.5.4"}}))
    raise OSError("not installed")


def make_home(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"\ndependencies=["numpy>=1","Pillow"]\n[project.optional-dependencies]\ngui=["mss"]\n')
    return tmp_path


def test_direct_dependencies_are_normalised_with_extras(tmp_path):
    assert deps_cmd.direct_dependencies(make_home(tmp_path)) == ["mss", "numpy", "pillow"]


def test_freeze_then_check_is_clean_and_drift_is_named(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(deps_cmd, "host_packages", lambda: {"numpy": "2.5.4", "mss": "10.0.0"})
    lock = deps_cmd.freeze(home, {"envs": {}, "llm": {"model": "gemma4:12b"}}, runner)
    assert (home / "requirements.lock").read_text().count("==") == 2 and lock["ollama"] == {"gemma4:12b": "abc123"}
    assert lock["tools"]["git"] is None                                   # a missing tool is recorded as missing, not an error
    rows = deps_cmd.check(home, {"envs": {}}, runner)
    assert all(r["status"] != "fail" for r in rows)
    monkeypatch.setattr(deps_cmd, "host_packages", lambda: {"numpy": "2.0.0"})
    bad = {r["name"]: r for r in deps_cmd.check(home, {"envs": {}}, runner)}
    assert bad["package numpy"]["status"] == "fail" and "locked 2.5.4, installed 2.0.0" in bad["package numpy"]["detail"]
    assert bad["package mss"]["status"] == "fail"                         # direct and missing


def test_check_without_a_lock_fails_clearly(tmp_path):
    assert deps_cmd.check(tmp_path, {"envs": {}}, runner)[0]["status"] == "fail"


def test_hostile_subprocess_results_never_raise(tmp_path):
    def broken(argv, **kw):
        raise subprocess.TimeoutExpired(argv, 1)
    assert deps_cmd.ollama_models(broken) == {} and deps_cmd.env_packages("x", broken) == {}
    assert all(v is None for v in deps_cmd.tool_versions(broken).values())
    assert deps_cmd.env_packages("x", lambda a, **k: Done("not json")) == {}
    assert deps_cmd.ollama_models(lambda a, **k: Done("garbage\n\n   \n")) == {}


def test_install_plan_uses_the_locked_python_and_requirements(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    assert deps_cmd.host_install_plan(home) == []
    monkeypatch.setattr(deps_cmd, "host_packages", lambda: {"numpy": "2.5.4"})
    deps_cmd.freeze(home, {"envs": {}}, runner)
    plan = deps_cmd.host_install_plan(home)
    assert plan[0][0][:4] == ["uv", "venv", "--allow-existing", "--python"] and "requirements.lock" in plan[1][0][-1] and "--no-deps" in plan[2][0]


def test_docs_list_every_direct_package_and_every_stack(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(deps_cmd, "host_packages", lambda: {"numpy": "2.5.4", "mss": "10.0.0", "idna": "3.0"})
    text = deps_cmd.render_docs(deps_cmd.freeze(home, {"envs": {}}, runner))
    assert "| numpy | 2.5.4 |" in text and "| idna" not in text and "1 further packages" in text
    for stack in ("demucs", "basicpitch", "critique", "acestep"):
        assert "### " + stack in text
    assert "—" not in text                                           # no em dashes in delivered documents


def test_only_the_configured_model_is_locked_and_torch_is_checked(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(deps_cmd, "host_packages", lambda: {"numpy": "2.5.4"})
    lock = deps_cmd.freeze(home, {"envs": {}, "llm": {"model": "other:1b"}}, runner)
    assert lock["ollama"] == {}                                           # not pulled here, and nothing else is recorded
    from coproducer.cli.stacks import STACKS

    def env_runner(argv, **kw):
        return Done(json.dumps({"python": "3.12.1", "packages": {"torch": "2.11.0+cu128", "torchaudio": "2.10.0", "demucs": "4.1.0", "numpy": "2.5.4"}}))
    rows = {r["name"]: r for r in deps_cmd.check(home, {"envs": {"demucs": "py"}}, env_runner)}
    assert rows["env demucs"]["status"] == "warn" and "torchaudio 2.10.0!=%s" % STACKS["demucs"]["torchaudio"] in rows["env demucs"]["detail"]
    assert "torch " not in rows["env demucs"]["detail"]                   # the +cu128 build tag is not drift


def test_docs_in_the_repo_match_the_lock_when_both_exist():
    home = Path(__file__).resolve().parents[1]
    lock = deps_cmd.load_lock(home)
    doc = home / "docs" / "DEPENDENCIES.md"
    if lock is not None and doc.is_file():
        assert doc.read_text(encoding="utf-8") == deps_cmd.render_docs(lock)


def test_pyproject_pins_every_direct_dependency_to_the_lock():
    import json
    import re
    import tomllib
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    proj = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    specs = list(proj["dependencies"]) + [s for v in proj["optional-dependencies"].values() for s in v]
    lock = json.loads((root / "src" / "coproducer" / "data" / "deps.lock.json").read_text(encoding="utf-8"))["host"]
    lock = lock.get("packages", lock) if "packages" in lock else lock
    for s in specs:
        m = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;]+)", s)
        assert m, "%s is not an exact pin" % s
        assert lock[deps_cmd.norm(m.group(1))] == m.group(2), "%s differs from the lock" % s
    build = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["build-system"]["requires"]
    assert all(re.fullmatch(r"[A-Za-z0-9_.-]+==[^\s;]+", b) for b in build), build  # the isolated build fetches exactly this


def test_model_env_locks_hold_every_direct_pin_and_the_install_uses_them():
    """models/locks/<stack>.txt is the whole frozen environment; the direct pins in stacks.py must be in it, and installs read it."""
    from pathlib import Path

    from coproducer.cli import stacks
    root = Path(__file__).resolve().parents[1]
    for name, d in stacks.STACKS.items():
        lock = root / "models" / "locks" / (name + ".txt")
        assert lock.is_file(), name
        pins = {ln.split("==")[0].lower(): ln.split("==")[1].split("+")[0] for ln in lock.read_text().splitlines() if "==" in ln}
        for p in d.get("packages", []):
            pkg, ver = p.split("==")
            pkg = pkg.split("[")[0]
            assert pins.get(pkg.lower().replace("_", "-")) == ver or pins.get(pkg.lower()) == ver, (name, p)
        if d.get("torch"):
            assert pins["torch"] == d["torch"] and pins["torchaudio"] == d["torchaudio"], name
    cfg = {"paths": {"models": "models"}, "gpu": {"torch_index": "https://download.pytorch.org/whl/cu128"}}
    plan = stacks.install_plan("demucs", root, cfg)
    assert any("-r" in argv and argv[argv.index("-r") + 1].endswith("demucs.txt") for argv, _cwd in plan["commands"])


def test_the_critic_loads_the_snapshot_install_models_downloads():
    from coproducer.cli import stacks
    src = (Path(__file__).resolve().parents[1] / "src" / "coproducer" / "runners" / "critique_runner.py").read_text()
    w = stacks.STACKS["critique"]["weights"]
    assert 'MODEL_ID = "%s"' % w["repo"] in src and 'MODEL_REVISION = "%s"' % w["revision"] in src


def test_whisper_runner_and_tools_share_the_pinned_revision():
    from coproducer.cli import stacks
    root = Path(__file__).resolve().parents[1]
    for f in ("src/coproducer/runners/whisper_runner.py", "tools/transcribe_vocals.py", "tools/asr_probe.py", "tools/word_times.py"):
        assert stacks.WHISPER_REVISION in (root / f).read_text(), f
