import playlist


def op_playlist_get_display_zone() -> dict:
    """Run playlist.getDisplayZone inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.getDisplayZone)
