import playlist


def op_playlist_track_count() -> dict:
    """Run playlist.trackCount inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.trackCount)
