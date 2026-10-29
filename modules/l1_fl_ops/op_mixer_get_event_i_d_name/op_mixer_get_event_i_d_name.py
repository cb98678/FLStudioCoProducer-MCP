import mixer


def op_mixer_get_event_i_d_name(index: int, shortname: int = 0) -> dict:
    """Run mixer.getEventIDName inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"index": index, "shortname": shortname}, {"index": "i", "shortname": "i"})
    if bad:
        return bad
    return _run(mixer.getEventIDName, index, shortname)
