"""Loops, one-shots and patterns from stems (loopkit, skill loops-and-kits, 2026-10-28): averaging the repetitions of a bar removes bleed
that does not repeat, a kick averaged from many hits matches the kick that played, a clap that lands on the kick comes back without it,
the step patterns read the groove, bass notes come back on the 16th grid, MIDI files hold the notes, and a loop search ranks a matching
groove above a different one."""
from __future__ import annotations

import numpy as np
import pytest

from coproducer import loopkit, oneshots

SR = oneshots.SR
BPM = 128.0
BAR = 240.0 / BPM
STEP = BAR / 16


def place(buf: np.ndarray, shot: np.ndarray, t: float, gain: float = 1.0) -> None:
    i = int(round(t * SR))
    n = min(len(shot), len(buf) - i)
    if n > 0:
        buf[i:i + n] += gain * shot[:n]


def simple_kick(f0: float = 50.0, length: float = 0.4) -> np.ndarray:
    """One falling sine with a click: a kick whose envelope does not beat (oneshots.kick layers a second sine that beats against it)."""
    t = np.arange(int(length * SR)) / SR
    ph = 2 * np.pi * np.cumsum(f0 + 110 * np.exp(-t / 0.03)) / SR
    x = np.sin(ph) * np.exp(-t / 0.16)
    x[:int(0.002 * SR)] += np.random.default_rng(1).standard_normal(int(0.002 * SR)) * 0.15
    return x / np.max(np.abs(x))


def groove(bars: int = 12, fill_bar: int = 5, bleed: float = 0.25, seed: int = 3) -> tuple[np.ndarray, dict]:
    """A house drum stem: kick on the beats, clap on 2 and 4 (with the kick), open hat off the beat; random 'vocal' noise in every bar
    (different each bar) and one bar of snare 16ths as a fill."""
    rng = np.random.default_rng(seed)
    k, c, h, s = simple_kick(), oneshots.clap(), oneshots.hat(open_=True), oneshots.snare()
    x = np.zeros(int((bars * BAR + 1.0) * SR))
    for b in range(bars):
        t0 = 0.05 + b * BAR
        if b == fill_bar:
            for st in range(16):
                place(x, s, t0 + st * STEP, 0.6)
            continue
        for st in (0, 4, 8, 12):
            place(x, k, t0 + st * STEP)
        for st in (4, 12):
            place(x, c, t0 + st * STEP, 0.7)
        for st in (2, 6, 10, 14):
            place(x, h, t0 + st * STEP, 0.6)
        seg = rng.standard_normal(int(BAR * SR)) * bleed
        seg = np.convolve(seg, np.ones(30) / 30, mode="same")      # a band-limited, non-repeating bleed
        place(x, seg, t0)
    return x, {"kick": k, "clap": c, "hat": h, "first": 0.05}


def edges_for(x: np.ndarray, first: float = 0.05) -> np.ndarray:
    return loopkit.regular_edges([first + i * BAR for i in range(4)], BPM, len(x) / SR)


def corr(a: np.ndarray, b: np.ndarray, max_lag_ms: float = 0.0) -> float:
    """Correlation, at the best lag within max_lag_ms."""
    n = min(len(a), len(b))
    a, b = np.asarray(a[:n], float), np.asarray(b[:n], float)
    best = -1.0
    m = int(SR * max_lag_ms / 1000)
    for lag in range(-m, m + 1):
        x, y = (a[lag:], b[:n - lag]) if lag >= 0 else (a[:n + lag], b[-lag:])
        best = max(best, float(np.corrcoef(x, y)[0, 1]))
    return best


def test_regular_edges_keep_the_first_bar_and_exact_lengths():
    e = loopkit.regular_edges([0.06, 1.94, 3.82, 5.68, 7.58], 128.0, 20.0)
    assert e[0] == pytest.approx(0.0625, abs=0.01) and np.allclose(np.diff(e), BAR)
    assert e[-1] <= 20.0


