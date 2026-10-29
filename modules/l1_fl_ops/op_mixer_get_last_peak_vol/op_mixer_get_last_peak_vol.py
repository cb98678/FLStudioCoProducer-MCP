import mixer


def op_mixer_get_last_peak_vol(section: int) -> dict:
    """Run mixer.getLastPeakVol inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"section": section}, {"section": "i"})
    if bad:
        return bad
    return _run(mixer.getLastPeakVol, section)
