from coproducer.services import set_service
from coproducer.synth import drum_loop, to_wav


def test_grid_from_the_model(rig, ml, tmp_path):
    set_service("model_files", {"beat_this_final0": {"path": "C:/models/weights/beat_this/final0.ckpt", "sha256": "ab"}})
    src = to_wav(str(tmp_path / "mix.wav"), drum_loop(120, bars=1))
    r = rig.call("detect_beats_ml", path=src)
    assert r.ok and r.meta["verified"] and r.value["meter"] == 4 and abs(r.value["bpm"] - 120) < 0.01 and r.value["bar_count"] == 10
    assert r.value["odd_bars"] == [] and not r.value["drifting"] and r.value["origin_s"] == 0.25


def test_errors(rig, ml, tmp_path, monkeypatch):
    assert rig.call("detect_beats_ml", path=str(tmp_path / "none.wav")).error.code == "E_NOT_FOUND"
    src = to_wav(str(tmp_path / "mix.wav"), drum_loop(120, bars=1))
    monkeypatch.setenv("FAKE_BEATS_FEW", "1")
    ml.sched.unload_all()
    assert rig.call("detect_beats_ml", path=src).error.code == "E_NOT_VERIFIED"
