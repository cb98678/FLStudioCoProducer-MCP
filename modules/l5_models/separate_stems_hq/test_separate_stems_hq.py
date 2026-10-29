from coproducer.services import set_service
from coproducer.synth import drum_loop, to_wav


def test_four_stems_with_roformer_vocals(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    src = to_wav(str(tmp_path / "mix.wav"), drum_loop(140, bars=1))
    r = rig.call("separate_stems_hq", input_path=src, out_dir=str(tmp_path / "stems"))
    assert r.ok and r.meta["verified"] and sorted(r.value["stems"]) == ["bass", "drums", "instrumental", "other", "vocals"]
    assert r.value["models"]["rest"] == "htdemucs_ft" and "roformer" in r.value["stems"]["vocals"]


def test_errors(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path / "box"))
    assert rig.call("separate_stems_hq", input_path="a.wav", out_dir=str(tmp_path / "outside")).error.code == "E_SANDBOX_VIOLATION"
    (tmp_path / "box").mkdir()
    assert rig.call("separate_stems_hq", input_path=str(tmp_path / "no.wav"), out_dir=str(tmp_path / "box" / "s")).error.code == "E_NOT_FOUND"
