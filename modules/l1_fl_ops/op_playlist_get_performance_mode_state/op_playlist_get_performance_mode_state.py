import playlist


def op_playlist_get_performance_mode_state() -> dict:
    """Run playlist.getPerformanceModeState inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.getPerformanceModeState)
