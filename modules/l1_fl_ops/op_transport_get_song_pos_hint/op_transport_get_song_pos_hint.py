import transport


def op_transport_get_song_pos_hint() -> dict:
    """Run transport.getSongPosHint inside FL Studio and return the outcome as a result dict."""
    return _run(transport.getSongPosHint)
