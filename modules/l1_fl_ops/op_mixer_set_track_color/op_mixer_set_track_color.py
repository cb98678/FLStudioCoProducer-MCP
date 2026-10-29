import mixer


def op_mixer_set_track_color(index: int, color: int) -> dict:
    """Run mixer.setTrackColor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "color": color}, {"index": "i", "color": "i"})
    if bad:
        return bad
    return _run(mixer.setTrackColor, index, color)
