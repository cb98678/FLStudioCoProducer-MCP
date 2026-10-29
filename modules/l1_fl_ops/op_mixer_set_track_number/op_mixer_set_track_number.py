import mixer


def op_mixer_set_track_number(trackNumber: int, flags: int = 0) -> dict:
    """Run mixer.setTrackNumber inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"trackNumber": trackNumber, "flags": flags}, {"trackNumber": "i", "flags": "i"})
    if bad:
        return bad
    return _run(mixer.setTrackNumber, trackNumber, flags)
