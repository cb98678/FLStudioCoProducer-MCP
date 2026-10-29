import playlist


def op_playlist_get_vis_time_tick() -> dict:
    """Run playlist.getVisTimeTick inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.getVisTimeTick)
