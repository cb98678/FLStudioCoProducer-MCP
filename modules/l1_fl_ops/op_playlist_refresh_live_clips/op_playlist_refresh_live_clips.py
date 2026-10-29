import playlist


def op_playlist_refresh_live_clips() -> dict:
    """Run playlist.refreshLiveClips inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.refreshLiveClips)
