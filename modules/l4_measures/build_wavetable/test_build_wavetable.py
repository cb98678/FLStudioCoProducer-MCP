import numpy as np

from coproducer import wavetables
from coproducer.services import set_service

RATE = 48000


def test_a_held_bass_note_and_a_formula_become_tables(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    t = np.arange(int(0.9 * RATE)) / RATE
    x = sum(np.sin(2 * np.pi * k * 49.0 * t) / k for k in range(1, 12)) * 0.3 * np.minimum(1, t / 0.005)
    r = rig.call("build_wavetable", out_path=str(tmp_path / "sandbox" / "wt" / "bass.wav"), path=wav("bass", x), options={"frames": 8})
    assert r.ok and r.meta["verified"], r
    v = r.value
    assert v["note"] == "G1" and v["frames"] == 8 and v["oscillator"]["sample_frames"] == 8 and v["oscillator"]["sample_source"] == v["path"]
    assert abs(v["last"][1] - 0.5) < 0.05 and v["edge_loss_db"] < -25
    assert len(wavetables.read_table(v["path"])[0]) == 8
    f = rig.call("build_wavetable", out_path=str(tmp_path / "sandbox" / "wt" / "sub.wav"), formula="sin(pi*x + y*sin(2*pi*x))", options={"frames": 4})
    assert f.ok and f.value["wrap_jump"] < 1e-6 and f.value["first"][0] == 1.0


def test_failures(rig, wav, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    out = str(tmp_path / "sandbox" / "x.wav")
    assert rig.call("build_wavetable", out_path=str(tmp_path / "elsewhere.wav"), formula="sin(pi*x)").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("build_wavetable", out_path=out).error.code == "E_ARG"
    assert rig.call("build_wavetable", out_path=out, formula="open(x)").error.code == "E_ARG"
    noise = np.random.default_rng(1).standard_normal(RATE) * 0.2
    assert rig.call("build_wavetable", out_path=out, path=wav("noise", noise)).error.code == "E_NOT_FOUND"
    assert rig.call("build_wavetable", out_path=out, path=str(tmp_path / "missing.wav")).error.code == "E_IO"
