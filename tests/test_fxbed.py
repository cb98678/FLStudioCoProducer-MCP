import numpy as np
import pytest

from coproducer import fxbed as F

SR = F.SR


def _rms(x, bar, bars=1, bpm=140):
    spb = 60 / bpm
    s, e = int(bar * 4 * spb * SR), int((bar + bars) * 4 * spb * SR)
    return float(np.sqrt(np.mean(x[s:e] ** 2)))


def test_bed_length_and_determinism():
    cues = [{"kind": "impact", "bar": 1, "gain_db": -3}, {"kind": "noise_riser", "bar": 2, "bars": 2, "f0": 2500, "f1": 14000}]
    a, b = F.render_bed(cues, 140, 32), F.render_bed(cues, 140, 32)
    assert a.shape == (int(round(32 * 60 / 140 * SR)), 2) and np.array_equal(a, b) and np.isfinite(a).all()


def test_cues_land_on_their_bars():
    x = F.render_bed([{"kind": "impact", "bar": 3, "gain_db": 0}], 140, 64).mean(1)
    assert _rms(x, 3) > 0.05 and _rms(x, 1) < 1e-9 and _rms(x, 8) < 1e-9


def test_gain_db_scales_level():
    a = F.render_bed([{"kind": "impact", "bar": 0}], 140, 16)
    b = F.render_bed([{"kind": "impact", "bar": 0, "gain_db": -6.0}], 140, 16)
    assert np.max(np.abs(b)) == pytest.approx(np.max(np.abs(a)) * 10 ** (-6 / 20), rel=1e-6)


def test_air_sweep_ends_at_the_bar_end_and_riser_swells():
    x = F.render_bed([{"kind": "air_sweep", "bar": 2, "beats": 4}], 140, 16).mean(1)
    assert _rms(x, 2) > 1e-3 and _rms(x, 3) < 1e-2 * _rms(x, 2)
    r = F.render_bed([{"kind": "noise_riser", "bar": 0, "bars": 4, "f0": 500, "f1": 12000}], 140, 16).mean(1)
    assert _rms(r, 3) > 4 * _rms(r, 1)


def test_unknown_cue_kind_refused():
    with pytest.raises(ValueError):
        F.render_bed([{"kind": "nope", "bar": 0}], 140, 8)
