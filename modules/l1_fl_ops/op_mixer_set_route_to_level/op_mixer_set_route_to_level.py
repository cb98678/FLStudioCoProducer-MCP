import mixer


def op_mixer_set_route_to_level(index: int, destIndex: int, level: float) -> dict:
    """Run mixer.setRouteToLevel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "destIndex": destIndex, "level": level}, {"index": "i", "destIndex": "i", "level": "n"})
    if bad:
        return bad
    return _run(mixer.setRouteToLevel, index, destIndex, level)
