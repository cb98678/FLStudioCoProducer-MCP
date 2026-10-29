from __future__ import annotations

from coproducer import dsp
from coproducer.result import Result, fail, ok


def measure_band_energy(path: str, bands: dict | None = None) -> Result:
    """Measure the energy of named frequency bands in dB relative to the total energy."""
    try:
        x, rate = dsp.load_audio(path)
    except ValueError as e:
        return fail("E_IO", str(e))
    use = {k: tuple(v) for k, v in bands.items()} if bands else dsp.DEFAULT_BANDS
    return ok(dsp.band_energy_db(x, rate, use))
