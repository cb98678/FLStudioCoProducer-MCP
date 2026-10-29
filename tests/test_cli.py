"""CLI: parser, doctor, setup, installers, project commands, calibrate, and the host side of the probes."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from coproducer.cli import build_parser, commands, detect, doctor, models_cmd, probe_cmd, project_cmd, setup_cmd, stacks
from coproducer.cli.calibrate_cmd import calibrate
from coproducer.config import load_config

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    h.mkdir()
    (h / "modules").symlink_to(REPO / "modules")
    (h / "models").mkdir()
    (h / "models" / "registry.toml").write_text((REPO / "models" / "registry.toml").read_text())
    (h / "fl_side").mkdir()
    (h / "fl_side" / "device_coproducer.py").write_text((REPO / "fl_side" / "device_coproducer.py").read_text())
    (h / "probes").mkdir()
    (h / "probes" / "device_probe.py").write_text((REPO / "probes" / "device_probe.py").read_text())
    return h


def test_parser_knows_every_command_and_each_has_a_handler():
    p = build_parser()
    for name in ("setup", "doctor", "install-models", "lint", "gen", "new-project", "calibrate", "probe", "promote", "serve", "run", "resume"):
        assert hasattr(commands, "cmd_" + name.replace("-", "_")), name
    assert p.parse_args(["probe", "ping"]).which == "ping"
    with pytest.raises(SystemExit):
        p.parse_args(["frobnicate"])


def test_lint_command_reports_clean(home):
    lines = []
    assert commands.cmd_lint(home, None, lines.append) == 0 and lines[-1] == "lint clean"


def test_detect_fl_executables(tmp_path):
    exe = tmp_path / "PF" / "Image-Line" / "FL Studio 2026" / "FL64.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    assert detect.fl_exe_candidates({"ProgramFiles": str(tmp_path / "PF")}) == [exe]
    assert detect.fl_exe_candidates({}) == []
    assert str(detect.hardware_dir(Path("D"))).replace("\\", "/") == "D/Settings/Hardware/coproducer"


def test_setup_creates_config_folders_and_installs_script(home, tmp_path):
    data = tmp_path / "FLdata"
    r = setup_cmd.run_setup(home, "C:/FL/FL64.exe", str(data))
    assert r["config"] == "created" and (data / "Settings/Hardware/coproducer/device_coproducer.py").is_file()
    assert (home / "sandbox").is_dir() and load_config(home)["fl"]["exe"] == "C:/FL/FL64.exe"
    assert setup_cmd.run_setup(home, "other.exe", str(data))["config"] == "kept"
    text = setup_cmd.render_report(r)
    assert "loopMIDI" in text and "coproducer-in" in text and "\u2014" not in text


def test_doctor_flags_missing_environments_and_installed_script(home, tmp_path):
    setup_cmd.run_setup(home, "", str(tmp_path / "FLdata"))
    rows = {r["name"]: r for r in doctor.run_checks(home)}
    assert rows["python"]["status"] == "ok" and rows["module lint"]["status"] == "ok"
    assert rows["FL-side script installed"]["status"] == "ok"
    assert rows["model env demucs"]["status"] == "fail" and rows["model env flamingo"]["status"] == "warn"
    assert "failures" in doctor.render(list(rows.values()))


def test_install_plan_uses_documented_commands(home):
    cfg = load_config(home)
    cfg["gpu"]["torch_index"] = "https://example.invalid/whl/cu999"
    d = stacks.install_plan("demucs", home, cfg)
    flat = [" ".join(a) for a, _ in d["commands"]]
    assert any("uv venv --allow-existing --python 3.12" in c for c in flat) and any(c.endswith("demucs==4.1.0 numpy==2.5.4") for c in flat) and any("--index-url https://example.invalid" in c for c in flat)
    assert "hashlib" in flat[-1] and "955717e8-8726e21a.th" in flat[-1]      # the pinned checkpoints come last, checked by hash
    assert any("torch==2.11.0 torchaudio==2.11.0" in c for c in flat)
    assert all("==" in p for stack in ("demucs", "basicpitch") for p in stacks.STACKS[stack]["packages"])
    assert stacks.install_plan("basicpitch", home, cfg)["commands"][0][0][4] == "3.11"
    a = stacks.install_plan("acestep", home, cfg)
    assert a["commands"][0][0][:2] == ["git", "clone"] and a["commands"][1][0] == ["git", "checkout", "--detach", stacks.ACESTEP_COMMIT] and a["commands"][2][0] == ["uv", "sync", "--locked"]
    assert "pytorch.org" in stacks.install_plan("demucs", home, load_config(home))["notes"][0]
    assert stacks.install_plan("vision", home, cfg)["commands"] == []


def test_install_models_records_interpreter_only_on_success(home):
    calls = []

    def runner(argv, cwd=None, **kw):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0 if "basic-pitch" in " ".join(argv) or "venv" in argv else 7)

    rows = models_cmd.install(home, ["basicpitch", "demucs"], False, runner)
    assert rows["basicpitch"]["status"] == "installed" and rows["demucs"]["status"].startswith("failed")
    envs = load_config(home)["envs"]
    assert "basicpitch" in envs and "demucs" not in envs
    assert models_cmd.install(home, ["demucs"], True, runner)["demucs"]["status"] == "planned"


def test_new_project_and_promote_rules(home, tmp_path):
    src = tmp_path / "orig.flp"
    src.write_bytes(b"FLhd original")
    assert project_cmd.new_project(home, "song", "restyle", str(src))["ok"]
    spec = (home / "specs" / "song.md").read_text()
    assert "mode: restyle" in spec and re.search(r"original_hash: [0-9a-f]{64}", spec)
    assert not project_cmd.new_project(home, "bad", "dance", None)["ok"]

    (home / "sandbox").mkdir(exist_ok=True)
    result = home / "sandbox" / "out.flp"
    result.write_bytes(b"FLhd new")
    dest = tmp_path / "real" / "orig.flp"
    dest.parent.mkdir()
    dest.write_bytes(b"FLhd original")
    assert not project_cmd.promote(home, "r1", result, dest, "yes")["ok"] and dest.read_bytes() == b"FLhd original"
    assert not project_cmd.promote(home, "r1", src, dest, "promote")["ok"]                     # not inside the sandbox
    assert not project_cmd.promote(home, "r1", result, home / "sandbox" / "x.flp", "promote")["ok"]
    got = project_cmd.promote(home, "r1", result, dest, "promote")
    assert got["ok"] and dest.read_bytes() == b"FLhd new" and Path(got["backup"]).read_bytes() == b"FLhd original"
    assert "promotion" in (home / "runs" / "r1" / "ledger.jsonl").read_text()


def test_calibrate_saves_window_relative_anchors(home):
    points = iter([(10, 20), (300, 400)])
    done = calibrate(home, ["export_start", "export_split_checkbox"], read=lambda prompt: "", cursor=lambda: next(points), out=lambda t: None)
    assert done == [("export_start", "10,20"), ("export_split_checkbox", "300,400")]
    assert load_config(home)["anchors"] == {"export_start": "10,20", "export_split_checkbox": "300,400"}


def test_probe_install_and_report(home, tmp_path):
    dst = Path(probe_cmd.install_fl(home, tmp_path / "FL", mutating=True))
    assert re.search(r"^MUTATING = True", dst.read_text(), re.M) and dst.read_text().startswith("# name=Coproducer Probe")
    report = {"versions": {"ok": True, "value": {"title": "x"}}, "json": {"ok": False, "error": "ImportError: json"},
              "inventory": {"ok": True, "value": {"mixer": ["getTrackVolume", "brandNew"], "ui": None}}, "_meta": {"mutating": True}}
    planned = {"mixer.getTrackVolume": {}, "mixer.setTrackVolume": {}, "ui.getVersion": {}}
    d = probe_cmd.inventory_diff(report["inventory"]["value"], planned)
    assert d == {"planned_but_missing": ["mixer.setTrackVolume"], "present_but_unplanned": ["mixer.brandNew"], "modules_not_importable": ["ui"]}
    text = probe_cmd.summarize_report(report, planned)
    assert "FAILED ImportError" in text and "1 planned functions missing" in text


def test_probe_ping_and_throughput_through_the_loopback(run):
    from coproducer.bridge import BridgeClient
    from coproducer.loopback import LoopbackTransport, load_device_script

    s = run()
    client = BridgeClient(s.registry, LoopbackTransport(run.fake, load_device_script(run.fake)), max_payload=200)
    p = probe_cmd.ping(client, runs=2)
    assert p["passed"] and len(p["ms"]) == 2
    t = probe_cmd.throughput(client, sizes=(64, 256, 1024))
    assert t["passed"] and t["safe_frame_size"] == 1024


def test_in_fl_probe_runs_against_the_fake(tmp_path):
    import importlib.util
    from coproducer.fakefl import FakeFL

    fake = FakeFL().install()
    try:
        spec = importlib.util.spec_from_file_location("device_probe_test", REPO / "probes" / "device_probe.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod._here = lambda: str(tmp_path)
        mod.OnInit()
        mod.OnIdle()
        mod.OnIdle()                                           # runs once only
        rep = json.loads((tmp_path / "probe_report.json").read_text())
        assert rep["json"]["value"]["roundtrip"] is True and rep["file_io"]["value"]["write_read"] is True
        assert "inventory" in rep and rep["_meta"] == {"mutating": False} and "fader_law" not in rep
    finally:
        fake.uninstall()


def test_execute_reports_pending_questions_without_blocking(home, tmp_path, wav):
    from coproducer.cli.run_cmd import execute
    from coproducer.synth import RATE
    import numpy as np

    path = wav("tone", 0.2 * np.sin(2 * np.pi * 220 * np.arange(RATE) / RATE))
    plan = {"plan_id": "p", "steps": [{"id": "s1", "phase": "P1", "module": "measure_rms", "args": {"path": path}, "verifier": "none"}]}
    code, text = execute(home, "r1", plan, None, True, "A2", connect=False)
    assert code == 0 and "s1" in text
    code, text = execute(home, "r1", plan, None, True, "A2", connect=False)             # second call resumes from the ledger
    assert code == 0 and "resumed" in text
    code, text = execute(home, "r2", None, None, True, "A2", connect=False)
    assert code == 2


def test_shipped_templates_are_valid_but_unfilled(run):
    s = run()
    call = s.registry.call
    t = call("load_targets_file", path=str(REPO / "targets" / "streaming_default.toml"))
    assert t.error.code == "E_ARG" and "loudness.integrated_lufs" in t.error.detail["unfilled"]
    for g in ("dubstep", "techno"):
        r = call("load_genre_profile", path=str(REPO / "genre_profiles" / (g + ".toml")), allow_blanks=True)
        assert r.ok and r.value["unfilled"], g
    assert call("load_genre_profile", path=str(REPO / "genre_profiles" / "dubstep.toml")).error.code == "E_ARG"
    inv = call("load_invariants_file", path=str(REPO / "specs" / "templates" / "invariants.toml"))
    assert inv.error.code == "E_ARG" and "melody.contour_threshold" in inv.error.detail["unfilled"] and not inv.error.detail["missing"]


def test_check_cards_command_is_clean():
    lines = []
    assert commands.cmd_check_cards(REPO, None, lines.append) == 0 and len(lines) == 11


def test_model_smoke_probe_runs_every_model_through_the_tools(rig, ml, tmp_path):
    from coproducer.services import set_service
    set_service("sandbox_root", str(tmp_path))
    rig.reg.approver = lambda name, kwargs: True
    res = probe_cmd.models(rig.call, tmp_path / "probe_models")
    assert res["demucs"]["status"] == "passed" and res["acestep"]["status"] == "passed" and res["flamingo"]["status"] in ("passed", "failed", "skipped")
    assert res["basicpitch"].get("notes") is not None


def test_model_smoke_probe_reports_missing_environments_as_skipped(rig, tmp_path):
    from coproducer.models.factory import make_worker_factory
    from coproducer.models.scheduler import Scheduler
    from coproducer.models.spec import load_registry
    from coproducer.services import set_service
    set_service("sandbox_root", str(tmp_path))
    set_service("scheduler", Scheduler(load_registry(REPO / "models" / "registry.toml"), make_worker_factory({}), lambda: (16000, 16000)))
    rig.reg.approver = lambda name, kwargs: True
    res = probe_cmd.models(rig.call, tmp_path / "pm")
    assert {res[m]["status"] for m in ("demucs", "acestep", "basicpitch")} == {"skipped"} and res["passed"] is True
    assert res["flamingo"]["status"] == "fallback"                      # no model: the rule-based critique answers instead


def test_probe_report_comes_back_over_the_bridge(rig):
    report = probe_cmd.collect_report(rig.client)
    assert "_error" not in report and report["_meta"] == {"mutating": False}
    assert report["json"]["ok"] and report["json"]["value"]["roundtrip"] is True
    assert report["versions"]["ok"] and "inventory" in report
    assert "fader_law" not in report                         # writing probes run only on request


def test_probe_report_runs_writing_probes_only_when_asked(rig):
    report = probe_cmd.collect_report(rig.client, mutating=True)
    assert {"fader_law", "undo", "markers"} <= set(report) and report["_meta"] == {"mutating": True}


def test_unknown_probe_is_an_error_not_a_crash(rig):
    got = rig.client.request("bridge_probe", {"name": "nope"})
    assert not got.ok and got.error.code == "E_NOT_FOUND"


def test_brain_probe_reports_plain_reply_and_tool_call(rig):
    calls = []

    def fake(name, **kw):
        calls.append(kw)
        msg = {"content": "ready"} if "tools" not in kw else {"content": "", "tool_calls": [{"function": {"name": "set_tempo", "arguments": "{\"bpm\": 128}"}}]}
        from coproducer.result import ok
        return ok({"message": msg, "finish_reason": "stop", "usage": {"total_tokens": 9}})

    res = probe_cmd.brain(fake)
    assert res["passed"] and res["tool_call"]["tool_calls"][0]["name"] == "set_tempo" and len(calls) == 2


def test_brain_probe_fails_when_no_tool_call_is_made(rig):
    from coproducer.result import ok, fail
    res = probe_cmd.brain(lambda name, **kw: ok({"message": {"content": "sure"}, "finish_reason": "stop", "usage": {}}))
    assert not res["passed"] and res["tool_call"]["status"] == "failed"
    assert probe_cmd.brain(lambda name, **kw: fail("E_MODEL", "down"))["plain"]["status"] == "failed"


def test_install_saves_a_lock_file_of_installed_versions(home):
    def runner(argv, cwd=None, **kw):
        return subprocess.CompletedProcess(argv, 0, stdout="numpy==1.26.4\ntensorflow==2.14.0\n" if "freeze" in argv else "")

    rows = models_cmd.install(home, ["basicpitch"], False, runner)
    assert rows["basicpitch"]["status"] == "installed" and rows["basicpitch"]["lock"] is True
    assert (home / "models" / "locks" / "basicpitch.txt").read_text() == "numpy==1.26.4\ntensorflow==2.14.0\n"
    bad = models_cmd.record_lock(home, "x", "py", lambda argv, **kw: subprocess.CompletedProcess(argv, 1, stdout=""))
    assert bad is False and not (home / "models" / "locks" / "x.txt").exists()


def test_loop_probe_chains_generate_measure_and_brain(tmp_path):
    from coproducer.result import ok, fail
    seen = []

    def fake(name, **kw):
        seen.append(name)
        return {"generate_audio": lambda: ok({"paths": [str(tmp_path / "a.wav")]}),
                "build_measure_report": lambda: ok({"loudness": {"lufs": -20.0}}),
                "estimate_bpm_dsp": lambda: ok({"bpm": 128.2, "candidates": [{"bpm": 128.2, "strength": 0.5}], "matched_hint": True}),
                "estimate_key_dsp": lambda: ok({"key": "A minor"}),
                "critique_audio": lambda: ok({"text": "The kick is buried.", "source": "model"}),
                "call_agent_llm": lambda: ok({"message": {"content": "", "tool_calls": [{"function": {"name": "adjust_master_gain", "arguments": "{\"db\": 5}"}}]}})}[name]()

    res = probe_cmd.loop(fake, tmp_path)
    assert res["passed"] and seen == ["generate_audio", "build_measure_report", "estimate_bpm_dsp", "estimate_key_dsp", "critique_audio", "call_agent_llm"]
    assert res["listener_notes"] == "The kick is buried." and res["steps"]["listen"]["source"] == "model"
    assert res["proposals"][0]["name"] == "adjust_master_gain" and res["steps"]["tempo"]["measured"] == 128.2
    stopped = probe_cmd.loop(lambda name, **kw: fail("E_GPU_BUDGET", "full"), tmp_path)
    assert not stopped["passed"] and list(stopped["steps"]) == ["generate"]


def test_proposals_are_checked_against_the_tool_schema():
    tools = probe_cmd._LOOP_TOOLS
    assert probe_cmd.check_proposal({"name": "adjust_eq_band", "arguments": '{"band":"low","db":3}'}, tools)["valid"] is True
    bad = probe_cmd.check_proposal({"name": "adjust_eq_band", "arguments": '{"band":"high_mid","db":6}'}, tools)
    assert bad["valid"] is False and "high_mid" in bad["problem"]
    assert probe_cmd.check_proposal({"name": "adjust_master_gain", "arguments": "not json"}, tools)["valid"] is False
    assert probe_cmd.check_proposal({"name": "delete_everything", "arguments": "{}"}, tools)["problem"] == "no such tool"


class _ApplyWorld:
    """A fake pipeline for probe_cmd.apply: the master fader changes the loudness of the next render."""
    def __init__(self, tmp_path, proposal='{"db": 20}', louder_by=None, silent_brain=False):
        self.db, self.saved_db, self.renders, self.calls = 0.0, 0.0, 0, []
        self.proposal, self.louder_by, self.silent_brain, self.tmp = proposal, louder_by, silent_brain, tmp_path

    def __call__(self, name, **kw):
        from coproducer.result import ok
        self.calls.append(name)
        if name == "render_with_restart":
            self.renders += 1
            return ok({"path": str(self.tmp / ("r%d.wav" % self.renders)), "bridge_back_s": 1.0})
        if name == "build_measure_report":
            n = int(kw["path"].split("r")[-1].split(".")[0])
            return ok({"loudness": {"lufs": -30.0 + (self.saved_db if n > 1 else 0.0)}})
        if name == "op_mixer_get_track_volume":
            return ok(self.db)
        if name == "call_agent_llm":
            calls = [] if self.silent_brain else [{"function": {"name": "adjust_master_gain", "arguments": self.proposal}}]
            return ok({"message": {"content": "", "tool_calls": calls}, "finish_reason": "stop", "usage": {}})
        if name == "apply_gain_trim":
            step = max(-kw["max_delta_db"], min(kw["max_delta_db"], kw["delta_db"]))
            self.db += step
            return ok({"applied_delta_db": step})
        if name == "save_sandbox_project":
            self.saved_db = self.db if self.louder_by is None else self.louder_by
            return ok({"path": "p"})
        if name == "set_track_volume_db_verified":
            self.db = kw["db"]
            return ok(kw["db"])
        raise AssertionError(name)


def test_apply_probe_applies_saves_remeasures_and_restores(tmp_path):
    w = _ApplyWorld(tmp_path)
    res = probe_cmd.apply(w, tmp_path / "p.flp", tmp_path)
    assert res["passed"] and res["closes_the_loop"] and res["loudness"]["applied_db"] == 6.0 and res["loudness"]["moved_lu"] == 6.0
    assert w.db == 0.0 and w.calls[-1] == "save_sandbox_project" and w.calls.count("save_sandbox_project") == 2


def test_apply_probe_reports_a_change_the_audio_did_not_follow(tmp_path):
    w = _ApplyWorld(tmp_path, louder_by=1.0)
    res = probe_cmd.apply(w, tmp_path / "p.flp", tmp_path)
    assert not res["passed"] and res["closes_the_loop"] is False and w.db == 0.0      # fader restored either way


def test_apply_probe_stops_when_the_model_makes_no_valid_call(tmp_path):
    for kw in ({"silent_brain": True}, {"proposal": '{"db": 99}'}):
        w = _ApplyWorld(tmp_path, **kw)
        res = probe_cmd.apply(w, tmp_path / "p.flp", tmp_path)
        assert not res["passed"] and "apply" not in res["steps"] and w.db == 0.0


def test_critique_stack_downloads_weights_and_weights_only_touches_nothing_else(home):
    cfg = load_config(home)
    plan = stacks.install_plan("critique", home, cfg)
    assert "hf_hub_download" in plan["commands"][-1][0][2] and "nvidia/music-flamingo-2601-hf" in plan["commands"][-1][0][2] and "model.safetensors" in plan["commands"][-1][0][2]
    assert stacks.weights_command("basicpitch", home, cfg) is None
    assert "955717e8-8726e21a.th" in stacks.weights_command("demucs", home, cfg)[2]    # demucs checkpoints are pinned files now (2026-10-25)
    calls = []
    run = lambda argv, cwd=None, **kw: calls.append(argv) or subprocess.CompletedProcess(argv, 0)  # noqa: E731
    rows = models_cmd.install(home, ["critique", "basicpitch"], False, run, weights_only=True)
    assert len(calls) == 1 and "snapshot_download" in calls[0][2] and "openai/whisper-large-v3" in calls[0][2]   # Whisper; the 16 GB critic is optional
    calls.clear()
    models_cmd.install(home, ["critique"], False, run, weights_only=True, with_optional=True)
    assert len(calls) == 2 and "hf_hub_download" in calls[1][2]
    calls.clear()
    rows = models_cmd.install(home, ["critique", "basicpitch"], False, run, weights_only=True)
    assert rows["critique"]["status"] == "installed" and rows["basicpitch"]["status"] == "planned"
    assert "critique" not in load_config(home)["envs"]


def test_critique_probe_reports_the_source_and_why_the_model_was_not_used(rig, tmp_path):
    from coproducer.models.factory import make_worker_factory
    from coproducer.models.scheduler import Scheduler
    from coproducer.models.spec import load_registry
    from coproducer.services import set_service
    set_service("sandbox_root", str(tmp_path))
    set_service("scheduler", Scheduler(load_registry(REPO / "models" / "registry.toml"), make_worker_factory({}), lambda: (16000, 16000)))
    rig.reg.approver = lambda name, kwargs: True
    res = probe_cmd.critique(rig.call, Path(probe_cmd._mixture(str(tmp_path / "mix.wav"))))
    assert res["source"] == "dsp" and res["passed"] is False and res["text"] and res["fallback"]


def test_gain_direction_check_rejects_the_wrong_sign_and_allows_the_dead_zone():
    ok_ = probe_cmd.gain_direction_ok
    assert ok_(-0.5, -15.81) is False and ok_(1.8, -15.81) is True
    assert ok_(3.0, -10.0) is False and ok_(-3.0, -10.0) is True
    assert ok_(-2.0, -14.2) is True and ok_(2.0, -13.8) is True            # within half a dB of the target either way


def test_listen_probe_renders_listens_and_flags_a_wrong_direction_gain(tmp_path):
    from coproducer.result import ok
    seen = []

    def fake(name, **kw):
        seen.append(name)
        return {"render_with_restart": lambda: ok({"path": str(tmp_path / "r.wav")}),
                "build_measure_report": lambda: ok({"loudness": {"lufs": -15.8}}),
                "estimate_bpm_dsp": lambda: ok({"bpm": 126.0, "candidates": []}),
                "estimate_key_dsp": lambda: ok({"key": "A minor"}),
                "critique_audio": lambda: ok({"text": "thin", "source": "model"}),
                "call_agent_llm": lambda: ok({"message": {"tool_calls": [{"function": {"name": "adjust_master_gain", "arguments": "{\"db\": -0.5}"}}]}})}[name]()

    res = probe_cmd.listen(fake, tmp_path / "p.flp", tmp_path)
    assert res["passed"] and seen[0] == "render_with_restart" and res["proposals"][0]["direction_ok"] is False
    assert res["listener_notes"] == "thin"


def test_install_fl_side_empty_data_dir_uses_fl_folder(tmp_path, monkeypatch):
    """An empty [fl] data_dir must mean FL's own user data folder, not the current folder (it once landed in C:\\coproducer\\Settings)."""
    from coproducer.cli import detect
    from coproducer.cli.setup_cmd import install_fl_side
    home = tmp_path / "repo"
    (home / "fl_side").mkdir(parents=True)
    (home / "fl_side" / "device_coproducer.py").write_text("# script\n", encoding="utf-8")
    fl_data = tmp_path / "Image-Line" / "FL Studio"
    monkeypatch.setattr(detect, "fl_data_dir", lambda home=None: fl_data)
    for empty in (None, "", "."):
        dst = Path(install_fl_side(home, empty))
        assert fl_data in dst.parents and dst.name == "device_coproducer.py"


