import mixer


def op_mixer_set_track_volume(index: int, volume: float, pickupMode: int = 0) -> dict:
    """Run mixer.setTrackVolume inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "volume": volume, "pickupMode": pickupMode}, {"index": "i", "volume": "n", "pickupMode": "i"})
    if bad:
        return bad
    return _run(mixer.setTrackVolume, index, volume, pickupMode)
