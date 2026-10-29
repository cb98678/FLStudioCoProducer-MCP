import channels


def op_channels_selected_channel(canBeNone: bool = False, offset: int = 0, indexGlobal: bool = False) -> dict:
    """Run channels.selectedChannel inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"canBeNone": canBeNone, "offset": offset, "indexGlobal": indexGlobal}, {"canBeNone": "b", "offset": "i", "indexGlobal": "b"})
    if bad:
        return bad
    return _run(channels.selectedChannel, canBeNone, offset, indexGlobal)
