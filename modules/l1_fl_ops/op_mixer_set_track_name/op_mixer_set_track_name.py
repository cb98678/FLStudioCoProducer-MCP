import mixer


def op_mixer_set_track_name(index: int, name: str) -> dict:
    """Run mixer.setTrackName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "name": name}, {"index": "i", "name": "s"})
    if bad:
        return bad
    return _run(mixer.setTrackName, index, name)
