import playlist


def op_playlist_get_song_start_tick_pos() -> dict:
    """Run playlist.getSongStartTickPos inside FL Studio and return the outcome as a result dict."""
    return _run(playlist.getSongStartTickPos)
