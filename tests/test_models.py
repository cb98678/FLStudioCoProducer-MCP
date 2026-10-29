"""Worker protocol, scheduler decisions, registry data and the runners' pure helpers."""
import sys
from pathlib import Path

import pytest

from coproducer.config import load_config, merge, render_config
from coproducer.models.factory import make_worker_factory, python_for
from coproducer.models.scheduler import Scheduler
from coproducer.models.spec import ModelSpec, load_registry
from coproducer.models.vram import parse_nvidia_smi
from coproducer.models.worker import Worker
from coproducer.runners import acestep_runner, basicpitch_runner, critique_runner, demucs_runner
from coproducer.runners.runner_common import error_code, run_one

ROOT = Path(__file__).resolve().parents[1]
FAKE = str(ROOT / "src" / "coproducer" / "runners" / "fake_runner.py")


@pytest.fixture
def worker():
    w = Worker([sys.executable, FAKE])
    yield w
    w.stop()


def test_worker_round_trip_and_error_mapping(worker, tmp_path):
    assert worker.call("ping").value == "pong"
    r = worker.call("separate", {"out_dir": str(tmp_path)})
    assert r.ok and sorted(r.value["stems"]) == ["bass", "drums", "other", "vocals"] and Path(r.value["stems"]["drums"]).stat().st_size > 100
    assert worker.call("nope").error.code == "E_NOT_FOUND"
    assert worker.call("oom").error.code == "E_GPU_BUDGET"
    bad = worker.call("bad")
    assert bad.error.code == "E_ARG" and bad.error.detail == {"field": "x"}
    assert worker.call("ping").value == "pong"            # still alive after errors


def test_worker_timeout_kills_and_restarts(worker):
    first = worker.call("load", {"variant": "a"}).value["pid"]
    slow = worker.call("sleep", {"seconds": 5}, timeout_s=0.5)
    assert slow.error.code == "E_TIMEOUT" and slow.error.retryable and not worker.alive()
    assert worker.call("load", {"variant": "a"}).value["pid"] != first


def test_worker_survives_a_runner_crash_with_a_clear_error(worker):
    worker.call("ping")
    r = worker.call("crash", timeout_s=2)
    assert not r.ok and r.error.code == "E_TIMEOUT"
    assert worker.call("ping").value == "pong"


def test_worker_reports_a_missing_runner():
    r = Worker(["definitely-not-a-program-xyz"]).call("ping")
    assert r.error.code == "E_MODEL"


def specs():
    return {n: ModelSpec(n, "test", "test", vram_typical_mb=mb, default_variant="v1", runner="fake_runner.py")
            for n, mb in (("a", 6000), ("b", 6000), ("c", 6000), ("tiny", 0))}


def sched(free_total=16000, log=None):
    s = Scheduler(specs(), make_worker_factory({}), lambda: (free_total - sum(r.need_mb for r in s.resident.values()), free_total), ledger=log)
    return s


def test_scheduler_loads_reuses_and_evicts_least_recently_used():
    s = sched()
    try:
        assert s.load("a").ok and s.load("b").ok
        assert s.load("a").value["already_loaded"] is True
        assert s.load("c").ok                                   # needs 6000, only 4000 free: evicts b (older use than a)
        assert sorted(s.resident) == ["a", "c"]
    finally:
        s.unload_all()


def test_scheduler_refuses_what_cannot_fit_and_prefers_keeping_phase_models():
    s = sched(free_total=7000)
    try:
        s.phase_hints = {"P1": ("a",)}
        s.phase = "P1"
        assert s.load("a").ok
        r = s.load("b")                                         # a is wanted in this phase but b still needs the room
        assert r.ok and "a" not in s.resident                   # only one model fits at all
        big = Scheduler({"huge": ModelSpec("huge", "test", "test", vram_typical_mb=20000, runner="fake_runner.py")},
                        make_worker_factory({}), lambda: (7000, 7000))
        e = big.load("huge")
        assert e.error.code == "E_GPU_BUDGET" and e.error.detail["need_mb"] == 20000
        assert s.load("nope").error.code == "E_NOT_FOUND"
    finally:
        s.unload_all()


def test_scheduler_call_loads_on_demand_and_logs(tmp_path):
    from coproducer.orchestrator.ledger import Ledger
    log = Ledger(tmp_path / "l.jsonl")
    s = sched(log=log)
    try:
        assert s.run_op("tiny", "ping", {}).value == "pong"
        s.unload("tiny")
        kinds = [e["type"] for e in log.entries()]
        assert kinds == ["model_load", "model_unload"]
        assert s.status()["resident"] == {}
    finally:
        s.unload_all()


