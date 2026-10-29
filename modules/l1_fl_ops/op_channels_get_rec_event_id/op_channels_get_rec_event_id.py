import channels


def op_channels_get_rec_event_id(index: int, useGlobalIndex: bool = False) -> dict:
    """Run channels.getRecEventId inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "useGlobalIndex": useGlobalIndex}, {"index": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.getRecEventId, index, useGlobalIndex)
