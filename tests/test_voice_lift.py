"""remixaudio.voice_lift_db: a quiet vocal stem is raised toward the level the person's balances were set on, never lowered, never clipped."""
import numpy as np

from coproducer import remixaudio


def _voice(level_db, peak=None, rate=8000):
    t = np.arange(rate * 6) / rate
    x = np.sin(2 * np.pi * 180 * t) * (10 ** (level_db / 20) * np.sqrt(2))
    x[rate * 2:rate * 3] = 0.0                                   # a silence between lines does not count
    if peak is not None:
        x[100] = peak
    return np.stack([x, x], axis=1).astype("float32"), rate


def test_the_active_level_ignores_the_silences():
    x, rate = _voice(-30.0)
    assert abs(remixaudio.active_level_db(x, rate) + 30.0) < 0.5


def test_a_quiet_stem_comes_up_and_a_loud_one_is_left_alone():
    x, rate = _voice(-30.0)
    assert abs(remixaudio.voice_lift_db(x, rate) - 12.0) < 0.5
    y, _ = _voice(-15.0)
    assert remixaudio.voice_lift_db(y, rate) == 0.0


def test_the_lift_stops_at_the_peak_limit():
    x, rate = _voice(-30.0, peak=0.5)                            # a 0.5 peak leaves 5 dB of room to -1 dBFS
    assert abs(remixaudio.voice_lift_db(x, rate) - (-1.0 - 20 * np.log10(0.5))) < 0.05