def test_patterns_read_the_groove_and_fills_are_left_out():
    x, _ = groove()
    e = edges_for(x)
    envs = loopkit.band_envelopes(x, SR)
    bars = list(range(12))
    same = loopkit.matching_bars(envs, SR, e, bars)
    assert 5 not in same and len(same) == 11
    p = loopkit.drum_patterns(envs, SR, e, same)["patterns"]
    assert p["kick"] == "X...X...X...X..."
    assert p["snare"][4] == "X" and p["snare"][12] == "X" and p["snare"][0] in ".o"
    assert all(p["hat"][s] == "X" for s in (2, 6, 10, 14))


def test_averaging_the_repeats_removes_the_bleed():
    x, sh = groove(bleed=0.35)
    clean, _ = groove(bleed=0.0)
    e = edges_for(x)
    same = [b for b in range(12) if b != 5]
    loop, info = loopkit.average_loop(x[:, None], SR, e, same, 1)
    i0 = int(round(e[2] * SR))     # bar 3: the tails of bar 2's clap and hat ring into it, as into every bar but the first
    ref, single = clean[i0:i0 + info["samples"]], x[i0:i0 + info["samples"]]
    assert info["n"] == 11 and info["residual_db"] < -3
    err_loop, err_single = (float(np.sqrt(np.mean((y - ref) ** 2))) for y in (loop[:, 0], single))
    assert err_loop < 0.5 * err_single


def test_a_kick_from_many_hits_and_a_clap_without_its_kick():
    x, sh = groove(bleed=0.3)
    e = edges_for(x)
    bars = [b for b in range(12) if b != 5]
    fast = loopkit._env(x, SR, 1.0)
    kick, ki = loopkit.average_hits(x, SR, loopkit.hit_times(fast, SR, e, bars, [0, 8]), 0.2)
    assert ki["n"] == 22 and corr(kick, sh["kick"], 6.0) > 0.95
    on2, _ = loopkit.average_hits(x, SR, loopkit.hit_times(fast, SR, e, bars, [4, 12]), 0.2)
    clap, info = loopkit.subtract(on2, kick, SR)
    assert 0.8 < info["gain"] < 1.2 and info["low_cut_db"] < -15
    assert corr(clap, sh["clap"], 6.0) > 0.8


def test_the_tail_past_the_next_hit_keeps_only_the_low_end():
    x, sh = groove(bleed=0.0)
    e = edges_for(x)
    fast = loopkit._env(x, SR, 1.0)
    kick, _ = loopkit.average_hits(x, SR, loopkit.hit_times(fast, SR, e, [0, 1, 2, 3], [0, 8]), 0.44)
    tail = loopkit.lowpass_tail(kick, SR, 0.2)
    hi = loopkit._band(tail, SR, 3000, 0)[int(0.25 * SR):int(0.4 * SR)]
    raw = loopkit._band(kick, SR, 3000, 0)[int(0.25 * SR):int(0.4 * SR)]
    assert float(np.sqrt(np.mean(hi ** 2))) < 0.05 * float(np.sqrt(np.mean(raw ** 2)))     # the hat at step 2 is gone from the tail
    assert corr(tail[:int(0.19 * SR)], kick[:int(0.19 * SR)]) > 0.999                       # the kick itself is untouched


def test_bass_notes_come_back_on_the_grid():
    rate = SR
    notes = [(0, 3, 31), (4, 3, 31), (7, 3, 32), (10, 2, 32), (13, 2, 32), (16, 3, 29), (20, 3, 29), (23, 3, 34), (26, 2, 34), (29, 2, 36)]
    y = np.zeros(int(2 * BAR * rate))
    for st, ln, m in notes:
        f = 440 * 2 ** ((m - 69) / 12)
        n = int((ln - 0.6) * STEP * rate)          # a 70 ms gap before the next note, as a played bass has
        t = np.arange(n) / rate
        place(y, 0.5 * np.sign(np.sin(2 * np.pi * f * t)) * np.minimum(1, t / 0.004), st * STEP)
    got = loopkit.bass_notes(y, rate, BPM)
    assert [(g["step"], g["midi"]) for g in got] == [(s, m) for s, _ln, m in notes]


