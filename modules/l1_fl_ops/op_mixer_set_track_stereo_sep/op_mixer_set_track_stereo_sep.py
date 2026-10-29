import mixer


def op_mixer_set_track_stereo_sep(index: int, pan: float, pickupMode: int = 0) -> dict:
    """Run mixer.setTrackStereoSep inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "pan": pan, "pickupMode": pickupMode}, {"index": "i", "pan": "n", "pickupMode": "i"})
    if bad:
        return bad
    return _run(mixer.setTrackStereoSep, index, pan, pickupMode)
