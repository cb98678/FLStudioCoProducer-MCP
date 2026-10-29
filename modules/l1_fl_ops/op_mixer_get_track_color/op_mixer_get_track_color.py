import mixer


def op_mixer_get_track_color(index: int) -> dict:
    """Run mixer.getTrackColor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(mixer.getTrackColor, index)
