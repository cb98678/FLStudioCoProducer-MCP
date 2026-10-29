import playlist


def op_playlist_get_live_block_status(index: int, blockNum: int, mode: int = 0) -> dict:
    """Run playlist.getLiveBlockStatus inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "blockNum": blockNum, "mode": mode}, {"index": "i", "blockNum": "i", "mode": "i"})
    if bad:
        return bad
    return _run(playlist.getLiveBlockStatus, index, blockNum, mode)
