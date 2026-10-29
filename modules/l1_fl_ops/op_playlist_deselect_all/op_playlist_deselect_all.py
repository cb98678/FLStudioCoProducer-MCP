import playlist


def op_playlist_deselect_all() -> dict:
    """Run playlist.deselectAll inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.deselectAll)
