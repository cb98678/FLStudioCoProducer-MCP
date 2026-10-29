import json

import numpy as np
import soundfile as sf

from coproducer import loopkit, oneshots

SR = oneshots.SR
BAR = 240.0 / 128


def _loop(path, kick_steps, clap_steps, hat_steps, bars=2):
    x = np.zeros(int(bars * BAR * SR))
    for b in range(bars):
        for steps, shot, g in ((kick_steps, oneshots.kick(f0=50), 1.0), (clap_steps, oneshots.clap(), 0.7), (hat_steps, oneshots.hat(), 0.4)):
            for s in steps:
                i = int((b * BAR + s * BAR / 16) * SR)
                n = min(len(shot), len(x) - i)
                x[i:i + n] += g * shot[:n]
    sf.write(str(path), x * 0.3, SR)
    return x


def test_the_matching_groove_ranks_first(rig, tmp_path):
    lib = tmp_path / "lib"
    lib.mkdir()
    x = _loop(lib / "house.wav", (0, 4, 8, 12), (4, 12), (2, 6, 10, 14))
    _loop(lib / "break.wav", (0, 10), (4, 12), range(0, 16, 2))
    edges = loopkit.bar_edges([0.0], 128.0, len(x) / SR)
    d = loopkit.drum_patterns(loopkit.band_envelopes(x, SR), SR, edges, [0, 1])
    pat = tmp_path / "patterns.json"
    pat.write_text(json.dumps({"name": "song", "sections": {"groove": {"drums": d["patterns"], "profiles": d["profiles"]}}}), encoding="utf-8")
    sf.write(str(tmp_path / "kick.wav"), oneshots.kick(f0=50), SR)
    kicks = tmp_path / "kicks"
    kicks.mkdir()
    for f0 in (40, 50, 70):
        sf.write(str(kicks / ("k%d.wav" % f0)), oneshots.kick(f0=f0), SR)
    r = rig.call("find_matching_loops", patterns_path=str(pat), section="groove", folders=[str(lib)], kick_path=str(tmp_path / "kick.wav"),
                 kick_folders=[str(kicks)])
    assert r.ok, r
    assert [x["file"].split("/")[-1].split("\\")[-1] for x in r.value["loops"]] == ["house.wav", "break.wav"]
    assert r.value["loops"][0]["score"] > r.value["loops"][1]["score"] + 0.1 and r.value["loops"][0]["bpm"] == 128.0
    assert r.value["kicks"][0]["file"].endswith("k50.wav") and "| Score |" in r.value["summary"]


def test_failures(rig, tmp_path):
    assert rig.call("find_matching_loops", patterns_path=str(tmp_path / "no.json"), section="groove", folders=[str(tmp_path)]).error.code == "E_NOT_FOUND"
    pat = tmp_path / "p.json"
    pat.write_text(json.dumps({"name": "s", "sections": {"groove": {"drums": {}, "profiles": {}}}}), encoding="utf-8")
    assert rig.call("find_matching_loops", patterns_path=str(pat), section="drop", folders=[str(tmp_path)]).error.code == "E_ARG"
    assert rig.call("find_matching_loops", patterns_path=str(pat), section="groove", folders=[str(tmp_path / "missing")]).error.code == "E_NOT_FOUND"
