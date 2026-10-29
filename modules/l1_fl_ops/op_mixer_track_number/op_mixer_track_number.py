import mixer


def op_mixer_track_number() -> dict:
    """Run mixer.trackNumber inside FL Studio and return the outcome as a result dict."""
    return _run(mixer.trackNumber)
