import playlist


def op_playlist_scroll_to(a: int, b: int, c: int, d: int) -> dict:
    """Run playlist.scrollTo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"a": a, "b": b, "c": c, "d": d}, {"a": "i", "b": "i", "c": "i", "d": "i"})
    if bad:
        return bad
    return _run(playlist.scrollTo, a, b, c, d)
