import mixer


def op_mixer_get_current_tempo(asInt: bool = False) -> dict:
    """Run mixer.getCurrentTempo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"asInt": asInt}, {"asInt": "b"})
    if bad:
        return bad
    return _run(mixer.getCurrentTempo, asInt)
