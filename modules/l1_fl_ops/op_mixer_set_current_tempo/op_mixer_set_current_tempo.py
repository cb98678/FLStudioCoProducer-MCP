import mixer


def op_mixer_set_current_tempo(tempo: int) -> dict:
    """Run mixer.setCurrentTempo inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"tempo": tempo}, {"tempo": "i"})
    if bad:
        return bad
    return _run(mixer.setCurrentTempo, tempo)