def test_midi_files_hold_the_patterns(tmp_path):
    import mido
    pats = {"kick": "X...X...X...X...", "clap": "....X.......X...", "ohat": "..x...x...x...x."}
    notes = loopkit.pattern_notes(pats, 2)
    assert len(notes) == 2 * (4 + 2 + 4)
    p = loopkit.write_midi(tmp_path / "d.mid", {"drums groove": notes, "bass": [(0.0, 0.5, 31, 100)]}, BPM)
    m = mido.MidiFile(str(p))
    ons = [msg for t in m.tracks for msg in t if msg.type == "note_on" and msg.velocity > 0]
    assert len(ons) == 21 and {msg.channel for msg in ons} == {9, 0}
    assert round(mido.tempo2bpm(next(msg.tempo for msg in m.tracks[0] if msg.type == "set_tempo"))) == 128


def test_loop_search_ranks_the_matching_groove_first():
    x, _ = groove(bars=12, fill_bar=99, bleed=0.1)
    e = edges_for(x)
    envs = loopkit.band_envelopes(x, SR)
    target = loopkit.drum_patterns(envs, SR, e, list(range(8)))
    same_loop = x[int(e[0] * SR):int(e[4] * SR)]
    other = np.zeros(int(4 * BAR * SR))                      # a breakbeat: kick on 1 and the 'and' of 3, snare on 2 and 4, 8th hats
    k, s, h = simple_kick(), oneshots.snare(), oneshots.hat()
    for b in range(4):
        for st in (0, 10):
            place(other, k, b * BAR + st * STEP)
        for st in (4, 12):
            place(other, s, b * BAR + st * STEP, 0.7)
        for st in range(0, 16, 2):
            place(other, h, b * BAR + st * STEP, 0.3)
    a = loopkit.similarity(target, loopkit.describe_loop(same_loop[:, None], SR))
    b = loopkit.similarity(target, loopkit.describe_loop(other[:, None], SR))
    assert a > 0.9 and a > b + 0.1
    d = loopkit.describe_loop(same_loop[:, None], SR)
    assert d["bpm"] == pytest.approx(BPM, rel=0.02) and d["bars"] == pytest.approx(4, abs=0.1)


def test_kick_features_and_distance():
    k1, k2 = simple_kick(46), simple_kick(62, 0.3)
    f1, f2 = loopkit.shot_features(k1, SR), loopkit.shot_features(k2, SR)
    assert 40 < f1["pitch_hz"] < 60 and f2["pitch_hz"] > f1["pitch_hz"]
    assert loopkit.kick_distance(f1, f1) == 0 and loopkit.kick_distance(f1, f2) > 0.5


def test_fl_factory_loops_ogg_in_wav_are_read(tmp_path):
    """FL Studio's factory loops are Ogg Vorbis inside a WAV (format tag 0x674F), which libsndfile and ffmpeg refuse as WAV."""
    import io

    import soundfile as sf

    from coproducer import loopsets
    b = io.BytesIO()
    sf.write(b, np.stack([np.sin(np.arange(2 * SR) / 9)] * 2, 1) * 0.3, SR, format="OGG", subtype="VORBIS")
    ogg = b.getvalue()
    fmt = (0x674F).to_bytes(2, "little") + (2).to_bytes(2, "little") + SR.to_bytes(4, "little") + (20000).to_bytes(4, "little") + bytes([4, 0, 16, 0])
    body = b"WAVE" + b"fmt " + len(fmt).to_bytes(4, "little") + fmt + b"data" + len(ogg).to_bytes(4, "little") + ogg + (b"\0" if len(ogg) & 1 else b"")
    p = tmp_path / "DL Loop.wav"
    p.write_bytes(b"RIFF" + len(body).to_bytes(4, "little") + body)
    x, rate = loopsets._read(p, 1.0)
    assert x.shape == (SR, 2) and rate == SR and 0.25 < float(np.abs(x).max()) < 0.35
