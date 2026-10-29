import playlist


def op_playlist_get_vis_time_bar() -> dict:
    """Run playlist.getVisTimeBar inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.getVisTimeBar)
