import sys

from coproducer.services import set_service
from coproducer.testrig import runnable

FAKE = """#!{py}
import sys, numpy as np, soundfile as sf
out = [a[2:] for a in sys.argv if a.startswith("/O")][0]
t = np.arange(48000) / 48000
sf.write(out + "/render.wav", 0.3 * np.sin(2 * np.pi * 220 * t), 48000)
"""


def _setup(tmp_path, procs):
    exe = tmp_path / "fl.py"
    exe.write_text(FAKE.format(py=sys.executable))
    set_service("fl_exe", str(runnable(exe)))
    (tmp_path / "p.flp").write_bytes(b"FLhd")
    return str(tmp_path / "p.flp"), str(tmp_path / "out")


def test_closes_renders_restarts_and_reconnects(rig, desk, procs, tmp_path):
    project, out = _setup(tmp_path, procs)
    assert rig.call("render_with_restart", project=project, out_dir=out, wait_s=5).error.code == "E_AUTONOMY" and procs.log == []  # A1: asks first
    rig.reg.approver = lambda name, kw: name == "render_with_restart"
    r = rig.call("render_with_restart", project=project, out_dir=out, wait_s=5)
    assert r.ok and r.value["restarted"] is True and r.value["path"].endswith("render.wav") and r.meta["verified"] is True
    assert procs.log[0] == "close" and procs.log[1][0] == "launch" and procs.log[1][2] == project and procs.open


def test_refusals_leave_fl_alone(rig, desk, procs, tmp_path):
    project, out = _setup(tmp_path, procs)
    rig.reg.approver = lambda name, kw: name == "render_with_restart"
    assert rig.call("render_with_restart", project="/elsewhere/p.flp", out_dir=out).error.code == "E_SANDBOX_VIOLATION"
    rig.fake.changed = True
    assert rig.call("render_with_restart", project=project, out_dir=out).error.code == "E_NOT_VERIFIED" and procs.log == []
    rig.fake.changed = False
    procs.stuck = True
    assert rig.call("render_with_restart", project=project, out_dir=out).error.code == "E_BLOCKED_BY_DIALOG" and procs.log == ["close"]
    set_service("procs", None)
    assert rig.call("render_with_restart", project=project, out_dir=out).error.code == "E_UNSUPPORTED_API"
