import numpy as np
import soundfile as sf

from coproducer import flpfile, testflp


def _bench(tmp_path):
    p = tmp_path / "sandbox" / "bench.flp"
    p.parent.mkdir(exist_ok=True)
    f = testflp.project({0: "Kick", 1: "Voc"}, {0: [0]}, bpm=120.0, bars=4, samples={1: "x.wav"})
    f.add_audio_clips(1, 1, [(0, 384, 0.0, 1000.0)], flpfile.PATTERN_CLIP_TEMPLATE)
    f.save(str(p))
    return p


def _wav(tmp_path, name, seconds=2.0):
    p = tmp_path / "sandbox" / name
    p.parent.mkdir(exist_ok=True)
    sf.write(str(p), np.zeros(int(seconds * 8000)), 8000)
    return str(p)


def test_saves_clips_on_the_clock(rig, desk, tmp_path):
    a, b = _wav(tmp_path, "a.wav"), _wav(tmp_path, "b.wav", 1.0)
    out = tmp_path / "sandbox" / "projects" / "s.flp"
    r = rig.call("save_session_project", bench_path=str(_bench(tmp_path)), out_path=str(out), bpm=117.5,
                 clips=[{"file": a, "name": "a in", "row": 0}, {"file": b, "name": "b fitted", "row": 1, "start_s": 2.0}])
    assert r.ok and r.meta["verified"] is True and r.value["audio_clips"] == 2
    f = flpfile.Flp.load(str(out))
    assert f.tempo() == 117.5 and f.channel_count == 2          # the Kick channel is gone
    first, second = sorted(f.audio_clips(), key=lambda c: c["pos"])
    assert first["pos"] == 0 and second["pos"] == int(round(2.0 * 117.5 / 60 * 96))
    assert f.get_text(0, flpfile.EV_CH_NAME) == "a in" and f.channel_info(1)["sample"].endswith("b.wav")


def test_refuses_bad_input(rig, desk, tmp_path):
    a = _wav(tmp_path, "a.wav")
    bench, out = str(_bench(tmp_path)), str(tmp_path / "sandbox" / "o.flp")
    assert rig.call("save_session_project", bench_path=bench, out_path=out, bpm=120, clips=[{"name": "x"}]).error.code in ("E_ARG", "E_SCHEMA")
    assert rig.call("save_session_project", bench_path=bench, out_path="/elsewhere/o.flp", bpm=120, clips=[{"file": a}]).error.code == "E_SANDBOX_VIOLATION"
