import mixer


def op_mixer_is_track_swap_channels(index: int) -> dict:
    """Run mixer.isTrackSwapChannels inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.isTrackSwapChannels, index)
