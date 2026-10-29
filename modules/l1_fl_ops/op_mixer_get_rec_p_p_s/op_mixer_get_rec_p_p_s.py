import mixer


def op_mixer_get_rec_p_p_s() -> dict:
    """Run mixer.getRecPPS inside FL Studio and return the outcome as a result dict."""
    return _run(mixer.getRecPPS)
