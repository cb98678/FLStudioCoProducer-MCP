from coproducer.services import set_service
from coproducer.synth import drum_loop, to_wav


def test_notes_key_and_midi(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    src = to_wav(str(tmp_path / "vox.wav"), drum_loop(120, bars=1))
    r = rig.call("transcribe_vocal_melody", path=src, out_midi_path=str(tmp_path / "vox.mid"))
    assert r.ok and r.meta["verified"] and [n["pitch"] for n in r.value["notes"]] == [57, 61, 64]  # A3, C#4, E4
    assert r.value["key"]["tonic"] in (9, 1, 4) and (tmp_path / "vox.mid").is_file() and r.value["range"] == [57, 64]


def test_errors(rig, ml, tmp_path):
    assert rig.call("transcribe_vocal_melody", path=str(tmp_path / "none.wav")).error.code == "E_NOT_FOUND"
    set_service("sandbox_root", str(tmp_path / "box"))
    src = to_wav(str(tmp_path / "vox.wav"), drum_loop(120, bars=1))
    assert rig.call("transcribe_vocal_melody", path=src, out_midi_path=str(tmp_path / "out.mid")).error.code == "E_SANDBOX_VIOLATION"