def test_missing_environment_gives_a_plain_error():
    s = Scheduler({"x": ModelSpec("x", "separate", "demucs")}, make_worker_factory({}), lambda: (16000, 16000))
    r = s.load("x")
    assert r.error.code == "E_MODEL" and "coproducer setup" in r.error.message
    assert python_for(ModelSpec("x", "separate", "demucs"), {"envs": {"demucs": "py.exe"}}) == "py.exe"


def test_real_registry_file_parses_and_has_the_expected_models():
    reg = load_registry(ROOT / "models" / "registry.toml")
    assert {"acestep", "demucs", "basicpitch", "flamingo", "vision"} <= set(reg)
    assert reg["flamingo"].optional and reg["flamingo"].fallback == "critique_audio_dsp"
    assert reg["acestep"].vram_typical_mb == 12 * 1024 and "turbo+lm0.6B" in reg["acestep"].variants
    assert reg["basicpitch"].vram_typical_mb == 0


def test_registry_rejects_a_malformed_entry(tmp_path):
    f = tmp_path / "r.toml"
    f.write_text('[models.x]\nrole = "nonsense"\nstack = "s"\n')
    with pytest.raises(ValueError):
        load_registry(f)


def test_nvidia_smi_parsing():
    assert parse_nvidia_smi("11234, 16376\n") == (11234, 16376)
    assert parse_nvidia_smi("No devices were found") is None
    assert parse_nvidia_smi("") is None


def test_config_defaults_merge_and_render(tmp_path):
    assert load_config(tmp_path)["midi"]["out"] == "coproducer-in"
    (tmp_path / "config.toml").write_text('[envs]\ndemucs = "C:/x/python.exe"\n[gpu]\nbudget_mb = 12000\n')
    cfg = load_config(tmp_path)
    assert cfg["envs"]["demucs"] == "C:/x/python.exe" and cfg["gpu"]["budget_mb"] == 12000 and cfg["midi"]["in"] == "coproducer-out"
    again = tmp_path / "again"
    again.mkdir()
    (again / "config.toml").write_text(render_config(cfg))
    assert load_config(again) == cfg
    assert merge({"a": {"b": 1}}, {"a": {"c": 2}}) == {"a": {"b": 1, "c": 2}}


# ---------------------------------------------------------------- runners' pure helpers
def test_runner_error_mapping():
    assert run_one(None, "x", 1, {})["error"]["code"] == "E_NOT_FOUND"
    assert error_code(RuntimeError("CUDA out of memory")) == "E_GPU_BUDGET" and error_code(ValueError("x")) == "E_MODEL"
    assert run_one(lambda a: (_ for _ in ()).throw(SystemExit(2)), "x", 1, {})["error"]["code"] == "E_MODEL"


def test_demucs_helpers(tmp_path):
    assert demucs_runner.build_args("in.wav", "out", "htdemucs", "vocals", "cpu") == \
        ["-n", "htdemucs", "-o", "out", "--int24", "--two-stems", "vocals", "-d", "cpu", "in.wav"]
    folder = tmp_path / "htdemucs" / "song"
    folder.mkdir(parents=True)
    for n in ("drums", "bass", "other", "vocals"):
        (folder / (n + ".wav")).write_bytes(b"x")
    assert sorted(demucs_runner.find_stems(str(tmp_path), "htdemucs", "song")) == ["bass", "drums", "other", "vocals"]
    with pytest.raises(demucs_runner.RunnerError):
        demucs_runner.find_stems(str(tmp_path), "htdemucs", "other_song")


def test_basicpitch_converts_events():
    ev = [(0.5, 1.0, 64, 0.5, None), (0.0, 0.5, 60, 1.4, [1, 2])]
    assert basicpitch_runner.to_notes(ev) == [{"start": 0.0, "end": 0.5, "pitch": 60, "velocity": 1.0},
                                              {"start": 0.5, "end": 1.0, "pitch": 64, "velocity": 0.5}]


