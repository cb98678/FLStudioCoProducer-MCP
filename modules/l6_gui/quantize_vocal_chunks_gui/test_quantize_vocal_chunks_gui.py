import json

import numpy as np
import soundfile as sf

from coproducer.result import fail, ok
from coproducer.services import set_service

RATE = 48000


def _syllables(rate, bpm, early_s, n=8, jitter=0.0, seed=1):
    """Tone bursts on the beats of a short file (beat 0 at the file's start), each early_s early."""
    rng = np.random.default_rng(seed)
    step = 60.0 / bpm
    x = np.zeros(int(rate * (n + 1) * step))
    for k in range(1, n + 1):
        t = k * step - early_s + rng.uniform(-jitter, jitter)
        i, m = int(t * rate), int(0.16 * rate)
        env = np.minimum(1.0, np.arange(m) / (0.004 * rate)) * np.exp(-np.arange(m) / (0.08 * rate))
        x[i:i + m] += 0.4 * env * (np.sin(2 * np.pi * 220 * np.arange(m) / rate) + 0.3 * rng.standard_normal(m))
    return x


def _manifest(tmp_path, chunks):
    folder = tmp_path / "chunks"
    folder.mkdir()
    rows = []
    for i, x in enumerate(chunks):
        p = folder / ("v_%02d.wav" % i)
        sf.write(str(p), x, RATE)
        rows.append({"index": i, "file": str(p), "grid_s": 2.0 * i, "words": ["w%d" % i]})
    mp = folder / "chunks.json"
    mp.write_text(json.dumps({"bpm": 120.0, "origin_s": 0.0, "lead_s": 0.0, "rate": RATE, "duration_s": 2.0 * len(chunks), "chunks": rows}), encoding="utf-8")
    return mp


def _fake_newtime(rig, calls, fail_index=None):
    """Stands in for quantize_vocal_gui: writes a copy with the syllables moved onto the beats (a perfect fit), or fails for one chunk."""
    import dataclasses

    def fake(path, out_path, bpm, division=4, lead_s=-1.0, grid_up=442, grid_down=441, max_move_s=0.045, min_share=0.8):
        calls.append((path, out_path, lead_s, max_move_s))
        if fail_index is not None and ("_%02d" % fail_index) in path:
            return fail("E_NOT_VERIFIED", "only 1 of 8 warp markers were seen")
        sf.write(out_path, _syllables(RATE, bpm, 0.0), RATE)
        return ok({"out_path": out_path, "markers": 8, "verified": 8, "lead_s": lead_s, "mean_move_ms": 0.0, "onsets": 8, "grid_bpm": bpm})
    rig.reg.modules["quantize_vocal_gui"] = dataclasses.replace(rig.reg.modules["quantize_vocal_gui"], fn=fake)
    closed = []
    rig.reg.modules["run_gui_recipe"] = dataclasses.replace(rig.reg.modules["run_gui_recipe"], fn=lambda name, params=None: (closed.append(name), ok({"recipe": name}))[1])
    # the editor and the playlist stay open after a failed chunk, no dialog over them: only Newtime's X is clicked, no Escape, no F5
    rig.reg.modules["list_open_dialogs"] = dataclasses.replace(rig.reg.modules["list_open_dialogs"],
                                                               fn=lambda: ok({"dialogs": [{"title": "WarpCorrectionTrack (Master)", "rect": [0, 0, 741, 617]}, {"title": "Playlist - bench", "rect": [0, 0, 100, 100]}]}))
    rig.reg.modules["press_hotkey"] = dataclasses.replace(rig.reg.modules["press_hotkey"], fn=lambda keys: (closed.append("hotkey:" + "+".join(keys)), ok(True))[1])
    return closed


def test_fits_each_chunk_measures_and_skips_the_ones_on_the_grid(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    mp = _manifest(tmp_path, [_syllables(RATE, 120.0, 0.035, jitter=0.01), _syllables(RATE, 120.0, 0.0), _syllables(RATE, 120.0, 0.03, jitter=0.012, seed=4)])
    calls = []
    _fake_newtime(rig, calls)
    r = rig.call("quantize_vocal_chunks_gui", manifest_path=str(mp), lead_s=0.0, passes=2, target_ms=15.0)   # the detector marks a burst about 12 ms early
    assert r.ok, r
    assert r.value["fitted"] == 2 and r.value["skipped"] == [1] and r.value["failed"] == [] and r.value["median_after_ms"] <= 15.0
    assert len(calls) == 2 and all(c[2] == 0.0 and c[3] == 0.1 for c in calls)
    man = json.loads(mp.read_text(encoding="utf-8"))
    fit = man["fit"]
    assert [f["index"] for f in fit] == [0, 1, 2] and fit[1]["skipped"].startswith("already within")
    assert fit[0]["before"]["median_ms"] > 15.0 and fit[0]["after"]["median_ms"] <= 15.0 and fit[0]["out"].endswith("v_00_q.wav")
    assert (tmp_path / "chunks" / "v_00_q.wav").is_file() and (tmp_path / "chunks" / "v_02_q.wav").is_file()
    # only chunk 2 again: the manifest keeps the other records
    again = rig.call("quantize_vocal_chunks_gui", manifest_path=str(mp), lead_s=0.0, target_ms=15.0, options={"indices": [2]})
    assert again.ok and again.value["fitted"] == 2 and len(calls) == 3


def test_a_failed_chunk_is_closed_and_reported(rig, tmp_path):
    set_service("sandbox_root", str(tmp_path))
    mp = _manifest(tmp_path, [_syllables(RATE, 120.0, 0.035, jitter=0.01), _syllables(RATE, 120.0, 0.035, jitter=0.01, seed=2)])
    calls = []
    closed = _fake_newtime(rig, calls, fail_index=0)
    r = rig.call("quantize_vocal_chunks_gui", manifest_path=str(mp), lead_s=0.0, passes=1)
    assert r.ok, r
    assert r.value["failed"] == [{"index": 0, "error": "E_NOT_VERIFIED"}] and r.value["fitted"] == 1 and closed == ["newtime_close_gui"]
    assert rig.call("quantize_vocal_chunks_gui", manifest_path="/elsewhere/chunks.json").error.code == "E_SANDBOX_VIOLATION"
    assert rig.call("quantize_vocal_chunks_gui", manifest_path=str(tmp_path / "none.json")).error.code == "E_IO"
