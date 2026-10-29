import mixer


def op_mixer_set_route_to(index: int, destIndex: int, value: bool, updateUI: bool = False) -> dict:
    """Run mixer.setRouteTo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "destIndex": destIndex, "value": value, "updateUI": updateUI}, {"index": "i", "destIndex": "i", "value": "b", "updateUI": "b"})
    if bad:
        return bad
    return _run(mixer.setRouteTo, index, destIndex, value, updateUI)
