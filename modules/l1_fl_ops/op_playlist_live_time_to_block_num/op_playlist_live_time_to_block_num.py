import playlist


def op_playlist_live_time_to_block_num(time: int) -> dict:
    """Run playlist.liveTimeToBlockNum inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"time": time}, {"time": "i"})
    if bad:
        return bad
    return _run(playlist.liveTimeToBlockNum, time)
