import numpy as np

from coproducer import mixtools as M

SR = 44100


def burst(t, hz=60, ms=60, amp=0.5, n=SR * 4):
    x = np.zeros(n)
    k = int(ms / 1000 * SR)
    i = int(t * SR)
    x[i : i + k] = amp * np.sin(2 * np.pi * hz * np.arange(k) / SR)
    return x


def test_hit_levels_sees_the_hit_and_ignores_silence():
    step = 60 / 120 / 4
    x = burst(1 * 16 * step * 0 + 4 * step * 0 + 8 * step, hz=60)       # bar 0, step 8
    lv = M.hit_levels(x, SR, 120, [0], {"kick": ([0, 8], 30, 120)})
    assert lv["kick"][0][1] > lv["kick"][0][0] + 40


def test_level_scales_with_amplitude():
    step = 60 / 120 / 4
    a = M.hit_levels(burst(8 * step, amp=0.5), SR, 120, [0], {"k": ([8], 30, 120)})["k"][0][0]
    b = M.hit_levels(burst(8 * step, amp=0.25), SR, 120, [0], {"k": ([8], 30, 120)})["k"][0][0]
    assert abs((a - b) - 6.0) < 0.3


def test_bypassed_slot_edit_is_flagged():
    states = {0: [{"slot": 3, "plugin": "Fruity parametric EQ 2", "active": False}, {"slot": 5, "plugin": "Fruity Limiter", "active": True}]}
    edits = [{"module": "set_plugin_param_by_name", "args": {"index": 0, "name": "Band 7 level", "value": 0.4, "slot_index": 3}},
             {"module": "set_plugin_param_by_name", "args": {"index": 0, "name": "Limiter ceiling", "value": 0.4, "slot_index": 5}},
             {"module": "set_eq_db_verified", "args": {"index": 0, "band": 2, "db": -4}}]
    w = M.bypassed_edit_warnings(edits, states)
    assert len(w) == 1 and "slot 3" in w[0] and "bypassed" in w[0]


def test_missing_slot_is_flagged():
    w = M.bypassed_edit_warnings([{"module": "set_plugin_param_by_name", "args": {"index": 0, "name": "x", "value": 0, "slot_index": 8}}], {0: []})
    assert "no plugin" in w[0]


def test_headline_delta():
    a = {"lufs": -14.0, "tp": -2.0, "crest": 14.0, "centroid": 1000.0, "bands": {"air": -13.0, "sub": -6.0}}
    b = {"lufs": -13.5, "tp": -1.8, "crest": 13.9, "centroid": 900.0, "bands": {"air": -14.0, "sub": -5.0}}
    d = M.headline_delta(a, b)
    assert d["lufs"] == 0.5 and d["band_air"] == -1.0 and d["band_sub"] == 1.0