def test_acestep_variants_and_params():
    assert acestep_runner.parse_variant("turbo+lm0.6B") == ("acestep-v15-turbo", "acestep-5Hz-lm-0.6B", "turbo")
    assert acestep_runner.parse_variant("sft") == ("acestep-v15-sft", None, "sft")
    with pytest.raises(acestep_runner.RunnerError):
        acestep_runner.parse_variant("huge+lm9B")
    p = acestep_runner.build_params({"prompt": "dubstep", "duration": 20, "bpm": 140, "key": "F minor", "seed": 7}, "turbo", True)
    assert p["shift"] == 3.0 and p["inference_steps"] == 8 and p["bpm"] == 140 and p["keyscale"] == "F minor" and p["thinking"] is True
    cover = acestep_runner.build_params({"task_type": "cover", "src_audio": "a.wav", "strength": 0.4}, "sft", True)
    assert cover["audio_cover_strength"] == 0.4 and cover["thinking"] is False and "shift" not in cover
    rp = acestep_runner.build_params({"task_type": "repaint", "src_audio": "a.wav", "start_s": 4, "end_s": 8}, "sft", False)
    assert (rp["repainting_start"], rp["repainting_end"]) == (4.0, 8.0)


def test_critique_conversation_shape():
    c = critique_runner.build_conversation("a.wav", "")
    assert c[0]["content"][1] == {"type": "audio", "path": "a.wav"} and "low end" in c[0]["content"][0]["text"]


def test_scheduler_releases_the_external_brain_when_memory_is_short():
    free = {"mb": 5000}
    released = []

    def release():
        released.append(1)
        free["mb"] = 20000
        return True

    s = Scheduler({"big": ModelSpec("big", "test", "test", vram_typical_mb=12000, runner="fake_runner.py")}, make_worker_factory({}),
                  lambda: (free["mb"], 24000), release_external=release, settle_s=0)
    try:
        assert s.load("big").ok and released == [1]
    finally:
        s.unload_all()


def test_an_external_release_is_written_to_the_real_ledger(tmp_path):
    """Measured 2026-10-20: the scheduler logged external_release, the ledger refused the type, and critique_audio crashed instead of falling back."""
    from coproducer.orchestrator.ledger import Ledger
    free = {"mb": 2000}

    def release():
        free["mb"] = 20000
        return True

    led = Ledger(tmp_path / "ledger.jsonl")
    s = Scheduler({"big": ModelSpec("big", "test", "test", vram_typical_mb=12000, runner="fake_runner.py")}, make_worker_factory({}),
                  lambda: (free["mb"], 24000), ledger=led, release_external=release, settle_s=0)
    try:
        assert s.load("big").ok
    finally:
        s.unload_all()
    assert "external_release" in [e["type"] for e in led.entries()]


def test_scheduler_still_refuses_when_the_release_frees_nothing():
    s = Scheduler({"big": ModelSpec("big", "test", "test", vram_typical_mb=12000, runner="fake_runner.py")}, make_worker_factory({}),
                  lambda: (5000, 24000), release_external=lambda: True, settle_s=0)
    assert s.load("big").error.code == "E_GPU_BUDGET"
    s2 = Scheduler({"big": ModelSpec("big", "test", "test", vram_typical_mb=12000, runner="fake_runner.py")}, make_worker_factory({}),
                   lambda: (5000, 24000), release_external=lambda: False, settle_s=0)
    assert s2.load("big").error.code == "E_GPU_BUDGET"


def test_ollama_unload_posts_keep_alive_zero():
    import json as _json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from coproducer import ollama
    seen = {}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["path"], seen["body"] = self.path, _json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        assert ollama.unload("http://127.0.0.1:%d/v1" % srv.server_port, "gemma4:12b")
    finally:
        srv.shutdown()
    assert seen == {"path": "/api/generate", "body": {"model": "gemma4:12b", "keep_alive": 0}}
    assert ollama.native_base("http://h:1/v1/") == "http://h:1"
    assert not ollama.unload("http://127.0.0.1:9/v1", "x", timeout_s=1) and not ollama.unload("", "x")


def test_acestep_worker_reads_checkpoints_from_its_clone_not_the_current_folder(tmp_path, monkeypatch):
    monkeypatch.delenv("ACESTEP_HOME", raising=False)
    py = tmp_path / "models" / "acestep" / ".venv" / "Scripts" / "python.exe"
    w = make_worker_factory({"envs": {"acestep": str(py)}})(ModelSpec("acestep", "generate", "acestep"))
    assert w.env["ACESTEP_HOME"] == str((tmp_path / "models" / "acestep").resolve())
    other = make_worker_factory({"envs": {"demucs": str(py)}})(ModelSpec("demucs", "separate", "demucs"))
    assert "ACESTEP_HOME" not in other.env
