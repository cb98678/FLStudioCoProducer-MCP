import playlist


def op_playlist_select_all() -> dict:
    """Run playlist.selectAll inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.selectAll)
