import playlist


def op_playlist_get_live_block_color(index: int, blockNum: int) -> dict:
    """Run playlist.getLiveBlockColor inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "blockNum": blockNum}, {"index": "i", "blockNum": "i"})
    if bad:
        return bad
    return _run(playlist.getLiveBlockColor, index, blockNum)
