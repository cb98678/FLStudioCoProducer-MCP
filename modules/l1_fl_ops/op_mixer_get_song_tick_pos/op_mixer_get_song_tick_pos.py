import mixer


def op_mixer_get_song_tick_pos(mode: int = 0) -> dict:
    """Run mixer.getSongTickPos inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"mode": mode}, {"mode": "i"})
    if bad:
        return bad
    return _run(mixer.getSongTickPos, mode)
