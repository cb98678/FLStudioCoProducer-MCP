from coproducer.services import set_service
from coproducer.synth import drum_loop, to_wav


def test_makes_a_cover(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    src = to_wav(str(tmp_path / "src.wav"), drum_loop(140, bars=1))
    r = rig.call("generate_cover", src_path=src, prompt="dubstep half time", out_dir=str(tmp_path / "cov"), strength=0.5, seed=3)
    assert r.ok and r.meta["verified"] and r.value["paths"][0].endswith("gen_3.wav")


def test_missing_source(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    assert rig.call("generate_cover", src_path=str(tmp_path / "no.wav"), prompt="abc", out_dir=str(tmp_path / "c")).error.code == "E_NOT_FOUND"
    assert rig.call("generate_cover", src_path="x", prompt="abc", out_dir=str(tmp_path / "c"), strength=2).error.code == "E_ARG"
