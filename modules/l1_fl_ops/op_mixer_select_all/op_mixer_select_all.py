import mixer


def op_mixer_select_all() -> dict:
    """Run mixer.selectAll inside FL Studio and return the outcome as a result dict."""
    return _run(mixer.selectAll)
