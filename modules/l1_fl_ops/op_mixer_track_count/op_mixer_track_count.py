import mixer


def op_mixer_track_count() -> dict:
    """Run mixer.trackCount inside FL Studio and return the outcome as a result dict."""
    return _run(mixer.trackCount)
