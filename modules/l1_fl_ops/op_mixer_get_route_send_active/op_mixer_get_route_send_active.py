import mixer


def op_mixer_get_route_send_active(index: int, destIndex: int) -> dict:
    """Run mixer.getRouteSendActive inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "destIndex": destIndex}, {"index": "i", "destIndex": "i"})
    if bad:
        return bad
    return _run(mixer.getRouteSendActive, index, destIndex)
