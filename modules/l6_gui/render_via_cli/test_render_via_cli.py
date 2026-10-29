import sys

from coproducer.services import set_service
from coproducer.testrig import runnable

FAKE = """#!{py}
import sys, numpy as np, soundfile as sf
out = [a[2:] for a in sys.argv if a.startswith("/O")][0]
mode = "{mode}"
t = np.arange(48000) / 48000
x = (0.3 * np.sin(2 * np.pi * 220 * t)) if mode == "tone" else np.zeros(48000)
if mode != "none":
    sf.write(out + "/render.wav", x, 48000)
sys.exit(3 if mode == "fail" else 0)
"""


def fake_exe(tmp_path, mode):
    f = tmp_path / ("fl_" + mode + ".py")
    f.write_text(FAKE.format(py=sys.executable, mode=mode))
    set_service("fl_exe", str(runnable(f)))


def test_renders_with_fake_exe(rig, desk, tmp_path):
    (tmp_path / "p.flp").write_bytes(b"FLhd")
    fake_exe(tmp_path, "tone")
    r = rig.call("render_via_cli", project=str(tmp_path / "p.flp"), out_dir=str(tmp_path / "out"))
    assert r.ok and r.value["path"].endswith("render.wav") and r.meta["verified"] is True


def test_errors(rig, desk, tmp_path):
    (tmp_path / "p.flp").write_bytes(b"FLhd")
    proj = str(tmp_path / "p.flp")
    fake_exe(tmp_path, "tone")
    assert rig.call("render_via_cli", project="/elsewhere/p.flp", out_dir=str(tmp_path / "o")).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("render_via_cli", project=str(tmp_path / "gone.flp"), out_dir=str(tmp_path / "o")).error.code == "E_NOT_FOUND"
    for mode, code in (("silent", "E_NOT_VERIFIED"), ("fail", "E_IO"), ("none", "E_IO")):
        fake_exe(tmp_path, mode)
        assert rig.call("render_via_cli", project=proj, out_dir=str(tmp_path / ("out_" + mode))).error.code == code, mode
    set_service("fl_exe", None)
    assert rig.call("render_via_cli", project=proj, out_dir=str(tmp_path / "o2")).error.code == "E_UNSUPPORTED_API"


def test_relative_paths_are_made_absolute_for_fl(rig, desk, tmp_path, monkeypatch):
    seen = tmp_path / "seen.txt"
    exe = tmp_path / "fl_abs.py"
    exe.write_text("#!%s\nimport sys, numpy as np, soundfile as sf\nout=[a[2:] for a in sys.argv if a.startswith('/O')][0]\nopen(%r,'w').write(out+'|'+sys.argv[-1])\nt=np.arange(48000)/48000\nsf.write(out+'/r.wav',0.3*np.sin(2*np.pi*220*t),48000)\n" % (sys.executable, str(seen)))
    set_service("fl_exe", str(runnable(exe)))
    (tmp_path / "p.flp").write_bytes(b"FLhd")
    monkeypatch.chdir(tmp_path)
    r = rig.call("render_via_cli", project="p.flp", out_dir="out")
    out, proj = seen.read_text().split("|")
    assert r.ok and out == str(tmp_path / "out") and proj == str(tmp_path / "p.flp")


def test_refuses_while_fl_runs_or_its_state_is_unknown(rig, desk, procs, tmp_path):
    (tmp_path / "p.flp").write_bytes(b"FLhd")
    fake_exe(tmp_path, "tone")
    r = rig.call("render_via_cli", project=str(tmp_path / "p.flp"), out_dir=str(tmp_path / "out"))
    assert r.error.code == "E_PENDING_HUMAN" and not (tmp_path / "out").exists() and procs.log == []
    procs.fl_count = lambda: -1                     # tasklist failed: treated as running
    assert rig.call("render_via_cli", project=str(tmp_path / "p.flp"), out_dir=str(tmp_path / "out")).error.code == "E_PENDING_HUMAN"
    procs.open = False
    del procs.fl_count
    assert rig.call("render_via_cli", project=str(tmp_path / "p.flp"), out_dir=str(tmp_path / "out")).ok
