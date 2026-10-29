from __future__ import annotations

from scipy import signal

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_low_end_mono_ratio(path: str, cutoff_hz: float = 120.0) -> Result:
    """Measure how mono a stereo file is below a cutoff frequency, as side energy relative to mid energy in dB."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    if x.shape[1] < 2:
        return fail("E_ARG", "a stereo file is needed")
    sos = signal.butter(4, cutoff_hz, btype="low", fs=rate, output="sos")
    lo = signal.sosfilt(sos, x[:, :2], axis=0)
    mid, side = (lo[:, 0] + lo[:, 1]) / 2, (lo[:, 0] - lo[:, 1]) / 2
    rel = dsp.power_db(float((side ** 2).mean())) - dsp.power_db(float((mid ** 2).mean()))
    return ok({"side_over_mid_db": round(rel, 2), "mono_below_cutoff": rel < -20.0})
