import json

import numpy as np
import soundfile as sf

from coproducer import oneshots
from coproducer.services import set_service

SR = oneshots.SR
BAR = 240.0 / 128


def _song(tmp_path, bars=12):
    """A fake analysis folder: a house drum stem (kick on the beats, clap on 2 and 4, off-beat hats, noise bleed that changes every bar) and
    a bass stem playing G then A flat each bar."""
    rng = np.random.default_rng(5)
    n = int((bars * BAR + 1) * SR)
    d, b = np.zeros(n), np.zeros(n)
    t = np.arange(int(0.35 * SR)) / SR
    k = np.sin(2 * np.pi * np.cumsum(50 + 110 * np.exp(-t / 0.03)) / SR) * np.exp(-t / 0.15)   # one falling sine: a kick that does not beat
    c, h = oneshots.clap(), oneshots.hat(open_=True)

    def put(buf, x, t, g=1.0):
        i = int(t * SR)
        buf[i:i + len(x)] += g * x[:max(0, n - i)]
    for bar in range(bars):
        t0 = 0.1 + bar * BAR
        for s in (0, 4, 8, 12):
            put(d, k, t0 + s * BAR / 16)
        for s in (4, 12):
            put(d, c, t0 + s * BAR / 16, 0.7)
        for s in (2, 6, 10, 14):
            put(d, h, t0 + s * BAR / 16, 0.5)
        put(d, np.convolve(rng.standard_normal(int(BAR * SR)) * 0.2, np.ones(20) / 20, mode="same"), t0)
        for s0, midi in ((0, 31), (8, 32)):
            t = np.arange(int(0.4 * SR)) / SR
            put(b, 0.5 * np.sign(np.sin(2 * np.pi * 440 * 2 ** ((midi - 69) / 12) * t)), t0 + s0 * BAR / 16)
    song = tmp_path / "sandbox" / "songs" / "fake"
    (song / "stems").mkdir(parents=True)
    sf.write(str(song / "stems" / "drums.wav"), np.stack([d, d], axis=1) * 0.3, SR)
    sf.write(str(song / "stems" / "bass.wav"), np.stack([b, b], axis=1) * 0.3, SR)
    info = {"name": "fake", "grid": {"bpm": 128.0, "steady": True, "bars": [round(0.1 + i * BAR, 2) for i in range(bars)]},
            "stems": {"drums": "C:\\elsewhere\\fake\\stems\\drums.wav", "bass": "C:\\elsewhere\\fake\\stems\\bass.wav"}}
    (song / "song_analysis.json").write_text(json.dumps(info), encoding="utf-8")
    return song


def test_loops_kit_and_patterns_from_a_house_groove(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    song = _song(tmp_path)
    r = rig.call("extract_song_loops", song_dir=str(song), sections="groove:1-12", loop_bars=[1, 2], hook="")
    assert r.ok and r.meta["verified"], r
    g = r.value["sections"]["groove"]
    assert g["drums"]["kick"] == "X...X...X...X..." and g["drums"]["snare"][4] == "X" and g["drums"]["hat"][2] == "X"
    assert [(n["step"], n["midi"]) for n in g["bass_notes"]][:2] == [(0, 31), (8, 32)]
    assert set(r.value["kit"]) >= {"kick", "clap"} and r.value["kit"]["kick"]["hits"] >= 20
    out = tmp_path / "sandbox" / "loops" / "fake"
    assert (out / "drums" / "fake_groove_1bar_128bpm.wav").is_file() and (out / "midi" / "fake_groove_drums.mid").is_file()
    assert (out / "README.md").read_text(encoding="utf-8").startswith("# Loops and kit: fake")


def test_failures(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path / "sandbox"))
    song = _song(tmp_path, bars=4)
    assert rig.call("extract_song_loops", song_dir=str(tmp_path / "none"), sections="a:1-2").error.code == "E_NOT_FOUND"
    assert rig.call("extract_song_loops", song_dir=str(song), sections="a:3-1").error.code == "E_ARG"
    assert rig.call("extract_song_loops", song_dir=str(song), sections="a:1-99").error.code == "E_ARG"
    assert rig.call("extract_song_loops", song_dir=str(song), sections="a:1-2", out_dir=str(tmp_path / "out")).error.code == "E_SANDBOX_VIOLATION"
