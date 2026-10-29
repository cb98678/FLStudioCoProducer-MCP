import json

from coproducer.services import set_service
from coproducer.synth import drum_loop, to_wav


def test_intake_writes_the_plan_inputs(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    set_service("model_files", {"beat_this_final0": {"path": "x.ckpt", "sha256": ""}, "roformer_vocals": {"model_dir": "m", "model": "v.ckpt", "sha256": ""}})
    src = to_wav(str(tmp_path / "in.wav"), drum_loop(120, bars=8))
    r = rig.call("build_song_analysis", input_path=src, name="demo", title="friends in low places")
    assert r.ok and r.meta["verified"], r
    v = r.value
    assert v["grid"]["bpm"] == 120.0 and v["grid"]["meter"] == 4 and v["words"] == 8 and set(v["stems"]) >= {"vocals", "drums", "bass"}
    f = v["files"]
    words, hits, notes = (json.load(open(f[k])) for k in ("words", "hits", "bass"))
    assert words["words"][0]["word"] == "friends" and hits["bpm"] == 120.0 and "bass" in notes
    assert json.load(open(f["analysis"]))["name"] == "demo" and isinstance(v["ask"], list)


def test_errors(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    assert rig.call("build_song_analysis", input_path=str(tmp_path / "none.wav"), name="x").error.code == "E_NOT_FOUND"
    src = to_wav(str(tmp_path / "in.wav"), drum_loop(120, bars=2))
    assert rig.call("build_song_analysis", input_path=src, name="x", stems_dir=str(tmp_path / "nostems")).error.code == "E_NOT_FOUND"
    assert rig.call("build_song_analysis", input_path=src, name="Bad Name").error.code == "E_ARG"


def test_stems_dir_takes_fl_stems_with_other(rig, ml, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    set_service("model_files", {"beat_this_final0": {"path": "x.ckpt", "sha256": ""}})
    src = to_wav(str(tmp_path / "in.wav"), drum_loop(120, bars=8))
    stems = tmp_path / "fl"
    stems.mkdir()
    for k in ("vocals", "drums", "bass", "other"):
        to_wav(str(stems / (k + ".wav")), drum_loop(120, bars=8))
    r = rig.call("build_song_analysis", input_path=src, name="fl", stems_dir=str(stems))
    assert r.ok, r
    assert set(r.value["stems"]) == {"vocals", "drums", "bass", "other"} and r.value["stems"]["other"].endswith("other.wav")
