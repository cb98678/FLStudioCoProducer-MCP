import json

import numpy as np
import soundfile as sf

from coproducer.services import set_service

RATE = 48000


def _manifest(tmp_path, with_edit=True):
    folder = tmp_path / "chunks"
    folder.mkdir()
    a = np.zeros(int(0.5 * RATE)); a[int(0.1 * RATE):int(0.3 * RATE)] = 0.5      # chunk 0 at 1.0 s: audio 1.1 to 1.3
    b = np.zeros(int(0.5 * RATE)); b[int(0.05 * RATE):int(0.25 * RATE)] = 0.25   # chunk 1 at 2.0 s
    sf.write(str(folder / "c_00.wav"), a, RATE)
    sf.write(str(folder / "c_01.wav"), b, RATE)
    if with_edit:
        e = np.zeros(int(0.5 * RATE)); e[int(0.1 * RATE):int(0.3 * RATE)] = 0.25  # the edited copy of chunk 1: its sound moved later
        sf.write(str(folder / "c_01_q.wav"), e, RATE)
    man = {"bpm": 120.0, "origin_s": 0.0, "rate": RATE, "duration_s": 3.0,
           "chunks": [{"index": 0, "file": str(folder / "c_00.wav"), "grid_s": 1.0}, {"index": 1, "file": str(folder / "c_01.wav"), "grid_s": 2.0}]}
    mp = folder / "chunks.json"
    mp.write_text(json.dumps(man), encoding="utf-8")
    return mp


def test_lays_edited_chunks_back_at_their_grid_lines(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    mp = _manifest(tmp_path)
    r = rig.call("join_vocal_chunks", manifest_path=str(mp), out_path=str(tmp_path / "full.wav"), suffix="_q", shifts_16ths={"0": 2})
    assert r.ok, r
    assert r.value["edited"] == 1 and r.value["used"][1]["file"] == "c_01_q.wav" and r.value["used"][0]["shift_16ths"] == 2
    y, rate = sf.read(r.value["out_path"], always_2d=True)
    assert rate == RATE and len(y) == int(4.0 * RATE)
    # chunk 0 moved two 16ths (0.25 s) later: sound from 1.35 to 1.55; chunk 1's edited copy sounds from 2.1 to 2.3
    assert abs(y[int(1.4 * RATE), 0] - 0.5) < 1e-3 and abs(y[int(1.2 * RATE), 0]) < 1e-3
    assert abs(y[int(2.2 * RATE), 0] - 0.25) < 1e-3 and abs(y[int(2.07 * RATE), 0]) < 1e-3
    plain = rig.call("join_vocal_chunks", manifest_path=str(mp), out_path=str(tmp_path / "plain.wav"))
    z, _ = sf.read(plain.value["out_path"], always_2d=True)
    assert plain.value["edited"] == 0 and abs(z[int(2.07 * RATE), 0] - 0.25) < 1e-3


def test_refuses_bad_paths(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    mp = _manifest(tmp_path, with_edit=False)
    assert rig.call("join_vocal_chunks", manifest_path="/elsewhere/chunks.json", out_path=str(tmp_path / "o.wav")).error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("join_vocal_chunks", manifest_path=str(tmp_path / "none.json"), out_path=str(tmp_path / "o.wav")).error.code == "E_IO"
    (tmp_path / "chunks" / "c_01.wav").unlink()
    assert rig.call("join_vocal_chunks", manifest_path=str(mp), out_path=str(tmp_path / "o.wav")).error.code == "E_IO"
