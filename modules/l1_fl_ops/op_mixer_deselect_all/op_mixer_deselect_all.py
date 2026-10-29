import mixer


def op_mixer_deselect_all() -> dict:
    """Run mixer.deselectAll inside FL Studio and return the outcome as a result dict."""
    return _run(mixer.deselectAll)
