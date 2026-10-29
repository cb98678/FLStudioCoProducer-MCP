import playlist


def op_playlist_get_vis_time_step() -> dict:
    """Run playlist.getVisTimeStep inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.getVisTimeStep)
