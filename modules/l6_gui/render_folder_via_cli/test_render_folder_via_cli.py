import sys

from coproducer.services import set_service
from coproducer.testrig import runnable

FAKE = """#!{py}
import sys, pathlib, numpy as np, soundfile as sf
a = {{x[:2]: x[2:].strip('"') for x in sys.argv[1:] if x[:2] in ("/O", "/F")}}
t = np.arange(48000) / 48000
for p in sorted(pathlib.Path(a["/F"]).glob("*.flp")):
    if "{skip}" and "{skip}" in p.name:
        continue
    sf.write(a["/O"] + "/" + p.stem + ".wav", (0.3 * np.sin(2 * np.pi * 220 * t)) * (0 if "quiet" in p.name else 1), 48000)
sys.exit({code})
"""


def fake_exe(tmp_path, skip="", code=0):
    f = tmp_path / "fl_folder.py"
    f.write_text(FAKE.format(py=sys.executable, skip=skip, code=code))
    set_service("fl_exe", str(runnable(f)))


def test_renders_each_project(rig, desk, tmp_path):
    d = tmp_path / "solos"
    d.mkdir()
    for n in ("a__t01_kick", "a__t02_clap"):
        (d / (n + ".flp")).write_bytes(b"FLhd")
    fake_exe(tmp_path)
    r = rig.call("render_folder_via_cli", folder=str(d), out_dir=str(tmp_path / "out"))
    assert r.ok and r.meta["verified"] is True and {x["project"] for x in r.value["rendered"]} == {"a__t01_kick.flp", "a__t02_clap.flp"}
    assert all(x["written"] and not x["silent"] for x in r.value["rendered"])


def test_errors(rig, desk, tmp_path):
    d = tmp_path / "solos"
    d.mkdir()
    (d / "a.flp").write_bytes(b"FLhd")
    (d / "b.flp").write_bytes(b"FLhd")
    fake_exe(tmp_path, skip="b")
    part = rig.call("render_folder_via_cli", folder=str(d), out_dir=str(tmp_path / "o1"))
    assert part.ok and part.value["missing"] == ["b.flp"] and part.meta["verified"] is False
    fake_exe(tmp_path, code=3)
    assert rig.call("render_folder_via_cli", folder=str(d), out_dir=str(tmp_path / "o2")).error.code == "E_IO"
    assert rig.call("render_folder_via_cli", folder="/elsewhere/x", out_dir=str(tmp_path / "o3")).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("render_folder_via_cli", folder=str(tmp_path / "none"), out_dir=str(tmp_path / "o4")).error.code == "E_NOT_FOUND"
    set_service("fl_exe", None)
    assert rig.call("render_folder_via_cli", folder=str(d), out_dir=str(tmp_path / "o5")).error.code == "E_UNSUPPORTED_API"


def test_a_stalled_render_is_stopped_and_trial_plugins_are_refused(rig, desk, tmp_path):
    import struct
    import time

    from coproducer import flpfile as F
    from coproducer import testflp

    d = tmp_path / "solos"
    d.mkdir()
    (d / "a.flp").write_bytes(b"FLhd")
    hang = tmp_path / "fl_hang.py"
    hang.write_text("#!%s\nimport time\ntime.sleep(60)\n" % sys.executable)  # FL waiting on a dialog: no WAV ever appears
    set_service("fl_exe", str(runnable(hang)))
    began = time.time()
    r = rig.call("render_folder_via_cli", folder=str(d), out_dir=str(tmp_path / "o"), stall_s=3)
    assert r.error.code == "E_TIMEOUT" and "dialog" in r.error.message and time.time() - began < 30
    f = testflp.project({0: "Kick"}, {0: [0]})
    f.events += [[236, bytes(12)], [201, F.enc16("Transient Processor")], [212, struct.pack("<II", 1, 0) + bytes(44)], [213, b"\x00"], [98, b"\x00\x00"]]
    f.save(str(d / "b.flp"))
    set_service("fl_not_owned", ["Transient Processor"])
    try:
        blocked = rig.call("render_folder_via_cli", folder=str(d), out_dir=str(tmp_path / "o2"))
    finally:
        set_service("fl_not_owned", [])
    assert blocked.error.code == "E_BLOCKED_BY_DIALOG" and "b.flp" in blocked.error.message
