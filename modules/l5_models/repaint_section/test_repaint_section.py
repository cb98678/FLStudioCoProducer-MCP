from coproducer.services import set_service
from coproducer.synth import drum_loop, to_wav


def test_repaints_a_range(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    src = to_wav(str(tmp_path / "src.wav"), drum_loop(140, bars=1))
    r = rig.call("repaint_section", src_path=src, start_s=1, end_s=2, prompt="busier hats", out_dir=str(tmp_path / "rp"), seed=9)
    assert r.ok and r.meta["verified"]


def test_bad_range(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    r = rig.call("repaint_section", src_path="x", start_s=4, end_s=4, prompt="abc", out_dir=str(tmp_path / "rp"))
    assert r.error.code == "E_ARG"
    assert rig.call("repaint_section", src_path=str(tmp_path / "no.wav"), start_s=1, end_s=2, prompt="abc", out_dir=str(tmp_path / "rp")).error.code == "E_NOT_FOUND"
