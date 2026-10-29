from coproducer.services import set_service
from coproducer.synth import drum_loop, to_wav


def test_separates_into_stems(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    src = to_wav(str(tmp_path / "mix.wav"), drum_loop(140, bars=1))
    r = rig.call("separate_stems", input_path=src, out_dir=str(tmp_path / "stems"))
    assert r.ok and r.meta["verified"] and sorted(r.value["stems"]) == ["bass", "drums", "other", "vocals"]
    assert r.value["model"] == "htdemucs"
    assert rig.call("separate_stems", input_path=src, out_dir=str(tmp_path / "s6"), stems=6).value["model"] == "htdemucs_6s"
    assert rig.call("separate_stems", input_path=src, out_dir=str(tmp_path / "sh"), quality="high").value["model"] == "htdemucs_ft"


def test_input_and_sandbox_errors(rig, ml, tmp_path):
    assert rig.call("separate_stems", input_path="a.wav", out_dir=str(tmp_path)).error.code == "E_SANDBOX_VIOLATION"
    set_service("sandbox_root", str(tmp_path / "box"))
    assert rig.call("separate_stems", input_path="a.wav", out_dir=str(tmp_path / "outside")).error.code == "E_SANDBOX_VIOLATION"
    (tmp_path / "box").mkdir()
    assert rig.call("separate_stems", input_path=str(tmp_path / "no.wav"), out_dir=str(tmp_path / "box" / "s")).error.code == "E_NOT_FOUND"
    src = to_wav(str(tmp_path / "mix.wav"), drum_loop(140, bars=1))
    assert rig.call("separate_stems", input_path=src, out_dir=str(tmp_path / "box" / "s"), stems=2).error.code == "E_ARG"
    assert rig.call("separate_stems", input_path=src, out_dir=str(tmp_path / "box" / "s"), stems=3).error.code == "E_ARG"
