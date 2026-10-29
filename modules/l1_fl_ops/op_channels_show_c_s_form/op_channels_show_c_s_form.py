import channels


def op_channels_show_c_s_form(index: int, state: int = 1, useGlobalIndex: bool = False) -> dict:
    """Run channels.showCSForm inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "state": state, "useGlobalIndex": useGlobalIndex}, {"index": "i", "state": "i", "useGlobalIndex": "b"})
    if bad:
        return bad
    return _run(channels.showCSForm, index, state, useGlobalIndex)