def test_a_machine_without_git_gets_the_pinned_commit_as_an_archive(home, monkeypatch):
    """The one-command installer runs on machines with no git (2026-10-26): clone stacks download GitHub's archive of the commit."""
    cfg = load_config(home)
    monkeypatch.setattr(stacks.shutil, "which", lambda name: None)
    plan = stacks.install_plan("serummcp", home, cfg)
    argv = plan["commands"][0][0]
    assert argv[-2] == "https://codeload.github.com/Celian-mrc/serum-mcp/zip/" + stacks.STACKS["serummcp"]["commit"] and argv[-1].endswith("serum-mcp")
    assert plan["commands"][-1][0] == ["uv", "sync", "--locked"] and not any(a[0] == "git" for a, _ in plan["commands"])
    (home / "sandbox" / "third_party" / "serum-mcp").mkdir(parents=True)          # unpacked from the archive: no .git, so no checkout
    assert [a for a, _ in stacks.install_plan("serummcp", home, cfg)["commands"]] == [["uv", "sync", "--locked"]]
    assert stacks.zip_url({"clone": "https://github.com/ACE-Step/ACE-Step-1.5.git", "commit": "abc"}) == "https://codeload.github.com/ACE-Step/ACE-Step-1.5/zip/abc"


def test_mir_snapshots_are_optional_and_whisper_is_not(home):
    cfg = load_config(home)
    mir, crit = stacks.install_plan("mir", home, cfg), stacks.install_plan("critique", home, cfg)
    assert len(mir["optional"]) == 1 and "MuQ-MuLan" in mir["commands"][mir["optional"][0]][0][2]
    crit_opt = [crit["commands"][i][0][2] for i in crit["optional"]]
    assert len(crit_opt) == 1 and "music-flamingo" in crit_opt[0]
    assert any("whisper-large-v3" in a[2] for a, _ in crit["commands"] if len(a) > 2 and isinstance(a[2], str))


