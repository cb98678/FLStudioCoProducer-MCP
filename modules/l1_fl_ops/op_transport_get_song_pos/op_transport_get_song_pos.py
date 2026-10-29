import transport


def op_transport_get_song_pos(mode: int = -1) -> dict:
    """Run transport.getSongPos inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"mode": mode}, {"mode": "j"})
    if bad:
        return bad
    return _run(transport.getSongPos, mode)
