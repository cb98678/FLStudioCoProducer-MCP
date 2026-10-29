import numpy as np

from coproducer import chopfx

RATE = 44100


def test_echo_repeats_at_the_delay_and_decays():
    x = np.zeros(RATE // 4)
    x[:200] = 0.5 * np.hanning(200)
    x = np.sin(2 * np.pi * 1000 * np.arange(len(x)) / RATE) * 0.5 * (np.arange(len(x)) < 1500)
    y = chopfx.echo(x, RATE, 120.0, delay_beats=1.0, feedback=0.5, repeats=3)
    d = RATE // 2  # one beat at 120 bpm
    assert y.shape[1] == 2 and len(y) > len(x) + 3 * d
    peaks = [np.abs(y[i * d : i * d + 1500]).max() for i in range(4)]
    assert peaks[0] > peaks[1] > peaks[2] > peaks[3] > 0.0
    assert np.abs(y[: 1500]).max() <= 0.51  # the dry chop keeps its level