def test_doctor_reads_the_desktop_config_desktop_uses(home, tmp_path):
    from coproducer.cli import desktop_cmd as D
    cfg = tmp_path / "claude_desktop_config.json"
    assert doctor.check_desktop(home, cfg)["status"] == "warn"                     # nothing registered yet
    D.install(home, config=cfg, python=sys.executable)
    row = doctor.check_desktop(home, cfg)
    assert row["status"] == "ok" and "3 in" in row["detail"]
    data = json.loads(cfg.read_text())
    data["mcpServers"]["coproducer-fl-bridge"]["command"] = str(tmp_path / "gone" / "python.exe")
    cfg.write_text(json.dumps(data))
    assert doctor.check_desktop(home, cfg)["status"] == "fail"
    D.install(tmp_path / "elsewhere", config=cfg, python=sys.executable)
    row = doctor.check_desktop(home, cfg)
    assert row["status"] == "fail" and "not this install" in row["detail"]
    cfg.write_text("{")
    assert doctor.check_desktop(home, cfg)["status"] == "fail"


def test_doctor_checks_the_midi_registry_setup_midi_writes():
    from coproducer.cli import midi_setup as M
    reg = {(k, n): v for k, n, _, v in M.plan(["FL Studio 26"])}
    rows = doctor.check_midi_settings(lambda k, n: reg.get((k, n)), ["FL Studio 26"])
    assert [r["status"] for r in rows] == ["ok", "ok"]
    del reg[(M.LOOPMIDI_KEY + "\\Ports", "coproducer-out")]
    reg[("%s\\FL Studio 26\\Devices\\MIDI input\\coproducer-in" % M.FL_KEY, "Enabled")] = "0"
    rows = doctor.check_midi_settings(lambda k, n: reg.get((k, n)), ["FL Studio 26"])
    assert [r["status"] for r in rows] == ["fail", "fail"] and "coproducer-out" in rows[0]["detail"] and "Enabled" in rows[1]["detail"]
    assert doctor.check_midi_settings(lambda k, n: None, [])[1]["status"] == "warn"


