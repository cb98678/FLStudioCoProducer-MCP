import numpy as np


def _syllables(rate, bpm, lead, jitter):
    """Short noisy tone bursts on 8th notes, each starting `lead` early plus some scatter (a sung line on a beat)."""
    step = 60.0 / bpm / 2
    rng = np.random.default_rng(3)
    x = np.zeros(int(rate * 8.0))
    starts = []
    for k in range(2, 30):
        t = k * step - lead + rng.uniform(-jitter, jitter)
        i = int(t * rate)
        n = int(0.16 * rate)
        env = np.minimum(1.0, np.arange(n) / (0.004 * rate)) * np.exp(-np.arange(n) / (0.08 * rate))
        tone = np.sin(2 * np.pi * 220 * np.arange(n) / rate) + 0.3 * rng.standard_normal(n)
        x[i:i + n] += 0.4 * env * tone
        starts.append(t)
    return x, starts


def test_marks_onsets_near_the_grid_with_the_singers_lead(rig, wav):
    x, starts = _syllables(48000, 120.0, 0.03, 0.012)
    r = rig.call("detect_warp_markers", path=wav("v", x), bpm=120.0, division=2)
    assert r.ok, r
    v = r.value
    assert 0.02 <= v["lead_s"] <= 0.05 and len(v["markers"]) >= 20 and v["mean_move_ms"] < 15
    assert all(abs(g / 0.25 - round(g / 0.25)) < 1e-6 for g in v["grid"])
    assert len(v["peaks_5ms"]) == int(8.0 / 0.005)
    fixed = rig.call("detect_warp_markers", path=wav("v2", x), bpm=120.0, division=2, lead_s=0.0).value
    assert fixed["lead_s"] == 0.0


def test_refuses_bad_input(rig, tmp_path):
    assert rig.call("detect_warp_markers", path=str(tmp_path / "none.wav"), bpm=120.0).error.code == "E_IO"
    assert rig.call("detect_warp_markers", path="x.wav", bpm=500.0).error.code == "E_ARG"
    assert rig.call("detect_warp_markers", path="x.wav", bpm=120.0, division=5).error.code == "E_ARG"
