import mixer


def op_mixer_get_eq_band_count() -> dict:
    """Run mixer.getEqBandCount inside FL Studio and return the outcome as a result dict."""
    return _run(mixer.getEqBandCount)
