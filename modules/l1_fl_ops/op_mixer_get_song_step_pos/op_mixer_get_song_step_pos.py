import mixer


def op_mixer_get_song_step_pos() -> dict:
    """Run mixer.getSongStepPos inside FL Studio and return the outcome as a result dict."""
    return _run(mixer.getSongStepPos)
