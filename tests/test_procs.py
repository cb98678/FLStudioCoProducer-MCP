import subprocess

from coproducer import procs


def test_counts_closes_and_launches_fl(monkeypatch, tmp_path):
    state = {"running": 1, "calls": []}

    def run(argv, **kw):
        state["calls"].append(argv[0])
        if argv[0] == "taskkill":
            state["running"] = 0
        out = '"FL64.exe","1234","Console","1","300,000 K"\n' * state["running"] or "INFO: No tasks are running which match the specified criteria.\n"
        return subprocess.CompletedProcess(argv, 0, stdout=out)

    monkeypatch.setattr(procs.subprocess, "run", run)
    p = procs.Procs()
    assert p.fl_count() == 1 and p.close_fl(timeout_s=2) is True and p.fl_count() == 0 and "taskkill" in state["calls"]
    assert "/F" not in " ".join(state["calls"])
    seen = {}
    monkeypatch.setattr(procs.subprocess, "Popen", lambda argv, **kw: seen.update(argv=argv))
    monkeypatch.chdir(tmp_path)
    p.launch("C:/fl/FL64.exe", "sub/p.flp")
    assert seen["argv"] == ["C:/fl/FL64.exe", str((tmp_path / "sub" / "p.flp").resolve())]


def test_close_reports_a_copy_that_would_not_close(monkeypatch):
    monkeypatch.setattr(procs.subprocess, "run", lambda argv, **kw: subprocess.CompletedProcess(argv, 0, stdout='"FL64.exe","1","Console","1","1 K"\n'))
    assert procs.Procs().close_fl(timeout_s=0.6) is False
