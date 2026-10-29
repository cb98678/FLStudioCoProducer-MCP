from coproducer import dsp
from coproducer.services import set_service
from coproducer.synth import drum_loop, to_wav


def test_matches_loudness(rig, tmp_path):
    box = tmp_path / "box"
    box.mkdir()
    set_service("sandbox_root", str(box))
    loud = drum_loop(bpm=120, bars=4)
    quiet = loud * 0.25
    a, b = to_wav(str(tmp_path / "a.wav"), loud), to_wav(str(tmp_path / "b.wav"), quiet)
    r = rig.call("build_ab_package", a_path=a, b_path=b, out_dir=str(box / "ab"))
    assert r.ok
    la = dsp.integrated_loudness(*dsp.load_audio(r.value["paths"]["A"]))
    lb = dsp.integrated_loudness(*dsp.load_audio(r.value["paths"]["B"]))
    assert abs(la - lb) < 0.1 and r.value["report"]["B"]["gain_db"] == 0.0 and r.value["report"]["A"]["gain_db"] < -5
    hot = rig.call("build_ab_package", a_path=a, b_path=b, out_dir=str(box / "ab2"), target_lufs=-3.0, ceiling_db=-1.0)
    assert hot.ok and hot.value["report"]["B"]["true_peak_db"] <= -0.95        # never pushed past the ceiling


def test_errors(rig, tmp_path):
    assert rig.call("build_ab_package", a_path="a", b_path="b", out_dir=str(tmp_path)).error.code == "E_SANDBOX_VIOLATION"
    set_service("sandbox_root", str(tmp_path))
    assert rig.call("build_ab_package", a_path=str(tmp_path / "no.wav"), b_path="x", out_dir=str(tmp_path / "o")).error.code == "E_IO"
