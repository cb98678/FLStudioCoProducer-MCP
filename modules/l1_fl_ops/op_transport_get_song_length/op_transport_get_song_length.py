import transport


def op_transport_get_song_length(mode: int) -> dict:
    """Run transport.getSongLength inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"mode": mode}, {"mode": "i"})
    if bad:
        return bad
    return _run(transport.getSongLength, mode)
