import numpy as np

from coproducer import drumhits as D

RATE = 44100


def _kick(n=4000):
    t = np.arange(n) / RATE
    return np.sin(2 * np.pi * (45 + 80 * np.exp(-t * 40)) * t) * np.exp(-t * 18) * np.hanning(2 * n)[n:]


def _snare(n=4000):
    t = np.arange(n) / RATE
    rng = np.random.default_rng(1)
    return (0.6 * np.sin(2 * np.pi * 190 * t) + 0.8 * rng.standard_normal(n)) * np.exp(-t * 22) * 0.7 * np.hanning(2 * n)[n:]


def _hat(n=1500):
    t = np.arange(n) / RATE
    rng = np.random.default_rng(2)
    noise = rng.standard_normal(n)
    from scipy import signal
    b, a = signal.butter(4, 8000 / (RATE / 2), "highpass")
    return signal.lfilter(b, a, noise) * np.exp(-t * 90) * 0.5


def _pattern(bpm=108.0, bars=4, offset=0.31):
    step = 60.0 / bpm / 4
    x = np.zeros(int((offset + bars * 16 * step + 1) * RATE))
    truth = []
    for bar in range(bars):
        for s in range(16):
            t = offset + (bar * 16 + s) * step
            i = int(t * RATE)
            kind = None
            if s % 4 == 0 and s % 8 != 4:
                kind, w = "kick", _kick()
            elif s % 8 == 4:
                kind, w = "snare", _snare()
            elif s % 2 == 0:
                kind, w = "hat", _hat()
            if kind:
                x[i : i + len(w)] += w
                truth.append((kind, bar * 16 + s))
    return x, truth, step, offset


def test_detects_and_classifies_a_synthetic_pattern():
    x, truth, _step, _offset = _pattern()
    hits = D.detect_hits(x, RATE)
    kinds = {k: sum(1 for h in hits if h["kind"] == k) for k in ("kick", "snare", "hat")}
    want = {k: sum(1 for t in truth if t[0] == k) for k in kinds}
    for k, n in kinds.items():
        assert abs(n - want[k]) <= max(2, want[k] // 8), (k, kinds, want)


def test_grid_fit_recovers_tempo_and_offset():
    x, _, step, offset = _pattern(bpm=108.0, offset=0.31)
    hits = D.detect_hits(x, RATE)
    bpm, off = D.fit_grid([h["t"] for h in hits], bpm_guess=105.0)
    assert abs(bpm - 108.0) < 0.6
    rel = (off - offset) % step
    assert min(rel, step - rel) < 0.012


def test_note_rows_land_on_the_16th_grid():
    x, _, _step, _offset = _pattern()
    hits = D.detect_hits(x, RATE)
    bpm, off = D.fit_grid([h["t"] for h in hits], 108.0)
    rows = D.to_note_rows(hits, bpm, off, {"kick": 36, "snare": 38, "hat": 42})
    kicks = rows["kick"]
    assert kicks and all(abs(r[0] * 4 - round(r[0] * 4)) < 1e-9 for r in kicks) and all(r[2] == 36 for r in kicks)
    assert {r[0] % 4 for r in kicks} <= {0.0, 2.0}
    snares = {r[0] % 4 for r in rows["snare"]}
    assert snares == {1.0, 3.0}


def test_empty_input_is_quiet():
    assert D.detect_hits(np.zeros(RATE), RATE) == []
    assert D.fit_grid([], 120.0) == (120.0, 0.0)
