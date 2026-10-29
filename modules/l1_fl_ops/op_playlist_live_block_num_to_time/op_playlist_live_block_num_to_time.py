import playlist


def op_playlist_live_block_num_to_time(index: int) -> dict:
    """Run playlist.liveBlockNumToTime inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index}, {"index": "i"})
    if bad:
        return bad
    return _run(playlist.liveBlockNumToTime, index)