def test_installed_tools_go_first_on_path_once(tmp_path):
    from coproducer.cli import use_installed_tools
    (tmp_path / "runtime" / "uv").mkdir(parents=True)
    (tmp_path / "runtime" / "ffmpeg" / "bin").mkdir(parents=True)
    (tmp_path / "runtime" / "python").mkdir()
    env = {"PATH": "/usr/bin"}
    assert len(use_installed_tools(tmp_path, env)) == 2 and env["PATH"].split(os.pathsep)[0] == str(tmp_path / "runtime" / "uv")
    assert use_installed_tools(tmp_path, env) == [] and env["PATH"].count("ffmpeg") == 1
    assert env["UV_PYTHON_INSTALL_DIR"] == str(tmp_path / "runtime" / "python") and env["UV_MANAGED_PYTHON"] == "1"
    assert use_installed_tools(tmp_path / "none", {"PATH": "x"}) == []


def test_setup_records_what_the_installer_detected(home, tmp_path):
    setup_cmd.run_setup(home, "", str(tmp_path / "FLdata"))
    m = tmp_path / "M"
    assert setup_cmd.apply_settings(home, "https://download.pytorch.org/whl/cu128", str(m)) == [
        "gpu.torch_index = https://download.pytorch.org/whl/cu128", "paths.models = %s" % m.as_posix(), "paths.weights = %s" % (m / "weights").as_posix()]
    cfg = load_config(home)
    assert cfg["gpu"]["torch_index"].endswith("cu128") and Path(cfg["paths"]["models"]) == m and cfg["fl"]["data_dir"]
    assert setup_cmd.apply_settings(home, "https://download.pytorch.org/whl/cu128", str(m)) == []          # nothing changes the second time
    a = build_parser().parse_args(["setup", "--no-desktop", "--torch-index", "", "--models-dir", "D:/m"])
    assert a.torch_index == "" and a.models_dir == "D:/m"


def test_acestep_checkpoints_are_optional_downloads_after_the_sync(home):
    p = stacks.install_plan("acestep", home, load_config(home))
    assert p["commands"][2][0] == ["uv", "sync", "--locked"] and len(p["optional"]) == 2
    assert all(p["commands"][i][0][:4] == ["uv", "run", "--locked", "acestep-download"] for i in p["optional"])
