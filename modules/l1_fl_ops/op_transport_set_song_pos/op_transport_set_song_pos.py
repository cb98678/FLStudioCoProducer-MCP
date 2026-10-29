import transport


def op_transport_set_song_pos(position: float, mode: int = -1) -> dict:
    """Run transport.setSongPos inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"position": position, "mode": mode}, {"position": "n", "mode": "j"})
    if bad:
        return bad
    return _run(transport.setSongPos, position, mode)
